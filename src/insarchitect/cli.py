import typer
from .commands import download

app = typer.Typer()

app.add_typer(download.app)

if __name__ == "__main__":
    app()
