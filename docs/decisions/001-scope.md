# ADR 001: Problem Definition, Scope Lock, and Non-Goals

- Status: Accepted
- Date: 2026-10-03
- Domain: Domain B (Research Paper Onboarding)
- Focused Area: Retrieval-Augmented Generation (RAG) in NLP (2017â€“2024)
- Core Use Case: Prerequisite Reading Path Generation for Unseen Papers


## 1. Context and Motivation

When someone starts research in Retrieval-Augmented Generation (RAG), the biggest hurdle is not finding papers - it is figuring out what to read first and why. Between 2017 and 2024, the field produced dozens of architectural variants that build directly on one another. 

Existing discovery tools do not solve this problem:
- Google Scholar ranks papers by citation counts, which favors older seminal work regardless of immediate relevance to a specific paper.
- Semantic Scholar and Connected Papers surface co-citation clusters and text similarity, but they treat all citations equally. They cannot distinguish between a passing reference in the related work section and an architectural prerequisite without which the method cannot be understood.
- Vector search retrieves papers with similar wording, not papers that explain foundational concepts.

When an engineer or graduate student encounters a modern method like Self-RAG or CRAG, they face concepts like dual-encoder retrieval, cross-attention fusion, chunked retrieval, and reflection tokens. Reading these papers without understanding their direct predecessors leads to constant context switching and confusion.


## 2. Target User and Primary Scenario

- Target User: An incoming graduate student or ML engineer starting a RAG project.
- User Situation: The user has identified or written an abstract for a new paper/proposal outside the corpus (e.g., an adaptive retrieval mechanism with dynamic confidence thresholds).
- The Core Question: "What foundational and intermediate papers do I need to read to understand this new paper, in what order, and what is the exact reason each paper is required?"


## 3. The Single Chosen Use Case

### Prerequisite Reading Path Generation

Given a previously unseen paper (title and abstract):

1. Concept and Method Mapping: Match terms in the input abstract against a manually curated taxonomy of RAG concepts and methods.
2. Dependency Traversal: Traverse explicit, typed relationships (`REQUIRES_UNDERSTANDING`, `EXTENDS`, `BUILDS_ON`, `INTRODUCES_CONCEPT`, `INTRODUCES_METHOD`) to discover all upstream conceptual prerequisites.
3. Topological Ordering: Construct a directed acyclic graph (DAG) of the identified prerequisite papers and sort them so earlier foundations are read before downstream extensions.
4. Evidence Attribution: Output an ordered reading list where every recommendation is accompanied by concrete textual justification explaining the exact conceptual requirement that brought it in.


## 4. Corpus Boundary

### Why RAG (2017â€“2024)?
1. Well-defined lineage: The core architectural ideas follow a clear line of descent - from Transformers (Vaswani et al., 2017) and BERT (Devlin et al., 2018) to Dense Passage Retrieval (Karpukhin et al., 2020), standard RAG (Lewis et al., 2020), Fusion-in-Decoder (Izacard and Grave, 2021), RETRO (Borgeaud et al., 2022), and self-reflective architectures (Asai et al., 2023; Yan et al., 2024).
2. Right scale: The core architectural papers naturally total around 60â€“80 works. This matches the assignment scope (50â€“100 papers) without needing to pad with irrelevant papers or artificially chop off half a domain.
3. Strong dependency structure: In RAG, concepts are tightly coupled. You cannot meaningfully grasp sequence-level marginalization without understanding dual-encoder retrieval and seq2seq models.


## 5. Explicit Non-Goals

To keep the implementation focused on knowledge modeling and reasoning rather than generic features, the following items are intentionally excluded:

| Item | Why It Is Excluded |
| :--- | :--- |
| Automated KG construction tools | The goal of this assignment is to design the schema and mapping logic myself. Using black-box graph extraction tools defeats that purpose. |
| Vector search and embeddings | Nearest-neighbor vector retrieval is opaque and cannot guarantee transitive, step-by-step dependency reasoning. |
| Raw citation graph traversal | Raw citation graphs are noisy. Most citations do not represent true conceptual dependencies. |
| Author and institution analysis | Author collaboration networks do not help answer which paper should be read first. |
| Trend prediction and gap detection | Speculative research forecasting is separate from prerequisite path reasoning. |
| Web UI or complex frontend | An inspectable JSON knowledge state and a clean CLI script are sufficient to validate the system. |


## 6. Success Criteria

1. Deterministic output: Running the same input paper through the system always yields the exact same reading path and explanations.
2. Verified provenance: Every paper in the reading path must trace back to a documented dependency in the knowledge model.
3. Independent inspectability: The knowledge state must be fully legible in JSON format without running any code.
4. Robust handling of unseen inputs: Valid new papers produce justified reading paths; out-of-domain papers produce a clean, informative notification instead of hallucinations.
