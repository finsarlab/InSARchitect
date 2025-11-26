from pathlib import Path

import typer
from typing_extensions import Annotated

import insarchitect.cli.commands.download as download

app = typer.Typer()

app.add_typer(download.app)

if __name__ == "__main__":
    app()

