# Approach — Design Decisions, Reasoning, and Tradeoffs

> **Calyb AI Domain B: Research Paper Onboarding**

This document explains every significant design decision made in this project: why I chose this topic, how I modeled knowledge, what I deliberately chose NOT to model, how the reasoning algorithm works, and what I would build next.

---

## 1. Problem Statement

A researcher entering the RAG subfield of NLP encounters a fundamental ordering problem. Papers in this field form a dependency graph: you cannot understand Self-RAG without understanding sparse and dense retrieval; you cannot understand dense retrieval without understanding bi-encoder architectures; you cannot understand bi-encoder architectures without understanding BERT. But no paper states these dependencies explicitly — they are implied, assumed, and invisible to a newcomer.

The concrete pain: a researcher is handed a paper (e.g., "Self-RAG: Learning to Retrieve, Generate, and Critique") and told to understand it before a meeting in a week. They read it, get lost at section 2.3 ("we build upon DPR-style dense retrieval and the FiD reader"), and then face an unguided search across a 70+ paper field.

The question this system answers: **given this paper, what is the minimal, dependency-ordered set of papers I must read first?**

---

## 2. Topic Choice

### Why RAG (2017–2024)?

**Well-bounded**: RAG is a precisely defined subfield — not "all of NLP" (too broad, ~10,000 papers), not "Self-RAG and its variants" (too narrow, ~8 papers). The boundary is naturally defined by the presence of both a retrieval component and a generation component in the same system.

**Rich prerequisite structure**: RAG methods explicitly build on each other in a traceable chain: Attention → BERT → DPR → RAG → FiD → RETRO → Atlas → Self-RAG → CRAG. This dependency structure is not hypothetical — it is explicitly cited, described, and inherited in the papers themselves.

**Right corpus size**: Applying inclusion criteria (must introduce an architectural contribution or a concept that ≥3 RAG papers depend on) yields 77 papers — comfortably within 50–100 and large enough to demonstrate non-trivial prerequisite chains.

**Genuine value**: The prerequisite-reading-path problem is not contrived. It is the real experience of anyone entering a technical subfield, and the answer is genuinely useful rather than just a demonstration artifact.

### Why not other topics?

I considered knowledge graph completion (too broad, multiple disconnected subfields), dialogue systems (prerequisite chains are shallower — most papers are self-contained), and continual learning (smaller corpus, fewer multi-hop dependencies). RAG offered the best combination of corpus size, dependency depth, and traceability.

---

## 3. The Single Use Case

I deliberately chose **one** use case — Prerequisite Reading Path Generation — and optimized everything for it.

Alternative use cases I rejected:

| Use Case | Why Rejected |
|---|---|
| "What papers are similar to X?" | Requires semantic similarity — embeddings or LLM, kills determinism |
| "What are the trending topics in RAG?" | Requires temporal analysis, adds complexity without pedagogical value |
| "What papers should I read to understand concept X?" | Subsumed by the reading path use case |
| "Which authors should I follow?" | Author profiling: adds entity type, no pedagogical benefit |
| "What research gaps exist?" | Speculation, not grounded in the corpus |

Picking one use case forced every design decision to be justified against a single question: "Does this help answer 'what should I read first, and why?'" Components that didn't survive this filter were removed.

---

## 4. Knowledge Model

### Entity Types

**Paper**: The atomic unit. A paper is included only if it satisfies the corpus inclusion criteria. Each paper records its concepts discussed, methods introduced, and internal references (other corpus papers it explicitly cites).

**Concept**: An abstract, reusable idea that multiple papers depend on (e.g., `dense-passage-retrieval`, `cross-attention`, `in-context-learning`). I defined 25 concepts with:
- A human-written definition (not copied from abstracts)
- A list of aliases (e.g., "DPR" → `dense-passage-retrieval`)
- A `requires_understanding` list (which concepts must be understood first)

**Method**: A named architectural technique introduced by a specific paper (e.g., `fusion-in-decoder`, `self-rag`, `colbert`). I defined 20 methods, each linked to its introducing paper, its parent method (what it extends), and the concepts it uses.

