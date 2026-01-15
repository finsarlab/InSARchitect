from pathlib import Path

import typer
from .commands import download
from .commands import dem

app = typer.Typer()

app.add_typer(download.app)
app.add_typer(dem.app)

if __name__ == "__main__":
    app()