"""
Command-Line Interface (Phase 9)
Provides minimal, testable CLI entry points to evaluate unseen papers, inspect the
Knowledge State, and rebuild canonical artifacts.
"""

import sys
import argparse
import json
from pathlib import Path

from research_onboarding.taxonomy import Taxonomy
from research_onboarding.knowledge import KnowledgeStateManager
from research_onboarding.input_parser import UnseenInputParser
from research_onboarding.reasoning import PrerequisiteReasoningEngine
from research_onboarding.output import StructuredOutputFormatter
from research_onboarding.mapping import KnowledgeMapper


def get_base_paths():
    """Resolves standard repository paths."""
    base_dir = Path(__file__).resolve().parent.parent.parent
    return {
        "taxonomy": base_dir / "config" / "taxonomy.yaml",
        "rules": base_dir / "config" / "mapping_rules.yaml",
        "papers": base_dir / "data" / "processed" / "papers.jsonl",
        "knowledge_state": base_dir / "knowledge" / "knowledge_state.json"
    }


def handle_onboard(args):
    """Processes an unseen research paper and outputs the reading path."""
    paths = get_base_paths()
    if not paths["knowledge_state"].exists():
        print(f"Error: Knowledge State not found at {paths['knowledge_state']}. Run 'build' first.", file=sys.stderr)
        sys.exit(1)

    # 1. Load state and taxonomy
    km = KnowledgeStateManager(paths["knowledge_state"])
    state = km.load()
    tax = Taxonomy(paths["taxonomy"], paths["rules"])

    # 2. Parse input
    parser = UnseenInputParser(tax)
    if args.input_file:
        inp = parser.parse_file(Path(args.input_file))
    elif args.abstract:
        inp = parser.parse_abstract(args.abstract, title=args.title)
    else:
        print("Error: Must provide either an input file path or --abstract.", file=sys.stderr)
        sys.exit(1)

    # 3. Execute reasoning
    engine = PrerequisiteReasoningEngine(state)
    raw_result = engine.generate_reading_path(inp)

    # 4. Format output
    if args.json:
        canonical_json = StructuredOutputFormatter.format_json_output(raw_result)
        print(json.dumps(canonical_json, indent=2, ensure_ascii=False))
    else:
        console_report = StructuredOutputFormatter.format_console_report(raw_result)
        print(console_report)


def handle_inspect(args):
    """Inspects elements of the canonical Knowledge State."""
    paths = get_base_paths()
    if not paths["knowledge_state"].exists():
        print(f"Error: Knowledge State not found at {paths['knowledge_state']}.", file=sys.stderr)
        sys.exit(1)

    km = KnowledgeStateManager(paths["knowledge_state"])
    state = km.load()

    if args.stats:
        stats = state.get("statistics", {})
        print("=" * 50)
        print("Knowledge State Statistics")
        print("=" * 50)
        print(f"Topic:        {state.get('topic')}")
        print(f"Schema:       v{state.get('schema_version')}")
        print(f"Papers:       {stats.get('num_papers')}")
        print(f"Concepts:     {stats.get('num_concepts')}")
        print(f"Methods:      {stats.get('num_methods')}")
        print(f"Relationships: {stats.get('num_relationships')}")
        print("\nBreakdown by Relationship Type:")
        for k, v in stats.get("relationships_by_type", {}).items():
            print(f"  - {k:<25}: {v}")
        print("=" * 50)

    elif args.concept:
        cid = args.concept.strip().lower()
        concepts = {c["id"]: c for c in state["entities"]["concepts"]}
        if cid not in concepts:
            print(f"Concept '{cid}' not found. Available concepts:\n  " + ", ".join(sorted(concepts.keys())))
            sys.exit(1)
        c = concepts[cid]
        print("=" * 50)
        print(f"Concept: {c['name']} [{c['id']}]")
        print("=" * 50)
        print(f"Definition:     {c['definition']}")
        print(f"Aliases:        {', '.join(c.get('aliases', [])) or 'None'}")
        print(f"Introduced By:  {c.get('introduced_by')}")
        print(f"Prerequisites:  {', '.join(c.get('requires_understanding', [])) or 'None'}")
        print("=" * 50)

    elif args.paper:
        pid = args.paper.strip()
        papers = {p["paper_id"]: p for p in state["entities"]["papers"]}
        if pid not in papers:
            print(f"Paper '{pid}' not found.")
            sys.exit(1)
        p = papers[pid]
        print("=" * 50)
        print(f"Paper: [{p['paper_id']}]")
        print(f"Title: {p['title']} ({p['year']})")
        print("=" * 50)
        print(f"Venue:               {p.get('venue')}")
        print(f"Authors:             {', '.join(p.get('authors', []))}")
        print(f"Concepts Discussed:  {', '.join(p.get('concepts_discussed', []))}")
        print(f"Methods Introduced:  {', '.join(p.get('methods_introduced', [])) or 'None'}")
        print(f"Internal References: {', '.join(p.get('internal_references', [])) or 'None'}")
        print("=" * 50)

    else:
        print("Use 'inspect --stats', 'inspect --concept <id>', or 'inspect --paper <id>'.")


def handle_build(args):
    """Rebuilds the Knowledge State from processed corpus and taxonomy."""
    paths = get_base_paths()
    print("Rebuilding Knowledge State...")

    tax = Taxonomy(paths["taxonomy"], paths["rules"])
    papers = []
    with open(paths["papers"], "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                papers.append(json.loads(line))

    mapper = KnowledgeMapper(tax)
    entities, relationships = mapper.map_corpus(papers)

    km = KnowledgeStateManager(paths["knowledge_state"])
    km.build_state(entities, relationships)
    km.save()

    print(f"Successfully rebuilt Knowledge State at {paths['knowledge_state']}")


def main():
    parser = argparse.ArgumentParser(
        prog="research_onboarding",
        description="Calyb AI Domain B: Research Paper Onboarding & Reading Path Generation"
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # Onboard command
    onboard_parser = subparsers.add_parser("onboard", help="Analyze an unseen paper and generate reading path")
    onboard_parser.add_argument("input_file", nargs="?", help="Path to unseen paper JSON file")
    onboard_parser.add_argument("--abstract", help="Direct abstract string input")
    onboard_parser.add_argument("--title", help="Optional title for direct abstract input")
    onboard_parser.add_argument("--json", action="store_true", help="Output pure structured JSON")

    # Inspect command
    inspect_parser = subparsers.add_parser("inspect", help="Inspect Knowledge State entities and statistics")
    inspect_parser.add_argument("--stats", action="store_true", help="Display global statistics")
    inspect_parser.add_argument("--concept", help="Inspect a specific concept by ID")
    inspect_parser.add_argument("--paper", help="Inspect a specific paper by ID")

    # Build command
    build_parser = subparsers.add_parser("build", help="Rebuild the canonical Knowledge State")

    args = parser.parse_args()

    if args.subcommand == "onboard":
        handle_onboard(args)
    elif args.subcommand == "inspect":
        handle_inspect(args)
    elif args.subcommand == "build":
        handle_build(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
