"""CDISC Controlled Terminology lookup and validation.

Based on publicly available CDISC Controlled Terminology.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

# Version of CT this codebase was validated against
CT_VERSION = "2026-03"


@dataclass
class Codelist:
    code: str
    name: str
    terms: list[str] = field(default_factory=list)
    extensible: bool = False

    def is_valid_term(self, value: str) -> bool:
        if self.extensible:
            return True
        return value.upper() in {t.upper() for t in self.terms}


_BUILTIN_CODELISTS: dict[str, Codelist] = {
    "SEX": Codelist("C66731", "Sex", ["F", "M", "U", "UNDIFFERENTIATED"]),
    "NY": Codelist("C66742", "No Yes Response", ["N", "Y"]),
    "RACE": Codelist("C74457", "Race", [
        "AMERICAN INDIAN OR ALASKA NATIVE", "ASIAN",
        "BLACK OR AFRICAN AMERICAN",
        "NATIVE HAWAIIAN OR OTHER PACIFIC ISLANDER",
        "WHITE", "MULTIPLE", "OTHER",
    ], extensible=True),
    "ETHNIC": Codelist("C66790", "Ethnicity", [
        "HISPANIC OR LATINO", "NOT HISPANIC OR LATINO", "NOT REPORTED", "UNKNOWN"
    ]),
    "AGEU": Codelist("C66781", "Age Unit", ["YEARS", "MONTHS", "WEEKS", "DAYS", "HOURS"]),
    "AESEV": Codelist("C66769", "Severity", ["MILD", "MODERATE", "SEVERE"]),
    "ACN": Codelist("C66767", "Action Taken", [
        "DOSE INCREASED", "DOSE NOT CHANGED", "DOSE REDUCED",
        "DRUG INTERRUPTED", "DRUG WITHDRAWN", "NOT APPLICABLE", "UNKNOWN",
    ]),
    "OUT": Codelist("C66768", "Outcome of Event", [
        "FATAL", "NOT RECOVERED/NOT RESOLVED", "RECOVERED/RESOLVED",
        "RECOVERED/RESOLVED WITH SEQUELAE", "RECOVERING/RESOLVING", "UNKNOWN",
    ]),
    "NRIND": Codelist("C78736", "Reference Range Indicator",
                      ["ABNORMAL", "HIGH", "LOW", "NORMAL"], extensible=True),
    "POSITION": Codelist("C71148", "Position", ["SITTING", "STANDING", "SUPINE"]),
    "ROUTE": Codelist("C66729", "Route of Administration", [
        "ORAL", "INTRAVENOUS", "SUBCUTANEOUS", "INTRAMUSCULAR",
        "TOPICAL", "INHALATION", "TRANSDERMAL", "RECTAL",
    ], extensible=True),
    "FRM": Codelist("C66726", "Dosage Form", [
        "TABLET", "CAPSULE", "INJECTION", "SOLUTION", "SUSPENSION",
        "CREAM", "OINTMENT", "PATCH", "POWDER",
    ], extensible=True),
    "FREQ": Codelist("C71113", "Frequency", [
        "BID", "QD", "QID", "TID", "QW", "ONCE", "PRN",
    ], extensible=True),
    "COUNTRY": Codelist("C66732", "Country", [
        "USA", "CAN", "GBR", "DEU", "FRA", "JPN", "CHN", "IND", "BRA", "AUS",
    ], extensible=True),
    "VSTESTCD": Codelist("C66741", "VS Test Code", [
        "SYSBP", "DIABP", "PULSE", "HR", "TEMP", "RESP", "HEIGHT", "WEIGHT", "BMI",
    ]),
    "VSTEST": Codelist("C67153", "VS Test Name", [
        "Systolic Blood Pressure", "Diastolic Blood Pressure",
        "Pulse Rate", "Heart Rate", "Temperature",
        "Respiratory Rate", "Height", "Weight", "Body Mass Index",
    ]),
    "LBTESTCD": Codelist("C65047", "Lab Test Code", [
        "ALB", "ALP", "ALT", "AST", "BILI", "BUN", "CA", "CHOL", "CK",
        "CREAT", "GGT", "GLUC", "HBA1C", "HCT", "HGB", "K", "LDH",
        "MG", "NA", "PHOS", "PLAT", "PROT", "RBC", "TRIG", "URATE", "WBC",
    ], extensible=True),
}


class ControlledTerminology:
    def __init__(self) -> None:
        self._codelists: dict[str, Codelist] = dict(_BUILTIN_CODELISTS)

    def get_codelist(self, name: str) -> Codelist | None:
        return self._codelists.get(name.upper())

    def validate_value(self, codelist_name: str, value: str) -> bool:
        cl = self.get_codelist(codelist_name)
        if cl is None:
            return True
        return cl.is_valid_term(value)

    def get_valid_terms(self, codelist_name: str) -> list[str]:
        cl = self.get_codelist(codelist_name)
        return cl.terms if cl else []

    def load_from_json(self, path: Path) -> None:
        data = json.loads(path.read_text())
        for name, spec in data.items():
            self._codelists[name.upper()] = Codelist(
                code=spec.get("code", ""), name=spec.get("name", name),
                terms=spec.get("terms", []), extensible=spec.get("extensible", False),
            )

    @property
    def codelist_names(self) -> list[str]:
        return sorted(self._codelists.keys())
