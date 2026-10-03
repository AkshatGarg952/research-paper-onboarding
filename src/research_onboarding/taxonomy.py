"""
Taxonomy and Mapping Logic Module
Loads, validates, and manages the curated RAG ontology, concepts, methods,
and relationship schema. Enforces strict DAG acyclicity on prerequisite edges.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional, Set
import re
import yaml


class TaxonomyValidator:
    """Validates structural integrity and acyclicity of the curated taxonomy."""

    @staticmethod
    def check_dag_cycles(graph: Dict[str, List[str]], relation_name: str) -> None:
        """
        Enforces that the directed graph contains no cycles using DFS cycle detection.
        Raises ValueError if a cycle is found.
        """
        visited: Dict[str, int] = {}  # 0: unvisited, 1: visiting, 2: visited

        def dfs(node: str, path: List[str]):
            visited[node] = 1
            path.append(node)
            for neighbor in graph.get(node, []):
                if visited.get(neighbor, 0) == 1:
                    cycle = " -> ".join(path + [neighbor])
                    raise ValueError(f"Cycle detected in {relation_name} dependency graph: {cycle}")
                if visited.get(neighbor, 0) == 0:
                    dfs(neighbor, path)
            path.pop()
            visited[node] = 2

        for node in list(graph.keys()):
            if visited.get(node, 0) == 0:
                dfs(node, [])


class Taxonomy:
    """Represents the curated RAG knowledge taxonomy."""

    def __init__(self, taxonomy_path: Path, mapping_rules_path: Optional[Path] = None):
        self.taxonomy_path = Path(taxonomy_path)
        self.mapping_rules_path = Path(mapping_rules_path) if mapping_rules_path else None
        
        self.raw_data = self._load_yaml(self.taxonomy_path)
        self.rules_data = self._load_yaml(self.mapping_rules_path) if self.mapping_rules_path else {}

        self.concepts: Dict[str, Dict[str, Any]] = {c["id"]: c for c in self.raw_data.get("concepts", [])}
        self.methods: Dict[str, Dict[str, Any]] = {m["id"]: m for m in self.raw_data.get("methods", [])}

        self.validate()

    @staticmethod
    def _load_yaml(path: Optional[Path]) -> Dict[str, Any]:
        if not path or not path.exists():
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def validate(self) -> None:
        """Validates reference integrity and acyclicity across all entities."""
        # 1. Check concept prerequisite integrity
        concept_graph: Dict[str, List[str]] = {}
        for cid, cdata in self.concepts.items():
            reqs = cdata.get("requires_understanding", [])
            for r in reqs:
                if r not in self.concepts:
                    raise KeyError(f"Concept '{cid}' references unknown prerequisite concept '{r}'.")
            concept_graph[cid] = reqs

        TaxonomyValidator.check_dag_cycles(concept_graph, "REQUIRES_UNDERSTANDING")

        # 2. Check method extension integrity
        method_graph: Dict[str, List[str]] = {}
        for mid, mdata in self.methods.items():
            parent = mdata.get("extends_method")
            if parent:
                if parent not in self.methods:
                    raise KeyError(f"Method '{mid}' extends unknown parent method '{parent}'.")
                method_graph[mid] = [parent]
            else:
                method_graph[mid] = []

            # Check uses_concepts
            for ucid in mdata.get("uses_concepts", []):
                if ucid not in self.concepts:
                    raise KeyError(f"Method '{mid}' uses unknown concept '{ucid}'.")

        TaxonomyValidator.check_dag_cycles(method_graph, "EXTENDS")

    def match_concepts_in_text(self, text: str) -> List[str]:
        """
        Matches concepts mentioned in free text via canonical name and aliases
        using boundary-aware regex matching.
        """
        text_lower = text.lower()
        matched_ids: Set[str] = set()

        for cid, cdata in self.concepts.items():
            # Build search patterns: concept name + aliases
            candidates = [cdata["name"]] + cdata.get("aliases", [])
            for cand in candidates:
                # Safe regex escaping and word boundary check
                pattern = r"\b" + re.escape(cand.lower()) + r"\b"
                if re.search(pattern, text_lower):
                    matched_ids.add(cid)
                    break

        return sorted(list(matched_ids))

    def match_methods_in_text(self, text: str) -> List[str]:
        """
        Matches named methods mentioned in free text via method name and ID.
        """
        text_lower = text.lower()
        matched_ids: Set[str] = set()

        for mid, mdata in self.methods.items():
            candidates = [mdata["name"], mid.replace("-", " "), mid]
            for cand in candidates:
                pattern = r"\b" + re.escape(cand.lower()) + r"\b"
                if re.search(pattern, text_lower):
                    matched_ids.add(mid)
                    break

        return sorted(list(matched_ids))
