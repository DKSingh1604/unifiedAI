"""
ETL Pipeline for Electric Vehicle Data

This module handles:
1. Extract: Reading CSV from local file or S3
2. Transform: Data validation and cleaning
3. Load: Inserting data into MongoDB with proper schema
"""
import pandas as pd
import boto3
from io import StringIO
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from pydantic import ValidationError

from app.config import settings
from app.logger import setup_logger
from app.database import db_manager
from app.schemas.validation import VehicleRecord, DataQualityReport

logger = setup_logger(__name__)


class DataPipeline:
    """
    Handles the complete ETL pipeline for electric vehicle data
    """
    
    def __init__(self):
        self.validation_errors = []
        self.missing_values_summary = {}
        
    def extract_from_local(self, file_path: str) -> pd.DataFrame:
        """
        Extract data from local CSV file
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            DataFrame containing the CSV data
            
        Raises:
            FileNotFoundError: If file doesn't exist
            pd.errors.EmptyDataError: If file is empty
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"CSV file not found: {file_path}")
                
            logger.info(f"Reading CSV from local path: {file_path}")
            df = pd.read_csv(file_path, low_memory=False)
            logger.info(f"Successfully loaded {len(df)} records from CSV")
            return df
            
        except Exception as e:
            logger.error(f"Failed to read CSV from local path: {e}")
            raise
    
    def extract_from_s3(self, bucket: str, key: str) -> pd.DataFrame:
        """
        Extract data from S3 bucket
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            
        Returns:
            DataFrame containing the CSV data
            
        Raises:
            boto3.exceptions.S3UploadFailedError: If S3 access fails
        """
        try:
            logger.info(f"Reading CSV from S3: s3://{bucket}/{key}")
            
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region
            )
            
            response = s3_client.get_object(Bucket=bucket, Key=key)
            csv_content = response['Body'].read().decode('utf-8')
            
            df = pd.read_csv(StringIO(csv_content), low_memory=False)
            logger.info(f"Successfully loaded {len(df)} records from S3")
            return df
            
        except Exception as e:
            logger.error(f"Failed to read CSV from S3: {e}")
            raise
    
    def extract(self) -> pd.DataFrame:
        """
        Extract data based on configuration
        
        Returns:
            DataFrame containing the extracted data
        """
        if settings.csv_source == "local":
            return self.extract_from_local(settings.csv_local_path)
        elif settings.csv_source == "s3":
            return self.extract_from_s3(settings.csv_s3_bucket, settings.csv_s3_key)
        else:
            raise ValueError(f"Invalid CSV source: {settings.csv_source}")
    
    def analyze_missing_values(self, df: pd.DataFrame) -> Dict[str, int]:
        """
        Analyze missing values in the dataset
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dictionary with column names and count of missing values
        """
        missing = df.isnull().sum()
        missing_dict = {col: int(count) for col, count in missing.items() if count > 0}
        
        if missing_dict:
            logger.warning(f"Missing values found in {len(missing_dict)} columns")
            for col, count in missing_dict.items():
                logger.warning(f"  {col}: {count} missing values")
        
        return missing_dict
    
    def normalize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize column names to snake_case
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with normalized column names
        """
        column_mapping = {
            'VIN (1-10)': 'vin_1_10',
            'County': 'county',
            'City': 'city',
            'State': 'state',
            'Postal Code': 'postal_code',
            'Model Year': 'model_year',
            'Make': 'make',
            'Model': 'model',
            'Electric Vehicle Type': 'electric_vehicle_type',
            'Clean Alternative Fuel Vehicle (CAFV) Eligibility': 'cafv_eligibility',
            'Electric Range': 'electric_range',
            'Base MSRP': 'base_msrp',
            'Legislative District': 'legislative_district',
            'DOL Vehicle ID': 'dol_vehicle_id',
            'Vehicle Location': 'vehicle_location',
            'Electric Utility': 'electric_utility',
            '2020 Census Tract': 'census_tract_2020'
        }
        
        df = df.rename(columns=column_mapping)
        logger.info("Normalized column names to snake_case")
        return df
    
    def validate_record(self, record: dict) -> Tuple[bool, Optional[VehicleRecord], str]:
        """
        Validate a single record using Pydantic
        
        Args:
            record: Dictionary containing record data
            
        Returns:
            Tuple of (is_valid, validated_record, error_message)
        """
        try:
            validated = VehicleRecord(**record)
            return True, validated, ""
        except ValidationError as e:
            error_msg = str(e)
            return False, None, error_msg
    
    def transform(self, df: pd.DataFrame) -> Tuple[List[Dict], DataQualityReport]:
        """
        Transform and validate the data
        
        Args:
            df: Input DataFrame
            
        Returns:
            Tuple of (validated_records, quality_report)
        """
        logger.info("Starting data transformation and validation")
        
        # Normalize column names
        df = self.normalize_column_names(df)
        
        # Analyze missing values before transformation
        missing_values = self.analyze_missing_values(df)
        self.missing_values_summary = missing_values
        
        # Fill NaN values appropriately
        df = df.fillna({
            'postal_code': '',
            'legislative_district': '',
            'vehicle_location': '',
            'electric_utility': '',
            'census_tract_2020': '',
            'electric_range': 0,
            'base_msrp': 0
        })
        
        # Convert numeric fields that should be strings
        string_fields = ['postal_code', 'legislative_district', 'dol_vehicle_id', 'census_tract_2020']
        for field in string_fields:
            if field in df.columns:
                df[field] = df[field].astype(str).replace('nan', '').replace('', None)
        
        # Convert to list of dictionaries
        records = df.to_dict('records')
        total_records = len(records)
        
        logger.info(f"Validating {total_records} records...")
        
        valid_records = []
        validation_errors = []
        
        for idx, record in enumerate(records):
            is_valid, validated_record, error_msg = self.validate_record(record)
            
            if is_valid:
                # Convert Pydantic model to dict for MongoDB
                valid_records.append(validated_record.model_dump())
            else:
                validation_errors.append({
                    'record_index': idx,
                    'vin': record.get('vin_1_10', 'UNKNOWN'),
                    'error': error_msg
                })
                self.validation_errors.append(error_msg)
            
            # Log progress every 50k records
            if (idx + 1) % 50000 == 0:
                logger.info(f"Validated {idx + 1}/{total_records} records")
        
        # Create quality report
        quality_report = DataQualityReport(
            total_records=total_records,
            valid_records=len(valid_records),
            invalid_records=len(validation_errors),
            missing_values=missing_values,
            validation_errors=validation_errors[:100]  # Keep first 100 errors
        )
        
        logger.info(f"Validation complete: {len(valid_records)} valid, {len(validation_errors)} invalid")
        
        return valid_records, quality_report
    
    def load(self, records: List[Dict], batch_size: int = 10000):
        """
        Load validated records into MongoDB
        
        Args:
            records: List of validated records
            batch_size: Number of records to insert per batch
        """
        try:
            logger.info(f"Loading {len(records)} records into MongoDB")
            
            collection = db_manager.get_collection("vehicles")
            
            # Insert in batches for better performance
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                collection.insert_many(batch, ordered=False)
                logger.info(f"Inserted batch {i//batch_size + 1}: {len(batch)} records")
            
            logger.info(f"Successfully loaded {len(records)} records")
            
            # Create indexes after loading data
            logger.info("Creating indexes...")
            db_manager.create_indexes()
            
        except Exception as e:
            logger.error(f"Failed to load data into MongoDB: {e}")
            raise
    
    def run_pipeline(self, drop_existing: bool = False) -> DataQualityReport:
        """
        Run the complete ETL pipeline
        
        Args:
            drop_existing: Whether to drop existing data before loading
            
        Returns:
            Data quality report
        """
        try:
            logger.info("=" * 80)
            logger.info("Starting ETL Pipeline")
            logger.info("=" * 80)
            
            # Connect to database
            db_manager.connect()
            
            # Drop existing collection if requested
            if drop_existing:
                logger.info("Dropping existing vehicles collection")
                db_manager.drop_collection("vehicles")
            
            # Extract
            logger.info("Phase 1: Extract")
            df = self.extract()
            
            # Transform
            logger.info("Phase 2: Transform")
            valid_records, quality_report = self.transform(df)
            
            # Load
            logger.info("Phase 3: Load")
            self.load(valid_records)
            
            logger.info("=" * 80)
            logger.info("ETL Pipeline Complete")
            logger.info(f"Total Records: {quality_report.total_records}")
            logger.info(f"Valid Records: {quality_report.valid_records}")
            logger.info(f"Invalid Records: {quality_report.invalid_records}")
            logger.info("=" * 80)
            
            return quality_report
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise
        finally:
            db_manager.disconnect()


def run_etl_pipeline(drop_existing: bool = False):
    """
    Convenience function to run the ETL pipeline
    
    Args:
        drop_existing: Whether to drop existing data
        
    Returns:
        Data quality report
    """
    pipeline = DataPipeline()
    return pipeline.run_pipeline(drop_existing=drop_existing)


if __name__ == "__main__":
    # Run the pipeline when executed directly
    report = run_etl_pipeline(drop_existing=True)
    print("\n" + "=" * 80)
    print("DATA QUALITY REPORT")
    print("=" * 80)
    print(f"Total Records: {report.total_records}")
    print(f"Valid Records: {report.valid_records}")
    print(f"Invalid Records: {report.invalid_records}")
    print(f"\nProcessed at: {report.processed_at}")
