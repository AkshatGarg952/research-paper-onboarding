"""
Unit tests for Knowledge State Structure and Independent Inspectability (Phase 10)
"""

import pytest
from research_onboarding.knowledge import KnowledgeStateManager


def test_knowledge_state_top_level_fields(knowledge_state):
    """Verifies all mandatory top-level schema fields are present."""
    required = ["schema_version", "topic", "use_case", "statistics", "entities", "relationships"]
    for field in required:
        assert field in knowledge_state, f"Missing top-level field: {field}"


def test_knowledge_state_statistics(knowledge_state):
    """Verifies statistical counts match actual entity lists."""
    stats = knowledge_state["statistics"]
    entities = knowledge_state["entities"]
    relationships = knowledge_state["relationships"]

    assert stats["num_papers"] == len(entities["papers"])
    assert stats["num_concepts"] == len(entities["concepts"])
    assert stats["num_methods"] == len(entities["methods"])
    assert stats["num_relationships"] == len(relationships)
    assert stats["num_papers"] >= 50, "Corpus must meet 50-100 paper boundary."


def test_all_relationship_types_represented(knowledge_state):
    """Ensures all 6 relationship types defined in the schema are instantiated."""
    expected_types = {
        "INTRODUCES_CONCEPT",
        "INTRODUCES_METHOD",
        "USES_CONCEPT",
        "EXTENDS",
        "REQUIRES_UNDERSTANDING",
        "BUILDS_ON"
    }
    present_types = {r["type"] for r in knowledge_state["relationships"]}
    missing = expected_types - present_types
    assert not missing, f"Missing relationship types in Knowledge State: {missing}"


def test_invalid_state_validation_raises_error():
    """Confirms KnowledgeStateManager rejects corrupted or missing fields."""
    km = KnowledgeStateManager()
    corrupted_state = {"schema_version": "1.0"}  # missing other fields
    with pytest.raises(ValueError, match="missing mandatory top-level field"):
        km.validate_state(corrupted_state)
