"""Source data profiler — reads input datasets and extracts metadata.

Fixes applied:
- H4: Supports both CSV and XPT files via glob patterns
- M6: Uses nrows=1000 for profiling to avoid loading huge CSVs into memory
- L5: Accepts optional label_map dict for better variable labels
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import structlog

logger = structlog.get_logger()

# File extensions the profiler will pick up
_SUPPORTED_EXTENSIONS = ("*.csv", "*.xpt")


@dataclass
class VariableProfile:
    name: str
    label: str
    data_type: str  # "Char" or "Num"
    n_unique: int
    n_missing: int
    n_total: int
    sample_values: list[str] = field(default_factory=list)

    @property
    def missing_pct(self) -> float:
        return (self.n_missing / self.n_total * 100) if self.n_total > 0 else 0.0


@dataclass
class DatasetProfile:
    name: str
    file_path: str
    n_rows: int
    n_cols: int
    variables: list[VariableProfile] = field(default_factory=list)


class SourceDataProfiler:
    """Profiles source datasets to extract metadata for SDTM mapping."""

    def __init__(self, label_map: dict[str, str] | None = None) -> None:
        """Initialize with optional label_map: {variable_name: label_string}."""
        self.label_map = label_map or {}

    def profile_directory(self, dir_path: Path) -> list[DatasetProfile]:
        """Profile all CSV and XPT files in a directory.

        FIX H4: Globs both *.csv and *.xpt so downloaded pilot data is found.
        """
        profiles = []
        files = []
        for pattern in _SUPPORTED_EXTENSIONS:
            files.extend(dir_path.glob(pattern))
        for f in sorted(set(files)):
            profile = self._profile_file(f)
            if profile:
                profiles.append(profile)
        logger.info("profiling_complete", directory=str(dir_path), datasets=len(profiles))
        return profiles

    def _profile_file(self, file_path: Path) -> DatasetProfile | None:
        """Read and profile a single file (CSV or XPT)."""
        suffix = file_path.suffix.lower()
        try:
            if suffix == ".csv":
                # FIX M6: Read only a sample for profiling to control memory
                df_sample = pd.read_csv(file_path, nrows=1000, low_memory=False)
                # Get full row count cheaply
                # BUG 3 FIX: max(..., 0) prevents negative count on empty files
                with open(file_path, encoding="utf-8", errors="replace") as fh:
                    total_rows = max(sum(1 for _ in fh) - 1, 0)
            elif suffix == ".xpt":
                df_sample = self._read_xpt(file_path)
                if df_sample is None:
                    return None
                total_rows = len(df_sample)
            else:
                return None
        except Exception as e:
            logger.error("file_read_error", file=str(file_path), error=str(e))
            return None

        variables = self._profile_columns(df_sample)
        return DatasetProfile(
            name=file_path.stem,
            file_path=str(file_path),
            n_rows=total_rows,
            n_cols=len(df_sample.columns),
            variables=variables,
        )

    def _read_xpt(self, file_path: Path) -> pd.DataFrame | None:
        """Read a SAS XPT file. Requires optional `xport` dependency."""
        try:
            import xport.v56

            with open(file_path, "rb") as f:
                library = xport.v56.load(f)
            for _name, df in library.items():
                return df
        except ImportError:
            logger.error("xport_not_installed", hint="pip install 'sdtm-mapping-ai[xpt]'")
        except Exception as e:
            logger.error("xpt_read_error", file=str(file_path), error=str(e))
        return None

    def _profile_columns(self, df: pd.DataFrame) -> list[VariableProfile]:
        variables = []
        for col in df.columns:
            series = df[col]
            dtype = "Num" if pd.api.types.is_numeric_dtype(series) else "Char"
            non_null = series.dropna()
            samples = [str(v) for v in non_null.unique()[:10]]

            # FIX L5: Use label_map if available, otherwise generate from column name
            label = self.label_map.get(col, col.replace("_", " ").title())

            variables.append(VariableProfile(
                name=col, label=label, data_type=dtype,
                n_unique=int(series.nunique()),
                n_missing=int(series.isna().sum()),
                n_total=len(series),
                sample_values=samples,
            ))
        return variables

    def profile_dataframe(self, df: pd.DataFrame, name: str = "source") -> DatasetProfile:
        variables = self._profile_columns(df)
        return DatasetProfile(
            name=name, file_path="", n_rows=len(df), n_cols=len(df.columns), variables=variables,
        )
