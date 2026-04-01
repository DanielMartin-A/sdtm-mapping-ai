"""Tests for conformance checking."""

from sdtm_mapping_ai.sdtm.conformance import ConformanceChecker, MappingRecord, Severity


def test_valid_mapping():
    checker = ConformanceChecker()
    mapping = MappingRecord(
        source_dataset="dm", source_variable="SEX", source_label="Sex",
        target_domain="DM", target_variable="SEX", mapping_type="direct",
        confidence=0.9, justification="Direct.", target_value="F",
    )
    issues = checker.check_mapping(mapping)
    errors = [i for i in issues if i.severity == Severity.ERROR]
    assert len(errors) == 0


def test_invalid_domain():
    checker = ConformanceChecker()
    mapping = MappingRecord(
        source_dataset="x", source_variable="X", source_label="X",
        target_domain="ZZ", target_variable="X", mapping_type="direct",
        confidence=0.5, justification="",
    )
    issues = checker.check_mapping(mapping)
    assert any(i.rule_id == "SDTM-DOM-001" for i in issues)


def test_invalid_variable():
    checker = ConformanceChecker()
    mapping = MappingRecord(
        source_dataset="x", source_variable="X", source_label="X",
        target_domain="DM", target_variable="FAKEVARIABLE", mapping_type="direct",
        confidence=0.5, justification="",
    )
    issues = checker.check_mapping(mapping)
    assert any(i.rule_id == "SDTM-VAR-001" for i in issues)


def test_invalid_ct_value():
    checker = ConformanceChecker()
    mapping = MappingRecord(
        source_dataset="dm", source_variable="SEX", source_label="Sex",
        target_domain="DM", target_variable="SEX", mapping_type="recoding",
        confidence=0.9, justification="", target_value="INVALID_SEX_VALUE",
    )
    issues = checker.check_mapping(mapping)
    assert any(i.rule_id == "SDTM-CT-001" for i in issues)


def test_domain_completeness_missing_required():
    checker = ConformanceChecker()
    mapped = {"STUDYID", "DOMAIN", "USUBJID"}
    issues = checker.check_domain_completeness("DM", mapped)
    error_vars = {i.variable for i in issues if i.severity == Severity.ERROR}
    assert "SUBJID" in error_vars
    assert "SEX" in error_vars
