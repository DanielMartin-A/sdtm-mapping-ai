"""LLM-based SDTM variable-level mapping with confidence scoring.

Fixes applied:
- C1: Uses shared LLMClient
- M5: Uses sanitize_for_prompt
"""

from __future__ import annotations

from dataclasses import dataclass

import structlog

from sdtm_mapping_ai.models.llm_client import LLMClient, sanitize_for_prompt
from sdtm_mapping_ai.sdtm.standards import get_domain

logger = structlog.get_logger()

VARIABLE_MAPPING_PROMPT = """You are an expert SDTM programmer.
Map the source variable below to the correct SDTM target variable in domain {domain_code}.

## Target Domain: {domain_code} — {domain_name}
{domain_context}

## Retrieved SDTM Context
{rag_context}

## Source Variable
- Dataset: {dataset_name}
- Variable: {variable_name}
- Label: {variable_label}
- Data Type: {data_type}
- Sample Values: {sample_values}

## Instructions
Respond ONLY with valid JSON (no markdown fences):
{{"target_variable": "<SDTM variable name>",
  "mapping_type": "<direct|derivation|recoding|hardcode|unmapped>",
  "confidence": <float 0.0 to 1.0>, "reasoning": "<brief explanation>",
  "transformation_logic": "<description of any needed transformation or null>"}}
"""

SYSTEM_MSG = "You are an expert SDTM programmer. Respond only in JSON."


@dataclass
class VariableMapping:
    source_dataset: str
    source_variable: str
    source_label: str
    target_domain: str
    target_variable: str
    mapping_type: str
    confidence: float
    reasoning: str
    transformation_logic: str | None = None


class VariableMapper:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self._llm = llm_client or LLMClient()

    def map_variable(
        self,
        dataset_name: str,
        variable_name: str,
        variable_label: str,
        target_domain: str,
        data_type: str = "Char",
        sample_values: list[str] | None = None,
        rag_context: str = "",
    ) -> VariableMapping:
        try:
            domain = get_domain(target_domain)
        except KeyError:
            return VariableMapping(
                source_dataset=dataset_name, source_variable=variable_name,
                source_label=variable_label, target_domain=target_domain,
                target_variable="UNKNOWN", mapping_type="unmapped",
                confidence=0.0, reasoning=f"Unknown domain: {target_domain}",
            )

        prompt = VARIABLE_MAPPING_PROMPT.format(
            domain_code=target_domain,
            domain_name=domain.name,
            domain_context=domain.to_context_string(),
            rag_context=rag_context or "(No context)",
            dataset_name=dataset_name,
            variable_name=variable_name,
            variable_label=variable_label,
            data_type=data_type,
            sample_values=sanitize_for_prompt(sample_values or []),
        )

        try:
            data = self._llm.call_json(prompt, system=SYSTEM_MSG)
            return VariableMapping(
                source_dataset=dataset_name,
                source_variable=variable_name,
                source_label=variable_label,
                target_domain=target_domain,
                target_variable=data.get("target_variable", "UNKNOWN"),
                mapping_type=data.get("mapping_type", "unmapped"),
                confidence=min(max(float(data.get("confidence", 0.5)), 0.0), 1.0),
                reasoning=data.get("reasoning", ""),
                transformation_logic=data.get("transformation_logic"),
            )
        except (ValueError, KeyError) as e:
            logger.error("variable_mapping_error", error=str(e),
                         dataset=dataset_name, variable=variable_name)
            return VariableMapping(
                source_dataset=dataset_name, source_variable=variable_name,
                source_label=variable_label, target_domain=target_domain,
                target_variable="UNKNOWN", mapping_type="unmapped",
                confidence=0.0, reasoning=f"Error: {e}",
            )
