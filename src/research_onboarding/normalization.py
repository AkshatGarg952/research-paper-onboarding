"""
Corpus Normalization Module
Standardizes metadata, cleans abstract text, resolves intra-corpus reference links,
and produces the canonical data/processed/papers.jsonl dataset.
"""

import json
import re
import unicodedata
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple


VENUE_MAPPING = {
    "advances in neural information processing systems": "NeurIPS",
    "neural information processing systems": "NeurIPS",
    "neurips": "NeurIPS",
    "nips": "NeurIPS",
    "international conference on learning representations": "ICLR",
    "iclr": "ICLR",
    "international conference on machine learning": "ICML",
    "icml": "ICML",
    "association for computational linguistics": "ACL",
    "acl": "ACL",
    "emnlp": "EMNLP",
    "naacl": "NAACL",
    "eacl": "EACL",
    "findings of acl": "ACL Findings",
    "findings of emnlp": "EMNLP Findings",
    "transactions of the association for computational linguistics": "TACL",
    "tacl": "TACL",
    "transactions on machine learning research": "TMLR",
    "tmlr": "TMLR",
    "journal of machine learning research": "JMLR",
    "jmlr": "JMLR",
    "special interest group on information retrieval": "SIGIR",
    "sigir": "SIGIR",
    "automated knowledge base construction": "AKBC",
    "akbc": "AKBC",
    "aaai": "AAAI",
    "arxiv": "ArXiv",
    "openai": "Technical Report"
}


def clean_text(text: str) -> str:
    """Normalizes whitespace, unicode characters, and common typographic ligatures."""
    if not text:
        return ""
    # Normalize unicode to NFKC
    normalized = unicodedata.normalize("NFKC", text)
    # Collapse irregular whitespace
    collapsed = re.sub(r"\s+", " ", normalized).strip()
    return collapsed


def normalize_venue(venue_raw: str) -> str:
    """Maps varied venue strings to a canonical conference/journal name."""
    if not venue_raw:
        return "Preprint"
    cleaned = venue_raw.lower().strip()
    for pattern, canonical in VENUE_MAPPING.items():
        if pattern in cleaned:
            return canonical
    return venue_raw.strip()


def normalize_author_name(author: str) -> str:
    """Normalizes spacing and punctuation in author names."""
    cleaned = clean_text(author)
    # Ensure space after period in initials (e.g., 'J.Devlin' -> 'J. Devlin')
    cleaned = re.sub(r"\.([A-Za-z])", r". \1", cleaned)
    return cleaned


class CorpusNormalizer:
    """Validates, deduplicates, and resolves reference graphs for the paper corpus."""

    def __init__(self, raw_data_path: Path):
        self.raw_data_path = Path(raw_data_path)

    def load_raw(self) -> List[Dict[str, Any]]:
        with open(self.raw_data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("papers", [])

    def process(self) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        raw_papers = self.load_raw()
        seen_ids: Set[str] = set()
        seen_titles: Set[str] = set()
        normalized_papers: List[Dict[str, Any]] = []

        stats = {
            "total_raw": len(raw_papers),
            "duplicates_removed": 0,
            "malformed_skipped": 0,
            "valid_processed": 0,
            "resolved_internal_refs": 0,
            "external_refs_tagged": 0
        }

        # First pass: collect valid corpus IDs for reference resolution
        corpus_ids = {p.get("paper_id", "").strip() for p in raw_papers if p.get("paper_id")}

        for raw in raw_papers:
            pid = raw.get("paper_id", "").strip()
            title = clean_text(raw.get("title", ""))
            abstract = clean_text(raw.get("abstract", ""))
            year = raw.get("year")

            # Validation: must have id, title, abstract, and year
            if not pid or not title or not abstract or not year:
                stats["malformed_skipped"] += 1
                continue

            # Deduplication
            title_key = title.lower()
            if pid in seen_ids or title_key in seen_titles:
                stats["duplicates_removed"] += 1
                continue

            seen_ids.add(pid)
            seen_titles.add(title_key)

            # Authors normalization
            raw_authors = raw.get("authors", [])
            normalized_authors = [normalize_author_name(a) for a in raw_authors]

            # Venue normalization
            canonical_venue = normalize_venue(raw.get("venue", ""))

            # Reference graph resolution
            raw_refs = raw.get("references", [])
            internal_refs = []
            external_refs = []

            for ref in raw_refs:
                ref_clean = ref.strip()
                if ref_clean in corpus_ids:
                    internal_refs.append(ref_clean)
                    stats["resolved_internal_refs"] += 1
                else:
                    external_refs.append(ref_clean)
                    stats["external_refs_tagged"] += 1

            record = {
                "paper_id": pid,
                "arxiv_id": raw.get("arxiv_id", "").strip(),
                "title": title,
                "authors": normalized_authors,
                "year": int(year),
                "venue": canonical_venue,
                "abstract": abstract,
                "inclusion_criterion": raw.get("inclusion_criterion", "criterion_1"),
                "role_in_lineage": clean_text(raw.get("role_in_lineage", "")),
                "internal_references": internal_refs,
                "external_references": external_refs,
                "introduced_concepts": raw.get("introduced_concepts", []),
                "introduced_methods": raw.get("introduced_methods", [])
            }

            normalized_papers.append(record)

        stats["valid_processed"] = len(normalized_papers)
        return normalized_papers, stats

    def export_jsonl(self, output_path: Path) -> Dict[str, Any]:
        """Runs normalization and writes output to data/processed/papers.jsonl."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        normalized_papers, stats = self.process()

        with open(output_path, "w", encoding="utf-8") as f:
            for paper in normalized_papers:
                f.write(json.dumps(paper, ensure_ascii=False) + "\n")

        return stats
