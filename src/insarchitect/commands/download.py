import typer
from pathlib import Path
from typing_extensions import Annotated

from ..config import load_config
from ..core.download.download import download_main

app = typer.Typer()

ConfigFile = Annotated[Path, typer.Argument(help="Path to configuration TOML file")]

@app.command()
def download(config_file: ConfigFile):
    """Download SLC images and a KML file based on config"""

    download_config = load_config(config_file)
    if not download_config:
        print("No download config was specified on template file")
        typer.Exit(1)

    download_main(download_config)


if __name__ == "__main__":
    app()
