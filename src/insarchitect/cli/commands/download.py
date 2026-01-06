from pathlib import Path
import simplekml
import json
from shapely.geometry import shape
import os
import threading
import time

from typing import Annotated
import typer
from rich import print
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn

from shapely.geometry import box
import asf_search as asf
from asf_search.exceptions import ASFSearchError, ASFAuthenticationError

from insarchitect.config import load_config
from insarchitect.utils import parse_date

asf.REPORT_ERRORS = False

app = typer.Typer(help="ASF SLC and Burst downloads")
session = asf.ASFSession()

PLATFORM_MAP = {
    "SENTINEL-1": asf.PLATFORM.SENTINEL1,
}


def monitor_download_progress(download_dir, progress, task, expected_count, stop_event, initial_files):
    """
    Monitor download directory and update progress bar in real-time.

    Args:
        download_dir: Path to the download directory
        progress: Rich Progress object
        task: Progress task to update
        expected_count: Expected number of products to download
        stop_event: Threading event to signal when to stop monitoring
        initial_files: Set of files that existed before download started
    """
    last_count = 0

    while not stop_event.is_set():
        current_files = set()
        if download_dir.exists():
            for f in download_dir.iterdir():
                if f.is_file() and not f.name.endswith('.kml') and f not in initial_files:
                    current_files.add(f)

        new_file_count = len(current_files)

        if new_file_count > last_count:
            max_progress = max(1, expected_count - 1)  # Always leave at least 1 unit remaining
            estimated_progress = min(new_file_count, max_progress)
            progress.update(task, completed=estimated_progress)
            last_count = new_file_count

        time.sleep(0.5)

@app.command(name="download")
def download(
        config: Annotated[
            Path,
            typer.Argument(
                exists=True,
                file_okay=True,
                dir_okay=False,
                writable=True,
                readable=True,
                resolve_path=True
            )]):
    """Downloads SLC's based on template file"""

    # Get config
    download_config = load_config(config).download

    # Set product type
    burst_flag = download_config.burst_download
    product_type = asf.PRODUCT_TYPE.BURST if burst_flag else asf.PRODUCT_TYPE.SLC

    slc_dir = download_config.slc_dir
    slc_dir.mkdir(parents=True, exist_ok=True)

    # Display header
    print(f"[bold green]{'='*60}[/bold green]")
    print("[bold green]ASF DOWNLOAD[/bold green]")
    print(f"[bold green]{'='*60}[/bold green]")
    print(f"[bold]Platform[/bold]:           {download_config.platform}")
    print(f"[bold]Product Type[/bold]:       {'BURST' if burst_flag else 'SLC'}")
    print(f"[bold]Output Directory[/bold]:   {slc_dir}")
    print(f"[bold]Date Range[/bold]:         {download_config.start_date} to {download_config.end_date}")
    print(f"[bold]Max Results[/bold]:        {download_config.max_results}")
    print(f"[bold]Parallel Downloads[/bold]: {download_config.parallel_downloads}")

    # Options for the search
    opts = {
        'platform': PLATFORM_MAP.get(download_config.platform),
        'maxResults': download_config.max_results,
        'start': download_config.start_date,
        'end': download_config.end_date,
        'processingLevel': product_type
    }

    # Search section
    print("\n[bold magenta]Searching ASF catalog...[/bold magenta]\n")
    print(f"[bold]Bounding Box[/bold]: {download_config.bounding_box}")

    try:
        results = asf.geo_search(
            intersectsWith=download_config.bounding_box,
            **opts
        )
        results.raise_if_incomplete()
    except ASFSearchError as e:
        print(f"[bold red]ERROR: ASF search incomplete: {e}[/bold red]")
        raise typer.Exit(code=1)

    print(f"[bold cyan]\nFound {len(results)} product(s)[/bold cyan]")
    print(f"[bold]Creating KML file...[/bold]")

    kml = simplekml.Kml()

    for product in results:
        geom_json = product.geometry
        geom = shape(geom_json)

        coords = [(x, y) for x, y in list(geom.exterior.coords)]
        polygon = kml.newpolygon(name=product.properties['fileID'], outerboundaryis=coords)
        polygon.description = "Legacy"

    kml.save(download_config.slc_dir / "ssara_search_1.kml")
    print(f"[bold cyan]✓ KML saved:[/bold cyan] ssara_search_1.kml")

    # Download section
    print(f"\n[bold magenta]Downloading {len(results)} product(s)...[/bold magenta]\n")
    print(f"[bold]Destination[/bold]: {download_config.slc_dir}")
    print(f"[bold]Processes[/bold]:   {download_config.parallel_downloads}\n")

    # Get initial files in directory (to track new downloads)
    initial_files = set()
    if download_config.slc_dir.exists():
        initial_files = set(download_config.slc_dir.iterdir())

    # Create progress bar with custom columns
    with Progress(
        SpinnerColumn(style="cyan"),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(complete_style="green", finished_style="bold green"),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        transient=False
    ) as progress:
        # Add task for overall download progress
        download_task = progress.add_task(
            f"Downloading {len(results)} products",
            total=len(results)
        )

        # Create stop event for monitoring thread
        stop_event = threading.Event()

        # Start monitoring thread for real-time progress
        monitor_thread = threading.Thread(
            target=monitor_download_progress,
            args=(download_config.slc_dir, progress, download_task, len(results), stop_event, initial_files),
            daemon=True
        )
        monitor_thread.start()

        try:
            # Download with progress tracking
            results.download(
                path=download_config.slc_dir,
                session=session,
                processes=download_config.parallel_downloads
            )

            # Stop monitoring thread
            stop_event.set()
            monitor_thread.join(timeout=2)

            # Update progress to complete
            progress.update(download_task, completed=len(results))

        except ASFAuthenticationError as e:
            stop_event.set()
            monitor_thread.join(timeout=2)
            progress.stop()
            print(f"[bold red]ERROR: Authentication failed[/bold red]")
            print(f"[bold red]{e}[/bold red]")
            print("""
[bold yellow]Configure your NASA Earthdata credentials:[/bold yellow]

Place your credentials in ~/.netrc:
    [bold]machine urs.earthdata.nasa.gov
        login your_username
        password your_password[/bold]
            """)
            # Using os._exit to avoid mp error message from download
            os._exit(1)
        except KeyboardInterrupt:
            stop_event.set()
            monitor_thread.join(timeout=2)
            progress.stop()
            print("\n[bold red]Download interrupted by user[/bold red]")
            raise typer.Exit(code=1)

    # Success completion banner
    print(f"\n[bold green]{'='*60}[/bold green]")
    print("[bold green]DOWNLOAD COMPLETED SUCCESSFULLY[/bold green]")
    print(f"[bold green]{'='*60}[/bold green]")
    print(f"[bold]Total Products[/bold]:  {len(results)}")
    print(f"[bold]Saved to[/bold]:        {download_config.slc_dir}")
