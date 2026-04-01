"""Tests for domain prediction (mocked LLM calls)."""

from sdtm_mapping_ai.models.domain_predictor import DomainPredictor


def test_parse_valid_dict():
    result = DomainPredictor._parse_dict(
        {"predicted_domain": "AE", "confidence": 0.85, "reasoning": "Adverse event data"}
    )
    assert result.predicted_domain == "AE"
    assert result.confidence == 0.85


def test_parse_invalid_domain_fallback():
    result = DomainPredictor._parse_dict(
        {"predicted_domain": "ZZ", "confidence": 0.5, "reasoning": "unknown"}
    )
    assert result.predicted_domain == "DM"  # Fallback


def test_parse_confidence_clamped():
    result = DomainPredictor._parse_dict(
        {"predicted_domain": "LB", "confidence": 1.5, "reasoning": "over"}
    )
    assert result.confidence == 1.0

    result = DomainPredictor._parse_dict(
        {"predicted_domain": "LB", "confidence": -0.5, "reasoning": "under"}
    )
    assert result.confidence == 0.0
