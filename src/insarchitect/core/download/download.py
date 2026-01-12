import os
import sys
import datetime
import warnings
from functools import reduce
from pathlib import Path
import time
from concurrent.futures import ThreadPoolExecutor

from asf_search.exceptions import ASFAuthenticationError
from rich import print
from rich.progress import Progress, BarColumn, TextColumn, DownloadColumn, TransferSpeedColumn
from shapely.geometry import Polygon, shape
import asf_search as asf
import simplekml

from ...models import ProjectConfig

warnings.filterwarnings('ignore', message='File already exists, skipping download:*')


def download_main(config: ProjectConfig):
    """Download SLC images and a KML file based on config"""
    download_config = config.download
    if download_config is None:
        print(f"[Bold red]No valid configuration given for download command[/bold red]")
        sys.exit(1)

    work_dir = config.system.work_dir / config.project_name

    burst_flag = download_config.burst_download
    product_type = "BURST" if burst_flag else "SLC"

    slc_dir = work_dir / download_config.slc_dir
    slc_dir.mkdir(exist_ok=True, parents=True)


    print(f"[bold green]{'='*60}[/bold green]")
    print("[bold green]ASF DOWNLOAD[/bold green]")
    print(f"[bold green]{'='*60}[/bold green]")
    print(f"[bold]Working directory[/bold]:  {work_dir}")
    print(f"[bold]Platform[/bold]:           {download_config.platform}")
    print(f"[bold]Product Type[/bold]:       {product_type}")
    print(f"[bold]Relative orbit[/bold]:     {download_config.relative_orbit}")
    print(f"[bold]Bounding Box[/bold]:       {download_config.bounding_box}")
    print(f"[bold]Output Directory[/bold]:   {slc_dir}")
    print(f"[bold]Date Range[/bold]:         {download_config.start_date} to {download_config.end_date}")
    print(f"[bold]Max Results[/bold]:        {download_config.max_results}")
    print(f"[bold]Parallel Downloads[/bold]: {download_config.parallel_downloads}")

    start = datetime.datetime.strptime(str(download_config.start_date), "%Y%m%d")
    end = datetime.datetime.strptime(str(download_config.end_date), "%Y%m%d")

    opts = {
        'platform': download_config.platform,
        'maxResults': download_config.max_results,
        'start': start,
        'end': end,
        'processingLevel': "SLC",
        "intersectsWith": download_config.bounding_box
    }


    try:
        results = asf.geo_search(**opts)
        results.raise_if_incomplete()
    except asf.exceptions.ASFSearchError as e:
        print(f"[bold red]ERROR: ASF search incomplete: {e}[/bold red]")
        sys.exit(1)

    # Get total bytes for loading bar
    total_bytes = reduce(lambda x, y: x + y.properties["bytes"], results, 0)
    total_gigabytes = round(total_bytes / (1024**3), 2)
    print(f"[bold cyan]\nFound {len(results)} products for a total of {total_gigabytes}GB[/bold cyan]")

    create_kml(slc_dir, results)

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    ) as progress:
        task = progress.add_task("Downloading", total=total_bytes)

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                lambda: results.download(
                    path=str(slc_dir.resolve()),
                    processes=download_config.parallel_downloads
                )
            )

            last_downloaded = 0
            last_time = time.time()

            while not future.done():
                downloaded_bytes = sum(file.stat().st_size for file in slc_dir.glob("*.zip"))
                progress.update(task, completed=downloaded_bytes)
                last_downloaded = downloaded_bytes
                last_time = time.time()
                time.sleep(0.5)

        try:
            future.result()
        except ASFAuthenticationError as e:
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
            print("\n[bold red]Download interrupted by user[/bold red]")
            sys.exit(1)

        except:
            progress.stop()
            print("[bold red]Connection lost during download[/bold red]")
            sys.exit(1)




def create_kml(slc_dir: Path, results):
    print(f"[bold]Creating KML file...[/bold]")
    # Delete old kml(s)
    for file in slc_dir.glob("*.kml"):
        file.unlink(missing_ok=True)

    # Create kml
    kml = simplekml.Kml()
    for product in results:
        geom_json = product.geometry
        geom = shape(geom_json)
        if isinstance(geom, Polygon):
            coords = [(x, y) for x, y in list(geom.exterior.coords)]
            polygon = kml.newpolygon(name=product.properties['fileID'], outerboundaryis=coords)
            polygon.description = "Legacy"
        else:
            print(f"[bold red]Geometry is a {type(geom)}, not a Polygon.[/bold red]")
            sys.exit(1)
    kml.save(slc_dir / f"ssara_search_{datetime.datetime.now().strftime('%Y%m%d')}.kml")
    print(f"[bold cyan]✓ KML saved:[/bold cyan] ssara_search_1.kml")




