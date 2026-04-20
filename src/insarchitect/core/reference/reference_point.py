import sys
from scipy.ndimage import distance_transform_edt
import numpy as np
from rich import print

from ...models import ReferenceFileType

from mintpy.utils import readfile, writefile

def find_nearest_valid_pixel(data: np.array, y: int, x: int) -> tuple:
    """
    Create a mask where NaN is 1 and value is 0, using distance transform
    return for each pixel, the coordinate of the nearest valid pixel, 
    this method use euclidean distances
    """
    print("[bold magenta]\nSearching nearest valid pixel using distance transform...\n[/bold magenta]")

    nan_mask = np.isnan(data)

    indexes = distance_transform_edt(nan_mask, return_distances=False, return_indices=True) # return (2, rows, cols)

    nearest_y = indexes[0, y, x] # 0 for y coordinates
    nearest_x = indexes[1, y, x] # 1 for x coordinates

    return int(nearest_y), int(nearest_x)

def apply_reference(data: np.array, y: int, x: int) -> np.array:
    """
    Reference point subtracting the point value to all data
    """
    print("[bold magenta]\nReferencing point...[/bold magenta]")
    if data.ndim == 3: # for timeseries
        ref_point = data[:, y, x]
        ref_point = ref_point[:, None, None] # from [] -> [[[]]]
    elif data.ndim == 2: # for velocity
        ref_point = data[y, x]
 
    new_data = data - ref_point

    return new_data

def update_metadata(attr: dict, ref_y: int, ref_x: int, ref_lat: float, ref_lon: float) -> dict:
    """
    Update the attributes values
    """
    print(f"[bold magenta]\nUpdating metadata...[/bold magenta]")
    attr["REF_Y"] = ref_y
    attr["REF_X"] = ref_x
    attr["REF_LAT"] = ref_lat
    attr["REF_LON"] = ref_lon
    return attr

def reference_point(results: dict, lat: float, lon: float, file_type: str):
    print(f"[bold green]\nApplying reference point...\n[/bold green]")
    for r in results:
        path = r["path"]
        print(f"[bold cyan]File[/bold cyan] {path}")

        data, attr = readfile.read(path)

        is_timeseries = file_type == ReferenceFileType.timeseries
        
        if is_timeseries:
            print(f"[bold]Data shape (dates, rows, cols):[/bold] {data.shape}")
        else: 
            print(f"[bold]Data shape (rows, cols):[/bold] {data.shape}")

        h = data.shape[-2]
        w = data.shape[-1]
        
        y_first = float(attr["Y_FIRST"])
        x_first = float(attr["X_FIRST"])
        y_step = float(attr["Y_STEP"])
        x_step = float(attr["X_STEP"])
        ref_y = int(attr["REF_Y"])
        ref_x = int(attr["REF_X"])

        y = round((lat - y_first) / y_step)
        x = round((lon - x_first) / x_step)

        if not (0 <= y < h and 0 <= x < w):
            print("[bold red]\nComputed pixel is outside grid[/bold red]")
            sys.exit(1)

        if y == ref_y and x == ref_x:
            print("[bold yellow]\nSelected reference point is equal to current point. Nothing to do...[/bold yellow]")
            sys.exit(1)

        og_lat = y_first + (y * y_step)
        og_lon = x_first + (x * x_step)

        print(f"[bold cyan]User input...[/bold cyan]")
        print(f"[bold]Latitude:[/bold] {og_lat} [bold]-> Row:[/bold] {y}")
        print(f"[bold]Longitude:[/bold] {og_lon} [bold]-> Column:[/bold] {x}")

        layer = data[0, :, :] if is_timeseries else data

        if np.isnan(layer[y, x]):
            print("[bold yellow]\nThe selected point is NaN[/bold yellow]")

            nearest_y, nearest_x = find_nearest_valid_pixel(data=layer, y=y, x=x)
            new_lat = y_first + (nearest_y * y_step)
            new_lon = x_first + (nearest_x * x_step)

            print(f"[bold cyan]New reference point found at...[/bold cyan]")
            print(f"[bold]Latitude:[/bold] {new_lat} [bold]-> Row:[/bold] {nearest_y}")
            print(f"[bold]Longitude:[/bold] {new_lon} [bold]-> Column:[/bold] {nearest_x}")

            print(f"[bold cyan]Distancing from the original point...[/bold cyan]")
            print(f"[bold]Latitude difference:[/bold] {new_lat - og_lat}")
            print(f"[bold]Longitude difference:[/bold] {new_lon - og_lon}")

            data = apply_reference(data=data, y=nearest_y, x=nearest_x)
            attr = update_metadata(attr=attr, ref_y=nearest_y, ref_x=nearest_x, ref_lat=new_lat, ref_lon=new_lon)
        else:
            data = apply_reference(data=data, y=y, x=x)
            attr = update_metadata(attr=attr, ref_y=y, ref_x=x, ref_lat=og_lat, ref_lon=og_lon)

        print(f"[bold green]\nWriting output file:[/bold green] {path}")
        #writefile.write(data, path, metadata=attr)
        #output_path = path.replace(".h5", "_ref.h5")
        #print(f"[bold green]Writing output file:[/bold green] {output_path}")
        #writefile.write(data, output_path, metadata=attr)
        
