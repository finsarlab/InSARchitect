import tomllib
import sys
from dataclasses import dataclass
from pathlib import Path

from .utils import parse_date

@dataclass
class DownloadConfig:
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
class Config:
    download: DownloadConfig

def load_config(path: Path) -> Config:
    """Load config file
    
    Parameters
    ----------
    path: Path
        Path to config file

    Returns
    -------
    Config
        An Config object containing every parameter
    """
    try:
        with path.open("rb") as f:
            data = tomllib.load(f)
        download_config = DownloadConfig(**data['download'])
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except TypeError as e:
        print(f"Argument not supported: {e}")
        sys.exit(1)

    config = Config(
        download_config
    )

    return config

