import sys
import time
import tomllib
import shutil
import subprocess
from pathlib import Path

import platformdirs
from rich import print
from rich.live import Live
from rich.table import Table
from rich.console import Console

from ...models import ProjectConfig, SlurmStepConfig

console = Console()

SLURM_CONFIG_PATH = Path(platformdirs.user_config_dir("insarchitect")) / "slurm.toml"


def _load_slurm_config() -> dict[str, SlurmStepConfig]:
    """Load SLURM configuration from ~/.config/insarchitect/slurm.toml.

    Auto-generates a template on first run. Returns a dict mapping
    section names to SlurmStepConfig ('default' key is always present).
    """
    if not SLURM_CONFIG_PATH.exists():
        SLURM_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        template = """\
# SLURM Configuration for ISCE2 Processing
# Edit this file to customize SLURM job parameters

[default]
partition = "all"
walltime = "04:00:00"
ntasks = 1
memory = "8G"

# Override defaults for specific steps by adding a section
# with the step name (from run file name, without run_XX_ prefix).
# Example:
# [unwrap]
# walltime = "08:00:00"
# memory = "16G"
"""
        SLURM_CONFIG_PATH.write_text(template)
        print(f"[bold yellow]Generated SLURM config: {SLURM_CONFIG_PATH}[/bold yellow]")

    data = tomllib.load(SLURM_CONFIG_PATH.open("rb"))

    configs = {}
    defaults = SlurmStepConfig(**data.get("default", {}))
    configs["default"] = defaults

    for section, values in data.items():
        if section == "default":
            continue
        merged = defaults.model_dump()
        merged.update(values)
        configs[section] = SlurmStepConfig(**merged)

    return configs


def _get_step_config(slurm_configs: dict[str, SlurmStepConfig], step_name: str) -> SlurmStepConfig:
    """Get SLURM config for a step, falling back to defaults."""
    return slurm_configs.get(step_name, slurm_configs["default"])



def _parse_run_file(run_file: Path) -> tuple[list[str], bool]:
    """Parse an ISCE2 run file.

    Returns:
        commands: list of command strings (trailing & stripped)
        is_parallel: True if commands can run in parallel
    """
    commands = []
    is_parallel = False
    with open(run_file) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.endswith("&"):
                is_parallel = True
                line = line.rstrip("&").rstrip()
            commands.append(line)
    return commands, is_parallel


def _step_name_from_run_file(run_file_name: str) -> str:
    """Extract step name from run file name.

    'run_01_unpack_topo_reference' -> 'unpack_topo_reference'
    """
    parts = run_file_name.split("_", 2)
    return parts[2] if len(parts) > 2 else run_file_name


def _generate_job_script(
    command: str,
    job_name: str,
    slurm_cfg: SlurmStepConfig,
    log_dir: Path,
) -> str:
    """Generate the contents of a SLURM job script."""
    return f"""\
#!/bin/bash
#SBATCH --job-name={job_name}
#SBATCH --output={log_dir}/{job_name}.out
#SBATCH --error={log_dir}/{job_name}.err
#SBATCH --partition={slurm_cfg.partition}
#SBATCH --ntasks={slurm_cfg.ntasks}
#SBATCH --mem={slurm_cfg.memory}
#SBATCH --time={slurm_cfg.walltime}

{command}
"""


