"""
API routes for vehicle endpoints
"""
from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional, Literal
import math

from app.database import db_manager
from app.logger import setup_logger
from app.schemas.api_models import (
    SummaryResponse,
    VehicleTypeSummary,
    MakeSummary,
    EligibilitySummary,
    CountyVehiclesResponse,
    Vehicle,
    MakeModelsResponse,
    ModelStatistics,
    AnalyzeRequest,
    AnalyzeResponse,
    GroupStatistics,
    TrendsResponse,
    YearTrend,
    ErrorResponse
)

logger = setup_logger(__name__)
router = APIRouter()


@router.get(
    "/vehicles/summary",
    response_model=SummaryResponse,
    summary="Get dataset summary",
    description="Returns overall statistics about the vehicle dataset"
)
async def get_summary():
    """
    Get summary statistics of the entire dataset
    
    Returns:
    - Total number of vehicles
    - Vehicle counts by type (BEV vs PHEV)
    - Top 10 makes by count
    - Average electric range
    - CAFV eligibility counts
    """
    try:
        collection = db_manager.get_collection("vehicles")
        
        # Total vehicles
        total_vehicles = collection.count_documents({})
        
        # Vehicles by type
        type_pipeline = [
            {"$group": {
                "_id": "$electric_vehicle_type",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}
        ]
        vehicles_by_type = [
            VehicleTypeSummary(type=doc["_id"], count=doc["count"])
            for doc in collection.aggregate(type_pipeline)
        ]
        
        # Top 10 makes
        make_pipeline = [
            {"$group": {
                "_id": "$make",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        top_10_makes = [
            MakeSummary(make=doc["_id"], count=doc["count"])
            for doc in collection.aggregate(make_pipeline)
        ]
        
        # Average electric range
        range_pipeline = [
            {"$match": {"electric_range": {"$gt": 0}}},
            {"$group": {
                "_id": None,
                "avg_range": {"$avg": "$electric_range"}
            }}
        ]
        range_result = list(collection.aggregate(range_pipeline))
        average_electric_range = round(range_result[0]["avg_range"], 2) if range_result else 0.0
        
        # Eligibility summary
        eligibility_pipeline = [
            {"$group": {
                "_id": "$cafv_eligibility",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}
        ]
        eligibility_summary = [
            EligibilitySummary(eligibility=doc["_id"], count=doc["count"])
            for doc in collection.aggregate(eligibility_pipeline)
        ]
        
        return SummaryResponse(
            total_vehicles=total_vehicles,
            vehicles_by_type=vehicles_by_type,
            top_10_makes=top_10_makes,
            average_electric_range=average_electric_range,
            eligibility_summary=eligibility_summary
        )
        
    except Exception as e:
        logger.error(f"Error in get_summary: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/vehicles/county/{county_name}",
    response_model=CountyVehiclesResponse,
    summary="Get vehicles by county",
    description="Returns all vehicles in a specific county with pagination and filtering"
)
async def get_vehicles_by_county(
    county_name: str = Path(..., description="County name"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    model_year: Optional[int] = Query(None, description="Filter by model year"),
    sort_by: Literal["model_year", "make", "model"] = Query("model_year", description="Sort field"),
    sort_order: Literal["asc", "desc"] = Query("desc", description="Sort order")
):
    """
    Get all vehicles in a specific county
    
    Query Parameters:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    - model_year: Optional filter by model year
    - sort_by: Field to sort by (model_year, make, or model)
    - sort_order: Sort order (asc or desc)
    """
    try:
        collection = db_manager.get_collection("vehicles")
        
        # Build query
        query = {"county": county_name.upper()}
        if model_year:
            query["model_year"] = model_year
        
        # Count total matching documents
        total_count = collection.count_documents(query)
        
        if total_count == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No vehicles found in county: {county_name}"
            )
        
        # Calculate pagination
        total_pages = math.ceil(total_count / page_size)
        skip = (page - 1) * page_size
        
        # Sort direction
        sort_direction = -1 if sort_order == "desc" else 1
        
        # Fetch paginated results
        cursor = collection.find(query).sort(sort_by, sort_direction).skip(skip).limit(page_size)
        
        vehicles = []
        for doc in cursor:
            doc.pop('_id', None)  # Remove MongoDB _id
            vehicles.append(Vehicle(**doc))
        
        return CountyVehiclesResponse(
            county=county_name.upper(),
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            vehicles=vehicles
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_vehicles_by_county: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/vehicles/make/{make}/models",
    response_model=MakeModelsResponse,
    summary="Get models by make",
    description="Returns all models for a specific manufacturer with statistics"
)
async def get_models_by_make(
    make: str = Path(..., description="Vehicle manufacturer/make")
):
    """
    Get all models for a specific manufacturer with statistics
    
    Returns:
    - Count per model
    - Average electric range per model
    - Most popular model
    """
    try:
        collection = db_manager.get_collection("vehicles")
        
        # Pipeline to get model statistics
        pipeline = [
            {"$match": {"make": make.upper()}},
            {"$group": {
                "_id": "$model",
                "count": {"$sum": 1},
                "avg_range": {"$avg": "$electric_range"}
            }},
            {"$sort": {"count": -1}}
        ]
        
        results = list(collection.aggregate(pipeline))
        
        if not results:
            raise HTTPException(
                status_code=404,
                detail=f"No vehicles found for make: {make}"
            )
        
        # Build model statistics
        models = [
            ModelStatistics(
                model=doc["_id"],
                count=doc["count"],
                average_electric_range=round(doc["avg_range"], 2)
            )
            for doc in results
        ]
        
        # Most popular model
        most_popular = results[0]
        
        return MakeModelsResponse(
            make=make.upper(),
            total_models=len(models),
            most_popular_model=most_popular["_id"],
            most_popular_count=most_popular["count"],
            models=models
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_models_by_make: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post(
    "/vehicles/analyze",
    response_model=AnalyzeResponse,
    summary="Analyze vehicles with complex filters",
    description="Accepts complex queries and returns aggregated results"
)
async def analyze_vehicles(request: AnalyzeRequest):
    """
    Analyze vehicles with complex filtering and grouping
    
    Request Body:
    - filters: Object with optional filters (makes, model_years, min_electric_range, etc.)
    - group_by: Field to group by (county, make, model_year, or vehicle_type)
    
    Returns:
    - Grouped counts
    - Average electric range per group
    - Most common vehicle in each group
    """
    try:
        collection = db_manager.get_collection("vehicles")
        
        # Build match stage
        match_stage = {}
        
        if request.filters.makes:
            match_stage["make"] = {"$in": [m.upper() for m in request.filters.makes]}
        
        if request.filters.model_years:
            year_filter = {}
            if "start" in request.filters.model_years:
                year_filter["$gte"] = request.filters.model_years["start"]
            if "end" in request.filters.model_years:
                year_filter["$lte"] = request.filters.model_years["end"]
            if year_filter:
                match_stage["model_year"] = year_filter
        
        if request.filters.min_electric_range:
            match_stage["electric_range"] = {"$gte": request.filters.min_electric_range}
        
        if request.filters.counties:
            match_stage["county"] = {"$in": [c.upper() for c in request.filters.counties]}
        
        if request.filters.vehicle_types:
            match_stage["electric_vehicle_type"] = {"$in": [vt.upper() for vt in request.filters.vehicle_types]}
        
        # Build aggregation pipeline
        pipeline = []
        
        if match_stage:
            pipeline.append({"$match": match_stage})
        
        # Group stage
        group_field = f"${request.group_by}"
        pipeline.extend([
            {"$group": {
                "_id": group_field,
                "count": {"$sum": 1},
                "avg_range": {"$avg": "$electric_range"},
                "vehicles": {"$push": {"make": "$make", "model": "$model"}}
            }},
            {"$sort": {"count": -1}}
        ])
        
        results = list(collection.aggregate(pipeline))
        
        if not results:
            raise HTTPException(
                status_code=404,
                detail="No vehicles match the specified filters"
            )
        
        # Calculate most common vehicle per group
        groups = []
        total_matching = 0
        
        for doc in results:
            total_matching += doc["count"]
            
            # Find most common vehicle
            vehicle_counts = {}
            for v in doc["vehicles"]:
                key = f"{v['make']} {v['model']}"
                vehicle_counts[key] = vehicle_counts.get(key, 0) + 1
            
            most_common = max(vehicle_counts.items(), key=lambda x: x[1])[0] if vehicle_counts else None
            
            groups.append(GroupStatistics(
                group_value=str(doc["_id"]),
                count=doc["count"],
                average_electric_range=round(doc["avg_range"], 2),
                most_common_vehicle=most_common
            ))
        
        return AnalyzeResponse(
            group_by=request.group_by,
            total_matching_vehicles=total_matching,
            groups=groups
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in analyze_vehicles: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/vehicles/trends",
    response_model=TrendsResponse,
    summary="Get vehicle trends over time",
    description="Returns trends by model year including counts, range, and BEV/PHEV ratio"
)
async def get_trends():
    """
    Get trends over time
    
    Returns:
    - Vehicle count by model year
    - Average electric range by model year
    - BEV vs PHEV ratio by year
    - Overall growth and improvement rates
    """
    try:
        collection = db_manager.get_collection("vehicles")
        
        # Aggregation pipeline for trends
        pipeline = [
            {"$group": {
                "_id": "$model_year",
                "vehicle_count": {"$sum": 1},
                "avg_range": {"$avg": "$electric_range"},
                "bev_count": {
                    "$sum": {
                        "$cond": [
                            {"$regexMatch": {"input": "$electric_vehicle_type", "regex": "BEV"}},
                            1,
                            0
                        ]
                    }
                },
                "phev_count": {
                    "$sum": {
                        "$cond": [
                            {"$regexMatch": {"input": "$electric_vehicle_type", "regex": "PHEV"}},
                            1,
                            0
                        ]
                    }
                }
            }},
            {"$sort": {"_id": 1}}  # Sort by year ascending
        ]
        
        results = list(collection.aggregate(pipeline))
        
        if not results:
            raise HTTPException(status_code=404, detail="No trend data available")
        
        # Build trend data
        trends = []
        for doc in results:
            total = doc["bev_count"] + doc["phev_count"]
            bev_pct = (doc["bev_count"] / total * 100) if total > 0 else 0
            phev_pct = (doc["phev_count"] / total * 100) if total > 0 else 0
            
            trends.append(YearTrend(
                model_year=doc["_id"],
                vehicle_count=doc["vehicle_count"],
                average_electric_range=round(doc["avg_range"], 2),
                bev_count=doc["bev_count"],
                phev_count=doc["phev_count"],
                bev_percentage=round(bev_pct, 2),
                phev_percentage=round(phev_pct, 2)
            ))
        
        # Calculate growth rate (comparing first and last year)
        if len(trends) >= 2:
            first_year_count = trends[0].vehicle_count
            last_year_count = trends[-1].vehicle_count
            years_diff = trends[-1].model_year - trends[0].model_year
            
            if years_diff > 0 and first_year_count > 0:
                overall_growth_rate = ((last_year_count - first_year_count) / first_year_count / years_diff) * 100
            else:
                overall_growth_rate = None
            
            # Range improvement rate
            first_year_range = trends[0].average_electric_range
            last_year_range = trends[-1].average_electric_range
            
            if first_year_range > 0:
                range_improvement_rate = ((last_year_range - first_year_range) / first_year_range / years_diff) * 100
            else:
                range_improvement_rate = None
        else:
            overall_growth_rate = None
            range_improvement_rate = None
        
        return TrendsResponse(
            trends=trends,
            overall_growth_rate=round(overall_growth_rate, 2) if overall_growth_rate else None,
            range_improvement_rate=round(range_improvement_rate, 2) if range_improvement_rate else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_trends: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
