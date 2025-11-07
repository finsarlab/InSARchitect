from pathlib import Path

from typing import Annotated
import typer

app = typer.Typer(help="ASF SLC and Burst downloads")

@app.command(name="download")
def download(
        config: Annotated[
            Path,
            typer.Argument(
                exists=True,
                file_okay=True,
                dir_okay=False,
                writable=True,
                readable=True,
                resolve_path=True
            )]):

    print(config)

