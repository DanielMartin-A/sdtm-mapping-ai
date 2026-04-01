"""End-to-end SDTM mapping orchestrator.

Fixes applied:
- H1: Concurrent variable mapping via ThreadPoolExecutor
- C1: Uses shared LLMClient injected into predictor/mapper
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
import structlog

from sdtm_mapping_ai.config import get_settings
from sdtm_mapping_ai.models.domain_predictor import DomainPredictor
from sdtm_mapping_ai.models.llm_client import LLMClient
from sdtm_mapping_ai.models.variable_mapper import VariableMapper
from sdtm_mapping_ai.pipeline.confidence import ConfidenceScorer
from sdtm_mapping_ai.pipeline.profiler import DatasetProfile, SourceDataProfiler, VariableProfile
from sdtm_mapping_ai.rag.retriever import SDTMRetriever
from sdtm_mapping_ai.sdtm.conformance import ConformanceChecker, MappingRecord

logger = structlog.get_logger()


class SDTMMapper:
    def __init__(self, confidence_threshold: float | None = None) -> None:
        self.settings = get_settings()
        self.profiler = SourceDataProfiler()
        self.retriever = SDTMRetriever()
        # FIX C1: Single shared LLMClient for both predictor and mapper
        llm = LLMClient()
        self.domain_predictor = DomainPredictor(llm_client=llm)
        self.variable_mapper = VariableMapper(llm_client=llm)
        self.confidence_scorer = ConfidenceScorer(threshold=confidence_threshold)
        self.conformance_checker = ConformanceChecker()

        # BUG 4 FIX: Force eager initialization of lazy-loaded resources so that
        # concurrent threads in _map_dataset_concurrent don't race on first access.
        # Without this, multiple threads see None simultaneously and each construct
        # a separate client/collection — wasteful and non-deterministic.
        _ = llm.client
        _ = self.retriever.collection

    def map_study(self, input_dir: str | Path, dry_run: bool = False) -> pd.DataFrame:
        input_path = Path(input_dir)
        logger.info("pipeline_start", input_dir=str(input_path), dry_run=dry_run)
        start_time = time.time()

        profiles = self.profiler.profile_directory(input_path)
        if not profiles:
            logger.warning("no_datasets_found", dir=str(input_path))
            return pd.DataFrame()

        if dry_run:
            return self._dry_run_report(profiles)

        # FIX H1: Concurrent mapping across all variables
        all_mappings = []
        for profile in profiles:
            dataset_mappings = self._map_dataset_concurrent(profile)
            all_mappings.extend(dataset_mappings)

        df = pd.DataFrame(all_mappings)

        mapping_records = [
            MappingRecord(
                source_dataset=row["source_dataset"],
                source_variable=row["source_variable"],
                source_label=row["source_label"],
                target_domain=row["target_domain"],
                target_variable=row["target_variable"],
                mapping_type=row["mapping_type"],
                confidence=row["confidence"],
                justification=row["reasoning"],
            )
            for _, row in df.iterrows()
        ]
        report = self.conformance_checker.validate_full_study(mapping_records)

        elapsed = time.time() - start_time
        logger.info(
            "pipeline_complete", total_mappings=len(df),
            elapsed_seconds=round(elapsed, 1), conformance=report.summary(),
        )
        return df

    def map_dataframe(self, df: pd.DataFrame, name: str = "source") -> pd.DataFrame:
        profile = self.profiler.profile_dataframe(df, name)
        mappings = self._map_dataset_concurrent(profile)
        return pd.DataFrame(mappings)

    def _map_dataset_concurrent(self, profile: DatasetProfile) -> list[dict]:
        """FIX H1: Map variables concurrently using ThreadPoolExecutor."""
        mappings: list[dict] = []
        max_workers = self.settings.max_concurrent_calls

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            future_to_var = {
                pool.submit(self._map_single_variable, profile.name, var): var
                for var in profile.variables
            }
            for future in as_completed(future_to_var):
                var = future_to_var[future]
                try:
                    result = future.result()
                    mappings.append(result)
                except Exception as e:
                    logger.error("mapping_error", dataset=profile.name,
                                 variable=var.name, error=str(e))
                    mappings.append({
                        "source_dataset": profile.name,
                        "source_variable": var.name,
                        "source_label": var.label,
                        "target_domain": "UNKNOWN",
                        "target_variable": "UNKNOWN",
                        "mapping_type": "error",
                        "confidence": 0.0,
                        "raw_confidence": 0.0,
                        "domain_confidence": 0.0,
                        "domain_reasoning": "",
                        "status": "reject",
                        "reasoning": f"Error: {e}",
                        "transformation_logic": None,
                    })

        logger.info("dataset_mapped", dataset=profile.name, variables=len(mappings))
        return mappings

    def _map_single_variable(self, dataset_name: str, var: VariableProfile) -> dict:
        results = self.retriever.retrieve_for_source_variable(
            variable_name=var.name, variable_label=var.label,
            sample_values=var.sample_values, dataset_name=dataset_name,
        )
        rag_context = self.retriever.format_context(results)
        top_score = results[0].relevance_score if results else 0.0

        domain_pred = self.domain_predictor.predict(
            dataset_name=dataset_name, variable_name=var.name,
            variable_label=var.label, data_type=var.data_type,
            sample_values=var.sample_values, rag_context=rag_context,
        )

        var_mapping = self.variable_mapper.map_variable(
            dataset_name=dataset_name, variable_name=var.name,
            variable_label=var.label, target_domain=domain_pred.predicted_domain,
            data_type=var.data_type, sample_values=var.sample_values,
            rag_context=rag_context,
        )

        conf_result = self.confidence_scorer.score(
            mapping_id=f"{dataset_name}.{var.name}",
            llm_confidence=var_mapping.confidence,
            domain_retrieval_score=top_score,
        )

        return {
            "source_dataset": dataset_name,
            "source_variable": var.name,
            "source_label": var.label,
            "target_domain": domain_pred.predicted_domain,
            "domain_confidence": domain_pred.confidence,
            "domain_reasoning": domain_pred.reasoning,
            "target_variable": var_mapping.target_variable,
            "mapping_type": var_mapping.mapping_type,
            "confidence": conf_result.adjusted_confidence,
            "raw_confidence": conf_result.raw_confidence,
            "status": conf_result.status,
            "reasoning": var_mapping.reasoning,
            "transformation_logic": var_mapping.transformation_logic,
        }

    @staticmethod
    def _dry_run_report(profiles: list[DatasetProfile]) -> pd.DataFrame:
        """Generate a profiling-only report without making LLM calls."""
        rows = []
        for p in profiles:
            for v in p.variables:
                rows.append({
                    "source_dataset": p.name,
                    "source_variable": v.name,
                    "source_label": v.label,
                    "data_type": v.data_type,
                    "n_unique": v.n_unique,
                    "n_missing": v.n_missing,
                    "missing_pct": round(v.missing_pct, 1),
                    "sample_values": "; ".join(v.sample_values[:5]),
                    "target_domain": "(dry run)",
                    "target_variable": "(dry run)",
                    "mapping_type": "(dry run)",
                    "confidence": 0.0,
                    "status": "dry_run",
                    "reasoning": "Dry run — no LLM calls made",
                })
        return pd.DataFrame(rows)
