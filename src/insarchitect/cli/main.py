from pathlib import Path

import typer
from typing_extensions import Annotated

import insarchitect.cli.commands.download as download
import insarchitect.cli.commands.download_dem as download_dem

app = typer.Typer()

app.add_typer(download.app)
app.add_typer(download_dem.app)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    config_file: Annotated[Path, typer.Argument()] = None
):
    """
    Main entry point. Runs all of the processing
    """
    if ctx.invoked_subcommand is not None:
        return

    if config_file is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()

    typer.echo(f"Processing config file: {config_file}")
    download.download(config_file)
    download_dem.download_dem(config_file)


if __name__ == "__main__":
    app()

