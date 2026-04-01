"""Evaluation CLI for SDTM mapping predictions.

Fixes applied:
- H5: configure_logging() called at entry point
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import typer
from rich.console import Console
from rich.table import Table

from sdtm_mapping_ai.evaluation.metrics import evaluate_mappings, precision_at_threshold
from sdtm_mapping_ai.utils.logging import configure_logging

app = typer.Typer(help="Evaluate SDTM mapping predictions")
console = Console()


@app.command()
def main(
    predictions: Path = typer.Option(..., "--predictions", "-p"),
    gold_standard: Path = typer.Option(..., "--gold-standard", "-g"),
    output: Path = typer.Option("results/evaluation.json", "--output", "-o"),
    thresholds: str = typer.Option("0.5,0.6,0.7,0.8,0.9", "--thresholds"),
) -> None:
    """Evaluate predicted SDTM mappings against a gold standard."""
    configure_logging()  # FIX H5

    pred_df = pd.read_csv(predictions)
    gold_df = pd.read_csv(gold_standard)

    pred_records = pred_df.to_dict("records")
    gold_records = gold_df.to_dict("records")

    metrics = evaluate_mappings(pred_records, gold_records)
    summary = metrics.summary()

    console.print("\n[bold blue]SDTM Mapping Evaluation[/bold blue]\n")

    table = Table(title="Overall Metrics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    for k, v in summary.items():
        table.add_row(k, str(v))
    console.print(table)

    thresh_list = [float(t) for t in thresholds.split(",")]
    thresh_results = []

    thresh_table = Table(title="Precision @ Confidence Threshold")
    thresh_table.add_column("Threshold")
    thresh_table.add_column("Coverage")
    thresh_table.add_column("Precision")
    thresh_table.add_column("Recall")

    for t in thresh_list:
        result = precision_at_threshold(pred_records, gold_records, t)
        thresh_results.append(result)
        thresh_table.add_row(
            f"{t:.1f}", f"{result['coverage']:.3f}",
            f"{result['precision']:.3f}", f"{result['recall']:.3f}",
        )
    console.print(thresh_table)

    output.parent.mkdir(parents=True, exist_ok=True)
    full_results = {
        "overall": summary,
        "precision_at_threshold": thresh_results,
        "confidence_bins": metrics.confidence_bins,
    }
    output.write_text(json.dumps(full_results, indent=2))
    console.print(f"\n[green]✓ Results saved to {output}[/green]")


if __name__ == "__main__":
    app()
