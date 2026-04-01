"""Shared test fixtures."""

from __future__ import annotations

import pandas as pd
import pytest

from sdtm_mapping_ai.sdtm.conformance import ConformanceChecker, MappingRecord
from sdtm_mapping_ai.sdtm.controlled_terminology import ControlledTerminology


@pytest.fixture
def ct() -> ControlledTerminology:
    return ControlledTerminology()


@pytest.fixture
def conformance_checker(ct: ControlledTerminology) -> ConformanceChecker:
    return ConformanceChecker(ct=ct)


@pytest.fixture
def sample_dm_mapping() -> MappingRecord:
    return MappingRecord(
        source_dataset="demographics", source_variable="GENDER",
        source_label="Gender of Subject", target_domain="DM",
        target_variable="SEX", mapping_type="recoding",
        confidence=0.92, justification="Gender maps to SEX.", target_value="F",
    )


@pytest.fixture
def sample_source_df() -> pd.DataFrame:
    return pd.DataFrame({
        "SUBJID": ["001", "002", "003"],
        "AGE": [45, 62, 38],
        "SEX": ["M", "F", "M"],
        "RACE": ["WHITE", "ASIAN", "BLACK OR AFRICAN AMERICAN"],
        "SITEID": ["101", "102", "101"],
    })
