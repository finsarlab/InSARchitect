from pathlib import Path

import typer
from typing_extensions import Annotated

import insarchitect.cli.commands.download as download
import insarchitect.cli.commands.download_dem as download_dem

app = typer.Typer()

app.add_typer(download.app)
app.add_typer(download_dem.app)

if __name__ == "__main__":
    app()

