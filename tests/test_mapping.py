"""
Unit tests for Knowledge Mapping and Evidence Provenance (Phase 10)
"""

import json


def test_all_methods_have_origin_papers(taxonomy, base_dir):
    """Ensures every method points to an actual paper in the corpus."""
    papers_path = base_dir / "data" / "processed" / "papers.jsonl"
    paper_ids = set()
    with open(papers_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                paper_ids.add(json.loads(line)["paper_id"])

    for mid, mdata in taxonomy.methods.items():
        origin = mdata.get("introduced_by")
        assert origin in paper_ids, f"Method '{mid}' references missing paper '{origin}'"


def test_no_orphan_concepts(taxonomy, knowledge_state):
    """Ensures every concept in the knowledge state is introduced by at least one paper."""
    relationships = knowledge_state["relationships"]
    introduced_concepts = {
        r["to_id"] for r in relationships if r["type"] == "INTRODUCES_CONCEPT"
    }
    for cid in taxonomy.concepts:
        assert cid in introduced_concepts, f"Concept '{cid}' has no INTRODUCES_CONCEPT relationship."


def test_evidence_presence_and_confidence(knowledge_state):
    """Guarantees every relationship contains non-empty textual evidence and valid confidence."""
    for rel in knowledge_state["relationships"]:
        evidence = rel.get("evidence", "").strip()
        confidence = rel.get("confidence")
        assert len(evidence) > 10, f"Relationship {rel['id']} has empty or inadequate evidence: '{evidence}'"
        assert confidence in ["high", "medium"], f"Relationship {rel['id']} has invalid confidence '{confidence}'"
