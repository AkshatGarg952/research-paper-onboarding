"""
Pytest configuration and shared fixtures for the test suite.
"""

import sys
from pathlib import Path
import pytest
import json

# Add src to python path
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from research_onboarding.taxonomy import Taxonomy
from research_onboarding.knowledge import KnowledgeStateManager
from research_onboarding.input_parser import UnseenInputParser
from research_onboarding.reasoning import PrerequisiteReasoningEngine


@pytest.fixture(scope="session")
def base_dir():
    return Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def taxonomy(base_dir):
    tax_path = base_dir / "config" / "taxonomy.yaml"
    rules_path = base_dir / "config" / "mapping_rules.yaml"
    return Taxonomy(tax_path, rules_path)


@pytest.fixture(scope="session")
def knowledge_state(base_dir):
    state_path = base_dir / "knowledge" / "knowledge_state.json"
    km = KnowledgeStateManager(state_path)
    return km.load()


@pytest.fixture(scope="session")
def reasoning_engine(knowledge_state):
    return PrerequisiteReasoningEngine(knowledge_state)


@pytest.fixture(scope="session")
def input_parser(taxonomy):
    return UnseenInputParser(taxonomy)
