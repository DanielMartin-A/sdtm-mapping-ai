"""Tests for the RAG retriever (requires index to be built)."""

import pytest


@pytest.mark.integration
def test_retriever_loads():
    from sdtm_mapping_ai.rag.retriever import SDTMRetriever

    try:
        retriever = SDTMRetriever()
        results = retriever.retrieve("blood pressure measurement", n_results=3)
        assert len(results) > 0
        assert results[0].relevance_score > 0
    except Exception:
        pytest.skip("Index not built — run `python -m sdtm_mapping_ai.rag.build_index` first")
