from pydantic import BaseModel, Field
from enum import Enum
from pathlib import Path
from typing import Optional

# ========= Global ========= #
class SystemConfig(BaseModel):
    scratch_dir: Path = Field(..., description="Scratch space for temporary files")
    work_dir: Path = Field(..., description="Permanent working directory")
    orbits_dir: Path = Field(..., description="Directory to place EOF files")
    max_parallel_jobs: int = Field(4, description="Max number of jobs at the same time")
    slurm_partition: str = Field(..., description="Name of the slurm partition to use")

class Platforms(str, Enum):
    SENTINEL = "SENTINEL-1"
    SKY = "SKYSAR"

# ========= Download ========= #
class DownloadConfig(BaseModel):
    platform: Platforms = Field(Platforms.SENTINEL, description="Which platform to download data from (e.g SENTINEL-1)")
    relative_orbit: int = Field(..., description="Relative orbit number")
    start_date: int = Field(..., description="Start date with YYYYMMDD format")
    end_date: int = Field(..., description="End date with YYYYMMDD format")
    max_results: int = Field(1000, description="Max results to get from source")
    bounding_box: str = Field(..., description="Polygon describing AOI (e.g  POLYGON((-99.20 19.25, -99.10 19.25, -99.10 19.35, -99.20 19.35, -99.20 19.25)))")
    parallel_downloads: int = Field(8, description="Number of parallel downloads")
    burst_download: bool = Field(False, description="Flag to activate burst download instead of SLC")
    slc_dir: Path = Field(Path("./SLC"), description="Directory to save downloaded products")

# ========= Dem ========= #
class DataSource(str, Enum):
    COP = "COP"
    NASA = "NASA"

class OutputFormat(str, Enum):
    ENVI = "ENVI"
    GTIFF = "GTiff"

class OutputType(str, Enum):
    INT16 = "int16"
    FLOAT32 = "float32"

class DemConfig(BaseModel):
    data_source: DataSource = Field(DataSource.COP, description="Which DEM provider to use [COP, NASA]")
    dem_dir: Path = Field(Path("./DEM"), description="Directory to save downloaded DEM")
    delta_latitude: float = Field(0.0, description="Delta latitude to subtract/add from min/max latitude")
    delta_longitude: float = Field(0.0, description="Delta longitude to subtract/add from min/max longitude")
    make_isce_xml: bool = Field(True, description="Make an ISCE2 XML file for the DEM")
    x_rate: int = Field(1, ge=1, le=50, description="Upsampling rate in X direction")
    y_rate: int = Field(1, ge=1, le=50, description="Upsampling rate in Y direction")
    keep_egm: bool = Field(False, description="Keep heights relative to EGM geoid instead of converting to WGS84")
    shift_rsc: bool = Field(False, description="Shift RSC metadata to pixel center instead of pixel edge")
    output_format: OutputFormat = Field(OutputFormat.GTIFF, description="Output raster format (GTiff for COP data and ENVI for NASA data).")
    output_type: OutputType = Field(OutputType.FLOAT32, description="Output DEM data type [int16, float32]")

# ========= Jobfiles ========= #
class JobfilesConfig(BaseModel):
    jobfiles_dir: Path = Field(Path("./jobfiles"), description="Directory to save jobfiles")

# ========= Project ========= #
class ProjectConfig(BaseModel):
    download: Optional[DownloadConfig] = Field(None, description="Download configuration section")
    dem: Optional[DemConfig] = Field(None, description="DEM configuration section")
    jobfiles: Optional[JobfilesConfig] = Field(None, description="Jobfiles configuration section")
    system: SystemConfig = Field(..., description="System configuration")
    project_name: str = Field(..., description="Name of the project (Same as template)")

