"""
Tests for the data pipeline
"""
import pytest
import pandas as pd
from pathlib import Path
from app.pipeline.etl import DataPipeline
from app.schemas.validation import VehicleRecord


class TestDataPipeline:
    """Test the ETL pipeline"""
    
    @pytest.fixture
    def sample_dataframe(self):
        """Create a sample DataFrame for testing"""
        data = {
            'VIN (1-10)': ['5YJSA1E26K', '1G1RD6E44D', '5YJSA1E28L'],
            'County': ['King', 'Snohomish', 'Pierce'],
            'City': ['Seattle', 'Everett', 'Tacoma'],
            'State': ['WA', 'WA', 'WA'],
            'Postal Code': ['98101', '98201', '98401'],
            'Model Year': [2023, 2022, 2024],
            'Make': ['TESLA', 'CHEVROLET', 'TESLA'],
            'Model': ['MODEL S', 'BOLT EV', 'MODEL 3'],
            'Electric Vehicle Type': ['Battery Electric Vehicle (BEV)', 'Battery Electric Vehicle (BEV)', 'Battery Electric Vehicle (BEV)'],
            'Clean Alternative Fuel Vehicle (CAFV) Eligibility': ['Eligible', 'Eligible', 'Eligible'],
            'Electric Range': [405, 259, 358],
            'Base MSRP': [0, 0, 0],
            'Legislative District': ['43', '38', '27'],
            'DOL Vehicle ID': ['12345', '67890', '11111'],
            'Vehicle Location': ['', '', ''],
            'Electric Utility': ['', '', ''],
            '2020 Census Tract': ['', '', '']
        }
        return pd.DataFrame(data)
    
    def test_normalize_column_names(self, sample_dataframe):
        """Test column name normalization"""
        pipeline = DataPipeline()
        df = pipeline.normalize_column_names(sample_dataframe)
        
        assert 'vin_1_10' in df.columns
        assert 'model_year' in df.columns
        assert 'electric_vehicle_type' in df.columns
        assert 'VIN (1-10)' not in df.columns
    
    def test_analyze_missing_values(self, sample_dataframe):
        """Test missing value analysis"""
        # Add some missing values
        df = sample_dataframe.copy()
        df.loc[0, 'Postal Code'] = None
        df.loc[1, 'Electric Range'] = None
        
        pipeline = DataPipeline()
        missing = pipeline.analyze_missing_values(df)
        
        assert 'Postal Code' in missing
        assert 'Electric Range' in missing
        assert missing['Postal Code'] == 1
        assert missing['Electric Range'] == 1
    
    def test_validate_record_success(self):
        """Test successful record validation"""
        pipeline = DataPipeline()
        record = {
            'vin_1_10': '5YJSA1E26K',
            'county': 'KING',
            'city': 'SEATTLE',
            'state': 'WA',
            'postal_code': '98101',
            'model_year': 2023,
            'make': 'TESLA',
            'model': 'MODEL S',
            'electric_vehicle_type': 'BATTERY ELECTRIC VEHICLE (BEV)',
            'cafv_eligibility': 'Eligible',
            'electric_range': 405,
            'base_msrp': 0,
            'legislative_district': '43',
            'dol_vehicle_id': '12345',
            'vehicle_location': '',
            'electric_utility': '',
            'census_tract_2020': ''
        }
        
        is_valid, validated_record, error_msg = pipeline.validate_record(record)
        
        assert is_valid
        assert validated_record is not None
        assert error_msg == ""
    
    def test_validate_record_missing_required(self):
        """Test validation fails for missing required field"""
        pipeline = DataPipeline()
        record = {
            'vin_1_10': '5YJSA1E26K',
            'county': 'KING',
            # Missing required fields
        }
        
        is_valid, validated_record, error_msg = pipeline.validate_record(record)
        
        assert not is_valid
        assert validated_record is None
        assert error_msg != ""
    
    def test_validate_record_invalid_year(self):
        """Test validation fails for invalid year"""
        pipeline = DataPipeline()
        record = {
            'vin_1_10': '5YJSA1E26K',
            'county': 'KING',
            'city': 'SEATTLE',
            'state': 'WA',
            'model_year': 1990,  # Too old
            'make': 'TESLA',
            'model': 'MODEL S',
            'electric_vehicle_type': 'BEV',
            'cafv_eligibility': 'Eligible',
            'dol_vehicle_id': '12345'
        }
        
        is_valid, validated_record, error_msg = pipeline.validate_record(record)
        
        assert not is_valid


class TestVehicleRecordValidation:
    """Test the VehicleRecord Pydantic model"""
    
    def test_normalize_strings(self):
        """Test string normalization"""
        record = VehicleRecord(
            vin_1_10='5yjsa1e26k',
            county='king',
            city='seattle',
            state='WA',
            model_year=2023,
            make='tesla',
            model='model s',
            electric_vehicle_type='battery electric vehicle (bev)',
            cafv_eligibility='Eligible',
            dol_vehicle_id='12345'
        )
        
        assert record.county == 'KING'
        assert record.city == 'SEATTLE'
        assert record.make == 'TESLA'
        assert record.model == 'MODEL S'
    
    def test_handle_numeric_na(self):
        """Test handling of NA values in numeric fields"""
        record = VehicleRecord(
            vin_1_10='5YJSA1E26K',
            county='KING',
            city='SEATTLE',
            state='WA',
            model_year=2023,
            make='TESLA',
            model='MODEL S',
            electric_vehicle_type='BEV',
            cafv_eligibility='Eligible',
            electric_range='NA',  # Should convert to 0
            base_msrp='',  # Should convert to 0
            dol_vehicle_id='12345'
        )
        
        assert record.electric_range == 0
        assert record.base_msrp == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
