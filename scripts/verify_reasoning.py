import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from research_onboarding.taxonomy import Taxonomy
from research_onboarding.knowledge import KnowledgeStateManager
from research_onboarding.input_parser import UnseenInputParser
from research_onboarding.reasoning import PrerequisiteReasoningEngine


def run_tests():
    base_dir = Path(__file__).resolve().parent.parent
    state_path = base_dir / "knowledge" / "knowledge_state.json"
    tax_path = base_dir / "config" / "taxonomy.yaml"
    rules_path = base_dir / "config" / "mapping_rules.yaml"

    km = KnowledgeStateManager(state_path)
    state = km.load()
    tax = Taxonomy(tax_path, rules_path)
    parser = UnseenInputParser(tax)
    engine = PrerequisiteReasoningEngine(state)

    print("=" * 60)
    print("Test 1: Primary Unseen Paper (Adaptive RAG with Learned Necessity)")
    print("=" * 60)
    inp1 = parser.parse_file(base_dir / "examples" / "new_input.json")
    print("Matched Concepts:", inp1.matched_concepts)
    print("Matched Methods:", inp1.matched_methods)

    res1 = engine.generate_reading_path(inp1)
    print(f"Status: {res1['status']}")
    print(f"Total Reading Path Length: {len(res1['reading_path'])} papers")
    for item in res1["reading_path"]:
        print(f"  {item['order']}. [{item['year']}] {item['title']}")
        print(f"     Why: {item['why_needed']}")
        print(f"     Chain: {item['dependency_chain']}")

    print("\n" + "=" * 60)
    print("Test 2: Out-of-Domain Paper (Instant Neural Graphics Primitives)")
    print("=" * 60)
    inp2 = parser.parse_file(base_dir / "examples" / "new_input_no_match.json")
    res2 = engine.generate_reading_path(inp2)
    print(f"Status: {res2['status']}")
    print(f"Message: {res2['message']}")

    print("\n" + "=" * 60)
    print("Test 3: Secondary Unseen Paper (Hierarchical Context Compression)")
    print("=" * 60)
    inp3 = parser.parse_file(base_dir / "examples" / "new_input_hierarchical.json")
    res3 = engine.generate_reading_path(inp3)
    print(f"Status: {res3['status']}")
    print(f"Total Reading Path Length: {len(res3['reading_path'])} papers")
    for item in res3["reading_path"]:
        print(f"  {item['order']}. [{item['year']}] {item['title']}")

    # Assertions
    assert res1["status"] == "success"
    assert len(res1["reading_path"]) > 0
    assert res2["status"] == "out_of_domain"
    assert len(res2["reading_path"]) == 0
    assert res3["status"] == "success"
    assert len(res3["reading_path"]) > 0

    print("\nALL REASONING & INPUT PARSING TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    run_tests()
