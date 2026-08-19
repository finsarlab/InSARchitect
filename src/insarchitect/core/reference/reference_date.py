import sys
import numpy as np
import h5py
from pathlib import Path
from rich import print
from datetime import datetime
from mintpy.utils import readfile
from .write_file import write_file

def compute_rms(layer: np.array) -> float:
    return np.sqrt(np.nanmean(layer ** 2))

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
    
    diff = np.abs(dates_int - target) # differences between each date and the ref date
    idx = np.argmin(diff) # index of the min difference
    exact_match = diff[idx] == 0 # check if the ref date exist

    return dates[idx], idx, exact_match

def reference_date(results: list, ref_date: str):
    print(f"[bold green]\nApplying reference date...\n[/bold green]")
    for r in results:
        path = r["path"]
        print(f"[bold cyan]File[/bold cyan] {path}")

        data, attr = readfile.read(path)

        ref_date_file = attr["REF_DATE"]
        print(f"[bold]Actual reference date:[/bold] {ref_date_file}")

        valid_ref_dates = {"zero_first", "minRMS"}
        if ref_date not in valid_ref_dates:
            if ref_date == ref_date_file:
                print("[bold yellow]\nSelected reference date is equal to current date. Nothing to do...[/bold yellow]")
                continue

        dates = get_dates_from_file(path=path)

        print(f"[bold cyan]\nUser input...[/bold cyan]")
        print(f"[bold]Reference date method:[/bold] {ref_date}")
        # ZERO FIRST implementation
        if ref_date == "zero_first":
            print(f"[bold magenta]\nApplying zero first referencing...[/bold magenta]")
            new_ref_date = dates[0]
            print(f"[bold]\nSelected reference date (first date):[/bold] {new_ref_date}")

            print("[bold magenta]\nReferencing date...[/bold magenta]")
            layer = data[0, :, :]
            data = data - layer

            attr["REF_DATE"] = new_ref_date

        # MINRMS implementation
        elif ref_date == "minRMS":
            print(f"[bold magenta]\nApplying miRMS referencing...[/bold magenta]")
            
            if len(results) == 1: # just one file
                n_dates = data.shape[0]
                rms_values = []

                print("[bold cyan]\nComputing RMS per date...[/bold cyan]")
                for i in range(n_dates):
                    layer = data[i, :, :]
                    rms = compute_rms(layer=layer)
                    rms_values.append(rms)

                rms_values = np.array(rms_values)
                idx = np.argmin(rms_values)
                new_ref_date = dates[idx]

                if ref_date_file == new_ref_date:
                    print(f"[bold yellow]\nSelected reference date is the same as the actual one[/bold yellow] {new_ref_date}")
                else:
                    print(f"[bold green]\nSelected reference date (minRMS):[/bold green] {new_ref_date}")
                    print(f"[bold yellow]RMS value:[/bold yellow] {rms_values[idx]}")

                    print("[bold magenta]\nReferencing date...[/bold magenta]")
                    layer = data[idx, :, :]
                    data = data - layer

                    attr["REF_DATE"] = new_ref_date
            elif len(results) == 2:
                from .geo_intersect import geographic_intersection, get_geo_slice

                first_file_path = results[0]["path"]
                second_file_path = results[1]["path"]

                data1, attr1 = readfile.read(first_file_path)
                data2, attr2 = readfile.read(second_file_path)

                first_dates = get_dates_from_file(path=first_file_path)
                second_dates = get_dates_from_file(path=second_file_path)

                # geo intersection
                intersection = geographic_intersection(attr1, attr2)
                if intersection is None:
                    print("[bold red]No spatial overlap between files. Cannot compute minRMS.[/bold red]")
                    sys.exit(1)

                lat_min, lat_max, lon_min, lon_max = intersection
                print(f"[bold cyan]Spatial intersection:[/bold cyan] lat [{lat_min:.4f}, {lat_max:.4f}], lon [{lon_min:.4f}, {lon_max:.4f}]")

                row_slice1, col_slice1 = get_geo_slice(attr1, lat_min, lat_max, lon_min, lon_max)
                row_slice2, col_slice2 = get_geo_slice(attr2, lat_min, lat_max, lon_min, lon_max)

                pairs = []
                for i, d1 in enumerate(first_dates):
                    for j, d2 in enumerate(second_dates):
                        date1 = datetime.strptime(d1, "%Y%m%d")
                        date2 = datetime.strptime(d2, "%Y%m%d")
                        diff = abs(date1 - date2)
                        pairs.append({"date1": d1, "idx1": i, "date2": d2, "idx2": j, "diff": diff})

                pairs = sorted(pairs, key=lambda x: x["diff"])
                candidate_pairs = pairs[:5]

                best_rmse = np.inf
                best_pair = None

                for pair in candidate_pairs:
                    # temporal clipping just for rmse
                    patch1 = data1[pair["idx1"], row_slice1, col_slice1]
                    patch2 = data2[pair["idx2"], row_slice2, col_slice2]

                    # both patches could have different shapes, take the minimum
                    min_rows = min(patch1.shape[0], patch2.shape[0])
                    min_cols = min(patch1.shape[1], patch2.shape[1])
                    patch1 = patch1[:min_rows, :min_cols]
                    patch2 = patch2[:min_rows, :min_cols]

                    diff = patch1 - patch2
                    rmse = np.sqrt(np.nanmean(diff ** 2))

                    if rmse < best_rmse:
                        best_rmse = rmse
                        best_pair = pair

                # reference using original data
                layer1 = data1[best_pair["idx1"], :, :]
                data1 = data1 - layer1

                layer2 = data2[best_pair["idx2"], :, :]
                data2 = data2 - layer2

                print(f"[bold green]\nBest reference date pair found (minRMS = {best_rmse:.6f}):[/bold green]")
                print(f"[bold]  File 1:[/bold] {first_file_path.name} → [bold cyan]{best_pair['date1']}[/bold cyan]")
                print(f"[bold]  File 2:[/bold] {second_file_path.name} → [bold cyan]{best_pair['date2']}[/bold cyan]")
                print(f"[bold]  Date difference:[/bold] {best_pair['diff'].days} days")

                attr1["REF_DATE"] = best_pair["date1"]
                write_file(path=first_file_path, data=data1, metadata=attr1, dataset_name="timeseries")
                attr2["REF_DATE"] = best_pair["date2"]
                write_file(path=second_file_path, data=data2, metadata=attr2, dataset_name="timeseries")
                return
            else:
                print("[bold red]Not implemented yet, working on it!!!![bold red]")
                sys.exit(1)
            
        else: # MANUAL DATE implementation
            print(f"[bold magenta]\nReferencing using manual date...[/bold magenta]")
            nearest_ref_date, idx, exact_match = find_nearest_date(dates=dates, target=ref_date)
            
            if not exact_match:
                print(f"[bold yellow]\nExact date could not be found; the closest one has been selected\n[/bold yellow]")
                print(f"[bold]Selected reference date:[/bold] {nearest_ref_date}")
                ref_date = nearest_ref_date
            else:
                print(f"[bold green]\nExact reference date found in dates...[/bold green]")
                print(f"[bold]Reference date:[/bold] {ref_date}")
            
            print("[bold magenta]\nReferencing date...[/bold magenta]")
            layer = data[idx, :, :]
            data = data - layer

            attr["REF_DATE"] = ref_date

        write_file(path=path, data=data, metadata=attr, dataset_name="timeseries")