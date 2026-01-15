"""Tests for download commands (SLC and DEM downloads)."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
import tempfile
import shutil

from insarchitect.commands.download import download
from insarchitect.commands.dem import (
    download_dem,
    format_bbox,
    exist_valid_dem_dir
)


class TestFormatBbox:
    """Test the format_bbox helper function."""

    def test_all_positive_coordinates(self):
        """Test formatting with all positive coordinates."""
        bbox = (10, 20, 15, 25)
        result = format_bbox(bbox)
        assert result == "N20_N25_E010_E015"

    def test_all_negative_coordinates(self):
        """Test formatting with all negative coordinates."""
        bbox = (-80, -10, -75, -5)
        result = format_bbox(bbox)
        assert result == "S10_S05_W080_W075"

    def test_mixed_coordinates(self):
        """Test formatting with mixed positive and negative coordinates."""
        bbox = (-78, -1, -76, 1)
        result = format_bbox(bbox)
        assert result == "S01_N01_W078_W076"

    def test_zero_coordinates(self):
        """Test formatting with zero coordinates."""
        bbox = (0, 0, 5, 5)
        result = format_bbox(bbox)
        assert result == "N00_N05_E000_E005"

    def test_large_coordinates(self):
        """Test formatting with three-digit coordinates."""
        bbox = (-120, -45, -100, -30)
        result = format_bbox(bbox)
        assert result == "S45_S30_W120_W100"


class TestExistValidDemDir:
    """Test the exist_valid_dem_dir helper function."""

    def test_nonexistent_directory(self):
        """Test with non-existent directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dem_dir = Path(tmpdir) / "nonexistent"
            result = exist_valid_dem_dir(dem_dir)
            assert result is False

    def test_valid_dem_directory(self):
        """Test with valid DEM directory containing required files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dem_dir = Path(tmpdir) / "DEM"
            dem_dir.mkdir()

            # Create dummy DEM files
            (dem_dir / "elevation.dem.wgs84").touch()
            (dem_dir / "elevation.dem.wgs84.xml").touch()
            (dem_dir / "elevation.dem.wgs84.vrt").touch()

            with patch('builtins.print'):
                result = exist_valid_dem_dir(dem_dir)

            assert result is True

    def test_incomplete_dem_directory(self):
        """Test with incomplete DEM directory (less than 3 files)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dem_dir = Path(tmpdir) / "DEM"
            dem_dir.mkdir()

            # Create only 2 files (incomplete)
            (dem_dir / "elevation.dem.wgs84").touch()
            (dem_dir / "elevation.dem.wgs84.xml").touch()

            with patch('builtins.print'):
                result = exist_valid_dem_dir(dem_dir)

            assert result is False
            assert not dem_dir.exists()  # Should be removed

    def test_empty_dem_directory(self):
        """Test with empty DEM directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dem_dir = Path(tmpdir) / "DEM"
            dem_dir.mkdir()

            with patch('builtins.print'):
                result = exist_valid_dem_dir(dem_dir)

            assert result is False
            assert not dem_dir.exists()  # Should be removed


class TestDownloadCommand:
    """Test the SLC/Burst download command."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration object."""
        config = Mock()
        config.download = Mock()
        config.download.burst_download = False
        config.download.slc_dir = Path("/tmp/test_slc")
        config.download.platform = "SENTINEL-1"
        config.download.max_results = 100
        config.download.start_date = "2023-01-01"
        config.download.end_date = "2023-12-31"
        config.download.bounding_box = "POLYGON((-78 -1, -76 -1, -76 1, -78 1, -78 -1))"
        config.download.parallel_downloads = 4
        return config

    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write("""
[download]
burst_download = false
slc_dir = "/tmp/test_slc"
platform = "SENTINEL-1"
max_results = 100
start_date = "2023-01-01"
end_date = "2023-12-31"
bounding_box = "POLYGON((-78 -1, -76 -1, -76 1, -78 1, -78 -1))"
parallel_downloads = 4
            """)
            temp_path = Path(f.name)

        yield temp_path

        if temp_path.exists():
            temp_path.unlink()

    @patch('insarchitect.commands.download.load_config')
    @patch('insarchitect.commands.download.asf')
    @patch('insarchitect.commands.download.simplekml')
    @patch('shapely.geometry.shape')
    def test_successful_slc_download(self, mock_shape, mock_kml, mock_asf, mock_load_config, mock_config):
        """Test successful SLC download."""
        mock_load_config.return_value = mock_config

        # Mock ASF search results
        mock_result = Mock()
        mock_result.geometry = {"type": "Polygon", "coordinates": [[[-78, -1], [-76, -1], [-76, 1], [-78, 1], [-78, -1]]]}
        mock_result.properties = {"fileID": "S1A_test_file"}

        # Mock shapely geometry
        mock_geom = Mock()
        mock_geom.exterior.coords = [(-78, -1), (-76, -1), (-76, 1), (-78, 1), (-78, -1)]
        mock_shape.return_value = mock_geom

        mock_results = Mock()
        mock_results.__iter__ = Mock(return_value=iter([mock_result]))
        mock_results.raise_if_incomplete = Mock()
        mock_results.download = Mock()

        mock_asf.geo_search.return_value = mock_results
        mock_asf.PRODUCT_TYPE.SLC = "SLC"
        mock_asf.PLATFORM.SENTINEL1 = "SENTINEL-1"

        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "test.toml"
            config_file.touch()

            mock_config.download.slc_dir = Path(tmpdir) / "SLC"

            download(config_file)

            assert mock_asf.geo_search.called
            assert mock_results.download.called

    @patch('insarchitect.commands.download.load_config')
    @patch('insarchitect.cli.commands.download.asf')
    @patch('insarchitect.commands.download.simplekml')
    def test_burst_download_mode(self, mock_kml, mock_asf, mock_load_config, mock_config):
        """Test burst download mode is correctly set."""
        mock_config.download.burst_download = True
        mock_load_config.return_value = mock_config

        mock_results = Mock()
        mock_results.raise_if_incomplete = Mock()
        mock_results.__iter__ = Mock(return_value=iter([]))
        mock_results.download = Mock()

        mock_asf.geo_search.return_value = mock_results
        mock_asf.PRODUCT_TYPE.BURST = "BURST"
        mock_asf.PRODUCT_TYPE.SLC = "SLC"
        mock_asf.PLATFORM.SENTINEL1 = "SENTINEL-1"

        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "test.toml"
            config_file.touch()

            mock_config.download.slc_dir = Path(tmpdir) / "SLC"

            download(config_file)

            # Verify geo_search was called with BURST product type
            call_args = mock_asf.geo_search.call_args
            assert call_args[1]['processingLevel'] == mock_asf.PRODUCT_TYPE.BURST

    @patch('insarchitect.commands.download.load_config')
    @patch('insarchitect.commands.download.asf')
    def test_asf_search_error(self, mock_asf, mock_load_config, mock_config):
        """Test handling of ASF search errors."""
        from asf_search.exceptions import ASFSearchError
        import typer

        mock_load_config.return_value = mock_config
        mock_asf.PRODUCT_TYPE.SLC = "SLC"
        mock_asf.PLATFORM.SENTINEL1 = "SENTINEL-1"

        mock_results = Mock()
        mock_results.raise_if_incomplete.side_effect = ASFSearchError("Search incomplete")
        mock_asf.geo_search.return_value = mock_results

        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "test.toml"
            config_file.touch()

            mock_config.download.slc_dir = Path(tmpdir) / "SLC"

            with patch('builtins.print'):
                with pytest.raises(typer.Exit) as exc_info:
                    download(config_file)
                assert exc_info.value.exit_code == 1

    @patch('insarchitect.commands.download.load_config')
    @patch('insarchitect.commands.download.asf')
    @patch('insarchitect.commands.download.os._exit')
    @patch('insarchitect.commands.download.simplekml')
    @patch('shapely.geometry.shape')
    def test_authentication_error(self, mock_shape, mock_kml, mock_exit, mock_asf, mock_load_config, mock_config):
        """Test handling of authentication errors."""
        from asf_search.exceptions import ASFAuthenticationError

        mock_load_config.return_value = mock_config

        mock_result = Mock()
        mock_result.geometry = {"type": "Polygon", "coordinates": [[[-78, -1], [-76, -1], [-76, 1], [-78, 1], [-78, -1]]]}
        mock_result.properties = {"fileID": "S1A_test_file"}

        # Mock shapely geometry
        mock_geom = Mock()
        mock_geom.exterior.coords = [(-78, -1), (-76, -1), (-76, 1), (-78, 1), (-78, -1)]
        mock_shape.return_value = mock_geom

        mock_results = Mock()
        mock_results.__iter__ = Mock(return_value=iter([mock_result]))
        mock_results.raise_if_incomplete = Mock()
        mock_results.download.side_effect = ASFAuthenticationError("Auth failed")

        mock_asf.geo_search.return_value = mock_results
        mock_asf.PRODUCT_TYPE.SLC = "SLC"
        mock_asf.PLATFORM.SENTINEL1 = "SENTINEL-1"

        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "test.toml"
            config_file.touch()

            mock_config.download.slc_dir = Path(tmpdir) / "SLC"

            with patch('builtins.print'):
                download(config_file)

            assert mock_exit.called
            mock_exit.assert_called_once_with(1)


