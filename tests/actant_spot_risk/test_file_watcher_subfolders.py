"""Test the file watcher with daily subfolder structure."""

import os
import shutil
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest
import pandas as pd

from lib.trading.actant.spot_risk.file_watcher import (
    SpotRiskFileHandler,
    SpotRiskWatcher,
    get_spot_risk_date_folder,
    ensure_date_folder
)


class TestDateFolderUtils:
    """Test date folder utility functions."""
    
    def test_get_spot_risk_date_folder_afternoon(self):
        """Test date folder calculation after 3pm EST."""
        # Create a timestamp for 4pm EST
        from datetime import datetime
        import pytz
        
        est = pytz.timezone('US/Eastern')
        test_time = est.localize(datetime(2024, 1, 15, 16, 0, 0))  # 4pm EST
        
        date_folder = get_spot_risk_date_folder(test_time)
        assert date_folder == "2024-01-15"
    
    def test_get_spot_risk_date_folder_morning(self):
        """Test date folder calculation before 3pm EST."""
        from datetime import datetime
        import pytz
        
        est = pytz.timezone('US/Eastern')
        test_time = est.localize(datetime(2024, 1, 15, 10, 0, 0))  # 10am EST
        
        date_folder = get_spot_risk_date_folder(test_time)
        assert date_folder == "2024-01-14"  # Previous day
    
    def test_ensure_date_folder(self):
        """Test date folder creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            date_folder = "2024-01-15"
            
            result_path = ensure_date_folder(base_path, date_folder)
            
            assert result_path.exists()
            assert result_path.is_dir()
            assert result_path.name == date_folder


class TestFileWatcherSubfolders:
    """Test file watcher with subfolder support."""
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary input and output directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_dir = Path(temp_dir) / "input"
            output_dir = Path(temp_dir) / "output"
            input_dir.mkdir()
            output_dir.mkdir()
            
            yield input_dir, output_dir
    
    @pytest.fixture
    def sample_csv_content(self):
        """Create sample CSV content."""
        data = {
            'Strike': [100, 105, 110],
            'Expiry': ['2024-03-15', '2024-03-15', '2024-03-15'],
            'CP': ['C', 'C', 'P'],
            'ImpVol': [0.15, 0.16, 0.17],
            'TV': [5.0, 3.0, 2.0],
            'Price': [105.5, 105.5, 105.5],
            'Rate': [0.05, 0.05, 0.05]
        }
        return pd.DataFrame(data)
    
    def test_file_in_date_subfolder(self, temp_dirs, sample_csv_content):
        """Test processing a file in a date subfolder."""
        input_dir, output_dir = temp_dirs
        
        # Create date subfolder
        date_folder = "2024-01-15"
        input_date_dir = input_dir / date_folder
        input_date_dir.mkdir()
        
        # Create test file
        test_file = input_date_dir / "bav_analysis_20240115_120000.csv"
        sample_csv_content.to_csv(test_file, index=False)
        
        # Create handler
        handler = SpotRiskFileHandler(str(input_dir), str(output_dir))
        
        # Process file
        handler._process_csv_file(test_file)
        
        # Check output structure
        expected_output_dir = output_dir / date_folder
        assert expected_output_dir.exists()
        
        output_files = list(expected_output_dir.glob("*.csv"))
        assert len(output_files) == 1
        assert output_files[0].name == "bav_analysis_processed_20240115_120000.csv"
        
        # Verify tracking
        assert f"{date_folder}/bav_analysis_20240115_120000.csv" in handler.processed_files
    
    def test_file_in_root_creates_date_folder(self, temp_dirs, sample_csv_content):
        """Test that files in root create appropriate date folder."""
        input_dir, output_dir = temp_dirs
        
        # Create test file in root
        test_file = input_dir / "bav_analysis_20240115_140000.csv"
        sample_csv_content.to_csv(test_file, index=False)
        
        # Create handler
        handler = SpotRiskFileHandler(str(input_dir), str(output_dir))
        
        # Process file
        handler._process_csv_file(test_file)
        
        # Check that a date folder was created
        output_subdirs = [d for d in output_dir.iterdir() if d.is_dir()]
        assert len(output_subdirs) == 1
        
        # The actual date folder depends on current time, just verify structure
        date_folder = output_subdirs[0]
        output_files = list(date_folder.glob("*.csv"))
        assert len(output_files) == 1
        assert output_files[0].name == "bav_analysis_processed_20240115_140000.csv"
    
    def test_existing_files_discovery(self, temp_dirs, sample_csv_content):
        """Test discovery of existing processed files in subfolders."""
        input_dir, output_dir = temp_dirs
        
        # Create some already processed files in different date folders
        date1 = "2024-01-14"
        date2 = "2024-01-15"
        
        # Create output structure
        (output_dir / date1).mkdir()
        (output_dir / date2).mkdir()
        
        # Create processed files
        processed1 = output_dir / date1 / "bav_analysis_processed_20240114_100000.csv"
        processed2 = output_dir / date2 / "bav_analysis_processed_20240115_100000.csv"
        sample_csv_content.to_csv(processed1, index=False)
        sample_csv_content.to_csv(processed2, index=False)
        
        # Create matching input files (should be skipped)
        (input_dir / date1).mkdir()
        (input_dir / date2).mkdir()
        input1 = input_dir / date1 / "bav_analysis_20240114_100000.csv"
        input2 = input_dir / date2 / "bav_analysis_20240115_100000.csv"
        sample_csv_content.to_csv(input1, index=False)
        sample_csv_content.to_csv(input2, index=False)
        
        # Create unprocessed file
        input3 = input_dir / date2 / "bav_analysis_20240115_150000.csv"
        sample_csv_content.to_csv(input3, index=False)
        
        # Create watcher and process existing
        watcher = SpotRiskWatcher(str(input_dir), str(output_dir))
        watcher._process_existing_files()
        
        # Check processed files tracking
        assert f"{date1}/bav_analysis_20240114_100000.csv" in watcher.handler.processed_files
        assert f"{date2}/bav_analysis_20240115_100000.csv" in watcher.handler.processed_files
        
        # Check that new file was processed
        expected_output = output_dir / date2 / "bav_analysis_processed_20240115_150000.csv"
        assert expected_output.exists() 