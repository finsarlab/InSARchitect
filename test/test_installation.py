"""Test installation integrity for InSARchitect."""

import sys
import importlib
import subprocess
import warnings
from pathlib import Path

import pytest

def check_import(package: str) -> tuple[bool, str]:
    """Check if a package can be imported."""
    try:
        importlib.import_module(package)
        return True, ""
    except ImportError as e:
        return False, str(e)


def check_cli_command(command: str) -> tuple[bool, str]:
    """Check if a CLI command works."""
    try:
        result = subprocess.run(
            [command, "--help"],
            capture_output=True,
            timeout=10
        )
        return (result.returncode == 0, "" if result.returncode == 0 else f"exit code {result.returncode}")
    except FileNotFoundError:
        return False, "not found"
    except Exception as e:
        return False, str(e)


def test_python_version():
    """Test Python version is correct."""
    assert sys.version_info >= (3, 10) and sys.version_info < (3, 12), \
        f"Python version {sys.version_info.major}.{sys.version_info.minor} is not supported"


def test_cmake():
    """Test cmake is available."""
    try:
        subprocess.run(["cmake", "--version"], capture_output=True, timeout=5, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        pytest.fail("cmake not found")
    except Exception as e:
        pytest.fail(f"cmake test failed: {e}")


def test_setuptools():
    """Test setuptools can be imported."""
    success, error = check_import("setuptools")
    assert success, f"Failed to import setuptools: {error}"


def test_insarchitect_package():
    """Test insarchitect package can be imported."""
    success, error = check_import("insarchitect")
    assert success, f"Failed to import insarchitect: {error}"


def test_insarchitect_cli():
    """Test insarchitect CLI command works."""
    success, error = check_cli_command("insarchitect")
    assert success, f"insarchitect CLI failed: {error}"


def get_tools_dir() -> Path:
    """Get the tools directory path."""
    project_root = Path(__file__).parent.parent
    return project_root / "tools"


def test_mintpy_installation():
    """Test MintPy core tool installation and import."""
    tools_dir = get_tools_dir()
    mintpy_dir = tools_dir / "MintPy"
    
    assert mintpy_dir.exists(), f"MintPy repository not found at {mintpy_dir}"
    assert mintpy_dir.is_dir(), f"MintPy path exists but is not a directory: {mintpy_dir}"
    
    success, error = check_import("mintpy")
    assert success, f"Failed to import mintpy: {error}"


def test_miaplpy_installation():
    """Test MiaplPy core tool installation and import."""
    tools_dir = get_tools_dir()
    miaplpy_dir = tools_dir / "MiaplPy"
    
    assert miaplpy_dir.exists(), f"MiaplPy repository not found at {miaplpy_dir}"
    assert miaplpy_dir.is_dir(), f"MiaplPy path exists but is not a directory: {miaplpy_dir}"
    
    success, error = check_import("miaplpy")
    assert success, f"Failed to import miaplpy: {error}"


def test_isce2_installation():
    """Test ISCE2 core tool installation."""
    tools_dir = get_tools_dir()
    isce2_dir = tools_dir / "isce2"
    
    assert isce2_dir.exists(), f"ISCE2 repository not found at {isce2_dir}"
    assert isce2_dir.is_dir(), f"ISCE2 path exists but is not a directory: {isce2_dir}"


def test_numpy_integrity():
    """Test numpy functionality."""
    import numpy as np
    arr = np.array([1, 2, 3])
    assert arr is not None


def test_typer_integrity():
    """Test typer functionality."""
    import typer
    app = typer.Typer()
    assert app is not None


def test_pandas_integrity():
    """Test pandas functionality."""
    import pandas as pd
    df = pd.DataFrame({"a": [1, 2, 3]})
    assert df is not None


def test_gdal_integrity():
    """Test GDAL functionality."""
    from osgeo import gdal
    version = gdal.__version__
    assert version is not None


def test_cli_app():
    """Test CLI app structure."""
    from insarchitect.cli import app
    assert hasattr(app, 'registered_commands')

