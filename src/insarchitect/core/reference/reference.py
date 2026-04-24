from pathlib import Path
import sys
import shutil
from datetime import datetime 
from rich import print
from ...models import ReferenceFileType

from mintpy.utils import readfile

from .reference_point import reference_point
from .reference_date import reference_date

def normalize_inputs(path: Path) -> list[Path]:
    if path.is_dir():
        return sorted(path.glob("*.h5"))
    return [path]

def validation_yyyymmdd_date(attr: dict, ref_date_str: str):
    valid_ref_dates = {"zero_first", "minRMS"}
    if ref_date_str not in valid_ref_dates:
        ref_date = datetime.strptime(ref_date_str, "%Y%m%d")
        start_date_str = attr["START_DATE"]
        end_date_str = attr["END_DATE"]
        start_date = datetime.strptime(start_date_str, "%Y%m%d")
        end_date = datetime.strptime(end_date_str, "%Y%m%d")
        
        if not (start_date <= ref_date <= end_date):
            print(f"[bold red]Provided reference date is not within {start_date_str} - {end_date_str}[/bold red]")
            sys.exit(1)

def copy_h5_files(files: list[Path], output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    copied_files = []
    for f in files:
        copy_path = output_dir / f.name
        shutil.copy2(f, copy_path)
        copied_files.append(copy_path)
    return copied_files

def reference_main(path: Path, file_type: ReferenceFileType, lat: float , lon: float, meters: int, ref_date: str, output_dir: Path):
    """
    Referencing timeseries in space and in time, or velocity
    is space, using user requirements.
    """
    # path to a list of paths for processing
    files = normalize_inputs(path=path)

    is_timeseries = file_type == ReferenceFileType.timeseries

    results = [] # to storage attributes of each file

    print("[bold magenta]Validating files...[/bold magenta]")
    for f in files:
        print(f"[bold cyan]\nFile attributes from[/bold cyan] {f}")
        _, attr = readfile.read(f) # explore attributes of the file

        attr_file_type = attr["FILE_TYPE"]
        if attr_file_type != file_type:
            print(f"[bold red]Invalid file type '{attr_file_type}' for files of type '{file_type.value}'[/bold red]")
            sys.exit(1)

        # reference point and date from file
        ref_lat = float(attr["REF_LAT"])
        ref_lon = float(attr["REF_LON"])
        ref_y = int(attr["REF_Y"])
        ref_x = int(attr["REF_X"])
        ref_date_file = attr.get("REF_DATE")

        # bounding box
        lat0 = float(attr["Y_FIRST"])
        lon0 = float(attr["X_FIRST"])
        y_step = float(attr["Y_STEP"])
        x_step = float(attr["X_STEP"])
        length = int(attr["LENGTH"]) # for latitude
        width = int(attr["WIDTH"]) # for longitude

        lat1 = lat0 + (y_step * (length - 1))
        lon1 = lon0 + (x_step * (width - 1))

        lat_min = min(lat0, lat1)
        lat_max = max(lat0, lat1)
        lon_min = min(lon0, lon1)
        lon_max = max(lon0, lon1)

        bbox = [lon_min, lat_min, lon_max, lat_max] # (west, south, east, north)

        # reference date validation for timeseries
        if is_timeseries:
            validation_yyyymmdd_date(attr=attr, ref_date_str=ref_date)

        # latitude and longitude validation
        if lat is not None and lon is not None:
            if not (lat_min <= lat <= lat_max) or not (lon_min <= lon <= lon_max):
                print(f"[bold red]Provided reference point is not within the bounding box:[/bold red] {bbox}")
                sys.exit(1)

        print(f"[bold]Reference point (lat, lon):[/bold] {ref_lat, ref_lon}")
        print(f"[bold]Reference point (y, x):[/bold] {ref_y, ref_x}")
        if is_timeseries:
            print(f"[bold]Reference date:[/bold] {ref_date_file}")
        print(f"[bold]Bounding box (lon_min, lat_min, lon_max, lat_max):[/bold] {bbox}")

        results.append({
            "og_path": f,
            "ref_lat": ref_lat,
            "ref_lon": ref_lon,
            "ref_date": ref_date_file,
            "bbox": bbox,
        })

    print("[bold magenta]\nCreating h5 copies...[/bold magenta]")
    copied_files = copy_h5_files(files=files, output_dir=output_dir)

    for i, copied_path in enumerate(copied_files):
        results[i]["path"] = copied_path
    
    # Processing
    print("[bold magenta]\nReferencing...[/bold magenta]")
    if file_type == ReferenceFileType.velocity:
        reference_point(results=results, lat=lat, lon=lon, meters=meters, file_type=file_type)
    elif is_timeseries:
        if lat is not None and lon is not None:
            reference_point(results=results, lat=lat, lon=lon, file_type=file_type)
        reference_date(results=results, ref_date=ref_date)

    print(f"[bold green]{'='*60}[/bold green]")
    print("[bold green]REFERENCING COMPLETED[/bold green]")
    print(f"[bold green]{'='*60}[/bold green]")