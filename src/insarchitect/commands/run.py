from pathlib import Path
from insarchitect.models import ProjectConfig
import typer
from typing_extensions import Annotated
from typing import Callable, Optional

from ..config import load_config
from ..core.download.download import download_main
from ..core.dem.dem import dem_main
from ..core.jobfiles.download_orbits import download_orbits

app = typer.Typer()

ConfigFile = Annotated[Path, typer.Argument(help="Path to configuration TOML file")]

STEPS = {
    "download": (download_main, "Download step"),
    "dem": (dem_main, "DEM processing step"),
    "jobfiles": (download_orbits, "Job files generation (orbits)"),
    "isce": (None, "ISCE processing step (to be implemented)"),
}

# execution order
STEP_ORDER = ["download", "dem", "jobfiles", "isce"]

def _get_step_function(step_name: str) -> Optional[Callable]:
    """Get the function for a step, handling not-yet-implemented steps"""
    func, _ = STEPS[step_name]
    if func is None:
        typer.echo(f"Warning: {step_name} step is not yet implemented")
        return None
    return func

@app.command()
def run(
    config_file: Annotated[Path, typer.Argument(help="Configuration file to process")],
    download: Annotated[bool, typer.Option("--download", help="Run download step")] = False,
    dem: Annotated[bool, typer.Option("--dem", help="Run DEM processing step")] = False,
    jobfiles: Annotated[bool, typer.Option("--jobfiles", help="Run job files generation step")] = False,
    isce: Annotated[bool, typer.Option("--isce", help="Run ISCE processing step (to be implemented)")] = False,
    start: Annotated[Optional[str], typer.Option("--start", help="Start from a specific step (e.g., --start jobfiles)")] = None,
):
    """
    Run processing steps with the given config file
    
    If no flags are specified, all steps will be executed.
    Use flags to run only specific steps (e.g., --download --dem).
    Use --start to run from a specific step onwards (e.g., --start jobfiles).
    """
    project_config = load_config(config_file)
    typer.echo(f"Processing config file: {config_file}")

    if start is not None:
        if start not in STEPS:
            typer.echo(f"Error: Unknown step '{start}'. Available steps: {', '.join(STEPS.keys())}")
            raise typer.Exit(1)
        
        # find the index of the start step
        try:
            start_index = STEP_ORDER.index(start)
        except ValueError:
            typer.echo(f"Error: Step '{start}' is not in the execution order.")
            raise typer.Exit(1)
        
        # get all steps from start onwards
        selected_steps = set(STEP_ORDER[start_index:])
        typer.echo(f"Starting from step '{start}'...")
    else:
        # just add the flag parameter below if you add a new step
        # add as string to find the step name in the STEP_ORDER list
        flag_to_step = {
            "download": download,
            "dem": dem,
            "jobfiles": jobfiles,
            "isce": isce,
        }
        
        # determine which steps to run
        selected_steps = {step for step, flag in flag_to_step.items() if flag}
        
        # if no flags specified, run all available steps (e.g. insarchitect run <config_file>)
        if not selected_steps:
            selected_steps = set(STEPS.keys())
            typer.echo("Running all processing steps...")
        else:
            typer.echo("Running selected processing steps...")
    
    # execute steps in defined order
    for step_name in STEP_ORDER:
        if step_name in selected_steps:
            _, description = STEPS[step_name]
            typer.echo(f"Running {description}...")
            func = _get_step_function(step_name)
            if func:
                func(project_config)

if __name__ == "__main__":
    app()

