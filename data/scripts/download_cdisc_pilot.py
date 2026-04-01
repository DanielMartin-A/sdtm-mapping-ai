#!/usr/bin/env python3
"""Download CDISC Pilot 01 datasets from the public GitHub repository.

Source: https://github.com/cdisc-org/sdtm-adam-pilot-project
License: Public use

Fixes applied:
- H4: Downloads XPT files AND converts them to CSV so the profiler finds them
- L4: Removed unused `import sys`
"""

from __future__ import annotations

from pathlib import Path

import httpx

BASE_URL = (
    "https://raw.githubusercontent.com/cdisc-org/"
    "sdtm-adam-pilot-project/master/updated-pilot-submission-package/"
    "900172/m5/datasets/cdiscpilot01/tabulations/sdtm"
)

DOMAINS = ["dm", "ae", "cm", "ds", "ex", "lb", "mh", "sv", "vs"]


def download_file(url: str, dest: Path) -> bool:
    try:
        response = httpx.get(url, follow_redirects=True, timeout=30)
        response.raise_for_status()
        dest.write_bytes(response.content)
        print(f"  ✓ {dest.name} ({len(response.content):,} bytes)")
        return True
    except httpx.HTTPError as e:
        print(f"  ✗ {dest.name}: {e}")
        return False


def convert_xpt_to_csv(xpt_path: Path) -> bool:
    """FIX H4: Convert XPT to CSV so the profiler's *.csv glob finds files."""
    try:
        import xport.v56

        with open(xpt_path, "rb") as f:
            library = xport.v56.load(f)
        for _name, df in library.items():
            csv_path = xpt_path.with_suffix(".csv")
            df.to_csv(csv_path, index=False)
            print(f"  → Converted to {csv_path.name} ({len(df)} rows)")
            return True
    except ImportError:
        print("  ⚠ xport not installed — XPT files will not be converted to CSV.")
        print("    Install with: pip install 'sdtm-mapping-ai[xpt]'")
    except Exception as e:
        print(f"  ✗ Conversion failed for {xpt_path.name}: {e}")
    return False


def main() -> None:
    output_dir = Path(__file__).resolve().parent.parent / "pilot01"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Downloading CDISC Pilot 01 SDTM datasets to {output_dir}\n")
    print("Source: cdisc-org/sdtm-adam-pilot-project (public GitHub)\n")

    success = 0
    for domain in DOMAINS:
        url = f"{BASE_URL}/{domain}.xpt"
        dest = output_dir / f"{domain}.xpt"
        if download_file(url, dest):
            success += 1
            convert_xpt_to_csv(dest)

    print(f"\nDownloaded {success}/{len(DOMAINS)} datasets.")

    # Create gold standard for evaluation
    gold_path = output_dir / "gold_standard.csv"
    if not gold_path.exists():
        gold_path.write_text(
            "source_dataset,source_variable,target_domain,target_variable\n"
            "dm,STUDYID,DM,STUDYID\n"
            "dm,USUBJID,DM,USUBJID\n"
            "dm,SUBJID,DM,SUBJID\n"
            "dm,SITEID,DM,SITEID\n"
            "dm,AGE,DM,AGE\n"
            "dm,SEX,DM,SEX\n"
            "dm,RACE,DM,RACE\n"
            "dm,ARMCD,DM,ARMCD\n"
            "dm,ARM,DM,ARM\n"
            "ae,AETERM,AE,AETERM\n"
            "ae,AEDECOD,AE,AEDECOD\n"
            "ae,AESEV,AE,AESEV\n"
            "ae,AESER,AE,AESER\n"
            "ae,AESTDTC,AE,AESTDTC\n"
            "vs,VSTESTCD,VS,VSTESTCD\n"
            "vs,VSTEST,VS,VSTEST\n"
            "vs,VSORRES,VS,VSORRES\n"
            "vs,VSORRESU,VS,VSORRESU\n"
            "lb,LBTESTCD,LB,LBTESTCD\n"
            "lb,LBTEST,LB,LBTEST\n"
            "lb,LBORRES,LB,LBORRES\n"
            "lb,LBORRESU,LB,LBORRESU\n",
            encoding="utf-8",
        )
        print("✓ Created gold_standard.csv")


if __name__ == "__main__":
    main()
