"""Tests for the pipeline profiler and confidence scoring."""

from sdtm_mapping_ai.pipeline.confidence import ConfidenceScorer
from sdtm_mapping_ai.pipeline.profiler import SourceDataProfiler


def test_profiler_dataframe(sample_source_df):
    profiler = SourceDataProfiler()
    profile = profiler.profile_dataframe(sample_source_df, "test_dm")
    assert profile.name == "test_dm"
    assert profile.n_rows == 3
    assert profile.n_cols == 5
    assert len(profile.variables) == 5

    age_var = next(v for v in profile.variables if v.name == "AGE")
    assert age_var.data_type == "Num"
    assert age_var.n_unique == 3


def test_profiler_with_label_map(sample_source_df):
    """FIX L5: Test that label_map overrides auto-generated labels."""
    profiler = SourceDataProfiler(label_map={"AGE": "Subject Age at Screening"})
    profile = profiler.profile_dataframe(sample_source_df, "test")
    age_var = next(v for v in profile.variables if v.name == "AGE")
    assert age_var.label == "Subject Age at Screening"


def test_confidence_scorer():
    scorer = ConfidenceScorer(threshold=0.70)
    assert scorer.score("test.VAR1", llm_confidence=0.95).status == "auto_accept"
    assert scorer.score("test.VAR2", llm_confidence=0.50).status == "human_review"
    assert scorer.score("test.VAR3", llm_confidence=0.10).status == "reject"


def test_confidence_scorer_zero_threshold():
    """FIX M2: Verify threshold=0.0 is honored, not treated as falsy."""
    scorer = ConfidenceScorer(threshold=0.0)
    assert scorer.threshold == 0.0
    result = scorer.score("test.VAR1", llm_confidence=0.01)
    assert result.status == "auto_accept"


def test_confidence_filter():
    scorer = ConfidenceScorer(threshold=0.70)
    mappings = [
        {"name": "A", "confidence": 0.95},
        {"name": "B", "confidence": 0.60},
        {"name": "C", "confidence": 0.20},
        {"name": "D", "confidence": 0.85},
    ]
    accept, review, reject = scorer.filter_mappings(mappings)
    assert len(accept) == 2
    assert len(review) == 1
    assert len(reject) == 1
