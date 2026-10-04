"""
Input Parser Module for Unseen Papers (Phase 6)
Parses, validates, and taxonomically maps new, unseen research papers without
mutating or contaminating the existing Knowledge State.
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass, field
import json

from research_onboarding.taxonomy import Taxonomy


@dataclass
class UnseenPaperInput:
    """Represents a validated unseen paper submitted for onboarding analysis."""
    title: str
    abstract: str
    year: Optional[int] = None
    authors: List[str] = field(default_factory=list)
    venue: Optional[str] = None
    matched_concepts: List[str] = field(default_factory=list)
    matched_methods: List[str] = field(default_factory=list)

    @property
    def is_in_domain(self) -> bool:
        """Returns True if at least one RAG concept or method was matched."""
        return len(self.matched_concepts) > 0 or len(self.matched_methods) > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "abstract": self.abstract,
            "year": self.year,
            "authors": self.authors,
            "venue": self.venue,
            "matched_concepts": self.matched_concepts,
            "matched_methods": self.matched_methods,
            "is_in_domain": self.is_in_domain
        }


class UnseenInputParser:
    """Parses raw JSON or free text inputs and extracts taxonomic entities."""

    def __init__(self, taxonomy: Taxonomy):
        self.taxonomy = taxonomy

    def parse_file(self, file_path: Path) -> UnseenPaperInput:
        """Parses a JSON file representing a new unseen paper."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Input paper file not found at: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return self.parse_dict(data)

    def parse_dict(self, data: Dict[str, Any]) -> UnseenPaperInput:
        """Parses a dictionary input representing paper metadata."""
        title = data.get("title", "").strip()
        abstract = data.get("abstract", "").strip()

        if not title and not abstract:
            raise ValueError("Input paper must contain at least a 'title' or 'abstract'.")

        combined_text = f"{title} {abstract}"
        matched_concepts = self.taxonomy.match_concepts_in_text(combined_text)
        matched_methods = self.taxonomy.match_methods_in_text(combined_text)

        return UnseenPaperInput(
            title=title,
            abstract=abstract,
            year=data.get("year"),
            authors=data.get("authors", []),
            venue=data.get("venue"),
            matched_concepts=matched_concepts,
            matched_methods=matched_methods
        )

    def parse_abstract(self, abstract: str, title: Optional[str] = None) -> UnseenPaperInput:
        """Direct helper to parse raw abstract text from CLI arguments."""
        return self.parse_dict({
            "title": title or "Interactive Input Paper",
            "abstract": abstract
        })
