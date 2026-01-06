from pathlib import Path
import simplekml
import json
from shapely.geometry import shape
import os

from typing import Annotated
import typer

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

    # Options for the search
    opts = {
        'platform': PLATFORM_MAP.get(download_config.platform),
        'maxResults': download_config.max_results,
        'start': download_config.start_date,
        'end': download_config.end_date,
        'processingLevel': product_type
    }

    # Search and download
    try:
        results = asf.geo_search(
            intersectsWith=download_config.bounding_box,
            **opts
        )
        results.raise_if_incomplete()
    except ASFSearchError as e:
        print(f"Results from ASF search incomplete: {e}")
        raise typer.Exit(code=1)

    kml = simplekml.Kml()

    for product in results:
        geom_json = product.geometry
        geom = shape(geom_json)

        coords = [(x, y) for x, y in list(geom.exterior.coords)]
        polygon = kml.newpolygon(name=product.properties['fileID'], outerboundaryis=coords)
        polygon.description = "Legacy"

    kml.save("asf_results.kml")

    try:
        results.download(
            path=download_config.slc_dir,
            session=session, 
            processes=download_config.parallel_downloads
        )
    except ASFAuthenticationError as e:
        print(f"Error!: {e}")
        print("""
        Place your credentials inside ~/.netrc like this:
        machine urs.earthdata.nasa.gov
            login user_name
            password your_password
              """)
        # Using os._exit to avoid mp error message from download
        os._exit(1)
