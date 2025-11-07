from pathlib import Path

import typer
from typing_extensions import Annotated

from insarchitect.cli.commands.download import app as download

app = typer.Typer()

app.add_typer(download)

if __name__ == "__main__":
    app()

