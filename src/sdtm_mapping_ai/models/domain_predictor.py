"""LLM-based SDTM domain prediction.

Fixes applied:
- C1: Uses shared LLMClient (no duplicated init/call code)
- C3: Inherits retry logic from LLMClient
- M5: Uses sanitize_for_prompt for sample values
"""

from __future__ import annotations

from dataclasses import dataclass

import structlog

from sdtm_mapping_ai.models.llm_client import LLMClient, sanitize_for_prompt
from sdtm_mapping_ai.sdtm.standards import get_all_domains, get_domain_codes

logger = structlog.get_logger()

DOMAIN_PREDICTION_PROMPT = """You are an expert SDTM (Study Data Tabulation Model) programmer.
Given the source dataset metadata below, predict the most appropriate SDTM domain.

## Available SDTM Domains
{domain_list}

## Retrieved SDTM Context
{rag_context}

## Source Data
- Dataset: {dataset_name}
- Variable: {variable_name}
- Label: {variable_label}
- Data Type: {data_type}
- Sample Values: {sample_values}

## Instructions
Respond ONLY with valid JSON (no markdown fences):
{{"predicted_domain": "<two-letter SDTM domain code>",
  "confidence": <float 0.0 to 1.0>, "reasoning": "<one-sentence explanation>",
  "alternative_domain": "<second-best domain code or null>"}}
"""

SYSTEM_MSG = "You are an expert SDTM programmer. Respond only in JSON."


@dataclass
class DomainPrediction:
    predicted_domain: str
    confidence: float
    reasoning: str
    alternative_domain: str | None = None


class DomainPredictor:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self._llm = llm_client or LLMClient()

    def predict(
        self,
        dataset_name: str,
        variable_name: str,
        variable_label: str,
        data_type: str = "Char",
        sample_values: list[str] | None = None,
        rag_context: str = "",
    ) -> DomainPrediction:
        domains = get_all_domains()
        domain_list = "\n".join(
            f"- {code}: {d.name} ({d.observation_class.value})"
            for code, d in domains.items()
        )

        prompt = DOMAIN_PREDICTION_PROMPT.format(
            domain_list=domain_list,
            rag_context=rag_context or "(No context retrieved)",
            dataset_name=dataset_name,
            variable_name=variable_name,
            variable_label=variable_label,
            data_type=data_type,
            sample_values=sanitize_for_prompt(sample_values or []),
        )

        try:
            data = self._llm.call_json(prompt, system=SYSTEM_MSG)
            return self._parse_dict(data)
        except (ValueError, KeyError) as e:
            logger.error("domain_prediction_error", error=str(e))
            return DomainPrediction(
                predicted_domain="DM", confidence=0.0, reasoning=f"Error: {e}",
            )

    @staticmethod
    def _parse_dict(data: dict) -> DomainPrediction:
        domain = data["predicted_domain"].upper()
        if domain not in get_domain_codes():
            logger.warning("invalid_domain_predicted", domain=domain)
            domain = "DM"
        return DomainPrediction(
            predicted_domain=domain,
            confidence=min(max(float(data.get("confidence", 0.5)), 0.0), 1.0),
            reasoning=data.get("reasoning", ""),
            alternative_domain=data.get("alternative_domain"),
        )
