import h5py
import numpy as np
import sys
from rich import print

def write_file(path: str, data: np.ndarray, metadata: dict, dataset_name: str):
    """
    Minimal HDF5 writer that updates ONLY dataset + attributes
    """
    print(f"[bold green]\nWriting output file:[/bold green] {path}")
    with h5py.File(path, "r+") as f:
        ds = f[dataset_name]
        if ds.shape != data.shape:
            print(f"[bold red]Shape mismatch -> file: {ds.shape} and data: {data.shape}[/bold red]")
            sys.exit(1)

        print(f"[bold cyan]\nUpdating dataset:[/bold cyan] {dataset_name}")
        ds[:] = data
        
        print("[bold cyan]\nUpdating metadata...[/bold cyan]")
        for k, v in metadata.items():
            f.attrs[k] = str(v)

    print("[bold green]\nWrite completed...[/bold green]")