### Why these three entity types?

I considered adding:

- **Author**: Rejected. Author expertise profiling is out of scope. Adding it would require building a co-authorship graph and expertise inference — a separate problem.
- **Dataset**: Rejected. Datasets (NQ, TriviaQA, MSMARCO) are referenced pervasively but rarely form prerequisite chains. Knowing "FiD was evaluated on NQ" doesn't help you understand FiD.
- **Venue/Conference**: Rejected. Venue information carries no prerequisite semantics.

### Relationship Types

I defined exactly 6 relationship types:

| Relationship | Direction | Meaning |
|---|---|---|
| `INTRODUCES_CONCEPT` | Paper → Concept | This paper is the canonical source for this concept |
| `INTRODUCES_METHOD` | Paper → Method | This paper is where this method was first described |
| `USES_CONCEPT` | Method → Concept | This method's architecture relies on this concept |
| `EXTENDS` | Method → Method | This method is a direct architectural extension of another |
| `REQUIRES_UNDERSTANDING` | Concept → Concept | You must understand concept B before concept A |
| `BUILDS_ON` | Paper → Paper | This paper explicitly extends or requires prior work |

**Why not `CITES`?** Citation is not the same as prerequisite. Papers cite related work (background context), ablations (competing baselines), and prior methods. Raw citation edges are noisy — they include papers that happen to be mentioned, not papers that are required reading. I only create `BUILDS_ON` when the citing paper's architecture or methodology actually depends on the cited work.

**Why not `RELATED_TO`?** Too vague. A generic "related to" edge carries no pedagogical information. Every edge in this system has a specific semantic: it tells the reasoning engine exactly *why* one paper depends on another.

### Evidence Requirements

Every relationship must have:
- `evidence`: a verbatim or paraphrased textual excerpt from the paper, or an explicit rule from `mapping_rules.yaml`
- `confidence`: `high` (explicit mention), `medium` (structural inference), or `low` (general thematic dependency)

No relationship exists without evidence. This constraint prevents the mapper from hallucinating connections.

---

## 5. What I Chose NOT to Model

| Omitted Element | Reason |
|---|---|
| Author entities | No prerequisite semantics; adds complexity without reading-path value |
| Dataset entities | Referenced pervasively but form no prerequisite chains |
| Temporal "trend" edges | No pedagogical value for reading order |
| Semantic similarity edges | Would require embeddings — kills determinism and inspectability |
| Confidence scores on papers (impact, H-index) | Not relevant to prerequisite ordering |
| Full paper text | Not available for all papers; abstract + metadata is sufficient for concept matching |

The knowledge model is minimal by design. Each entity type and relationship type exists because it directly participates in answering the reading-path question.

---

## 6. Knowledge Construction

### Step 1: Corpus Collection (`scripts/build_corpus.py`)

Papers were fetched from the Semantic Scholar API using seed paper IDs for known RAG milestones. Each candidate paper was then evaluated against inclusion/exclusion criteria. Borderline cases were resolved manually and documented in `data/selection/corpus.csv` with a one-line justification.

### Step 2: Normalization (`scripts/normalize_corpus.py`)

Raw API responses were cleaned: title normalization (trim, lowercase comparison for dedup), abstract cleaning (remove HTML artifacts), author list normalization (first + last name only), and venue canonicalization. Output: `data/processed/papers.jsonl`.

### Step 3: Taxonomy Construction (`config/taxonomy.yaml`)

The taxonomy was hand-curated. I did not use an LLM to generate the taxonomy schema. Concept and method definitions were written by hand after reading each paper. Aliases were added by observing the actual terms used in abstracts (e.g., "dense retrieval", "DPR-style retrieval", "bi-encoder retrieval" all map to `dense-passage-retrieval`).

### Step 4: Mapping (`src/research_onboarding/mapping.py`)

The mapper links papers to entities by:
1. Keyword + alias matching: scanning each paper's title and abstract for concept/method mentions
2. Explicit taxonomy rules: the taxonomy specifies which paper introduced each method (`introduced_by` field)
3. `mapping_rules.yaml` specifies when to create each relationship type and what evidence to record