def _generate_submit_script(run_groups: list[dict], job_files_dir: Path) -> str:
    """Generate submit_jobs.sh that submits all jobs with correct dependencies."""
    lines = [
        "#!/bin/bash",
        "# Auto-generated SLURM submission script",
        "# Submits job files in run-step order with dependencies",
        "",
        "set -e",
        "",
    ]

    prev_var = None

    for i, group in enumerate(run_groups):
        group_var = f"STEP_{i:02d}_JIDS"
        lines.append(f"# === {group['name']} ===")
        lines.append(f'{group_var}=""')

        if group["is_parallel"]:
            for job_path in group["jobs"]:
                dep_clause = ""
                if prev_var:
                    dep_clause = f"--dependency=afterok:${{{prev_var}}} "
                lines.append(
                    f'JID=$(sbatch {dep_clause}--parsable "{job_path}")'
                )
                lines.append(f'{group_var}="${{{group_var}}}:${{JID}}"')
        else:
            for j, job_path in enumerate(group["jobs"]):
                if j == 0 and prev_var:
                    dep_clause = f"--dependency=afterok:${{{prev_var}}} "
                elif j > 0:
                    dep_clause = "--dependency=afterok:${JID} "
                else:
                    dep_clause = ""
                lines.append(
                    f'JID=$(sbatch {dep_clause}--parsable "{job_path}")'
                )
                lines.append(f'{group_var}="${{{group_var}}}:${{JID}}"')

        lines.append(f'{group_var}="${{{group_var}#:}}"')
        lines.append(f'echo "Submitted {group["name"]}: ${{{group_var}}}"')
        lines.append("")
        prev_var = group_var

    lines.append('echo "All jobs submitted."')
    return "\n".join(lines) + "\n"


def _submit_jobs(run_groups: list[dict]) -> list[dict]:
    """Submit all job scripts to SLURM with proper dependencies.

    Returns a list of dicts: {job_id, job_name, step_name, step_index}
    """
    submitted = []
    prev_step_ids = []

    for step_idx, group in enumerate(run_groups):
        step_ids = []

        if group["is_parallel"]:
            for job_path in group["jobs"]:
                cmd = ["sbatch", "--parsable"]
                if prev_step_ids:
                    dep_str = ":".join(prev_step_ids)
                    cmd.append(f"--dependency=afterok:{dep_str}")
                cmd.append(str(job_path))

                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"[bold red]sbatch failed for {job_path.name}: {result.stderr.strip()}[/bold red]")
                    sys.exit(1)

                job_id = result.stdout.strip()
                step_ids.append(job_id)
                submitted.append({
                    "job_id": job_id,
                    "job_name": job_path.stem,
                    "step_name": group["name"],
                    "step_index": step_idx,
                })
        else:
            last_id = None
            for j, job_path in enumerate(group["jobs"]):
                cmd = ["sbatch", "--parsable"]
                if j == 0 and prev_step_ids:
                    dep_str = ":".join(prev_step_ids)
                    cmd.append(f"--dependency=afterok:{dep_str}")
                elif j > 0 and last_id:
                    cmd.append(f"--dependency=afterok:{last_id}")
                cmd.append(str(job_path))

                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"[bold red]sbatch failed for {job_path.name}: {result.stderr.strip()}[/bold red]")
                    sys.exit(1)

                job_id = result.stdout.strip()
                step_ids.append(job_id)
                last_id = job_id
                submitted.append({
                    "job_id": job_id,
                    "job_name": job_path.stem,
                    "step_name": group["name"],
                    "step_index": step_idx,
                })

        prev_step_ids = step_ids

    return submitted


def _query_squeue(job_ids: list[str]) -> dict[str, str]:
    """Query squeue for active job states. Returns {job_id: state}."""
    result = subprocess.run(
        ["squeue", "--jobs", ",".join(job_ids), "--format=%i %T", "--noheader"],
        capture_output=True, text=True,
    )
    states = {}
    for line in result.stdout.strip().splitlines():
        parts = line.split()
        if len(parts) >= 2:
            states[parts[0]] = parts[1]
    return states


def _query_sacct(job_ids: list[str]) -> dict[str, str]:
    """Query sacct for final job states. Returns {job_id: state}."""
    result = subprocess.run(
        ["sacct", "-j", ",".join(job_ids), "--format=JobID,State", "-P", "--noheader"],
        capture_output=True, text=True,
    )
    states = {}
    for line in result.stdout.strip().splitlines():
        parts = line.split("|")
        if len(parts) >= 2:
            jid = parts[0]
            # sacct includes sub-steps like "12345.batch" — skip those
            if "." not in jid:
                states[jid] = parts[1]
    return states


