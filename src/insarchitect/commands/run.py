from pathlib import Path
from insarchitect.models import ProjectConfig
import typer
from typing_extensions import Annotated

from ..config import load_config
from ..core.download.download import download_main
from ..core.dem.dem import dem_main
from ..core.jobfiles.download_orbits import download_orbits

app = typer.Typer()

ConfigFile = Annotated[Path, typer.Argument(help="Path to configuration TOML file")]

@app.command()
def run(
    config_file: Annotated[Path, typer.Argument(help="Configuration file to process")]
):
    """
    Run all processing steps with the given config file
    """
    project_config = load_config(config_file)

    typer.echo(f"Processing config file: {config_file}")

    download_main(project_config)
    dem_main(project_config)
    download_orbits(project_config)

if __name__ == "__main__":
    app()