### Step 5: Knowledge State Assembly (`src/research_onboarding/knowledge.py`)

The mapper's output (entities + relationships) is assembled into a canonical JSON snapshot with schema validation. Every relationship endpoint is verified against the entity set — no dangling references are allowed.

---

## 7. LLM Usage

LLMs were used in **one bounded step only**: concept mention extraction during corpus construction.

Specifically: for each paper, I prompted an LLM to identify which concepts from the taxonomy the abstract was discussing. This was a classification task ("which of these 25 concepts appear in this abstract?") — not schema design, not edge creation, not reasoning.

**LLM was NOT used for:**
- Defining entity types or relationship types (done by me, reasoning about the use case)
- Creating relationship edges (done by the deterministic mapper)
- Query-time reasoning (done by the topological sort engine)
- Generating concept definitions or aliases (done by reading the source papers)

The LLM's output during extraction was treated as a suggestion, not ground truth. Every concept mapping was verified against the actual paper text.

**Why this boundary?**

If an LLM were used at query time, the output would be:
- Non-deterministic: the same input would yield different paths on different runs
- Non-inspectable: you couldn't trace why a paper was included in the reading path
- Fragile: the system would degrade silently when the LLM's context window fills or when it hallucinates a dependency

The assignment's phrase "Knowledge State must be independently inspectable" was a strong signal: the evaluators want to be able to read the JSON and verify every claim. An LLM-generated graph fails this test.

---

## 8. New Input Handling

When a user provides an unseen paper, the system:

1. **Verifies it is not in the corpus** (`input_parser.py`): title matching against all 77 corpus paper titles. If it matches, the system raises a `CorpusContaminationError`.
2. **Extracts concept mentions** (`input_parser.py`): keyword + alias matching against the taxonomy's 25 concepts. Each concept mention records the matching keyword found in the abstract.
3. **Identifies method mentions** (`input_parser.py`): similarly, scans for method names and aliases.
4. **Passes to the reasoning engine** with the matched concept and method IDs.

The unseen paper itself is **never added to the Knowledge State**. It is processed as a query against the existing state. This preserves the canonical nature of the Knowledge State and ensures the reasoning output is reproducible.

---

## 9. Reasoning Algorithm

The core algorithm is a two-phase graph traversal followed by topological sort.

### Phase 1: Seed Collection

For each concept `C` mentioned in the new paper's abstract:
- Find the paper that `INTRODUCES_CONCEPT` C → add to seed set
- Find all concepts `P` where `C` REQUIRES_UNDERSTANDING `P` → recursively include `P` and its introducer

For each method `M` mentioned:
- Find the paper that `INTRODUCES_METHOD` M → add to seed set
- Find all concepts `M` USES_CONCEPT → recursively include those concepts and their introducers
- Follow `EXTENDS` chain: if M extends M', include M's introducer and recurse into M'

For each paper `P` in the seed set:
- Follow `BUILDS_ON` edges: if P BUILDS_ON Q, add Q to seed set

### Phase 2: Transitive Expansion

Repeat Phase 1 until no new papers are added (fixed-point iteration). This ensures all transitive dependencies are captured even when concepts form multi-hop chains.

### Phase 3: Topological Sort (Kahn's Algorithm)

Build a dependency graph over the seed paper set using `BUILDS_ON` edges. Run Kahn's algorithm (BFS-based topological sort):

1. Compute in-degree for each paper (number of other seed papers it BUILDS_ON)
2. Start with papers that have in-degree 0 (no dependencies on other seed papers)
3. Process papers in BFS order, decrementing in-degrees
4. Ties broken by publication year (earlier paper listed first)

The result is a reading list where paper `i` in the list does not depend on paper `j` where `j > i`. The reader can proceed linearly without backtracking.

### Evidence Attribution

For each paper in the reading path, the output records:
- Which concepts from the new paper triggered this paper's inclusion
- Which relationship type(s) created the dependency
- The textual evidence from the Knowledge State that justifies each relationship

