"""Evaluation metrics for SDTM mapping accuracy.

Fixes applied:
- M3: domain_confusion uses string keys for JSON serializability
- M4: walrus operator replaced with explicit loop for clarity
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field


@dataclass
class EvaluationMetrics:
    total: int = 0
    correct_domain: int = 0
    correct_variable: int = 0
    correct_both: int = 0
    # FIX M3: string keys instead of tuple keys for JSON serializability
    domain_confusion: dict[str, int] = field(default_factory=dict)
    confidence_bins: dict[str, dict[str, int]] = field(default_factory=dict)

    @property
    def domain_accuracy(self) -> float:
        return self.correct_domain / self.total if self.total > 0 else 0.0

    @property
    def variable_accuracy(self) -> float:
        return self.correct_variable / self.total if self.total > 0 else 0.0

    @property
    def end_to_end_accuracy(self) -> float:
        return self.correct_both / self.total if self.total > 0 else 0.0

    def summary(self) -> dict:
        return {
            "total_mappings": self.total,
            "domain_accuracy": round(self.domain_accuracy, 4),
            "variable_accuracy": round(self.variable_accuracy, 4),
            "end_to_end_accuracy": round(self.end_to_end_accuracy, 4),
        }


def evaluate_mappings(
    predictions: list[dict],
    gold_standard: list[dict],
) -> EvaluationMetrics:
    """Compare predicted mappings against a gold standard."""
    metrics = EvaluationMetrics()

    gold_lookup: dict[tuple[str, str], dict] = {}
    for g in gold_standard:
        key = (g["source_dataset"], g["source_variable"])
        gold_lookup[key] = g

    domain_pairs: list[tuple[str, str]] = []

    for pred in predictions:
        key = (pred["source_dataset"], pred["source_variable"])
        gold = gold_lookup.get(key)
        if gold is None:
            continue

        metrics.total += 1
        domain_correct = pred["target_domain"] == gold["target_domain"]
        variable_correct = pred["target_variable"] == gold["target_variable"]

        if domain_correct:
            metrics.correct_domain += 1
        if variable_correct:
            metrics.correct_variable += 1
        if domain_correct and variable_correct:
            metrics.correct_both += 1

        domain_pairs.append((gold["target_domain"], pred["target_domain"]))

        conf = pred.get("confidence", 0.0)
        bin_key = f"{int(conf * 10) / 10:.1f}"
        if bin_key not in metrics.confidence_bins:
            metrics.confidence_bins[bin_key] = {"total": 0, "correct": 0}
        metrics.confidence_bins[bin_key]["total"] += 1
        if domain_correct and variable_correct:
            metrics.confidence_bins[bin_key]["correct"] += 1

    # FIX M3: string keys for JSON serializability
    raw_counts = Counter(domain_pairs)
    metrics.domain_confusion = {
        f"{gold}->{pred}": count for (gold, pred), count in raw_counts.items()
    }

    return metrics


def precision_at_threshold(
    predictions: list[dict],
    gold_standard: list[dict],
    threshold: float,
) -> dict:
    """Compute precision/recall at a given confidence threshold.

    FIX M4: Replaced walrus-in-generator with explicit loop for clarity.
    """
    gold_lookup: dict[tuple[str, str], dict] = {}
    for g in gold_standard:
        gold_lookup[(g["source_dataset"], g["source_variable"])] = g

    above_threshold = [p for p in predictions if p.get("confidence", 0) >= threshold]

    # FIX M4: explicit loop instead of walrus-operator-in-sum
    tp = 0
    for p in above_threshold:
        key = (p["source_dataset"], p["source_variable"])
        gold = gold_lookup.get(key)
        if gold is None:
            continue
        if (p["target_domain"] == gold["target_domain"]
                and p["target_variable"] == gold["target_variable"]):
            tp += 1

    total = len(predictions)
    precision = tp / len(above_threshold) if above_threshold else 0.0
    recall = tp / len(gold_lookup) if gold_lookup else 0.0

    return {
        "threshold": threshold,
        "total_predictions": total,
        "above_threshold": len(above_threshold),
        "below_threshold": total - len(above_threshold),
        "true_positives": tp,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "coverage": round(len(above_threshold) / total, 4) if total else 0.0,
    }
