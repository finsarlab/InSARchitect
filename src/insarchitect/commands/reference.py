import typer
from pathlib import Path
from typing_extensions import Annotated
from typing import Optional
from rich import print
import sys

app = typer.Typer()

@app.command()
def reference(
    path: Annotated[Path, typer.Argument(help="Path of the timeseries/velocity file or directory where are located")],
    file_type: Annotated[str, typer.Option(help="File(s) type: 'timeseries' or 'velocity'")] = None,
    lat: Annotated[Optional[float], typer.Option(help="Latitude of reference pixel (optional)")] = None,
    lon: Annotated[Optional[float], typer.Option(help="Longitude of reference pixel (optional)")] = None,
    ref_date: Annotated[str, typer.Option(help="Reference date (optional): 'zero_first', 'minRMS', or date in YYYYMMDD format")] = "zero_first",
):
    """
    Timeseries referencing in space and time, velocity referencing in space.
    
    Example:
    reference /path/to/ts/data --file-type timeseries --lat -23.6345 --lon -102.5528 --ref-date minRMS
    """
    
    # path validation
    path_obj = Path(path)
    if not path_obj.exists():
        print(f"[bold red]The path '{path}' doesn't exist[/bold red]")
        sys.exit(1)
    
    # file type validation
    valid_file_types = {"timeseries", "velocity"}
    if file_type not in valid_file_types:
        print(f"[bold red]File(s) type must be 'timeseries' or 'velocity'[/bold red]")
        sys.exit(1)

    # reference date validation
    valid_ref_dates = {"zero_first", "minRMS"}
    if ref_date not in valid_ref_dates and not is_valid_yyyymmdd(ref_date):
        print(f"[bold red]Reference date must be 'zero_first', 'minRMS' or YYYYMMDD format, received: {ref_date}[/bold red]")
        sys.exit(1)
    
    # received parameters
    print("[bold cyan]Received parameters:[/bold cyan]")
    if path_obj.is_dir():
        print(f"[bold]Directory path:[/bold] {path_obj.absolute()}")
    else:
        print(f"[bold]File path:[/bold] {path_obj.absolute()}")
    print(f"[bold]Latitude:[/bold] {lat if lat is not None else 'Unspecified'}")
    print(f"[bold]Longitude:[/bold] {lon if lon is not None else 'Unspecified'}")
    print(f"[bold]Reference date:[/bold] {ref_date}")
    
    print(f"[bold green]{'='*60}[/bold green]")
    print("[bold green]REFERENCING[/bold green]")
    print(f"[bold green]{'='*60}[/bold green]")
    # process_timeseries(path_obj, lat, lon, ref_date)

def is_valid_yyyymmdd(date_str: str) -> bool:
    """Date format YYYYMMDD validation."""
    if len(date_str) != 8 or not date_str.isdigit():
        return False
    year = int(date_str[:4])
    month = int(date_str[4:6])
    day = int(date_str[6:8])
    
    return 1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31

if __name__ == "__main__":
    app()