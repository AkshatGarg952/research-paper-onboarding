"""
Unit tests for Deterministic Reasoning and Reading Path Generation (Phase 10)
"""

from pathlib import Path


def test_deterministic_output(input_parser, reasoning_engine, base_dir):
    """Verifies that running reasoning twice on the exact same input produces identical output."""
    input_path = base_dir / "examples" / "new_input.json"
    inp1 = input_parser.parse_file(input_path)
    inp2 = input_parser.parse_file(input_path)

    res1 = reasoning_engine.generate_reading_path(inp1)
    res2 = reasoning_engine.generate_reading_path(inp2)

    assert res1["status"] == res2["status"] == "success"
    pids1 = [p["paper_id"] for p in res1["reading_path"]]
    pids2 = [p["paper_id"] for p in res2["reading_path"]]
    assert pids1 == pids2, "Reasoning engine output must be strictly deterministic."


def test_topological_sort_preserves_chronological_prerequisites(input_parser, reasoning_engine, base_dir):
    """Verifies that foundational papers are read before downstream extensions."""
    input_path = base_dir / "examples" / "new_input.json"
    inp = input_parser.parse_file(input_path)
    res = reasoning_engine.generate_reading_path(inp)

    path = res["reading_path"]
    pids = [p["paper_id"] for p in path]

    # Attention Is All You Need (2017) must come before BERT (2018)
    assert pids.index("vaswani_2017") < pids.index("devlin_2018")
    # BERT (2018) must come before DPR (2020)
    assert pids.index("devlin_2018") < pids.index("karpukhin_2020")
    # DPR (2020) must come before RAG (2020)
    assert pids.index("karpukhin_2020") < pids.index("lewis_2020")
    # RAG (2020) must come before Self-RAG (2023)
    assert pids.index("lewis_2020") < pids.index("asai_2023_selfrag")


def test_out_of_domain_graceful_handling(input_parser, reasoning_engine, base_dir):
    """Verifies that out-of-domain inputs produce an explicit status without hallucinations."""
    input_path = base_dir / "examples" / "new_input_no_match.json"
    inp = input_parser.parse_file(input_path)
    res = reasoning_engine.generate_reading_path(inp)

    assert res["status"] == "out_of_domain"
    assert len(res["reading_path"]) == 0
    assert "No recognized Retrieval-Augmented Generation" in res["message"]


def test_unseen_paper_not_in_corpus(input_parser, knowledge_state, base_dir):
    """Guarantees the test input paper is genuinely unseen and absent from the corpus."""
    input_path = base_dir / "examples" / "new_input.json"
    inp = input_parser.parse_file(input_path)

    corpus_titles = {p["title"].lower().strip() for p in knowledge_state["entities"]["papers"]}
    assert inp.title.lower().strip() not in corpus_titles, "Test input must not exist inside the training corpus."
