import sys
import asyncio
from concurrent.futures import ThreadPoolExecutor
from s1_orbits import fetch_for_scene
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TransferSpeedColumn, DownloadColumn
from ...models import ProjectConfig

async def download_orbits(config: ProjectConfig):
    if not config.download:
        print("No valid download config file given")
        sys.exit(1)

    work_dir = config.system.work_dir / config.project_name
    slc_dir = work_dir / config.download.slc_dir
    orbits_dir = config.system.orbits_dir
    orbits_dir.mkdir(exist_ok=True)

    burst_flag = config.download.burst_download
    pattern = "*.tiff" if burst_flag else "*.zip"
    downloaded_products = list(slc_dir.glob(pattern))

    loop = asyncio.get_event_loop()
    avg_file_size = int(4.3 * 1_000_000)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TransferSpeedColumn(),
        DownloadColumn(),
    ) as progress:
        task = progress.add_task("Downloading orbits...", total=len(downloaded_products) * avg_file_size)

        with ThreadPoolExecutor(max_workers=50) as executor:
            tasks = []
            for orbit in downloaded_products:
                tasks.append(loop.run_in_executor(executor, fetch_for_scene, orbit.stem, orbits_dir))

            results = []
            for coro in asyncio.as_completed(tasks):
                result = await coro
                results.append(result)
                progress.update(task, advance=avg_file_size)
