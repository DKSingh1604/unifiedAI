"""
Data validation schemas using Pydantic
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime


class VehicleRecord(BaseModel):
    """
    Pydantic model for validating electric vehicle records
    
    This model ensures data quality by:
    - Validating data types
    - Checking required fields
    - Normalizing string fields
    - Handling missing values appropriately
    """
    model_config = ConfigDict(protected_namespaces=())
    
    vin_1_10: str = Field(..., description="First 10 characters of VIN")
    county: str = Field(..., description="County where vehicle is registered")
    city: str = Field(..., description="City where vehicle is registered")
    state: str = Field(default="WA", description="State code")
    postal_code: Optional[str] = Field(None, description="ZIP/Postal code")
    model_year: int = Field(..., ge=1997, le=2026, description="Model year of the vehicle")
    make: str = Field(..., description="Vehicle manufacturer")
    model: str = Field(..., description="Vehicle model")
    electric_vehicle_type: str = Field(..., description="BEV or PHEV")
    cafv_eligibility: str = Field(..., description="Clean Alternative Fuel Vehicle eligibility")
    electric_range: int = Field(default=0, ge=0, description="Electric range in miles")
    base_msrp: int = Field(default=0, ge=0, description="Manufacturer's suggested retail price")
    legislative_district: Optional[str] = Field(None, description="Legislative district")
    dol_vehicle_id: str = Field(..., description="Department of Licensing vehicle ID")
    vehicle_location: Optional[str] = Field(None, description="Geographic coordinates")
    electric_utility: Optional[str] = Field(None, description="Electric utility provider")
    census_tract_2020: Optional[str] = Field(None, description="2020 Census tract")
    
    @field_validator('make', 'model', 'electric_vehicle_type', 'county', 'city', mode='before')
    @classmethod
    def normalize_strings(cls, v):
        """Normalize string fields to uppercase and strip whitespace"""
        if isinstance(v, str):
            return v.strip().upper()
        return v
    
    @field_validator('electric_vehicle_type', mode='after')
    @classmethod
    def validate_ev_type(cls, v):
        """Ensure electric vehicle type is valid"""
        valid_types = ['BATTERY ELECTRIC VEHICLE (BEV)', 'PLUG-IN HYBRID ELECTRIC VEHICLE (PHEV)', 'BEV', 'PHEV']
        if v not in valid_types:
            # Try to normalize
            if 'BEV' in v.upper():
                return 'BATTERY ELECTRIC VEHICLE (BEV)'
            elif 'PHEV' in v.upper():
                return 'PLUG-IN HYBRID ELECTRIC VEHICLE (PHEV)'
        return v
    
    @field_validator('electric_range', 'base_msrp', mode='before')
    @classmethod
    def handle_numeric_na(cls, v):
        """Handle NA or missing numeric values"""
        if v in ['', 'NA', 'N/A', None]:
            return 0
        try:
            return int(float(v))
        except (ValueError, TypeError):
            return 0


class DataQualityReport(BaseModel):
    """Report on data quality after validation"""
    total_records: int
    valid_records: int
    invalid_records: int
    missing_values: dict
    validation_errors: list
    processed_at: datetime = Field(default_factory=datetime.utcnow)
