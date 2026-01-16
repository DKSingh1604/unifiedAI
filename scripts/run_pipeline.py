#!/usr/bin/env python3
"""
Script to run the ETL pipeline
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.pipeline.etl import run_etl_pipeline
from app.logger import setup_logger

logger = setup_logger(__name__)


def main():
    """Run the ETL pipeline"""
    print("=" * 80)
    print("Electric Vehicle Data ETL Pipeline")
    print("=" * 80)
    print()
    
    # Prompt user for drop existing
    drop_existing = input("Drop existing data? (y/N): ").lower() == 'y'
    
    try:
        report = run_etl_pipeline(drop_existing=drop_existing)
        
        print("\n" + "=" * 80)
        print("ETL PIPELINE COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print(f"\nTotal Records Processed: {report.total_records}")
        print(f"Valid Records Loaded: {report.valid_records}")
        print(f"Invalid Records: {report.invalid_records}")
        
        if report.invalid_records > 0:
            print(f"\nFirst few validation errors:")
            for error in report.validation_errors[:5]:
                print(f"  - Record {error['record_index']}: {error['error'][:100]}...")
        
        print(f"\nProcessed at: {report.processed_at}")
        print("=" * 80)
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        print(f"\nERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
