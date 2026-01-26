import typer
import sys
from asyncio import run
from pathlib import Path
from typing_extensions import Annotated

from ..config import load_config
from ..core.isce import download_orbits, run_files
from ..models import Platforms

app = typer.Typer()

ConfigFile = Annotated[Path, typer.Argument(help="Path to configuration TOML file")]

@app.command()
def isce(config_file: ConfigFile):
    """Download SLC images and a KML file based on config"""

    config = load_config(config_file)
    if not config:
        print("No config was specified on template file")
        sys.exit(1)

    if not config.download:
        print("No download config was specified on template file")
        sys.exit(1)

    if config.download.platform == Platforms.SENTINEL:
        pass
        # run(download_orbits.download_orbits(config))

    run_files.main()


if __name__ == "__main__":
    app()
