from pathlib import Path
import os

import math
import shutil
from typing import Annotated
import typer

import sardem.dem
from insarchitect.config import load_config
import insarchitect.utils.get_boundingbox_from_kml as get_boundingbox_from_kml

app = typer.Typer(help="Creates a DEM based on ssara_*.kml file using COPERNICUS or NASA")


def format_bbox(bbox: tuple) -> str:
    """
    Format bounding box to readable string format.
    
    Args:
        bbox: List or tuple of [west, south, east, north]
    
    Returns:
        Formatted string like "S00_N01_W078_W076"
    """
    west, south, east, north = bbox

    # Determine hemisphere for each coordinate
    south_str = f"S{abs(south):02d}" if south < 0 else f"N{abs(south):02d}"
    north_str = f"S{abs(north):02d}" if north < 0 else f"N{abs(north):02d}"
    west_str = f"W{abs(west):03d}" if west < 0 else f"E{abs(west):03d}"
    east_str = f"W{abs(east):03d}" if east < 0 else f"E{abs(east):03d}"

    # Format the output string
    name = f"{south_str}_{north_str}_{west_str}_{east_str}"
    return name


def exist_valid_dem_dir(dem_dir: Path) -> bool:
    """
    Check if a valid DEM directory exists.
    
    Args:
        dem_dir: Path to DEM directory
    
    Returns:
        True if valid DEM exists, False otherwise
        
    Note:
        If directory exists but doesn't contain valid products, it will be removed.
    """
    if dem_dir.is_dir():
        products = list(dem_dir.glob('*dem.wgs84*'))
        if len(products) >= 3:
            print('DEM products already exist. If not satisfying, remove the folder and run again')
            return True
        else:
            print('Incomplete DEM directory found. Removing and recreating...')
            shutil.rmtree(dem_dir)
            return False
    else:
        return False


@app.command(name="download-dem")
def download_dem(
    config: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            writable=True,
            readable=True,
            resolve_path=True,
            help="Path to configuration template file"
        )
    ]
):
    """
    Download DEM based on template file and KML bounding box.
    
    This command:
    1. Reads the configuration from the template file
    2. Locates the SSARA KML file with bounding box information
    3. Extracts the bounding box coordinates
    4. Downloads the DEM using sardem from Copernicus DEM
    5. Creates ISCE-compatible XML files
    
    Example:
        pixi run insarchitect download-dem config.template
    """
    
    # Get config
    dem_download_config = load_config(config).dem
    asf_download_config = load_config(config).download
    
    # Set directories
    work_dir = dem_download_config.work_dir
    dem_dir = work_dir / 'DEM'
    slc_dir = asf_download_config.slc_dir
    
    print("DEM DOWNLOAD")
    print(f"Work directory: {work_dir}")
    print(f"DEM directory:  {dem_dir}")
    print(f"SLC directory:  {slc_dir}")
    
    # Check for existing valid DEM
    if exist_valid_dem_dir(dem_dir):
        print("\nValid DEM already exists. Exiting.")
        raise typer.Exit()
    
    # Create DEM directory
    dem_dir.mkdir(parents=True, exist_ok=True)
    
    # Adjust SLC directory based on platform
    values = [str(v).upper() for v in dem_download_config.__dict__.values()]
    if any("COSMO-SKYMED" in value for value in values):
        slc_dir = Path(str(slc_dir).replace('SLC', 'RAW_data'))
        print(f"Platform detected: COSMO-SKYMED, using RAW_data directory")
    if any("TSX" in value for value in values):
        slc_dir = Path(str(slc_dir).replace('SLC', 'SLC_ORIG'))
        print(f"Platform detected: TerraSAR-X, using SLC_ORIG directory")
    
    # Find KML file
    print('Searching for KML file...')
    try:
        kml_files = sorted(slc_dir.glob('ssara_search_*.kml'))
        if not kml_files:
            raise FileNotFoundError(
                f'No ssara_search_*.kml found in {slc_dir}\n'
                'Please run the download command first to generate the KML file.'
            )
        ssara_kml_file = kml_files[-1]
    except Exception as e:
        print(f"Error finding KML file: {e}")
        raise typer.Exit(code=1)
    
    print(f'Using KML file: {ssara_kml_file.name}')
    
    # Get bounding box from KML
    print(f"\n{'='*60}")
    print('Extracting bounding box from KML...')
    try:
        bbox = get_boundingbox_from_kml.main( [ssara_kml_file, '--delta_lon', '0'] )
        print(f'Raw bbox: {bbox}')
        
    except Exception as e:
        print(f'Problem with KML file: {e}')
        raise typer.Exit(code=1)
    
    # Parse bbox string
    bbox = bbox.split('SNWE:')[1]
    print(f'bbox: {bbox}')
    bbox = [val for val in bbox.split()]

    south = bbox[0]
    north = bbox[1]
    west = bbox[2]
    east = bbox[3].split('\'')[0]

    # Expand bbox with buffer
    south = math.floor(float(south) - 0.5)
    north = math.ceil(float(north) + 0.5)
    west = math.floor(float(west) - 0.5)
    east = math.ceil(float(east) + 0.5)
    
    print(f'Buffered bbox: S={south}, N={north}, W={west}, E={east}')
    
    # Format bbox for sardem (Left, Bottom, Right, Top)
    bbox_LeftBottomRightTop = [int(west), int(south), int(east), int(north)]
    output_name = f"elevation_{format_bbox(bbox_LeftBottomRightTop)}.dem"
    
    print(f"\n{'='*60}")
    print('Downloading DEM...')
    print(f"Output file: {output_name}")
    print(f"Data source: Copernicus DEM")
    print(f"Bounding box: {bbox_LeftBottomRightTop}")
    
    command = (
        f"sardem --bbox {int(west)} {int(south)} {int(east)} {int(north)} "
        f"--data COP --make-isce-xml --output {output_name}"
    )
    print(f"Command: {command}")
    
    # Change to DEM directory
    original_dir = Path.cwd()
    os.chdir(dem_dir)
    
    try:
        sardem.dem.main(
            bbox=bbox_LeftBottomRightTop,
            data_source="COP",
            make_isce_xml=True,
            output_name=output_name
        )
        print('DEM download completed successfully')
        
        # Verify output files
        dem_files = list(Path('.').glob(f'{output_name}*'))
        if dem_files:
            print("Created files:")
            for f in sorted(dem_files):
                print(f"  - {f.name}")
        
    except KeyboardInterrupt:
        print("\nDownload interrupted by user")
        raise typer.Exit(code=1)
    except Exception as e:
        print(f"\nERROR during DEM download: {e}")
        raise typer.Exit(code=1)
    finally:
        os.chdir(original_dir)

if __name__ == '__main__':
    app()