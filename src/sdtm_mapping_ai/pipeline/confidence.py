"""Confidence scoring and thresholding for SDTM mappings.

Fixes applied:
- M2: threshold=0.0 falsy-value bug fixed with `is not None` check
"""

from __future__ import annotations

from dataclasses import dataclass

import structlog

from sdtm_mapping_ai.config import get_settings

logger = structlog.get_logger()


@dataclass
class ConfidenceResult:
    mapping_id: str
    raw_confidence: float
    adjusted_confidence: float
    status: str  # "auto_accept", "human_review", "reject"
    reason: str | None = None


class ConfidenceScorer:
    def __init__(self, threshold: float | None = None) -> None:
        # FIX M2: `threshold or default` treats 0.0 as falsy → use `is not None`
        self.threshold = threshold if threshold is not None else get_settings().confidence_threshold

    def score(
        self,
        mapping_id: str,
        llm_confidence: float,
        domain_retrieval_score: float = 1.0,
        variable_retrieval_score: float = 1.0,
    ) -> ConfidenceResult:
        retrieval_factor = (domain_retrieval_score + variable_retrieval_score) / 2
        adjusted = llm_confidence * (0.7 + 0.3 * retrieval_factor)
        adjusted = min(max(adjusted, 0.0), 1.0)

        if adjusted >= self.threshold:
            status = "auto_accept"
            reason = None
        elif adjusted >= self.threshold * 0.5:
            status = "human_review"
            reason = f"Below threshold ({adjusted:.2f} < {self.threshold:.2f})"
        else:
            status = "reject"
            reason = f"Very low confidence ({adjusted:.2f})"

        return ConfidenceResult(
            mapping_id=mapping_id, raw_confidence=llm_confidence,
            adjusted_confidence=adjusted, status=status, reason=reason,
        )

    def filter_mappings(
        self, mappings: list[dict]
    ) -> tuple[list[dict], list[dict], list[dict]]:
        auto_accept, review, reject = [], [], []
        for m in mappings:
            conf = m.get("confidence", 0.0)
            if conf >= self.threshold:
                auto_accept.append(m)
            elif conf >= self.threshold * 0.5:
                review.append(m)
            else:
                reject.append(m)
        logger.info("confidence_filter", auto_accept=len(auto_accept),
                    review=len(review), reject=len(reject))
        return auto_accept, review, reject
