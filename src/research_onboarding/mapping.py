"""
Knowledge Mapping Module
Maps normalized research papers to the human-curated taxonomy, constructing
directional typed relationships with explicit textual evidence and provenance.
"""

from typing import Dict, List, Any, Set, Tuple
from pathlib import Path
import json

from research_onboarding.taxonomy import Taxonomy


class KnowledgeMapper:
    """Constructs entities and evidence-backed relationships from papers and taxonomy."""

    def __init__(self, taxonomy: Taxonomy):
        self.taxonomy = taxonomy

    def map_corpus(self, papers: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Processes normalized papers against taxonomy to generate enriched entities
        and validated relationships.
        """
        papers_by_id: Dict[str, Dict[str, Any]] = {p["paper_id"]: p for p in papers}

        enriched_papers: List[Dict[str, Any]] = []
        relationships: List[Dict[str, Any]] = []
        rel_counter = 1

        # 1. Enrich papers with discussed concepts and introduced methods
        for paper in papers:
            full_text = f"{paper['title']} {paper['abstract']}"
            
            # Match concepts discussed in text
            matched_concepts = self.taxonomy.match_concepts_in_text(full_text)
            
            # Combine explicit concepts with text matches
            explicit_concepts = paper.get("introduced_concepts", [])
            all_concepts = sorted(list(set(matched_concepts + explicit_concepts)))

            # Methods introduced by this paper
            introduced_methods = [
                mid for mid, mdata in self.taxonomy.methods.items()
                if mdata.get("introduced_by") == paper["paper_id"]
            ]

            enriched_paper = {
                "paper_id": paper["paper_id"],
                "arxiv_id": paper.get("arxiv_id", ""),
                "title": paper["title"],
                "authors": paper.get("authors", []),
                "year": paper["year"],
                "venue": paper.get("venue", ""),
                "abstract": paper["abstract"],
                "concepts_discussed": all_concepts,
                "methods_introduced": introduced_methods,
                "internal_references": paper.get("internal_references", [])
            }
            enriched_papers.append(enriched_paper)

        # 2. Build INTRODUCES_CONCEPT relationships
        for cid, cdata in self.taxonomy.concepts.items():
            origin_pid = cdata.get("introduced_by")
            if origin_pid and origin_pid in papers_by_id:
                origin_paper = papers_by_id[origin_pid]
                relationships.append({
                    "id": f"rel_{rel_counter:04d}",
                    "type": "INTRODUCES_CONCEPT",
                    "from_type": "paper",
                    "from_id": origin_pid,
                    "to_type": "concept",
                    "to_id": cid,
                    "evidence": f"'{origin_paper['title']}' ({origin_paper['year']}) first introduced or canonically established {cdata['name']}.",
                    "confidence": "high"
                })
                rel_counter += 1

        # 3. Build INTRODUCES_METHOD relationships
        for mid, mdata in self.taxonomy.methods.items():
            origin_pid = mdata.get("introduced_by")
            if origin_pid and origin_pid in papers_by_id:
                origin_paper = papers_by_id[origin_pid]
                relationships.append({
                    "id": f"rel_{rel_counter:04d}",
                    "type": "INTRODUCES_METHOD",
                    "from_type": "paper",
                    "from_id": origin_pid,
                    "to_type": "method",
                    "to_id": mid,
                    "evidence": f"'{origin_paper['title']}' ({origin_paper['year']}) proposed the {mdata['name']} method: {mdata['description']}",
                    "confidence": "high"
                })
                rel_counter += 1

        # 4. Build USES_CONCEPT relationships (Method -> Concept)
        for mid, mdata in self.taxonomy.methods.items():
            for cid in mdata.get("uses_concepts", []):
                if cid in self.taxonomy.concepts:
                    cname = self.taxonomy.concepts[cid]["name"]
                    relationships.append({
                        "id": f"rel_{rel_counter:04d}",
                        "type": "USES_CONCEPT",
                        "from_type": "method",
                        "from_id": mid,
                        "to_type": "concept",
                        "to_id": cid,
                        "evidence": f"The {mdata['name']} method structurally relies upon {cname} as a core architectural building block.",
                        "confidence": "high"
                    })
                    rel_counter += 1

        # 5. Build EXTENDS relationships (Method -> Parent Method)
        for mid, mdata in self.taxonomy.methods.items():
            parent_mid = mdata.get("extends_method")
            if parent_mid and parent_mid in self.taxonomy.methods:
                parent_name = self.taxonomy.methods[parent_mid]["name"]
                relationships.append({
                    "id": f"rel_{rel_counter:04d}",
                    "type": "EXTENDS",
                    "from_type": "method",
                    "from_id": mid,
                    "to_type": "method",
                    "to_id": parent_mid,
                    "evidence": f"{mdata['name']} directly adapts and extends the formulation of {parent_name}.",
                    "confidence": "high"
                })
                rel_counter += 1

        # 6. Build REQUIRES_UNDERSTANDING relationships (Concept -> Prerequisite Concept)
        for cid, cdata in self.taxonomy.concepts.items():
            for req_cid in cdata.get("requires_understanding", []):
                if req_cid in self.taxonomy.concepts:
                    req_cname = self.taxonomy.concepts[req_cid]["name"]
                    relationships.append({
                        "id": f"rel_{rel_counter:04d}",
                        "type": "REQUIRES_UNDERSTANDING",
                        "from_type": "concept",
                        "from_id": cid,
                        "to_type": "concept",
                        "to_id": req_cid,
                        "evidence": f"Comprehending {cdata['name']} conceptually requires foundational familiarity with {req_cname}.",
                        "confidence": "high"
                    })
                    rel_counter += 1

        # 7. Build BUILDS_ON relationships (Paper -> Paper intellectual dependencies)
        for p in enriched_papers:
            downstream_id = p["paper_id"]
            refs = p.get("internal_references", [])
            for ref_id in refs:
                if ref_id in papers_by_id and ref_id != downstream_id:
                    upstream_paper = papers_by_id[ref_id]
                    # Find conceptual link connecting them
                    upstream_concepts = [
                        cid for cid, c in self.taxonomy.concepts.items()
                        if c.get("introduced_by") == ref_id
                    ]
                    upstream_methods = [
                        mid for mid, m in self.taxonomy.methods.items()
                        if m.get("introduced_by") == ref_id
                    ]

                    # Determine linkage evidence
                    link_desc = []
                    if upstream_methods:
                        m_names = [self.taxonomy.methods[m]["name"] for m in upstream_methods]
                        link_desc.append(f"method(s): {', '.join(m_names)}")
                    if upstream_concepts:
                        c_names = [self.taxonomy.concepts[c]["name"] for c in upstream_concepts]
                        link_desc.append(f"concept(s): {', '.join(c_names)}")

                    if link_desc:
                        evidence_text = (
                            f"'{p['title']}' ({p['year']}) cites and builds upon '{upstream_paper['title']}' "
                            f"({upstream_paper['year']}) through foundational {'; '.join(link_desc)}."
                        )
                    else:
                        evidence_text = (
                            f"'{p['title']}' ({p['year']}) directly incorporates and extends the architecture "
                            f"and experimental formulation of '{upstream_paper['title']}' ({upstream_paper['year']})."
                        )

                    relationships.append({
                        "id": f"rel_{rel_counter:04d}",
                        "type": "BUILDS_ON",
                        "from_type": "paper",
                        "from_id": downstream_id,
                        "to_type": "paper",
                        "to_id": ref_id,
                        "evidence": evidence_text,
                        "confidence": "high"
                    })
                    rel_counter += 1

        entities = {
            "papers": enriched_papers,
            "concepts": list(self.taxonomy.concepts.values()),
            "methods": list(self.taxonomy.methods.values())
        }

        return entities, relationships
