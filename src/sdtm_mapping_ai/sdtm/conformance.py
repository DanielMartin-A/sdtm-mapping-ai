"""Conformance checking for SDTM mappings against structural rules and CT."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

import structlog

from sdtm_mapping_ai.sdtm.controlled_terminology import ControlledTerminology
from sdtm_mapping_ai.sdtm.standards import get_domain

logger = structlog.get_logger()


class Severity(StrEnum):
    ERROR = "Error"
    WARNING = "Warning"
    INFO = "Info"


@dataclass
class ConformanceIssue:
    rule_id: str
    severity: Severity
    domain: str
    variable: str | None
    message: str


@dataclass
class ConformanceReport:
    issues: list[ConformanceIssue] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.WARNING)

    @property
    def is_conformant(self) -> bool:
        return self.error_count == 0

    def summary(self) -> str:
        status = "PASS" if self.is_conformant else "FAIL"
        return f"Conformance: {status} ({self.error_count} errors, {self.warning_count} warnings)"


@dataclass
class MappingRecord:
    source_dataset: str
    source_variable: str
    source_label: str
    target_domain: str
    target_variable: str
    mapping_type: str
    confidence: float
    justification: str
    target_value: str | None = None


class ConformanceChecker:
    def __init__(self, ct: ControlledTerminology | None = None) -> None:
        self.ct = ct or ControlledTerminology()

    def check_mapping(self, mapping: MappingRecord) -> list[ConformanceIssue]:
        issues: list[ConformanceIssue] = []
        issues.extend(self._check_domain_exists(mapping))
        issues.extend(self._check_variable_exists(mapping))
        issues.extend(self._check_ct_value(mapping))
        return issues

    def check_domain_completeness(
        self, domain_code: str, mapped_variables: set[str]
    ) -> list[ConformanceIssue]:
        issues: list[ConformanceIssue] = []
        try:
            domain = get_domain(domain_code)
        except KeyError:
            return issues
        for var in domain.get_required_variables():
            if var.name not in mapped_variables:
                issues.append(ConformanceIssue(
                    "SDTM-REQ-001", Severity.ERROR, domain_code, var.name,
                    f"Required variable {var.name} ({var.label}) is not mapped.",
                ))
        for var in domain.get_expected_variables():
            if var.name not in mapped_variables:
                issues.append(ConformanceIssue(
                    "SDTM-EXP-001", Severity.WARNING, domain_code, var.name,
                    f"Expected variable {var.name} ({var.label}) is not mapped.",
                ))
        return issues

    def validate_full_study(self, mappings: list[MappingRecord]) -> ConformanceReport:
        report = ConformanceReport()
        for m in mappings:
            report.issues.extend(self.check_mapping(m))
        domains_mapped: dict[str, set[str]] = {}
        for m in mappings:
            domains_mapped.setdefault(m.target_domain, set()).add(m.target_variable)
        for domain_code, variables in domains_mapped.items():
            report.issues.extend(self.check_domain_completeness(domain_code, variables))
        logger.info("conformance_complete", errors=report.error_count,
                    warnings=report.warning_count)
        return report

    def _check_domain_exists(self, m: MappingRecord) -> list[ConformanceIssue]:
        try:
            get_domain(m.target_domain)
            return []
        except KeyError:
            return [ConformanceIssue(
                "SDTM-DOM-001", Severity.ERROR, m.target_domain, m.target_variable,
                f"Target domain '{m.target_domain}' is not recognized.",
            )]

    def _check_variable_exists(self, m: MappingRecord) -> list[ConformanceIssue]:
        try:
            domain = get_domain(m.target_domain)
        except KeyError:
            return []
        if m.target_variable not in {v.name for v in domain.variables}:
            return [ConformanceIssue(
                "SDTM-VAR-001", Severity.ERROR, m.target_domain, m.target_variable,
                f"Variable '{m.target_variable}' not defined in {m.target_domain}.",
            )]
        return []

    def _check_ct_value(self, m: MappingRecord) -> list[ConformanceIssue]:
        if not m.target_value:
            return []
        try:
            domain = get_domain(m.target_domain)
        except KeyError:
            return []
        var_def = next((v for v in domain.variables if v.name == m.target_variable), None)
        if var_def is None or var_def.codelist is None:
            return []
        if not self.ct.validate_value(var_def.codelist, m.target_value):
            return [ConformanceIssue(
                "SDTM-CT-001", Severity.ERROR, m.target_domain, m.target_variable,
                f"Value '{m.target_value}' not valid for codelist {var_def.codelist}.",
            )]
        return []
