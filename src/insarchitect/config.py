import tomllib
import sys
from pathlib import Path
import platformdirs

from pydantic import ValidationError
from rich import print

from .models import ProjectConfig, SystemConfig

DEFAULT_SYSTEM_CONFIG_PATH = Path(platformdirs.user_config_dir("insarchitect")) / "config.toml"

def load_system_config() -> SystemConfig:
    """Loads global system configuration"""
    config_path = DEFAULT_SYSTEM_CONFIG_PATH

    if config_path.exists():
        data = tomllib.load(DEFAULT_SYSTEM_CONFIG_PATH.open("rb"))
        return SystemConfig(**data)
    else:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        scratch_dir = Path().home() / "scratch"
        work_dir = Path().home() / "workdir"
        orbits_dir = work_dir / Path("S1orbits")

        scratch_dir.mkdir(exist_ok=True)
        work_dir.mkdir(exist_ok=True)
        orbits_dir.mkdir(exist_ok=True)

        template = f"""# InSARchitect System Configuration
# This file contains machine-specific settings

scratch_dir = "{scratch_dir}"
work_dir = "{work_dir}"
orbits_dir = "{orbits_dir}"

max_parallel_jobs = 4
slurm_partition = "all"
    """
        config_path.write_text(template)

        data = tomllib.load(DEFAULT_SYSTEM_CONFIG_PATH.open("rb"))
        return SystemConfig(**data)

def load_config(config_path: Path) -> ProjectConfig:
    """Loads and validate TOML config file"""
    try:
        with open(config_path, "rb") as f:
            data = tomllib.load(f)

        system_config = load_system_config()
        data["system"] = system_config
        data["project_name"] = config_path.stem

        return ProjectConfig(**data)

    except FileNotFoundError:
        print(f"Configuration file not found: {config_path}")
        sys.exit(1)

    except ValidationError as e:
        print(f"Invalid configuration in {config_path}")
        for error in e.errors():
            section = str(error['loc'][0])
            field = error['loc'][1]

            if error['type'] == 'missing':
                print(f"Missing field in {section}: {field}",)
            else:
                print(f"Error in {section}: {field} -> {error['msg']}")
        sys.exit(1)

# def get_config_section(config_path: Path, section: str):
#     """Load specific section from config."""
#     config = load_config(config_path)
#     return getattr(config, section)