import typer
from pathlib import Path
from typing_extensions import Annotated

from ..config import load_config
from ..core.download.download import download_main

app = typer.Typer()

ConfigFile = Annotated[Path, typer.Argument(help="Path to configuration TOML file")]

@app.command(name="download")
def download(config_file: ConfigFile):
    """
    Download SLC images and a KML file based on config

    Example:
        pixi run insarchitect download <template>
    """

    project_config = load_config(config_file)
    download_main(project_config)

if __name__ == "__main__":
    app()