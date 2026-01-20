import typer
from .commands import download, jobfiles, dem, run

app = typer.Typer()

app.add_typer(download.app)
app.add_typer(dem.app)
app.add_typer(jobfiles.app)
app.add_typer(run.app)

if __name__ == "__main__":
    app()
