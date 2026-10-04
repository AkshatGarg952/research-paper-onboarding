"""
Unit tests for Taxonomy and Mapping Rules (Phase 10)
"""

import pytest
from research_onboarding.taxonomy import TaxonomyValidator


def test_taxonomy_concepts_count(taxonomy):
    """Ensures at least 20 foundational concepts are defined."""
    assert len(taxonomy.concepts) >= 20
    assert "dense-passage-retrieval" in taxonomy.concepts
    assert "retrieval-augmented-generation" in taxonomy.concepts


def test_taxonomy_methods_count(taxonomy):
    """Ensures at least 15 architectural methods are defined."""
    assert len(taxonomy.methods) >= 15
    assert "rag-token" in taxonomy.methods
    assert "self-rag" in taxonomy.methods
    assert "crag" in taxonomy.methods


def test_concept_alias_matching(taxonomy):
    """Verifies concept matching using abbreviations and aliases."""
    text = "We compare against dual-encoder retrieval baselines."
    matches = taxonomy.match_concepts_in_text(text)
    assert "dense-passage-retrieval" in matches


def test_method_matching(taxonomy):
    """Verifies named method matching in text."""
    text = "Our system builds upon FiD and Self-RAG paradigms."
    matches = taxonomy.match_methods_in_text(text)
    assert "fid" in matches
    assert "self-rag" in matches


def test_no_cycles_in_prerequisites(taxonomy):
    """Enforces that the concept prerequisite graph is a strict DAG."""
    concept_graph = {cid: cdata.get("requires_understanding", []) for cid, cdata in taxonomy.concepts.items()}
    # Should not raise ValueError
    TaxonomyValidator.check_dag_cycles(concept_graph, "REQUIRES_UNDERSTANDING")


def test_cycle_detection_raises_error():
    """Confirms cycle detector actively catches circular dependencies."""
    cyclic_graph = {
        "A": ["B"],
        "B": ["C"],
        "C": ["A"]
    }
    with pytest.raises(ValueError, match="Cycle detected"):
        TaxonomyValidator.check_dag_cycles(cyclic_graph, "TEST_CYCLE")
