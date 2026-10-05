# ADR 002: Knowledge Model Design, Schema, and Mapping Principles

- Status: Accepted
- Date: 2026-10-03
- Domain: Domain B (Research Paper Onboarding)
- Focused Area: Retrieval-Augmented Generation (RAG) in NLP (2017â€“2024)
- Core Use Case: Prerequisite Reading Path Generation for Unseen Papers


## 1. Context and Problem Statement

To generate a deterministic, pedagogical prerequisite reading path for an unseen paper, the system cannot rely on a flat document store or generic text similarity. It requires a structured knowledge representation that encodes:
1. Conceptual primitives: The foundational technical ideas in RAG (e.g., dense passage retrieval, cross-attention fusion).
2. Concrete algorithmic methods: The named systems that combine these primitives (e.g., DPR, FiD, Self-RAG).
3. Directional prerequisite dependencies: Which concepts or methods strictly require prior comprehension of other concepts or methods.
4. Attribution provenance: Which papers introduced which ideas, and what textual evidence justifies that claim.

The design challenge is striking the right level of abstraction: fine-grained enough to make meaningful distinctions between techniques, but focused enough to avoid cluttering the graph with extraneous metadata.


## 2. Core Entity Types

The model restricts itself to three first-class entity types.

### 2.1 Paper
The physical unit of literature.
- `paper_id` (string, primary key): Normalized slug (e.g., `lewis_2020`, `asai_2023_selfrag`).
- `title` (string): Full publication title.
- `authors` (list of strings): Normalized author names.
- `year` (integer): Publication year (2017â€“2024).
- `venue` (string): Canonical conference or journal.
- `abstract` (string): Full text abstract used for concept grounding and evidence extraction.
- `arxiv_id` (string, optional): External identifier for linking.

### 2.2 Concept
An abstract technical principle, architectural mechanism, or theoretical formulation. Concepts transcend individual papers; multiple papers may discuss or utilize the same concept.
- `concept_id` (string, primary key): Semantic slug (e.g., `dense-passage-retrieval`, `cross-attention-fusion`).
- `name` (string): Canonical display title.
- `definition` (string): Concise, hand-authored 1â€“2 sentence definition stating what the concept is and its functional purpose in RAG.
- `aliases` (list of strings): Synonymous phrases, abbreviations, or variants observed in literature (e.g., `["DPR-style retrieval", "dual-encoder retrieval"]`).
- `introduced_by` (string): Foreign key pointing to the paper that first established or formalized the concept.

### 2.3 Method
A specific, named algorithmic system, framework, or model architecture. A method is implemented by a specific paper, incorporates multiple concepts, and often directly extends an earlier method.
- `method_id` (string, primary key): Method slug (e.g., `rag-sequence`, `fid`, `self-rag`).
- `name` (string): Formal name of the method.
- `description` (string): Summary of architectural formulation.
- `introduced_by` (string): Foreign key pointing to the origin paper.
- `uses_concepts` (list of strings): Concepts that constitute the method's core architecture.
- `extends_method` (string, optional): Upstream method that this system directly modifies or builds upon.


## 3. Relationship Schema and Semantics

Relationships are directional, typed, and require explicit justification.

| Relationship Type | Source Entity | Target Entity | Semantic Meaning | Required Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `INTRODUCES_CONCEPT` | Paper | Concept | The source paper is the canonical originator of this technical concept. | Abstract or introduction explicitly defines or establishes the mechanism. |
| `INTRODUCES_METHOD` | Paper | Method | The source paper proposes and names this specific system. | The paper formally names and presents the algorithm. |
| `BUILDS_ON` | Paper | Paper | Direct intellectual lineage: Paper A adopts, evaluates against, or extends architectural elements of Paper B. | Paper A cites Paper B and builds upon its architectural mechanisms. |
| `EXTENDS` | Method | Method | Method A is an explicit modification, generalization, or enhancement of Method B. | The method formulation explicitly defines itself as an extension or alternative to Method B. |
| `USES_CONCEPT` | Method | Concept | Method A requires Concept C as a necessary component of its architecture. | The system design incorporates Concept C (e.g., RAG uses dense-passage-retrieval). |
| `REQUIRES_UNDERSTANDING` | Concept | Concept | Concept Y cannot be mathematically or conceptually understood without prior comprehension of Concept X. | Understanding Concept Y relies on primitives established in Concept X (e.g., RAG requires dense-passage-retrieval, which requires self-attention). |


## 4. Evidence and Provenance Constraints

To prevent arbitrary edge creation, every relationship instance in the Knowledge State must satisfy four rules:

1. Textual Justification: Every edge carries an `evidence` string containing either a direct excerpt or a concise synthetic explanation grounded in the paper's abstract or methodology section.
2. Confidence Classification: Edges are assigned a confidence rating:
   - `high`: Verified directly from publication text or author claims.
   - `medium`: Inferred through unambiguous architectural dependency (e.g., a seq2seq RAG model inherently requiring transformer encoder-decoder mechanics).
3. Non-Cyclic Prerequisite Enforcement: The subgraph formed by `REQUIRES_UNDERSTANDING` and `EXTENDS` must form a strict Directed Acyclic Graph (DAG). Circular prerequisite loops are forbidden and checked during validation.
4. Transitive Parsimony: If Concept A is a prerequisite for Concept B, and Concept B is a prerequisite for Concept C ($A \rightarrow B \rightarrow C$), we do not add a redundant direct edge $A \rightarrow C$ unless A provides an independent prerequisite separate from B.


## 5. Deliberately Excluded Entities and Relationships

To maintain high reasoning fidelity for the reading-path use case, several common knowledge graph elements were intentionally omitted:

| Excluded Element | Rationale |
| :--- | :--- |
| `Author` as an Entity Node | Authorship does not determine conceptual prerequisites. An author moving between labs or topics introduces noise into prerequisite traversal. Author names remain attributes on Paper entities for display purposes only. |
| `Dataset` / `Benchmark` Entities | While benchmarks like FEVER or PopQA are influential, including them as graph nodes distracts from architectural lineages. Benchmarks are treated as concepts (`fact-verification`) when they represent core evaluation concepts. |
| Unweighted `CITES` Edges | Raw citations are overly dense and non-discriminative. Papers cite related work for courtesy, contrast, or tangential context. Only citations that represent true conceptual building blocks are promoted to `BUILDS_ON`. |
| Temporal Sequencing Edges (`PRECEDES`) | Publication order is already captured by publication year integers. Prerequisite ordering must be based on conceptual dependencies, not chronological timestamps. |


## 6. How this Model Serves the Reading Path Use Case

When an unseen paper is analyzed:
1. Its text is scanned against the concept and method taxonomy (including aliases).
2. The matched concepts and methods serve as entry nodes in the knowledge graph.
3. The reasoning engine traverses incoming `REQUIRES_UNDERSTANDING`, `EXTENDS`, and `BUILDS_ON` edges backwards to identify all upstream ancestors.
4. Topological sorting of the ancestral subgraph produces a clean, non-redundant reading order from foundational building blocks to the immediate precursor.
5. The attached evidence strings provide the exact rationale for why each paper must be read.
