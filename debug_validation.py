import pandas as pd
from app.pipeline.etl import DataPipeline
from app.schemas.validation import VehicleRecord

# Load full CSV
df = pd.read_csv('data/raw/Electric_Vehicle_Population_Data.csv', nrows=5)

# Use the actual transform method
pipeline = DataPipeline()
valid_records, quality_report = pipeline.transform(df)

print(f'Total: {quality_report.total_records}')
print(f'Valid: {quality_report.valid_records}')
print(f'Invalid: {quality_report.invalid_records}')

if quality_report.valid_records > 0:
    print('\n✅ Validation working!')
    print(f'First valid record VIN: {valid_records[0]["vin_1_10"]}')
else:
    print('\n❌ All records invalid')
    if quality_report.validation_errors:
        print(f'First error: {quality_report.validation_errors[0]}')