This makes the reading path fully auditable: the user can inspect exactly why each paper was included.

---

## 10. Tradeoffs and Limitations

### Scope: RAG-only

The taxonomy and corpus are RAG-specific. A paper about reinforcement learning, computer vision, or even a different NLP subfield will receive "no prerequisites identified" — not because it has no prerequisites, but because none of its concepts are in the RAG taxonomy. This is a deliberate scope constraint, not a bug.

**What this means**: The system is a deep specialist for one domain, not a general research assistant. This was the right tradeoff for a 77-paper corpus with a single well-defined use case.

### Keyword Matching Limitations

Concept matching uses keyword and alias matching against a curated list, not semantic similarity. This means:

- **Novel paraphrases will be missed**: If a 2025 paper describes dense retrieval as "vector-space passage lookup", it won't match `dense-passage-retrieval`.
- **Disambiguation is absent**: "attention" could mean self-attention (transformer) or cross-attention (FiD) or sparse attention. The matcher will include all concepts whose aliases appear, which may over-include.

The upside: zero false positives from LLM hallucination, and the alias list is directly auditable.

### Manual Curation Doesn't Scale

The `REQUIRES_UNDERSTANDING` edges between concepts and the `EXTENDS` edges between methods were manually curated. For 77 papers and 25 concepts, this was feasible (~4 hours). For a 500-paper corpus, this would require either a much larger manual effort or a hybrid approach (LLM-assisted suggestion + human validation).

### Reading Path Ignores Reader's Existing Knowledge

The current system assumes the reader starts from zero. If a reader already knows BERT and transformers, including those in the reading path wastes their time. The system has no mechanism to accept a "known concepts" profile.

### No Confidence-Weighted Ordering

All `BUILDS_ON` edges have the same weight in the topological sort. In practice, some dependencies are stronger than others (FiD fundamentally requires DPR; Self-RAG loosely builds on RAG). A weighted sort could prioritize the critical path over peripheral dependencies.

---

## 11. What I Would Build Next

In priority order:

**Reader knowledge profile** — Accept a list of concepts or papers the reader already knows and subtract them from the reading path. This turns the system from "read everything from zero" to "read only what you don't know". Mechanically straightforward: filter the seed set before topological sort.

**Confidence-weighted edges** — Assign weights to `BUILDS_ON` edges (strong architectural dependency vs. loose thematic connection). Use weighted topological sort to surface the critical path first, with optional peripheral papers marked as "recommended but not required."

**Automatic corpus expansion** — Given a new paper, suggest whether it qualifies for corpus inclusion by checking whether it introduces a new concept or method not yet in the taxonomy. Semi-automate the inclusion decision, with human review of the suggestion.

**Concept difficulty estimation** — Annotate each concept with a difficulty level (introductory, intermediate, advanced) based on how many prerequisite concepts it requires. Use this to estimate the total cognitive load of a reading path and surface a "minimum viable path" vs. a "comprehensive path."

**Multi-domain support** — Extend the taxonomy to a second NLP subfield (e.g., instruction tuning or RLHF). Validate that the entity model and reasoning algorithm generalize without modification — the only change should be the taxonomy YAML and corpus.

---

## Summary

| Decision | Choice | Rationale |
|---|---|---|
| Topic | RAG in NLP, 2017–2024, 77 papers | Well-bounded, rich prerequisite structure, right corpus size |
| Use case | Prerequisite reading path generation | Single high-value output, drives every design decision |
| Entity types | Paper, Concept, Method | Minimum set that supports prerequisite reasoning |
| Relationship types | 6 typed, directional edges | Each has distinct semantics for the reasoning algorithm |
| Reasoning | Deterministic graph traversal + Kahn's sort | Reproducible, inspectable, zero LLM at query time |
| LLM use | Extraction only (concept mention detection) | Bounded, verifiable, never for schema or reasoning |
| Knowledge State | Flat JSON, human-readable | Independently inspectable without code or setup |
| Scope | RAG-only | Deep specialist beats shallow generalist for 77-paper corpus |
