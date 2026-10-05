# Research Paper Onboarding â€” Prerequisite Reading Path Generator

> **Calyb AI Engineering Intern Assignment â€” Domain B**

Given an unseen research paper (abstract + metadata), this system returns a **dependency-ordered reading list** of the RAG corpus papers you must read first â€” and explains exactly why each one is a prerequisite.


## What It Does

A new researcher entering the field of **Retrieval-Augmented Generation (RAG) in NLP** faces a disorienting landscape: 77 papers published between 2017â€“2024, each introducing methods that silently depend on concepts from earlier work. Reading them in the wrong order means hitting walls of assumed knowledge.

This system answers one question: **"What should I read first, and why?"**

**The core use case â€” Prerequisite Reading Path Generation:**

1. You provide an unseen paper (not in the corpus) as a JSON file with its title and abstract.
2. The system identifies which RAG concepts and methods the paper references.
3. It finds the foundational corpus papers that introduced those concepts/methods.
4. It resolves transitive dependencies (if concept A requires understanding concept B, the paper introducing B is included too).
5. It returns a **topologically sorted reading list** with per-paper evidence explaining why each paper is a prerequisite.

**Reasoning is fully deterministic** â€” no LLM is invoked at query time. The output for the same input is always identical.


## Quick Start

### 1. Install

```bash
pip install -e .
```

Requires Python â‰¥ 3.9. The only runtime dependency is `pyyaml`.

### 2. Run the demo

```bash
python -m research_onboarding.cli onboard examples/new_input.json
```

This processes the bundled example paper (a hypothetical "Adaptive RAG" paper not in the corpus) and prints a human-readable prerequisite reading path to stdout.

### 3. Get structured JSON output

```bash
python -m research_onboarding.cli onboard examples/new_input.json --json
```

### 4. Try an edge case (no RAG concepts detected)

```bash
python -m research_onboarding.cli onboard examples/new_input_no_match.json
```

The system gracefully returns a "no prerequisites identified" message â€” no crash, no hallucination.

### 5. Inspect the Knowledge State

```bash
# Global statistics
python -m research_onboarding.cli inspect --stats

# Inspect a specific concept
python -m research_onboarding.cli inspect --concept dense-passage-retrieval

# Inspect a specific paper
python -m research_onboarding.cli inspect --paper DPR2020
```

### 6. Rebuild the Knowledge State from scratch

```bash
python -m research_onboarding.cli build
```

### 7. Run tests

```bash
pytest tests/
```

All 21 tests pass in ~1.4s with no external dependencies.


## Repository Structure

```
Assignment/
â”œâ”€â”€ README.md                        # This file
â”œâ”€â”€ approach.md                      # Design decisions, tradeoffs, and reasoning
â”œâ”€â”€ pyproject.toml                   # Package config; entry point: `onboard` CLI
â”‚
â”œâ”€â”€ config/
â”‚   â”œâ”€â”€ topic.yaml                   # Topic definition + paper inclusion/exclusion criteria
â”‚   â”œâ”€â”€ taxonomy.yaml                # 25 concepts, 20 methods, aliases, definitions
â”‚   â””â”€â”€ mapping_rules.yaml           # Rules for constructing relationships + evidence requirements
â”‚
â”œâ”€â”€ data/
â”‚   â”œâ”€â”€ raw/
â”‚   â”‚   â””â”€â”€ papers_raw.json          # Raw Semantic Scholar API responses (77 papers)
â”‚   â”œâ”€â”€ processed/
â”‚   â”‚   â””â”€â”€ papers.jsonl             # Normalized paper corpus (one JSON object per line)
â”‚   â””â”€â”€ selection/
â”‚       â””â”€â”€ corpus.csv               # Paper selection log with inclusion justification per paper
â”‚
â”œâ”€â”€ docs/
â”‚   â””â”€â”€ decisions/
â”‚       â”œâ”€â”€ 001-scope.md             # ADR: Problem definition, scope lock, and non-goals
â”‚       â””â”€â”€ 002-knowledge-model.md   # ADR: Entity types, relationship types, and design reasoning
â”‚
â”œâ”€â”€ knowledge/
â”‚   â””â”€â”€ knowledge_state.json         # Canonical, inspectable Knowledge State snapshot
â”‚                                    # (77 papers, 25 concepts, 20 methods, 268 relationships)
â”‚
â”œâ”€â”€ scripts/
â”‚   â”œâ”€â”€ build_corpus.py              # Fetches papers from Semantic Scholar API + hand-curation
â”‚   â”œâ”€â”€ normalize_corpus.py          # Cleans and deduplicates raw paper data
â”‚   â”œâ”€â”€ build_knowledge.py           # Runs full mapping pipeline to generate knowledge_state.json
â”‚   â””â”€â”€ verify_reasoning.py          # Spot-checks the reasoning engine on bundled examples
â”‚
â”œâ”€â”€ src/research_onboarding/
â”‚   â”œâ”€â”€ __init__.py
â”‚   â”œâ”€â”€ acquisition.py               # Semantic Scholar API client
â”‚   â”œâ”€â”€ normalization.py             # Metadata normalization, dedup, and JSONL serialization
â”‚   â”œâ”€â”€ taxonomy.py                  # Load/query concepts, methods, aliases from taxonomy.yaml
â”‚   â”œâ”€â”€ mapping.py                   # Maps normalized papers â†’ entities + typed relationships
â”‚   â”œâ”€â”€ knowledge.py                 # Builds, validates, serializes the canonical Knowledge State
â”‚   â”œâ”€â”€ input_parser.py              # Parses unseen paper JSON + keyword-based concept matching
â”‚   â”œâ”€â”€ reasoning.py                 # Dependency expansion + Kahn's topological sort
â”‚   â”œâ”€â”€ output.py                    # Formats results as structured JSON or console report
â”‚   â””â”€â”€ cli.py                       # CLI entry point (onboard / inspect / build subcommands)
â”‚
â”œâ”€â”€ examples/
â”‚   â”œâ”€â”€ new_input.json               # Primary example: hypothetical "Adaptive RAG" paper
â”‚   â”œâ”€â”€ new_input_hierarchical.json  # Example triggering transitive dependency expansion
â”‚   â””â”€â”€ new_input_no_match.json      # Edge case: non-RAG paper (computer vision abstract)
â”‚
â””â”€â”€ tests/
    â”œâ”€â”€ conftest.py                  # Shared fixtures (loads knowledge state, taxonomy)
    â”œâ”€â”€ test_taxonomy.py             # Tests concept/method counts, alias matching, cycle detection
    â”œâ”€â”€ test_mapping.py              # Tests relationship integrity (no orphan concepts, dangling refs)
    â”œâ”€â”€ test_knowledge.py            # Tests Knowledge State schema, statistics, validation
    â”œâ”€â”€ test_reasoning.py            # Tests topological order, determinism, out-of-domain handling
    â””â”€â”€ test_end_to_end.py           # Full CLI integration tests
```


