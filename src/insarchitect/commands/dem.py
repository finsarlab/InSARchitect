import typer
from pathlib import Path
from typing_extensions import Annotated

from ..config import load_config
from ..core.dem.dem import dem_main

app = typer.Typer()

ConfigFile = Annotated[Path, typer.Argument(help="Path to configuration TOML file")]

@app.command()
def dem(config_file: ConfigFile):
    """Creates DEM based on template file and KML bounding box."""

    project_config = load_config(config_file)
    dem_main(project_config)

if __name__ == "__main__":
    app()