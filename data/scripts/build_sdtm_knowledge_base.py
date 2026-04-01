#!/usr/bin/env python3
"""Build SDTM knowledge base JSON files from built-in standards definitions."""

from __future__ import annotations

import json
from pathlib import Path

from sdtm_mapping_ai.sdtm.controlled_terminology import CT_VERSION, ControlledTerminology
from sdtm_mapping_ai.sdtm.standards import get_all_domains


def main() -> None:
    output_dir = Path(__file__).resolve().parent.parent / "sdtm_standards"
    output_dir.mkdir(parents=True, exist_ok=True)

    domains = get_all_domains()
    domains_export = {}
    for code, domain in domains.items():
        domains_export[code] = {
            "name": domain.name,
            "observation_class": domain.observation_class.value,
            "description": domain.description,
            "variables": [
                {
                    "name": v.name, "label": v.label,
                    "data_type": v.data_type.value, "core": v.core.value,
                    "description": v.description, "codelist": v.codelist,
                }
                for v in domain.variables
            ],
        }

    domains_path = output_dir / "sdtm_domains.json"
    domains_path.write_text(json.dumps(domains_export, indent=2), encoding="utf-8")
    print(f"✓ Exported {len(domains_export)} domains to {domains_path}")

    ct = ControlledTerminology()
    ct_export = {}
    for name in ct.codelist_names:
        cl = ct.get_codelist(name)
        if cl:
            ct_export[name] = {
                "code": cl.code, "name": cl.name,
                "terms": cl.terms, "extensible": cl.extensible,
            }

    ct_path = output_dir / "controlled_terminology.json"
    ct_path.write_text(json.dumps(ct_export, indent=2), encoding="utf-8")
    print(f"✓ Exported {len(ct_export)} codelists to {ct_path} (CT version: {CT_VERSION})")


if __name__ == "__main__":
    main()
