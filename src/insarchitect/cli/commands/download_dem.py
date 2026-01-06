from pathlib import Path
import os

import math
import shutil
from typing import Annotated
import typer
from rich import print

import sardem.dem
from insarchitect.config import load_config, load_dem_config
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
            print('[bold yellow]\nDEM products already exist. If not satisfying, remove the folder and run again[/bold yellow]')
            return True
        else:
            print('[bold yellow]\nIncomplete DEM directory found. Removing and recreating...[/bold yellow]')
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
    4. Downloads the DEM using sardem from Copernicus or NASA DEM
    5. Creates ISCE-compatible XML files
    
    Example:
        pixi run insarchitect download-dem <template>
    """
    
    # Get config
    
    dem_download_config = load_dem_config(config).dem    
    asf_download_config = load_config(config).download
    
    # Set directories
    work_dir = dem_download_config.work_dir
    data_source = dem_download_config.data_source
    dem_dir = work_dir / 'DEM'
    #slc_dir = Path('./')
    slc_dir = asf_download_config.slc_dir
    
    print(f"[bold green]{'='*60}[/bold green]")
    print("[bold green]DEM DOWNLOAD[/bold green]")
    print(f"[bold green]{'='*60}[/bold green]")
    print(f"[bold]Work directory[/bold]: {work_dir}")
    print(f"[bold]DEM directory[/bold]:  {dem_dir}")
    print(f"[bold]SLC directory[/bold]:  {slc_dir}")
    
    # Check for existing valid DEM
    if exist_valid_dem_dir(dem_dir):
        print("\n[bold cyan]Valid DEM already exists. Exiting.[/bold cyan]")
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
    print('[bold magenta]\nSearching for KML file...\n[/bold magenta]')
    try:
        kml_files = sorted(slc_dir.glob('*.kml'))
        if not kml_files:
            raise FileNotFoundError(
                f'[bold red]No *.kml found in {slc_dir}\n'
                'Please run the download command first to generate the KML file.[/bold red]'
            )
        ssara_kml_file = kml_files[-1]
    except Exception as e:
        print(f'[bold red]Error finding KML file: {e}[/bold red]')
        raise typer.Exit(code=1)
    
    print(f'[bold]Using KML file[/bold]: {ssara_kml_file.name}')
    
    # Get bounding box from KML
    print('[bold magenta]\nExtracting bounding box from KML...\n[/bold magenta]')
    try:
        bbox = get_boundingbox_from_kml.main( [str(ssara_kml_file), '--delta_lon', '0'] )    
    except Exception as e:
        print(f'[bold red]Problem with KML file: {e}[/bold red]')
        raise typer.Exit(code=1)
    
    # Parse bbox string
    bbox = bbox.split('SNWE:')[1]
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
    
    # Format bbox for sardem (Left, Bottom, Right, Top)
    bbox_LeftBottomRightTop = [int(west), int(south), int(east), int(north)]
    output_name = f"elevation_{format_bbox(bbox_LeftBottomRightTop)}.dem"
    data_source_str = "NASA DEM" if data_source == "NASA" else "Copernicus DEM"

    print('[bold magenta]\nDownloading DEM...\n[/bold magenta]')
    print(f"[bold]Output file[/bold]: {output_name}")
    print(f"[bold]Data source[/bold]: {data_source_str}")
    print(f"[bold]Bounding box[/bold]: {bbox_LeftBottomRightTop}")
    
    command = (
        f"sardem --bbox {int(west)} {int(south)} {int(east)} {int(north)} "
        f"--data {data_source} --make-isce-xml --output {output_name}"
    )
    print(f"[bold magenta]\nSARDEM execution...\n[/bold magenta]")
    print(f'[bold]Command[/bold]: {command}')
    # Change to DEM directory
    original_dir = Path.cwd()
    os.chdir(dem_dir)
    
    try:
        sardem.dem.main(
            bbox=bbox_LeftBottomRightTop,
            data_source=data_source,
            make_isce_xml=True,
            output_name=output_name
        )
        # Verify output files
        dem_files = list(Path('.').glob(f'{output_name}*'))
        if dem_files:
            print("[bold]\nCreated files[/bold]:")
            for f in sorted(dem_files):
                print(f"  - [bold cyan]{f.name}[/bold cyan]")
        print(f"[bold green]{'='*60}[/bold green]")
        print('[bold green]DEM DOWNLOAD COMPLETED SUCESSFULLY[/bold green]')
        print(f"[bold green]{'='*60}[/bold green]")
        
    except KeyboardInterrupt:
        print("[bold red]\nDownload interrupted by user[/bold red]")
        raise typer.Exit(code=1)
    except Exception as e:
        print(f"[bold red]\nERROR during DEM download: {e}[/bold red]")
        raise typer.Exit(code=1)
    finally:
        os.chdir(original_dir)

if __name__ == '__main__':
    app()