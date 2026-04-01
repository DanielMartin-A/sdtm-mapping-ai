"""Tests for variable mapping."""

from sdtm_mapping_ai.models.variable_mapper import VariableMapper


def test_map_variable_unknown_domain():
    mapper = VariableMapper()
    result = mapper.map_variable(
        dataset_name="test", variable_name="VAR1", variable_label="Test",
        target_domain="ZZ", data_type="Char",
    )
    assert result.target_variable == "UNKNOWN"
    assert result.mapping_type == "unmapped"
    assert result.confidence == 0.0
