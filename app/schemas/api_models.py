"""
API Request and Response Models using Pydantic
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Literal
from datetime import datetime


# ============================================================================
# Summary Endpoint Models
# ============================================================================

class VehicleTypeSummary(BaseModel):
    """Summary by vehicle type"""
    type: str
    count: int


class MakeSummary(BaseModel):
    """Summary by make"""
    make: str
    count: int


class EligibilitySummary(BaseModel):
    """Summary by CAFV eligibility"""
    eligibility: str
    count: int


class SummaryResponse(BaseModel):
    """Response for /api/v1/vehicles/summary"""
    total_vehicles: int
    vehicles_by_type: List[VehicleTypeSummary]
    top_10_makes: List[MakeSummary]
    average_electric_range: float
    eligibility_summary: List[EligibilitySummary]


# ============================================================================
# Vehicle Model
# ============================================================================

class Vehicle(BaseModel):
    """Individual vehicle record"""
    model_config = ConfigDict(protected_namespaces=())
    
    vin_1_10: str
    county: str
    city: str
    state: str
    postal_code: Optional[str] = None
    model_year: int
    make: str
    model: str
    electric_vehicle_type: str
    cafv_eligibility: str
    electric_range: int
    base_msrp: int
    legislative_district: Optional[str] = None
    dol_vehicle_id: str
    vehicle_location: Optional[str] = None
    electric_utility: Optional[str] = None
    census_tract_2020: Optional[str] = None


# ============================================================================
# County Endpoint Models
# ============================================================================

class CountyVehiclesResponse(BaseModel):
    """Response for /api/v1/vehicles/county/{county_name}"""
    county: str
    total_count: int
    page: int
    page_size: int
    total_pages: int
    vehicles: List[Vehicle]


# ============================================================================
# Make Models Endpoint
# ============================================================================

class ModelStatistics(BaseModel):
    """Statistics for a specific model"""
    model: str
    count: int
    average_electric_range: float


class MakeModelsResponse(BaseModel):
    """Response for /api/v1/vehicles/make/{make}/models"""
    make: str
    total_models: int
    most_popular_model: str
    most_popular_count: int
    models: List[ModelStatistics]


# ============================================================================
# Analyze Endpoint Models
# ============================================================================

class AnalyzeFilters(BaseModel):
    """Filters for analyze endpoint"""
    model_config = ConfigDict(protected_namespaces=())
    
    makes: Optional[List[str]] = Field(None, description="List of makes to filter")
    model_years: Optional[Dict[str, int]] = Field(
        None, 
        description="Year range with 'start' and 'end' keys"
    )
    min_electric_range: Optional[int] = Field(None, ge=0, description="Minimum electric range")
    counties: Optional[List[str]] = Field(None, description="List of counties to filter")
    vehicle_types: Optional[List[str]] = Field(None, description="List of vehicle types")


class AnalyzeRequest(BaseModel):
    """Request body for /api/v1/vehicles/analyze"""
    filters: AnalyzeFilters
    group_by: Literal["county", "make", "model_year", "vehicle_type"] = Field(
        ...,
        description="Field to group results by"
    )


class GroupStatistics(BaseModel):
    """Statistics for a group"""
    group_value: str
    count: int
    average_electric_range: float
    most_common_vehicle: Optional[str] = None


class AnalyzeResponse(BaseModel):
    """Response for /api/v1/vehicles/analyze"""
    group_by: str
    total_matching_vehicles: int
    groups: List[GroupStatistics]


# ============================================================================
# Trends Endpoint Models
# ============================================================================

class YearTrend(BaseModel):
    """Trend data for a specific year"""
    model_config = ConfigDict(protected_namespaces=())
    
    model_year: int
    vehicle_count: int
    average_electric_range: float
    bev_count: int
    phev_count: int
    bev_percentage: float
    phev_percentage: float


class TrendsResponse(BaseModel):
    """Response for /api/v1/vehicles/trends"""
    trends: List[YearTrend]
    overall_growth_rate: Optional[float] = None
    range_improvement_rate: Optional[float] = None


# ============================================================================
# Error Response
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
