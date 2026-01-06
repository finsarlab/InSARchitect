from pathlib import Path

import typer
from typing_extensions import Annotated

import insarchitect.cli.commands.download as download
import insarchitect.cli.commands.download_dem as download_dem

app = typer.Typer()

app.add_typer(download.app)
app.add_typer(download_dem.app)

@app.command()
def run(
    config_file: Annotated[Path, typer.Argument(help="Configuration file to process")]
):
    """
    Run all processing steps with the given config file
    """
    typer.echo(f"Processing config file: {config_file}")
    download.download(config_file)
    download_dem.download_dem(config_file)

if __name__ == "__main__":
    app()

