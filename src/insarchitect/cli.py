import typer
from .commands import download, jobfiles, dem, run, reference

app = typer.Typer()

app.add_typer(download.app)
app.add_typer(dem.app)
app.add_typer(jobfiles.app)
app.add_typer(run.app)
app.add_typer(reference.app)

if __name__ == "__main__":
    app()
