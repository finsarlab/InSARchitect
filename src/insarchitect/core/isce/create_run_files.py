import sys
import shutil

from rich import print as print
from topsStack import stackSentinel

from ...models import ProjectConfig

def run_files(config: ProjectConfig):
    work_dir = config.system.work_dir
    project_dir = work_dir / config.project_name

    # Remove previous run_files
    shutil.rmtree(project_dir / "run_files", ignore_errors=True)

    if config.dem:
        dem_dir = project_dir / config.dem.dem_dir
        dem_file = next(dem_dir.glob("*.dem"))
    if config.download:
        slc_dir = project_dir / config.download.slc_dir
    if not config.isce:
        print("No isce configuration given")
        sys.exit(1)

    isce = config.isce

    args = [ '--slc_directory', str(slc_dir),
        '--orbit_directory', str(config.system.orbits_dir),
        '--aux_directory', str(config.system.orbits_dir),
        '--working_directory', str(project_dir),
        '--dem', str(dem_file),
        '--polarization', str(isce.polarization.value),
        '--workflow', str(isce.workflow.value),
        '--swath_num', ' '.join(map(str, isce.swath_num)),
    ]

    if isce.bbox:
        args.extend(['--bbox', ' '.join(map(str, isce.bbox))])

    if isce.exclude_dates:
        args.extend(['--exclude_dates', ','.join(isce.exclude_dates)])
    if isce.include_date:
        args.extend(['--include_dates', ','.join(isce.include_date)])
    if isce.start_date:
        args.extend(['--start_date', str(isce.start_date)])
    if isce.stop_date:
        args.extend(['--stop_date', str(isce.stop_date)])

    args.extend([
        '--coregistration', str(isce.coregistration.value),
    ])

    if isce.reference_date:
        args.extend(['--reference_date', str(isce.reference_date)])

    args.extend([
        '--snr_misreg_threshold', str(isce.snr_misreg_threshold),
        '--esd_coherence_threshold', str(isce.esd_coherence_threshold),
        '--num_overlap_connections', str(isce.num_overlap_connections),
        '--num_connections', str(isce.num_connections),
        '--azimuth_looks', str(isce.azimuth_looks),
        '--range_looks', str(isce.range_looks),
        '--filter_strength', str(isce.filter_strength),
        '--unw_method', str(isce.unw_method.value),
    ])

    if isce.rm_filter:
        args.append('--rmFilter')

    if isce.param_ion:
        args.extend(['--param_ion', str(isce.param_ion)])

    args.extend([
        '--num_connections_ion', str(isce.num_connections_ion),
    ])

    if isce.use_gpu:
        args.append('--useGPU')

    args.extend([
        '--num_process', str(isce.num_proc),
        '--num_process4topo', str(isce.num_proc4topo),
        '--text_cmd', isce.text_cmd,
        '--virtual_merge', str(isce.virtual_merge),
    ])

    stackSentinel.main(iargs=args)

