"""Tests for evaluation metrics (M3, M4 fixes)."""

import json

from sdtm_mapping_ai.evaluation.metrics import evaluate_mappings, precision_at_threshold


def test_evaluate_basic():
    gold = [
        {"source_dataset": "dm", "source_variable": "SEX", "target_domain": "DM",
         "target_variable": "SEX"},
        {"source_dataset": "ae", "source_variable": "AETERM", "target_domain": "AE",
         "target_variable": "AETERM"},
    ]
    preds = [
        {"source_dataset": "dm", "source_variable": "SEX", "target_domain": "DM",
         "target_variable": "SEX", "confidence": 0.9},
        {"source_dataset": "ae", "source_variable": "AETERM", "target_domain": "AE",
         "target_variable": "AEDECOD", "confidence": 0.5},  # wrong variable
    ]
    metrics = evaluate_mappings(preds, gold)
    assert metrics.total == 2
    assert metrics.correct_domain == 2
    assert metrics.correct_variable == 1
    assert metrics.correct_both == 1


def test_domain_confusion_json_serializable():
    """FIX M3: domain_confusion must use string keys for JSON."""
    gold = [{"source_dataset": "dm", "source_variable": "SEX",
             "target_domain": "DM", "target_variable": "SEX"}]
    preds = [{"source_dataset": "dm", "source_variable": "SEX",
              "target_domain": "AE", "target_variable": "SEX", "confidence": 0.5}]
    metrics = evaluate_mappings(preds, gold)
    serialized = json.dumps(metrics.domain_confusion)
    assert "DM->AE" in serialized


def test_precision_at_threshold():
    gold = [{"source_dataset": "dm", "source_variable": "SEX",
             "target_domain": "DM", "target_variable": "SEX"}]
    preds = [{"source_dataset": "dm", "source_variable": "SEX",
              "target_domain": "DM", "target_variable": "SEX", "confidence": 0.9}]
    result = precision_at_threshold(preds, gold, 0.7)
    assert result["precision"] == 1.0
    assert result["recall"] == 1.0
    assert result["above_threshold"] == 1


def test_precision_at_threshold_filters():
    gold = [{"source_dataset": "dm", "source_variable": "SEX",
             "target_domain": "DM", "target_variable": "SEX"}]
    preds = [{"source_dataset": "dm", "source_variable": "SEX",
              "target_domain": "DM", "target_variable": "SEX", "confidence": 0.3}]
    result = precision_at_threshold(preds, gold, 0.7)
    assert result["above_threshold"] == 0
    assert result["precision"] == 0.0