## Knowledge State

The file `knowledge/knowledge_state.json` is the core artifact of the system. It is a self-contained, human-readable JSON snapshot that encodes all knowledge about the RAG corpus:

```
77 papers | 25 concepts | 20 methods | 268 relationships
  - INTRODUCES_CONCEPT    : 25
  - INTRODUCES_METHOD     : 20
  - USES_CONCEPT          : 42
  - EXTENDS               : 17
  - REQUIRES_UNDERSTANDING: 31
  - BUILDS_ON             : 133
```

You can inspect it directly without running any code:

```bash
# Pretty-print the top-level structure
python -m json.tool knowledge/knowledge_state.json | head -30

# Count relationships by type
python -c "
import json
ks = json.load(open('knowledge/knowledge_state.json'))
print(ks['statistics'])
"
```

To rebuild it from the processed corpus and taxonomy:

```bash
python -m research_onboarding.cli build
# or equivalently:
python scripts/build_knowledge.py
```


## New Input Format

Unseen papers are provided as JSON files. The minimum required fields are `title` and `abstract`:

```json
{
  "title": "Adaptive Retrieval-Augmented Generation with Dynamic Context Windows",
  "abstract": "We propose Adaptive RAG, a framework that dynamically adjusts retrieval granularity based on query complexity. Building on dense passage retrieval and cross-attention fusion, our approach extends Self-RAG with an adaptive controller that selects between sparse BM25 retrieval and dense bi-encoder retrieval. Experiments on knowledge-intensive NLP benchmarks demonstrate improvements over FiD and Atlas baselines.",
  "year": 2024,
  "authors": ["A. Researcher", "B. Collaborator"]
}
```

Optional fields: `year`, `authors`, `arxiv_id`, `venue`.

The `title` must **not** match any paper already in the corpus (verified automatically). If the abstract contains no recognizable RAG concepts, the system returns a graceful "no prerequisites identified" response with an explanation.


## Configuration

### `config/topic.yaml`
Defines the topic boundary: the RAG subfield scope (2017â€“2024), paper inclusion criteria, exclusion criteria, and the 77 paper IDs in the frozen corpus.

### `config/taxonomy.yaml`
Hand-curated taxonomy containing:
- **25 concepts**: Each with `id`, `name`, `definition`, `aliases`, and `requires_understanding` (prerequisite concepts)
- **20 methods**: Each with `id`, `name`, `introduced_by` (paper ID), `extends` (parent method), and `uses_concepts`

### `config/mapping_rules.yaml`
Defines the 6 relationship types (`INTRODUCES_CONCEPT`, `INTRODUCES_METHOD`, `USES_CONCEPT`, `EXTENDS`, `REQUIRES_UNDERSTANDING`, `BUILDS_ON`) along with evidence requirements and confidence levels for each.


## Tests

```bash
pytest tests/ -v
```

**21 tests, all passing:**

| Test Module | What It Covers |
|---|---|
| `test_taxonomy.py` | Concept/method counts, alias matching, DAG cycle detection |
| `test_mapping.py` | No orphan concepts, all methods have introducing papers, evidence presence |
| `test_knowledge.py` | Schema validation, statistics accuracy, invalid-state rejection |
| `test_reasoning.py` | Topological ordering, determinism, out-of-domain and unseen-paper handling |
| `test_end_to_end.py` | Full CLI pipeline: onboard, JSON mode, inspect stats, inspect concept |


## Design Principles

- **No LLM at query time**: Reasoning is pure graph traversal. Reproducible, auditable, zero inference cost.
- **LLM used only for extraction**: During corpus construction, an LLM assisted with concept mention extraction from abstracts. It was never used for schema design or reasoning.
- **Every relationship has evidence**: No relationship exists without a textual excerpt or explicit rule that justifies it.
- **Independently inspectable**: `knowledge_state.json` is readable as plain JSON. No database, no embeddings, no setup required.
- **Single use case, done well**: The system does one thing â€” prerequisite reading path generation â€” and does it correctly for every case in the test suite.
