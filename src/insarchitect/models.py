from pydantic import BaseModel, Field
from enum import Enum
from pathlib import Path
from datetime import date
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

class DemConfig(BaseModel):
    data_source: DataSource = Field(DataSource.COP, description="Which DEM provider to use [COP, NASA]")
    dem_dir: Path = Field(Path("./DEM"), description="Directory to save downloaded DEM")

# ========= ISCE ========= #
class Polarization(str, Enum):
    VV = "vv"
    VH = "vh"
    HH = "hh"
    HV = "hv"
    VV_HH = "vv+hh"
    HH_VH = "hh_vh"

class Workflow(str, Enum):
    SLC = "slc"
    CORRELATION = "correlation"
    INTERFEROGRAM = "interferogram"
    OFFSET = "offset"

class Coregistration(str, Enum):
    GEOMETRY = "geometry"
    NESD = "NESD"

class UnwrapMethod(str, Enum):
    ICU = "icu"
    SNAPHU = "snaphu"

class IsceConfig(BaseModel):
    # Options
    slc_dir: Path = Field(..., description="Directory with all SLCs")
    polarization: Polarization = Field(Polarization.VV, description="SAR data polarization (default: vv)")
    workflow: Workflow = Field(Workflow.INTERFEROGRAM, description="The InSAR processing workflow (default: interferogram)")
    # AOI
    swath_num: list[int] = Field([1, 2, 3], description="List of swaths to be processed")
    bbox: list[float] = Field([], description="Lat/Lon Bounding SNWE")
    # Dates
    exclude_dates: list[str] = Field([], description="List of the dates to be excluded for processing.")
    include_date: list[str] = Field([], description="List of the dates to be included for processing.")
    start_date: date | None = Field(None, description="Start date for stack processing (format: YYYY-MM-DD)")
    stop_date: date | None = Field(None, description="Stop date for stack processing (format: YYYY-MM-DD)")
    # Coregistration
    coregistration: Coregistration = Field(Coregistration.NESD, description="Coregistration method")
    reference_date: Path | None = Field(None, description="Directory with reference acquisition")
    snr_misreg_threshold: float = Field(10.0, description="SNR threshold for range misregistration")
    esd_coherence_threshold: float = Field(0.85, description="Coherence threshold for azimuth misregistration")
    num_overlap_connections: int = Field(3, description="Number of overlap interferograms for NESD computation")
    # Interferogram
    num_connections: int = Field(1, description="Number of interferograms between each date and subsequent dates")
    azimuth_looks: int = Field(3, description="Number of looks in azimuth for interferogram multi-looking")
    range_looks: int = Field(9, description="Number of looks in range for interferogram multi-looking")
    filter_strength: float = Field(0.5, description="Filter strength for interferogram filtering")
    # Phase unwrapping
    unw_method: UnwrapMethod = Field(UnwrapMethod.SNAPHU, description="Unwrapping method")
    rm_filter: bool = Field(False, description="Make an extra unwrap file with filtering effect removed")
    # Ionosphere
    param_ion: Path | None = Field(None, description="Ionosphere estimation parameter file path")
    num_connections_ion: int = Field(3, description="Number of interferograms for ionosphere estimation")
    # Computing
    use_gpu: bool = Field(False, description="Allow app to use GPU when available")
    num_proc: int = Field(1, description="Number of tasks running in parallel in each run file")
    num_proc4topo: int = Field(1, description="Number of parallel processes for topo only")
    text_cmd: str = Field("", description="Text command added to the beginning of each run file line")
    virtual_merge: bool = Field(True, description="Use virtual files for merged SLCs and geometry files")



# ========= Project ========= #
class ProjectConfig(BaseModel):
    download: Optional[DownloadConfig] = Field(None, description="Download configuration section")
    dem: Optional[DemConfig] = Field(None, description="DEM configuration section")
    isce: Optional[IsceConfig] = Field(None, description="Isce configuration section")
    system: SystemConfig = Field(..., description="System configuration")
    project_name: str = Field(..., description="Name of the project (Same as template)")

