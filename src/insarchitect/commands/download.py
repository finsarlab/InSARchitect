import typer
from pathlib import Path
from typing_extensions import Annotated

from ..config import get_config_section

app = typer.Typer()

ConfigFile = Annotated[Path, typer.Argument(help="Path to configuration TOML file")]

@app.command()
def download(config_file: ConfigFile):
    """Download SLC images and a KML file based on config"""

    download_config = get_config_section(config_file, "download")
    if not download_config:
        print("No download config was specified on template file")
        typer.Exit(1)


if __name__ == "__main__":
    app()
