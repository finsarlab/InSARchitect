import sys
import numpy as np
import h5py
from pathlib import Path
from rich import print

from mintpy.utils import readfile, writefile

def get_dates_from_file(path: Path) -> list:
    with h5py.File(path, "r") as f:
        if "date" in f.keys():
            dates = f["date"][:]
        else:
            print(f"[bold red]No date dataset found in:[/bold red] {path}")

    dates = [d.decode("utf-8") if isinstance(d, bytes) else str(d) for d in dates] # from bytes to string

    return dates

def find_nearest_date(dates: list, target: str) -> tuple:
    dates_int = np.array([int(d) for d in dates])
    target = int(target)

    diff = np.abs(dates_int - target)

    idx = np.argmin(diff)

    exact_match = diff[idx] == 0

    return dates[idx], idx, exact_match

def reference_date(results: list, ref_date: str):
    print(f"[bold green]\nApplying reference date...\n[/bold green]")
    for r in results:
        path = r["path"]
        print(f"[bold cyan]File[/bold cyan] {path}")

        data, attr = readfile.read(path)

        ref_date_file = attr["REF_DATE"]

        valid_ref_dates = {"zero_first", "minRMS"}
        if ref_date not in valid_ref_dates:
            if ref_date == ref_date_file:
                print("[bold yellow]\nSelected reference date is equal to current date. Nothing to do...[/bold yellow]")
                sys.exit(0)

        dates = get_dates_from_file(path=path)

        print(f"[bold cyan]User input...[/bold cyan]")
        if ref_date not in valid_ref_dates:
            print(f"[bold]Reference date:[/bold] {ref_date}")
        else:
            print(f"[bold]Reference date method:[/bold] {ref_date}")

        if ref_date == "zero_first":
            print(f"[bold magenta]\nApplying zero first referencing...[/bold magenta]")

            new_ref_date = dates[0]
            print(f"[bold]\nSelected reference date (first date):[/bold] {new_ref_date}")
            
            print("[bold magenta]\nReferencing date...[/bold magenta]")
            layer = data[0, :, :]
            data = data - layer
            print(f"[bold magenta]\nUpdating metadata...[/bold magenta]")
            attr["REF_DATE"] = new_ref_date
        elif ref_date == "min_rms":
            print(f"[bold magenta]\nApplying min RMS referencing...[/bold magenta]")
            pass
        else:
            print(f"[bold magenta]\nReferencing using selected user date...[/bold magenta]")
            nearest_ref_date, idx, exact_match = find_nearest_date(dates=dates, target=ref_date)
            if not exact_match:
                print(f"[bold yellow]\nExact date could not be found; the closest one has been selected\n[/bold yellow]")
                print(f"[bold cyan]New reference date...[/bold cyan]")
                print(f"[bold]Reference date:[/bold] {nearest_ref_date}")
                ref_date = nearest_ref_date
            else:
                print(f"[bold green]\nExact reference date found in dates...[/bold green]")
                print(f"[bold]Reference date:[/bold] {ref_date}")
            print("[bold magenta]\nReferencing date...[/bold magenta]")
            layer = data[idx, :, :]
            data = data - layer
            print(f"[bold magenta]\nUpdating metadata...[/bold magenta]")
            attr["REF_DATE"] = ref_date
