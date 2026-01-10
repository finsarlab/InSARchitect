import sys
import datetime
from functools import reduce

from rich import print
from shapely.geometry import Polygon, shape
import asf_search as asf
import simplekml

from ...models import ProjectConfig

def download_main(config: ProjectConfig):
    """Download SLC images and a KML file based on config"""
    download_config = config.download
    work_dir = config.system.work_dir
    if download_config is None:
        print(f"[Bold red]No valid configuration given for download command[/bold red]")
        sys.exit(1)

    burst_flag = download_config.burst_download
    product_type = "BURST" if burst_flag else "SLC"

    slc_dir = work_dir / download_config.slc_dir
    slc_dir.mkdir(exist_ok=True)

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
    total_gigabytes = round(total_bytes / 1024 / 1024 / 1024, 2)

    print(f"[bold cyan]\nFound {len(results)} products for a total of {total_gigabytes}GB[/bold cyan]")
    print(f"[bold]Creating KML file...[/bold]")

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




# def get_bytes(result):
#     return result.properties["bytes"]



