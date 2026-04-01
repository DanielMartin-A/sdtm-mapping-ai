"""CLI entry point for the SDTM mapping pipeline.

Fixes applied:
- H5: configure_logging() called at entry point
- L6: --verbose flag wired to LOG_LEVEL override
- Added --dry-run flag
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from sdtm_mapping_ai.pipeline.mapper import SDTMMapper
from sdtm_mapping_ai.utils.logging import configure_logging

app = typer.Typer(help="SDTM Mapping AI Pipeline")
console = Console()


@app.command()
def main(
    input_dir: Path = typer.Option(..., "--input", "-i", help="Input directory with source files"),
    output_dir: Path = typer.Option("results", "--output", "-o", help="Output directory"),
    threshold: float = typer.Option(0.70, "--threshold", "-t", help="Confidence threshold"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable DEBUG logging"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Profile only, no LLM calls"),
) -> None:
    """Run the SDTM mapping pipeline on source data."""
    # FIX H5 + L6: Initialize logging, honor --verbose
    configure_logging(level="DEBUG" if verbose else None)

    output_dir.mkdir(parents=True, exist_ok=True)

    console.print("\n[bold blue]SDTM Mapping AI Pipeline[/bold blue]")
    console.print(f"  Input:     {input_dir}")
    console.print(f"  Output:    {output_dir}")
    console.print(f"  Threshold: {threshold}")
    if dry_run:
        console.print("  Mode:      [yellow]DRY RUN (no LLM calls)[/yellow]")
    console.print()

    mapper = SDTMMapper(confidence_threshold=threshold)
    results = mapper.map_study(input_dir, dry_run=dry_run)

    if results.empty:
        console.print("[yellow]No mappings generated. Check input data.[/yellow]")
        raise typer.Exit(1)

    results.to_csv(output_dir / "mappings.csv", index=False)
    console.print(
        f"\n[green]✓ Saved {len(results)} mappings to {output_dir / 'mappings.csv'}[/green]"
    )

    table = Table(title="Mapping Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("Total variables mapped", str(len(results)))
    table.add_row("Unique domains", str(results["target_domain"].nunique()))
    if not dry_run:
        table.add_row("Auto-accepted", str(len(results[results["status"] == "auto_accept"])))
        table.add_row("Needs review", str(len(results[results["status"] == "human_review"])))
        table.add_row("Rejected", str(len(results[results["status"] == "reject"])))
        table.add_row("Mean confidence", f"{results['confidence'].mean():.3f}")
    console.print(table)


if __name__ == "__main__":
    app()
