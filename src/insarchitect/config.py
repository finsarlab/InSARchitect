import tomllib
import sys
from dataclasses import dataclass
from pathlib import Path
from rich import print

from .utils import parse_date

@dataclass
class DownloadSLCConfig:
    """Configuration for SLC download."""
    platform: str
    relative_orbit: int
    start_date: str
    end_date: str
    max_results: int
    bounding_box: str
    parallel_downloads: int
    burst_download: bool
    slc_dir: str | Path

    def __post_init__(self):
            self.slc_dir = Path(self.slc_dir)
            self.start_date = parse_date.parse_date_from_int(self.start_date)
            self.end_date = parse_date.parse_date_from_int(self.end_date)

@dataclass
class DownloadDEMConfig:
    """Configuration for DEM download and processing."""
    work_dir: str | Path
    data_source: str
    
    def __post_init__(self):
        self.work_dir = Path(self.work_dir)
        self.data_source = str(self.data_source)
        
        # Validate data source
        valid_sources = ["COP", "NASA"]
        if self.data_source.upper() not in valid_sources:
            print(f"Warning: data_source '{self.data_source}' not in {valid_sources}. Using 'COP'")
            self.data_source = "COP"
        else:
            self.data_source = self.data_source.upper()

@dataclass
class SLCConfig:
    download: DownloadSLCConfig

@dataclass
class DEMConfig:
    dem: DownloadDEMConfig

def load_config(path: Path) -> SLCConfig:
    """Load config file
    
    Parameters
    ----------
    path: Path
        Path to config file

    Returns
    -------
    SLCConfig
        A SLCConfig object containing parameters for SLC downloads
    """
    try:
        with path.open("rb") as f:
            data = tomllib.load(f)
        download_config = DownloadSLCConfig(**data['download'])
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except TypeError as e:
        print(f"Argument not supported: {e}")
        sys.exit(1)

    config = SLCConfig(
        download_config
    )

    return config


def load_dem_config(path: Path) -> DEMConfig:
    """Load dem parameters
    
    Parameters
    ----------
    path: Path
        Path to config file

    Returns
    -------
    DEMConfig
        A DEMConfig object containing parameters for DEM downloads
    """
    try:
        with path.open("rb") as f:
            data = tomllib.load(f)
        
        if 'dem' not in data:
            print('[bold yellow]Template file does not have dem key definition. Using default values.[/bold yellow]')
            dem_config = DownloadDEMConfig(
                work_dir="./", 
                data_source="COP"
            )
        else:
            dem_config = DownloadDEMConfig(**data['dem'])
            
    except FileNotFoundError as e:
        print(f"[bold red]Error finding config file: {e}[/bold red]")
        sys.exit(1)
    except TypeError as e:
        print(f"[bold red]Error managing the argument: {e}[/bold red]")
        sys.exit(1)

    config = DEMConfig(
        dem_config
    )

    return config
