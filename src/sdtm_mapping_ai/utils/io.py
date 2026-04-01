"""File I/O helpers for reading various clinical data formats."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import structlog

logger = structlog.get_logger()


def read_dataset(file_path: Path) -> pd.DataFrame | None:
    """Read a clinical dataset from CSV, TSV, or XPT format."""
    suffix = file_path.suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(file_path, low_memory=False)
    if suffix == ".xpt":
        try:
            import xport.v56

            with open(file_path, "rb") as f:
                library = xport.v56.load(f)
            for _name, df in library.items():
                return df
        except ImportError:
            logger.error("xport_not_installed", hint="pip install 'sdtm-mapping-ai[xpt]'")
            return None
        return None
    if suffix in (".tsv", ".txt"):
        return pd.read_csv(file_path, sep="\t", low_memory=False)
    logger.warning("unsupported_format", suffix=suffix)
    return None


def save_mapping_spec(df: pd.DataFrame, output_path: Path) -> None:
    """Save mapping specification to CSV or Excel."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    suffix = output_path.suffix.lower()

    if suffix == ".xlsx":
        df.to_excel(output_path, index=False, sheet_name="Mappings")
    else:
        df.to_csv(output_path, index=False)

    logger.info("spec_saved", path=str(output_path), rows=len(df))
