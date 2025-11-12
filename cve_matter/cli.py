"""Command-line interface for CVE Matter-Analysis OS."""
from pathlib import Path

import click
import yaml

from cve_matter.alignment.procrustes import ProcrustesAlignment
from cve_matter.arbiter.super_learner import SuperLearner
from cve_matter.evidence.model_selection import EvidenceAnalyzer
from cve_matter.ingest.nvd import NVDIngestor
from cve_matter.refractors.epsilon import EpsilonCalculator


@click.group()
@click.version_option(version="0.1.0")
@click.option('--config', type=click.Path(exists=True), default='config/matter.yaml',
              help='Path to configuration file')
@click.pass_context
def main(ctx: click.Context, config: str) -> None:
    """CVE Matter-Analysis OS - Blue-team vulnerability analysis platform.

    This tool provides defensive security capabilities for CVE analysis using
    advanced statistical methods. No offensive or cryptographic breaking capabilities.
    """
    ctx.ensure_object(dict)
    config_path = Path(config)
    if config_path.exists():
        with open(config_path) as f:
            ctx.obj['config'] = yaml.safe_load(f)
    else:
        ctx.obj['config'] = {}


@main.command()
@click.option('--source', default='nvd', help='Data source (nvd)')
@click.option('--output', type=click.Path(), default='data/cve_data.json',
              help='Output file path')
@click.option('--start-date', help='Start date for ingestion (YYYY-MM-DD)')
@click.option('--end-date', help='End date for ingestion (YYYY-MM-DD)')
@click.pass_context
def ingest(ctx: click.Context, source: str, output: str,
           start_date: str | None, end_date: str | None) -> None:
    """Ingest CVE data from NVD and other sources."""
    click.echo(f"Ingesting CVE data from {source}...")

    ingestor = NVDIngestor(config=ctx.obj.get('config', {}))
    data = ingestor.fetch_cves(start_date=start_date, end_date=end_date)

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ingestor.save_data(data, output_path)

    click.echo(f"✓ Ingested {len(data)} CVE records to {output}")


@main.command()
@click.option('--method', type=click.Choice(['procrustes', 'cca']), default='procrustes',
              help='Alignment method')
@click.option('--input', type=click.Path(exists=True), required=True,
              help='Input data file')
@click.option('--output', type=click.Path(), default='data/aligned_data.json',
              help='Output file path')
@click.pass_context
def align(ctx: click.Context, method: str, input: str, output: str) -> None:
    """Perform alignment analysis using Procrustes or CCA methods."""
    click.echo(f"Performing {method} alignment analysis...")

    if method == 'procrustes':
        aligner = ProcrustesAlignment(config=ctx.obj.get('config', {}))
    else:
        from cve_matter.alignment.cca import CCAAlignment
        aligner = CCAAlignment(config=ctx.obj.get('config', {}))

    result = aligner.align_from_file(Path(input))

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    aligner.save_results(result, output_path)

    click.echo(f"✓ Alignment complete, results saved to {output}")


@main.command()
@click.option('--input', type=click.Path(exists=True), required=True,
              help='Input data file')
@click.option('--output', type=click.Path(), default='data/predictions.json',
              help='Output file path')
@click.option('--n-folds', type=int, default=5, help='Number of CV folds')
@click.pass_context
def arbiter(ctx: click.Context, input: str, output: str, n_folds: int) -> None:
    """Run super-learner ensemble for CVE risk prediction."""
    click.echo("Running super-learner arbiter analysis...")

    learner = SuperLearner(config=ctx.obj.get('config', {}), n_folds=n_folds)
    predictions = learner.fit_predict_from_file(Path(input))

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    learner.save_predictions(predictions, output_path)

    click.echo(f"✓ Super-learner predictions saved to {output}")


@main.command()
@click.option('--input', type=click.Path(exists=True), required=True,
              help='Input data file')
@click.option('--output', type=click.Path(), default='data/epsilon_values.json',
              help='Output file path')
@click.option('--epsilon-range', nargs=2, type=float, default=(0.001, 0.1),
              help='Epsilon range (min max)')
@click.option('--use-gpu', is_flag=True, help='Use CUDA GPU acceleration')
@click.pass_context
def refract(ctx: click.Context, input: str, output: str,
            epsilon_range: tuple, use_gpu: bool) -> None:
    """Calculate epsilon refraction values for model refinement."""
    click.echo(f"Computing epsilon values (GPU: {use_gpu})...")

    calculator = EpsilonCalculator(
        config=ctx.obj.get('config', {}),
        use_gpu=use_gpu
    )
    results = calculator.compute_epsilon_sweep(
        Path(input),
        epsilon_min=epsilon_range[0],
        epsilon_max=epsilon_range[1]
    )

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    calculator.save_results(results, output_path)

    click.echo(f"✓ Epsilon calculations saved to {output}")


@main.command()
@click.option('--input', type=click.Path(exists=True), required=True,
              help='Input data file')
@click.option('--output', type=click.Path(), default='data/model_evidence.json',
              help='Output file path')
@click.option('--criteria', multiple=True, default=['bic', 'waic'],
              help='Information criteria to compute')
@click.pass_context
def evidence(ctx: click.Context, input: str, output: str, criteria: tuple) -> None:
    """Compute model evidence using BIC/WAIC criteria."""
    click.echo(f"Computing model evidence using {', '.join(criteria)}...")

    analyzer = EvidenceAnalyzer(config=ctx.obj.get('config', {}))
    results = analyzer.compute_evidence_from_file(Path(input), criteria=list(criteria))

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    analyzer.save_results(results, output_path)

    click.echo(f"✓ Model evidence analysis saved to {output}")


@main.command()
def version() -> None:
    """Display version information."""
    click.echo("CVE Matter-Analysis OS v0.1.0")
    click.echo("Python 3.11+ Blue-team Security Analysis Platform")


if __name__ == '__main__':
    main()