class TestDownloadDemCommand:
    """Test the DEM download command."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration object."""
        config = Mock()
        config.dem = Mock()
        config.dem.work_dir = Path("/tmp/test_work")
        config.dem.data_source = "NASA"

        config.download = Mock()
        config.download.slc_dir = Path("/tmp/test_slc")

        return config

    @patch('insarchitect.commands.download_dem.load_config')
    @patch('insarchitect.commands.download_dem.exist_valid_dem_dir')
    def test_existing_valid_dem(self, mock_exist, mock_load_config, mock_config):
        """Test early exit when valid DEM already exists."""
        import typer

        mock_load_config.return_value = mock_config
        mock_exist.return_value = True

        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "test.toml"
            config_file.touch()

            with patch('builtins.print'):
                with pytest.raises(typer.Exit):
                    download_dem(config_file)

            assert mock_exist.called

    @patch('insarchitect.commands.download_dem.load_config')
    @patch('insarchitect.commands.download_dem.exist_valid_dem_dir')
    @patch('insarchitect.commands.download_dem.get_boundingbox_from_kml')
    @patch('insarchitect.commands.download_dem.sardem')
    @patch('insarchitect.commands.download_dem.os.chdir')
    @patch('insarchitect.commands.download_dem.Path.cwd')
    @patch('insarchitect.commands.download_dem.Path.glob')
    def test_successful_dem_download(
        self, mock_glob, mock_cwd, mock_chdir, mock_sardem, mock_bbox, mock_exist, mock_load_config, mock_config
    ):
        """Test successful DEM download."""
        mock_load_config.return_value = mock_config
        mock_exist.return_value = False
        mock_bbox.main.return_value = "SNWE: -1 1 -78 -76 '"
        mock_cwd.return_value = Path("/tmp/original")

        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "test.toml"
            config_file.touch()

            slc_dir = Path(tmpdir) / "SLC"
            slc_dir.mkdir()

            # Create a KML file
            kml_file = slc_dir / "test.kml"
            kml_file.touch()

            mock_config.download.slc_dir = slc_dir
            mock_config.dem.work_dir = Path(tmpdir)

            # Mock DEM files that would be created
            mock_glob.return_value = [
                Path("elevation_S01_N01_W078_W076.dem.wgs84"),
                Path("elevation_S01_N01_W078_W076.dem.wgs84.xml"),
                Path("elevation_S01_N01_W078_W076.dem.wgs84.vrt")
            ]

            with patch('builtins.print'):
                download_dem(config_file)

            assert mock_sardem.dem.main.called
            call_kwargs = mock_sardem.dem.main.call_args[1]
            # Bounding box is buffered by 0.5 degrees: floor(west-0.5), floor(south-0.5), ceil(east+0.5), ceil(north+0.5)
            assert call_kwargs['bbox'] == [-79, -2, -75, 2]
            assert call_kwargs['data_source'] == "NASA"
            assert call_kwargs['make_isce_xml'] is True

    @patch('insarchitect.commands.download_dem.load_config')
    @patch('insarchitect.commands.download_dem.exist_valid_dem_dir')
    def test_missing_kml_file(self, mock_exist, mock_load_config, mock_config):
        """Test error handling when KML file is missing."""
        import typer

        mock_load_config.return_value = mock_config
        mock_exist.return_value = False

        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "test.toml"
            config_file.touch()

            slc_dir = Path(tmpdir) / "SLC"
            slc_dir.mkdir()

            mock_config.download.slc_dir = slc_dir
            mock_config.dem.work_dir = Path(tmpdir)

            with patch('builtins.print'):
                with pytest.raises(typer.Exit) as exc_info:
                    download_dem(config_file)
                assert exc_info.value.exit_code == 1

    @patch('insarchitect.commands.download_dem.load_config')
    @patch('insarchitect.commands.download_dem.exist_valid_dem_dir')
    @patch('insarchitect.commands.download_dem.get_boundingbox_from_kml')
    @patch('insarchitect.commands.download_dem.sardem')
    @patch('insarchitect.commands.download_dem.os.chdir')
    @patch('insarchitect.commands.download_dem.Path.cwd')
    @patch('insarchitect.commands.download_dem.Path.glob')
    def test_copernicus_data_source(
        self, mock_glob, mock_cwd, mock_chdir, mock_sardem, mock_bbox, mock_exist, mock_load_config, mock_config
    ):
        """Test DEM download with Copernicus data source."""
        mock_config.dem.data_source = "COPERNICUS"
        mock_load_config.return_value = mock_config
        mock_exist.return_value = False
        mock_bbox.main.return_value = "SNWE: -1 1 -78 -76 '"
        mock_cwd.return_value = Path("/tmp/original")

        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "test.toml"
            config_file.touch()

            slc_dir = Path(tmpdir) / "SLC"
            slc_dir.mkdir()

            kml_file = slc_dir / "test.kml"
            kml_file.touch()

            mock_config.download.slc_dir = slc_dir
            mock_config.dem.work_dir = Path(tmpdir)

            # Mock DEM files
            mock_glob.return_value = [
                Path("elevation_S01_N01_W078_W076.dem.wgs84"),
                Path("elevation_S01_N01_W078_W076.dem.wgs84.xml"),
                Path("elevation_S01_N01_W078_W076.dem.wgs84.vrt")
            ]

            with patch('builtins.print'):
                download_dem(config_file)

            call_kwargs = mock_sardem.dem.main.call_args[1]
            assert call_kwargs['data_source'] == "COPERNICUS"

    @patch('insarchitect.commands.download_dem.load_config')
    @patch('insarchitect.commands.download_dem.exist_valid_dem_dir')
    @patch('insarchitect.commands.download_dem.get_boundingbox_from_kml')
    @patch('insarchitect.commands.download_dem.sardem')
    @patch('insarchitect.commands.download_dem.os.chdir')
    @patch('insarchitect.commands.download_dem.Path.cwd')
    def test_keyboard_interrupt(
        self, mock_cwd, mock_chdir, mock_sardem, mock_bbox, mock_exist, mock_load_config, mock_config
    ):
        """Test handling of keyboard interrupt."""
        import typer

        mock_load_config.return_value = mock_config
        mock_exist.return_value = False
        mock_bbox.main.return_value = "SNWE: -1 1 -78 -76 '"
        mock_cwd.return_value = Path("/tmp/original")
        mock_sardem.dem.main.side_effect = KeyboardInterrupt()

        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "test.toml"
            config_file.touch()

            slc_dir = Path(tmpdir) / "SLC"
            slc_dir.mkdir()

            kml_file = slc_dir / "test.kml"
            kml_file.touch()

            mock_config.download.slc_dir = slc_dir
            mock_config.dem.work_dir = Path(tmpdir)

            with patch('builtins.print'):
                with pytest.raises(typer.Exit) as exc_info:
                    download_dem(config_file)
                assert exc_info.value.exit_code == 1

    @patch('insarchitect.commands.download_dem.load_config')
    @patch('insarchitect.commands.download_dem.exist_valid_dem_dir')
    @patch('insarchitect.commands.download_dem.get_boundingbox_from_kml')
    def test_bbox_extraction_error(self, mock_bbox, mock_exist, mock_load_config, mock_config):
        """Test error handling when bbox extraction fails."""
        import typer

        mock_load_config.return_value = mock_config
        mock_exist.return_value = False
        mock_bbox.main.side_effect = Exception("Failed to parse KML")

        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "test.toml"
            config_file.touch()

            slc_dir = Path(tmpdir) / "SLC"
            slc_dir.mkdir()

            kml_file = slc_dir / "test.kml"
            kml_file.touch()

            mock_config.download.slc_dir = slc_dir
            mock_config.dem.work_dir = Path(tmpdir)

            with patch('builtins.print'):
                with pytest.raises(typer.Exit) as exc_info:
                    download_dem(config_file)
                assert exc_info.value.exit_code == 1