STATE_COLORS = {
    "PENDING": "blue",
    "RUNNING": "yellow",
    "COMPLETED": "green",
    "FAILED": "red",
    "CANCELLED": "red",
    "TIMEOUT": "red",
}


def _build_monitor_table(run_groups: list[dict], submitted: list[dict], job_states: dict[str, str]) -> Table:
    """Build a Rich Table showing per-step job status."""
    table = Table(title="SLURM Job Monitor", expand=True)
    table.add_column("Step", style="bold", no_wrap=True)
    table.add_column("Total", justify="center")
    table.add_column("Pending", justify="center", style="blue")
    table.add_column("Running", justify="center", style="yellow")
    table.add_column("Done", justify="center", style="green")
    table.add_column("Failed", justify="center", style="red")

    # Group submitted jobs by step index
    step_jobs: dict[int, list[dict]] = {}
    for job in submitted:
        step_jobs.setdefault(job["step_index"], []).append(job)

    for group_idx, group in enumerate(run_groups):
        jobs = step_jobs.get(group_idx, [])
        total = len(jobs)
        pending = running = done = failed = 0

        for job in jobs:
            state = job_states.get(job["job_id"], "PENDING")
            if state in ("PENDING", "CONFIGURING"):
                pending += 1
            elif state in ("RUNNING", "COMPLETING"):
                running += 1
            elif state == "COMPLETED":
                done += 1
            else:
                failed += 1

        # Row style based on step status
        if failed > 0:
            row_style = "red"
        elif done == total:
            row_style = "green"
        elif running > 0:
            row_style = "yellow"
        else:
            row_style = ""

        table.add_row(
            group["name"],
            str(total),
            str(pending),
            str(running),
            str(done),
            str(failed),
            style=row_style,
        )

    return table


def _monitor_jobs(run_groups: list[dict], submitted: list[dict], poll_interval: int = 10):
    """Live-monitor submitted SLURM jobs until all complete or fail."""
    all_job_ids = [job["job_id"] for job in submitted]
    job_states: dict[str, str] = {jid: "PENDING" for jid in all_job_ids}

    print(f"\n[bold]Monitoring {len(submitted)} jobs (Ctrl+C to stop monitoring)...[/bold]\n")

    try:
        with Live(
            _build_monitor_table(run_groups, submitted, job_states),
            console=console,
            refresh_per_second=1,
        ) as live:
            while True:
                # Query squeue for active jobs
                active_states = _query_squeue(all_job_ids)

                # IDs not in squeue are finished — query sacct
                finished_ids = [jid for jid in all_job_ids if jid not in active_states]
                final_states = _query_sacct(finished_ids) if finished_ids else {}

                # Merge states
                for jid in all_job_ids:
                    if jid in active_states:
                        job_states[jid] = active_states[jid]
                    elif jid in final_states:
                        job_states[jid] = final_states[jid]

                live.update(_build_monitor_table(run_groups, submitted, job_states))

                # Check if all jobs are done
                active_count = sum(
                    1 for s in job_states.values()
                    if s in ("PENDING", "RUNNING", "CONFIGURING", "COMPLETING")
                )
                if active_count == 0:
                    break

                time.sleep(poll_interval)

    except KeyboardInterrupt:
        print("\n[bold yellow]Monitoring stopped. Jobs are still running on SLURM.[/bold yellow]")
        return

    # Final summary
    completed = sum(1 for s in job_states.values() if s == "COMPLETED")
    failed = [
        job for job in submitted
        if job_states.get(job["job_id"]) not in ("COMPLETED", "PENDING", "RUNNING")
    ]

    print(f"\n[bold green]All jobs finished: {completed}/{len(submitted)} completed[/bold green]")
    if failed:
        print(f"[bold red]{len(failed)} job(s) failed:[/bold red]")
        for job in failed:
            state = job_states.get(job["job_id"], "UNKNOWN")
            print(f"  [red]{job['job_name']} (ID: {job['job_id']}): {state}[/red]")


