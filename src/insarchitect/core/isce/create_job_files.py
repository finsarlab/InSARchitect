import sys

from rich import print as print

from ...models import ProjectConfig

def job_files(config: ProjectConfig):
    work_dir = config.system.work_dir
    project_dir = work_dir / config.project_name
    run_files_dir = project_dir / "run_files"
    if not config.isce:
        print("No isce configuration given")
        sys.exit(1)

    run_files = [f for f in run_files_dir.iterdir()]
    run_files = sorted(run_files)
    print(run_files)

