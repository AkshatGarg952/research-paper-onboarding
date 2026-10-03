"""
Execution script to build the canonical Knowledge State.
Reads data/processed/papers.jsonl and config/taxonomy.yaml,
executes KnowledgeMapper, and serializes knowledge/knowledge_state.json.
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from research_onboarding.taxonomy import Taxonomy
from research_onboarding.mapping import KnowledgeMapper
from research_onboarding.knowledge import KnowledgeStateManager


def main():
    base_dir = Path(__file__).resolve().parent.parent
    taxonomy_path = base_dir / "config" / "taxonomy.yaml"
    rules_path = base_dir / "config" / "mapping_rules.yaml"
    papers_path = base_dir / "data" / "processed" / "papers.jsonl"
    output_state_path = base_dir / "knowledge" / "knowledge_state.json"

    print("=" * 60)
    print("Building Canonical Knowledge State for Domain B (RAG Lineage)")
    print("=" * 60)

    # 1. Load taxonomy and rules
    print(f"Loading taxonomy from: {taxonomy_path}")
    taxonomy = Taxonomy(taxonomy_path, rules_path)
    print(f"Loaded {len(taxonomy.concepts)} concepts and {len(taxonomy.methods)} methods.")

    # 2. Load processed papers
    print(f"Loading processed corpus from: {papers_path}")
    papers = []
    with open(papers_path, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if line_str:
                papers.append(json.loads(line_str))
    print(f"Loaded {len(papers)} normalized papers.")

    # 3. Map entities and relationships
    print("Executing knowledge mapping...")
    mapper = KnowledgeMapper(taxonomy)
    entities, relationships = mapper.map_corpus(papers)

    # 4. Assemble and validate Knowledge State
    print("Assembling and validating Knowledge State...")
    manager = KnowledgeStateManager(output_state_path)
    state = manager.build_state(entities, relationships)

    # 5. Persist snapshot
    manager.save(output_state_path)

    stats = state["statistics"]
    print("\nKnowledge State Generation Successful!")
    print(f"Target file: {output_state_path}")
    print("\nSummary Statistics:")
    print(f"  - Total Papers: {stats['num_papers']}")
    print(f"  - Total Concepts: {stats['num_concepts']}")
    print(f"  - Total Methods: {stats['num_methods']}")
    print(f"  - Total Relationships: {stats['num_relationships']}")
    print("  - Breakdown by Relationship Type:")
    for rtype, count in stats["relationships_by_type"].items():
        print(f"      * {rtype}: {count}")


if __name__ == "__main__":
    main()
