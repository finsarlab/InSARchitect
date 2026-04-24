import typer
from pathlib import Path
from typing_extensions import Annotated
from typing import Optional
from rich import print
from datetime import datetime
import sys

from ..models import ReferenceFileType
from ..core.reference.reference import reference_main

app = typer.Typer()

@app.command()
def reference(
    path: Annotated[Path, typer.Argument(help="Path of the timeseries/velocity file or directory where are located")],
    file_type: Annotated[ReferenceFileType, typer.Option(help="File(s) type: 'timeseries' or 'velocity'")],
    lat: Annotated[Optional[float], typer.Option(help="Latitude of reference pixel (optional)")] = None,
    lon: Annotated[Optional[float], typer.Option(help="Longitude of reference pixel (optional)")] = None,
    meters: Annotated[Optional[int], typer.Option(help="Limit in meters for finding the nearest point")] = 100,
    ref_date: Annotated[str, typer.Option(help="Reference date (optional): 'zero_first', 'minRMS', or date in YYYYMMDD format")] = 'zero_first',
    output_dir: Annotated[Path, typer.Option(help="Path where referenced files will be storage")] = None
):
    """
    Timeseries referencing in space and time, velocity referencing in space.
    
    Example:
    - Velocity
        reference /path/to/velocity/data --file-type velocity --lat -23.6345 --lon -102.5528 --meters 50
    - Timeseries
        reference /path/to/ts/data --file-type timeseries --lat -23.6345 --lon -102.5528 --ref-date minRMS
    """
    
    # path validation
    path_obj = Path(path)
    if not path_obj.exists():
        print(f"[bold red]The path '{path}' doesn't exist[/bold red]")
        sys.exit(1)

    # latitude and longitude validation
    if file_type == ReferenceFileType.velocity and (lat is None or lon is None):
        print("[bold red]For velocity file(s) latitude and longitude are required[/bold red]")
        sys.exit(1)

    if (lat is not None and lon is None) or (lat is None and lon is not None): 
        print("[bold red]Both latitude and longitude are required[/bold red]")
        sys.exit(1)

    if lat is not None:
        if lat < -90 or lat > 90:
            print("[bold red]Latitude must be within -90 and 90[/bold red]")
            sys.exit(1)

    if lon is not None:
        if lon < -180 or lon > 180:
            print("[bold red]Longitude must be within -180 and 180[/bold red]")
            sys.exit(1)

    # reference date validation
    valid_ref_dates = {"zero_first", "minRMS"}
    if ref_date not in valid_ref_dates and not is_valid_yyyymmdd(ref_date):
        print(f"[bold red]Reference date must be 'zero_first', 'minRMS' or YYYYMMDD format, received: {ref_date}[/bold red]")
        sys.exit(1)
    
    # output dir path creation
    if output_dir is None:
        output_dir = path_obj.parent.joinpath("reference")
    
    # received parameters
    print("[bold cyan]Received parameters:[/bold cyan]")
    if path_obj.is_dir():
        print(f"[bold]Directory path:[/bold] {path_obj.absolute()}")
    else:
        print(f"[bold]File path:[/bold] {path_obj.absolute()}")
    print(f"[bold]File type:[/bold] {file_type.value}")
    if lat is not None:
        print(f"[bold]Latitude:[/bold] {lat}")
    if lon is not None:
        print(f"[bold]Longitude:[/bold] {lon}")
    if file_type == ReferenceFileType.timeseries:
        print(f"[bold]Reference date:[/bold] {ref_date}")
    print(f"[bold]Output directory path:[/bold] {output_dir}")
    
    print(f"[bold green]{'='*60}[/bold green]")
    print("[bold green]REFERENCING[/bold green]")
    print(f"[bold green]{'='*60}[/bold green]")
    
    reference_main(path=path_obj, file_type=file_type,lat=lat, lon=lon, meters=meters, ref_date=ref_date, output_dir=output_dir)

def is_valid_yyyymmdd(date_str: str) -> bool:
    """Date format YYYYMMDD validation."""
    try:
        datetime.strptime(date_str, "%Y%m%d")
        return True
    except ValueError:
        return False

if __name__ == "__main__":
    app()