def job_files(config: ProjectConfig):
    work_dir = config.system.work_dir
    project_dir = work_dir / config.project_name
    run_files_dir = project_dir / "run_files"
    job_files_dir = project_dir / "job_files"
    log_dir = job_files_dir / "logs"

    if not config.isce:
        print("[bold red]No isce configuration given[/bold red]")
        sys.exit(1)

    if not run_files_dir.exists():
        print(f"[bold red]Run files directory not found: {run_files_dir}[/bold red]")
        sys.exit(1)

    # Clean previous job files
    shutil.rmtree(job_files_dir, ignore_errors=True)
    job_files_dir.mkdir(parents=True)
    log_dir.mkdir(parents=True)

    slurm_configs = _load_slurm_config()

    run_files = sorted(f for f in run_files_dir.iterdir() if f.is_file())
    if not run_files:
        print(f"[bold red]No run files found in {run_files_dir}[/bold red]")
        sys.exit(1)

    print(f"[bold green]{'='*60}[/bold green]")
    print("[bold green]SLURM JOB FILE GENERATION[/bold green]")
    print(f"[bold green]{'='*60}[/bold green]")
    print(f"[bold]Run files directory[/bold]: {run_files_dir}")
    print(f"[bold]Job files directory[/bold]: {job_files_dir}")
    print(f"[bold]SLURM config[/bold]:        {SLURM_CONFIG_PATH}")
    print(f"[bold]Found run files[/bold]:     {len(run_files)}")

    run_groups = []

    for run_file in run_files:
        commands, is_parallel = _parse_run_file(run_file)
        run_name = run_file.stem
        step_name = _step_name_from_run_file(run_name)
        slurm_cfg = _get_step_config(slurm_configs, step_name)

        group_dir = job_files_dir / run_name
        group_dir.mkdir()

        mode_label = "parallel" if is_parallel else "sequential"
        print(f"  [bold]{run_name}[/bold]: {len(commands)} command(s) ({mode_label})")

        job_paths = []
        for idx, command in enumerate(commands, start=1):
            job_name = f"job_{run_name.removeprefix('run_')}_{idx}"
            script_content = _generate_job_script(
                command=command,
                job_name=job_name,
                slurm_cfg=slurm_cfg,
                log_dir=log_dir,
            )
            job_path = group_dir / f"{job_name}.sh"
            job_path.write_text(script_content)
            job_paths.append(job_path)

        run_groups.append({
            "name": run_name,
            "jobs": job_paths,
            "is_parallel": is_parallel,
        })

    # Generate master submission script
    submit_content = _generate_submit_script(run_groups, job_files_dir)
    submit_path = job_files_dir / "submit_jobs.sh"
    submit_path.write_text(submit_content)
    submit_path.chmod(0o755)

    total_jobs = sum(len(g["jobs"]) for g in run_groups)
    print(f"\n[bold green]Generated {total_jobs} job scripts across {len(run_groups)} run steps[/bold green]")
    print(f"[bold green]Submission script: {submit_path}[/bold green]")
    print(f"[bold green]{'='*60}[/bold green]")

    # Auto-submit jobs
    print(f"\n[bold green]{'='*60}[/bold green]")
    print("[bold green]SUBMITTING JOBS TO SLURM[/bold green]")
    print(f"[bold green]{'='*60}[/bold green]")

    submitted = _submit_jobs(run_groups)
    print(f"[bold green]Submitted {len(submitted)} jobs to SLURM[/bold green]")

    # Live monitoring
    _monitor_jobs(run_groups, submitted)
