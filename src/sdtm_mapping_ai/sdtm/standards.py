"""SDTM domain and variable definitions based on public SDTMIG v3.4 specifications.

All definitions are derived from publicly available CDISC standards documentation.
Reference: CDISC SDTMIG v3.4 (November 2021).

Fixes applied:
- M7: DataType enum replaces free-form str
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class ObservationClass(StrEnum):
    INTERVENTIONS = "Interventions"
    EVENTS = "Events"
    FINDINGS = "Findings"
    FINDINGS_ABOUT = "Findings About"
    SPECIAL_PURPOSE = "Special Purpose"
    TRIAL_DESIGN = "Trial Design"
    RELATIONSHIP = "Relationship"
    ASSOCIATED_PERSONS = "Associated Persons"


class CoreDesignation(StrEnum):
    REQUIRED = "Req"
    EXPECTED = "Exp"
    PERMISSIBLE = "Perm"


class DataType(StrEnum):
    """FIX M7: Enum for SDTM variable data types instead of free-form str."""
    CHAR = "Char"
    NUM = "Num"


@dataclass
class SDTMVariable:
    name: str
    label: str
    data_type: DataType
    core: CoreDesignation
    description: str
    codelist: str | None = None
    role: str = ""


@dataclass
class SDTMDomain:
    code: str
    name: str
    observation_class: ObservationClass
    description: str
    variables: list[SDTMVariable] = field(default_factory=list)

    def get_required_variables(self) -> list[SDTMVariable]:
        return [v for v in self.variables if v.core == CoreDesignation.REQUIRED]

    def get_expected_variables(self) -> list[SDTMVariable]:
        return [v for v in self.variables if v.core == CoreDesignation.EXPECTED]

    def to_context_string(self) -> str:
        lines = [
            f"Domain: {self.code} — {self.name}",
            f"Observation Class: {self.observation_class.value}",
            f"Description: {self.description}",
            "",
            "Variables:",
        ]
        for v in self.variables:
            cl = f" [Codelist: {v.codelist}]" if v.codelist else ""
            lines.append(f"  - {v.name} ({v.label}): {v.data_type.value}, {v.core.value}{cl}")
            lines.append(f"    {v.description}")
        return "\n".join(lines)


# ── Domain Builders ──────────────────────────────────────────────────────────


def _build_dm_domain() -> SDTMDomain:
    return SDTMDomain(
        code="DM", name="Demographics",
        observation_class=ObservationClass.SPECIAL_PURPOSE,
        description="One record per subject with essential standard variables.",
        variables=[
            SDTMVariable("STUDYID", "Study Identifier", DataType.CHAR, CoreDesignation.REQUIRED,
                         "Unique identifier for a study."),
            SDTMVariable("DOMAIN", "Domain Abbreviation", DataType.CHAR, CoreDesignation.REQUIRED,
                         "Two-character abbreviation for the domain."),
            SDTMVariable("USUBJID", "Unique Subject Identifier", DataType.CHAR,
                         CoreDesignation.REQUIRED,
                         "Identifier used to uniquely identify a subject across all studies."),
            SDTMVariable("SUBJID", "Subject Identifier for the Study", DataType.CHAR,
                         CoreDesignation.REQUIRED, "Subject identifier, unique within the study."),
            SDTMVariable("RFSTDTC", "Subject Reference Start Date/Time", DataType.CHAR,
                         CoreDesignation.EXPECTED, "Reference start date/time in ISO 8601."),
            SDTMVariable("RFENDTC", "Subject Reference End Date/Time", DataType.CHAR,
                         CoreDesignation.EXPECTED, "Reference end date/time in ISO 8601."),
            SDTMVariable("SITEID", "Study Site Identifier", DataType.CHAR,
                         CoreDesignation.REQUIRED, "Unique identifier for a site within a study."),
            SDTMVariable("BRTHDTC", "Date/Time of Birth", DataType.CHAR,
                         CoreDesignation.PERMISSIBLE, "Date/time of birth of the subject."),
            SDTMVariable("AGE", "Age", DataType.NUM, CoreDesignation.EXPECTED,
                         "Age of the subject at screening."),
            SDTMVariable("AGEU", "Age Units", DataType.CHAR, CoreDesignation.EXPECTED,
                         "Units associated with AGE.", codelist="AGEU"),
            SDTMVariable("SEX", "Sex", DataType.CHAR, CoreDesignation.REQUIRED,
                         "Sex of the subject.", codelist="SEX"),
            SDTMVariable("RACE", "Race", DataType.CHAR, CoreDesignation.EXPECTED,
                         "Race of the subject.", codelist="RACE"),
            SDTMVariable("ETHNIC", "Ethnicity", DataType.CHAR, CoreDesignation.PERMISSIBLE,
                         "Ethnicity of the subject.", codelist="ETHNIC"),
            SDTMVariable("ARMCD", "Planned Arm Code", DataType.CHAR, CoreDesignation.REQUIRED,
                         "Short code for the planned arm."),
            SDTMVariable("ARM", "Description of Planned Arm", DataType.CHAR,
                         CoreDesignation.REQUIRED,
                         "Name of the arm to which the subject was assigned."),
            SDTMVariable("COUNTRY", "Country", DataType.CHAR, CoreDesignation.EXPECTED,
                         "Country of the investigational site.", codelist="COUNTRY"),
            SDTMVariable("DMDTC", "Date/Time of Collection", DataType.CHAR,
                         CoreDesignation.PERMISSIBLE, "Date/time of demographics data collection."),
            SDTMVariable("DMDY", "Study Day of Collection", DataType.NUM,
                         CoreDesignation.PERMISSIBLE, "Study day of demographics data collection."),
        ],
    )


def _build_ae_domain() -> SDTMDomain:
    return SDTMDomain(
        code="AE", name="Adverse Events",
        observation_class=ObservationClass.EVENTS,
        description="Adverse events with verbatim/coded term, severity, seriousness.",
        variables=[
            SDTMVariable("STUDYID", "Study Identifier", DataType.CHAR, CoreDesignation.REQUIRED,
                         "Unique identifier for a study."),
            SDTMVariable("DOMAIN", "Domain Abbreviation", DataType.CHAR, CoreDesignation.REQUIRED,
                         "Two-character abbreviation for the domain."),
            SDTMVariable("USUBJID", "Unique Subject Identifier", DataType.CHAR,
                         CoreDesignation.REQUIRED, "Unique subject identifier."),
            SDTMVariable("AESEQ", "Sequence Number", DataType.NUM, CoreDesignation.REQUIRED,
                         "Sequence number for uniqueness within dataset."),
            SDTMVariable("AETERM", "Reported Term for the Adverse Event", DataType.CHAR,
                         CoreDesignation.REQUIRED, "Verbatim name of the event."),
            SDTMVariable("AEDECOD", "Dictionary-Derived Term", DataType.CHAR,
                         CoreDesignation.REQUIRED, "MedDRA Preferred Term."),
            SDTMVariable("AEBODSYS", "Body System or Organ Class", DataType.CHAR,
                         CoreDesignation.EXPECTED, "MedDRA System Organ Class."),
            SDTMVariable("AESEV", "Severity/Intensity", DataType.CHAR,
                         CoreDesignation.PERMISSIBLE, "Severity or intensity.", codelist="AESEV"),
            SDTMVariable("AESER", "Serious Event", DataType.CHAR, CoreDesignation.EXPECTED,
                         "Is this a serious event?", codelist="NY"),
            SDTMVariable("AEACN", "Action Taken with Study Treatment", DataType.CHAR,
                         CoreDesignation.EXPECTED, "Action taken.", codelist="ACN"),
            SDTMVariable("AEREL", "Causality", DataType.CHAR, CoreDesignation.EXPECTED,
                         "Relationship to study treatment."),
            SDTMVariable("AEOUT", "Outcome of Adverse Event", DataType.CHAR,
                         CoreDesignation.EXPECTED, "Outcome.", codelist="OUT"),
            SDTMVariable("AESTDTC", "Start Date/Time of AE", DataType.CHAR,
                         CoreDesignation.EXPECTED, "Start date/time in ISO 8601."),
            SDTMVariable("AEENDTC", "End Date/Time of AE", DataType.CHAR,
                         CoreDesignation.EXPECTED, "End date/time in ISO 8601."),
            SDTMVariable("AESTDY", "Study Day of Start of AE", DataType.NUM,
                         CoreDesignation.PERMISSIBLE, "Study day of start."),
            SDTMVariable("AEENDY", "Study Day of End of AE", DataType.NUM,
                         CoreDesignation.PERMISSIBLE, "Study day of end."),
        ],
    )


def _build_lb_domain() -> SDTMDomain:
    return SDTMDomain(
        code="LB", name="Laboratory Test Results",
        observation_class=ObservationClass.FINDINGS,
        description="Lab data: test name, result, units, reference ranges, specimen type.",
        variables=[
            SDTMVariable("STUDYID", "Study Identifier", DataType.CHAR,
                         CoreDesignation.REQUIRED, "Unique identifier for a study."),
            SDTMVariable("DOMAIN", "Domain Abbreviation", DataType.CHAR,
                         CoreDesignation.REQUIRED, "Two-character abbreviation."),
            SDTMVariable("USUBJID", "Unique Subject Identifier", DataType.CHAR,
                         CoreDesignation.REQUIRED, "Unique subject identifier."),
            SDTMVariable("LBSEQ", "Sequence Number", DataType.NUM,
                         CoreDesignation.REQUIRED, "Sequence number within domain."),
            SDTMVariable("LBTESTCD", "Lab Test Short Name", DataType.CHAR,
                         CoreDesignation.REQUIRED, "Short character value.", codelist="LBTESTCD"),
            SDTMVariable("LBTEST", "Lab Test Name", DataType.CHAR, CoreDesignation.REQUIRED,
                         "Long name for the lab test.", codelist="LBTEST"),
            SDTMVariable("LBCAT", "Category for Lab Test", DataType.CHAR,
                         CoreDesignation.EXPECTED, "Category (HEMATOLOGY, CHEMISTRY, etc.)."),
            SDTMVariable("LBORRES", "Result in Original Units", DataType.CHAR,
                         CoreDesignation.EXPECTED, "Result as originally received."),
            SDTMVariable("LBORRESU", "Original Units", DataType.CHAR, CoreDesignation.EXPECTED,
                         "Unit for LBORRES.", codelist="UNIT"),
            SDTMVariable("LBSTRESC", "Char Result in Std Format", DataType.CHAR,
                         CoreDesignation.EXPECTED, "Result in standard character format."),
            SDTMVariable("LBSTRESN", "Numeric Result in Std Units", DataType.NUM,
                         CoreDesignation.EXPECTED, "Numeric result in standard units."),
            SDTMVariable("LBSTRESU", "Standard Units", DataType.CHAR, CoreDesignation.EXPECTED,
                         "Standard unit.", codelist="UNIT"),
            SDTMVariable("LBNRIND", "Reference Range Indicator", DataType.CHAR,
                         CoreDesignation.EXPECTED, "Where value falls wrt ref range.",
                         codelist="NRIND"),
            SDTMVariable("LBSPEC", "Specimen Type", DataType.CHAR, CoreDesignation.PERMISSIBLE,
                         "Specimen type.", codelist="SPECTYPE"),
            SDTMVariable("VISITNUM", "Visit Number", DataType.NUM, CoreDesignation.EXPECTED,
                         "Clinical encounter number."),
            SDTMVariable("VISIT", "Visit Name", DataType.CHAR, CoreDesignation.EXPECTED,
                         "Protocol-defined visit description."),
            SDTMVariable("LBDTC", "Date/Time of Collection", DataType.CHAR,
                         CoreDesignation.EXPECTED, "Collection date/time in ISO 8601."),
            SDTMVariable("LBDY", "Study Day of Collection", DataType.NUM,
                         CoreDesignation.PERMISSIBLE, "Study day of specimen collection."),
        ],
    )


def _build_vs_domain() -> SDTMDomain:
    return SDTMDomain(
        code="VS", name="Vital Signs",
        observation_class=ObservationClass.FINDINGS,
        description="Vital signs: blood pressure, heart rate, temperature, height, weight.",
        variables=[
            SDTMVariable("STUDYID", "Study Identifier", DataType.CHAR,
                         CoreDesignation.REQUIRED, "Unique identifier."),
            SDTMVariable("DOMAIN", "Domain Abbreviation", DataType.CHAR,
                         CoreDesignation.REQUIRED, "Two-character abbreviation."),
            SDTMVariable("USUBJID", "Unique Subject Identifier", DataType.CHAR,
                         CoreDesignation.REQUIRED, "Unique subject identifier."),
            SDTMVariable("VSSEQ", "Sequence Number", DataType.NUM,
                         CoreDesignation.REQUIRED, "Sequence number."),
            SDTMVariable("VSTESTCD", "VS Test Short Name", DataType.CHAR,
                         CoreDesignation.REQUIRED, "Short name.", codelist="VSTESTCD"),
            SDTMVariable("VSTEST", "VS Test Name", DataType.CHAR, CoreDesignation.REQUIRED,
                         "Long name.", codelist="VSTEST"),
            SDTMVariable("VSPOS", "Position of Subject", DataType.CHAR,
                         CoreDesignation.PERMISSIBLE, "Position during measurement.",
                         codelist="POSITION"),
            SDTMVariable("VSORRES", "Result in Original Units", DataType.CHAR,
                         CoreDesignation.EXPECTED, "Result as originally recorded."),
            SDTMVariable("VSORRESU", "Original Units", DataType.CHAR,
                         CoreDesignation.EXPECTED, "Unit for VSORRES.", codelist="UNIT"),
            SDTMVariable("VSSTRESC", "Char Result in Std Format", DataType.CHAR,
                         CoreDesignation.EXPECTED, "Standard character format."),
            SDTMVariable("VSSTRESN", "Numeric Result in Std Units", DataType.NUM,
                         CoreDesignation.EXPECTED, "Numeric result in standard units."),
            SDTMVariable("VSSTRESU", "Standard Units", DataType.CHAR,
                         CoreDesignation.EXPECTED, "Standard unit.", codelist="UNIT"),
            SDTMVariable("VISITNUM", "Visit Number", DataType.NUM,
                         CoreDesignation.EXPECTED, "Clinical encounter number."),
            SDTMVariable("VISIT", "Visit Name", DataType.CHAR,
                         CoreDesignation.EXPECTED, "Protocol-defined visit description."),
            SDTMVariable("VSDTC", "Date/Time of VS", DataType.CHAR,
                         CoreDesignation.EXPECTED, "Date/time in ISO 8601."),
            SDTMVariable("VSDY", "Study Day of VS", DataType.NUM,
                         CoreDesignation.PERMISSIBLE, "Study day of measurement."),
        ],
    )


def _build_ex_domain() -> SDTMDomain:
    return SDTMDomain(
        code="EX", name="Exposure",
        observation_class=ObservationClass.INTERVENTIONS,
        description="Subject exposure to study treatment: dose, frequency, route, timing.",
        variables=[
            SDTMVariable("STUDYID", "Study Identifier", DataType.CHAR,
                         CoreDesignation.REQUIRED, "Unique identifier."),
            SDTMVariable("DOMAIN", "Domain Abbreviation", DataType.CHAR,
                         CoreDesignation.REQUIRED, "Two-character abbreviation."),
            SDTMVariable("USUBJID", "Unique Subject Identifier", DataType.CHAR,
                         CoreDesignation.REQUIRED, "Unique subject identifier."),
            SDTMVariable("EXSEQ", "Sequence Number", DataType.NUM,
                         CoreDesignation.REQUIRED, "Sequence number."),
            SDTMVariable("EXTRT", "Name of Treatment", DataType.CHAR,
                         CoreDesignation.REQUIRED, "Name of the study treatment."),
            SDTMVariable("EXDOSE", "Dose", DataType.NUM, CoreDesignation.EXPECTED,
                         "Amount of treatment administered."),
            SDTMVariable("EXDOSU", "Dose Units", DataType.CHAR, CoreDesignation.EXPECTED,
                         "Units for EXDOSE.", codelist="UNIT"),
            SDTMVariable("EXDOSFRM", "Dose Form", DataType.CHAR, CoreDesignation.EXPECTED,
                         "Dose form.", codelist="FRM"),
            SDTMVariable("EXDOSFRQ", "Dosing Frequency", DataType.CHAR,
                         CoreDesignation.EXPECTED, "Dosing frequency.", codelist="FREQ"),
            SDTMVariable("EXROUTE", "Route of Administration", DataType.CHAR,
                         CoreDesignation.EXPECTED, "Route.", codelist="ROUTE"),
            SDTMVariable("EXSTDTC", "Start Date/Time", DataType.CHAR,
                         CoreDesignation.EXPECTED, "Start date/time in ISO 8601."),
            SDTMVariable("EXENDTC", "End Date/Time", DataType.CHAR,
                         CoreDesignation.EXPECTED, "End date/time in ISO 8601."),
            SDTMVariable("EXSTDY", "Study Day of Start", DataType.NUM,
                         CoreDesignation.PERMISSIBLE, "Study day of start."),
            SDTMVariable("EXENDY", "Study Day of End", DataType.NUM,
                         CoreDesignation.PERMISSIBLE, "Study day of end."),
        ],
    )


def _build_cm_domain() -> SDTMDomain:
    return SDTMDomain(
        code="CM", name="Concomitant/Prior Medications",
        observation_class=ObservationClass.INTERVENTIONS,
        description="Concomitant and prior medications.",
        variables=[
            SDTMVariable("STUDYID", "Study Identifier", DataType.CHAR,
                         CoreDesignation.REQUIRED, "Unique identifier."),
            SDTMVariable("DOMAIN", "Domain Abbreviation", DataType.CHAR,
                         CoreDesignation.REQUIRED, "Two-character abbreviation."),
            SDTMVariable("USUBJID", "Unique Subject Identifier", DataType.CHAR,
                         CoreDesignation.REQUIRED, "Unique subject identifier."),
            SDTMVariable("CMSEQ", "Sequence Number", DataType.NUM,
                         CoreDesignation.REQUIRED, "Sequence number."),
            SDTMVariable("CMTRT", "Reported Name of Drug", DataType.CHAR,
                         CoreDesignation.REQUIRED, "Verbatim medication name."),
            SDTMVariable("CMDECOD", "Standardized Medication Name", DataType.CHAR,
                         CoreDesignation.PERMISSIBLE, "Dictionary-standardized name."),
            SDTMVariable("CMCAT", "Category", DataType.CHAR,
                         CoreDesignation.PERMISSIBLE, "Category (PRIOR, CONCOMITANT)."),
            SDTMVariable("CMDOSE", "Dose", DataType.NUM,
                         CoreDesignation.PERMISSIBLE, "Dose amount."),
            SDTMVariable("CMDOSU", "Dose Units", DataType.CHAR,
                         CoreDesignation.PERMISSIBLE, "Dose units.", codelist="UNIT"),
            SDTMVariable("CMROUTE", "Route", DataType.CHAR,
                         CoreDesignation.PERMISSIBLE, "Route.", codelist="ROUTE"),
            SDTMVariable("CMSTDTC", "Start Date/Time", DataType.CHAR,
                         CoreDesignation.EXPECTED, "Start date/time in ISO 8601."),
            SDTMVariable("CMENDTC", "End Date/Time", DataType.CHAR,
                         CoreDesignation.EXPECTED, "End date/time in ISO 8601."),
            SDTMVariable("CMINDC", "Indication", DataType.CHAR,
                         CoreDesignation.PERMISSIBLE, "Indication for medication."),
        ],
    )


def _build_mh_domain() -> SDTMDomain:
    return SDTMDomain(
        code="MH", name="Medical History",
        observation_class=ObservationClass.EVENTS,
        description="Relevant medical history conditions/diagnoses.",
        variables=[
            SDTMVariable("STUDYID", "Study Identifier", DataType.CHAR,
                         CoreDesignation.REQUIRED, "Unique identifier."),
            SDTMVariable("DOMAIN", "Domain Abbreviation", DataType.CHAR,
                         CoreDesignation.REQUIRED, "Two-character abbreviation."),
            SDTMVariable("USUBJID", "Unique Subject Identifier", DataType.CHAR,
                         CoreDesignation.REQUIRED, "Unique subject identifier."),
            SDTMVariable("MHSEQ", "Sequence Number", DataType.NUM,
                         CoreDesignation.REQUIRED, "Sequence number."),
            SDTMVariable("MHTERM", "Reported Term", DataType.CHAR,
                         CoreDesignation.REQUIRED, "Verbatim medical history term."),
            SDTMVariable("MHDECOD", "Dictionary-Derived Term", DataType.CHAR,
                         CoreDesignation.EXPECTED, "MedDRA Preferred Term."),
            SDTMVariable("MHBODSYS", "Body System or Organ Class", DataType.CHAR,
                         CoreDesignation.EXPECTED, "MedDRA System Organ Class."),
            SDTMVariable("MHCAT", "Category", DataType.CHAR,
                         CoreDesignation.PERMISSIBLE, "Category grouping."),
            SDTMVariable("MHSTDTC", "Start Date/Time", DataType.CHAR,
                         CoreDesignation.PERMISSIBLE, "Start date/time in ISO 8601."),
            SDTMVariable("MHENDTC", "End Date/Time", DataType.CHAR,
                         CoreDesignation.PERMISSIBLE, "End date/time in ISO 8601."),
        ],
    )


def _build_ds_domain() -> SDTMDomain:
    return SDTMDomain(
        code="DS", name="Disposition",
        observation_class=ObservationClass.EVENTS,
        description="Protocol milestones: informed consent, randomization, completion.",
        variables=[
            SDTMVariable("STUDYID", "Study Identifier", DataType.CHAR,
                         CoreDesignation.REQUIRED, "Unique identifier."),
            SDTMVariable("DOMAIN", "Domain Abbreviation", DataType.CHAR,
                         CoreDesignation.REQUIRED, "Two-character abbreviation."),
            SDTMVariable("USUBJID", "Unique Subject Identifier", DataType.CHAR,
                         CoreDesignation.REQUIRED, "Unique subject identifier."),
            SDTMVariable("DSSEQ", "Sequence Number", DataType.NUM,
                         CoreDesignation.REQUIRED, "Sequence number."),
            SDTMVariable("DSTERM", "Reported Term", DataType.CHAR,
                         CoreDesignation.REQUIRED, "Verbatim disposition term."),
            SDTMVariable("DSDECOD", "Standardized Disposition Term", DataType.CHAR,
                         CoreDesignation.REQUIRED, "Standardized term.", codelist="NCOMPLT"),
            SDTMVariable("DSCAT", "Category", DataType.CHAR,
                         CoreDesignation.EXPECTED, "Category."),
            SDTMVariable("DSSTDTC", "Start Date/Time", DataType.CHAR,
                         CoreDesignation.EXPECTED, "Date/time in ISO 8601."),
            SDTMVariable("DSSTDY", "Study Day", DataType.NUM,
                         CoreDesignation.PERMISSIBLE, "Study day."),
        ],
    )


def _build_sv_domain() -> SDTMDomain:
    return SDTMDomain(
        code="SV", name="Subject Visits",
        observation_class=ObservationClass.SPECIAL_PURPOSE,
        description="Actual start and end dates/times of each subject's visits.",
        variables=[
            SDTMVariable("STUDYID", "Study Identifier", DataType.CHAR,
                         CoreDesignation.REQUIRED, "Unique identifier."),
            SDTMVariable("DOMAIN", "Domain Abbreviation", DataType.CHAR,
                         CoreDesignation.REQUIRED, "Two-character abbreviation."),
            SDTMVariable("USUBJID", "Unique Subject Identifier", DataType.CHAR,
                         CoreDesignation.REQUIRED, "Unique subject identifier."),
            SDTMVariable("VISITNUM", "Visit Number", DataType.NUM,
                         CoreDesignation.REQUIRED, "Clinical encounter number."),
            SDTMVariable("VISIT", "Visit Name", DataType.CHAR,
                         CoreDesignation.EXPECTED, "Protocol-defined visit description."),
            SDTMVariable("SVSTDTC", "Start Date/Time of Visit", DataType.CHAR,
                         CoreDesignation.EXPECTED, "Start date/time in ISO 8601."),
            SDTMVariable("SVENDTC", "End Date/Time of Visit", DataType.CHAR,
                         CoreDesignation.EXPECTED, "End date/time in ISO 8601."),
        ],
    )


_DOMAIN_BUILDERS = {
    "DM": _build_dm_domain, "AE": _build_ae_domain, "LB": _build_lb_domain,
    "VS": _build_vs_domain, "EX": _build_ex_domain, "CM": _build_cm_domain,
    "MH": _build_mh_domain, "DS": _build_ds_domain, "SV": _build_sv_domain,
}


def get_domain(code: str) -> SDTMDomain:
    builder = _DOMAIN_BUILDERS.get(code.upper())
    if builder is None:
        raise KeyError(f"Unknown SDTM domain: {code}")
    return builder()


def get_all_domains() -> dict[str, SDTMDomain]:
    return {code: builder() for code, builder in _DOMAIN_BUILDERS.items()}


def get_domain_codes() -> list[str]:
    return list(_DOMAIN_BUILDERS.keys())
