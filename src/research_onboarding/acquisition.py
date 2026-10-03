"""
Acquisition module for research papers.
Handles loading frozen corpus data, querying scholarly APIs, and validating boundary criteria.
"""

import json
import csv
from pathlib import Path
from typing import Dict, List, Optional, Any
import urllib.request
import urllib.error


class CorpusAcquisition:
    """Manages frozen corpus loading, verification, and API acquisition fallbacks."""

    def __init__(self, raw_path: Path, selection_path: Path):
        self.raw_path = Path(raw_path)
        self.selection_path = Path(selection_path)

    def load_raw_corpus(self) -> Dict[str, Any]:
        """Loads the raw frozen papers dataset."""
        if not self.raw_path.exists():
            raise FileNotFoundError(f"Raw corpus file not found at: {self.raw_path}")
        with open(self.raw_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_selection_manifest(self) -> List[Dict[str, str]]:
        """Loads the corpus selection CSV manifest with inclusion criteria."""
        if not self.selection_path.exists():
            raise FileNotFoundError(f"Selection CSV not found at: {self.selection_path}")
        records = []
        with open(self.selection_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)
        return records

    def fetch_semantic_scholar_metadata(self, paper_id_or_doi: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
        """
        Optional live fetch utility from Semantic Scholar Academic Graph API.
        Used as fallback or verification mechanism.
        """
        url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id_or_doi}?fields=title,abstract,authors,year,venue,citationCount,references"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "CalybAI-ResearchOnboarding/1.0"}
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status == 200:
                    return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            return None
        return None
