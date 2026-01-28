import typer
import sys
from asyncio import run
from pathlib import Path
from typing_extensions import Annotated

from ..config import load_config
from ..core.isce import download_orbits, create_run_files, create_job_files
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
        #run(download_orbits.download_orbits(config))
        pass

    create_run_files.run_files(config)
    create_job_files.job_files(config)


if __name__ == "__main__":
    app()
