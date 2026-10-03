"""
Knowledge State Manager
Builds, validates, serializes, and inspects the canonical Knowledge State.
Guarantees independent inspectability and transparent provenance.
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime, timezone
import json


class KnowledgeStateManager:
    """Handles serialization, validation, and querying of the Knowledge State."""

    SCHEMA_VERSION = "1.0"
    TOPIC = "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks (2017-2024)"
    USE_CASE = "Prerequisite Reading Path Generation"

    def __init__(self, state_path: Optional[Path] = None):
        self.state_path = Path(state_path) if state_path else None
        self.data: Dict[str, Any] = {}

    def build_state(self, entities: Dict[str, Any], relationships: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assembles and validates the canonical Knowledge State dictionary."""
        stats = {
            "num_papers": len(entities.get("papers", [])),
            "num_concepts": len(entities.get("concepts", [])),
            "num_methods": len(entities.get("methods", [])),
            "num_relationships": len(relationships),
            "relationships_by_type": {}
        }

        for rel in relationships:
            rtype = rel.get("type", "UNKNOWN")
            stats["relationships_by_type"][rtype] = stats["relationships_by_type"].get(rtype, 0) + 1

        self.data = {
            "schema_version": self.SCHEMA_VERSION,
            "topic": self.TOPIC,
            "use_case": self.USE_CASE,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "statistics": stats,
            "entities": entities,
            "relationships": relationships
        }

        self.validate_state(self.data)
        return self.data

    def validate_state(self, state: Dict[str, Any]) -> None:
        """Validates schema requirements and relationship references."""
        for field in ["schema_version", "topic", "use_case", "statistics", "entities", "relationships"]:
            if field not in state:
                raise ValueError(f"Knowledge state missing mandatory top-level field: '{field}'")

        entities = state["entities"]
        paper_ids = {p["paper_id"] for p in entities.get("papers", [])}
        concept_ids = {c["id"] for c in entities.get("concepts", [])}
        method_ids = {m["id"] for m in entities.get("methods", [])}

        # Check relationships
        for rel in state["relationships"]:
            for req in ["id", "type", "from_type", "from_id", "to_type", "to_id", "evidence", "confidence"]:
                if req not in rel:
                    raise ValueError(f"Relationship {rel.get('id')} missing required field '{req}'")

            # Verify endpoints
            ftype, fid = rel["from_type"], rel["from_id"]
            ttype, tid = rel["to_type"], rel["to_id"]

            valid_from = (
                (ftype == "paper" and fid in paper_ids) or
                (ftype == "concept" and fid in concept_ids) or
                (ftype == "method" and fid in method_ids)
            )
            valid_to = (
                (ttype == "paper" and tid in paper_ids) or
                (ttype == "concept" and tid in concept_ids) or
                (ttype == "method" and tid in method_ids)
            )

            if not valid_from:
                raise ValueError(f"Relationship {rel['id']} has invalid source {ftype}:{fid}")
            if not valid_to:
                raise ValueError(f"Relationship {rel['id']} has invalid target {ttype}:{tid}")

    def save(self, output_path: Optional[Path] = None) -> Path:
        """Saves current state to formatted, human-readable JSON."""
        target = Path(output_path) if output_path else self.state_path
        if not target:
            raise ValueError("No target path provided to save Knowledge State.")

        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

        return target

    def load(self, input_path: Optional[Path] = None) -> Dict[str, Any]:
        """Loads and validates an existing Knowledge State JSON file."""
        source = Path(input_path) if input_path else self.state_path
        if not source or not source.exists():
            raise FileNotFoundError(f"Knowledge state file not found at: {source}")

        with open(source, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        self.validate_state(self.data)
        return self.data
