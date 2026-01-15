import typer
from pathlib import Path
from typing_extensions import Annotated

from ..config import load_config
from ..core.jobfiles.download_orbits import download_orbits

app = typer.Typer()

ConfigFile = Annotated[Path, typer.Argument(help="Path to configuration TOML file")]

@app.command()
def jobfiles(config_file: ConfigFile):
    """Download SLC images and a KML file based on config"""

    config = load_config(config_file)
    if not config:
        print("No download config was specified on template file")
        typer.Exit(1)

    download_orbits(config)


if __name__ == "__main__":
    app()
