"""
Integration tests for the FastAPI application
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import db_manager

client = TestClient(app)


class TestHealthEndpoints:
    """Test health and root endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint returns API information"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code in [200, 503]  # 503 if DB not available
        data = response.json()
        assert "status" in data
        assert "database" in data


class TestSummaryEndpoint:
    """Test /api/v1/vehicles/summary endpoint"""
    
    def test_get_summary_success(self):
        """Test successful summary retrieval"""
        response = client.get("/api/v1/vehicles/summary")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_vehicles" in data
        assert "vehicles_by_type" in data
        assert "top_10_makes" in data
        assert "average_electric_range" in data
        assert "eligibility_summary" in data
        
        # Validate structure
        assert isinstance(data["total_vehicles"], int)
        assert isinstance(data["vehicles_by_type"], list)
        assert isinstance(data["top_10_makes"], list)
        assert isinstance(data["average_electric_range"], float)
        
        # Check top 10 makes has at most 10 entries
        assert len(data["top_10_makes"]) <= 10
    
    def test_summary_vehicle_types(self):
        """Test that vehicle types are returned"""
        response = client.get("/api/v1/vehicles/summary")
        data = response.json()
        
        vehicle_types = [vt["type"] for vt in data["vehicles_by_type"]]
        # Should have BEV and/or PHEV
        assert len(vehicle_types) > 0


class TestCountyEndpoint:
    """Test /api/v1/vehicles/county/{county_name} endpoint"""
    
    def test_get_county_vehicles_success(self):
        """Test successful county query"""
        # Use KING county (Seattle area - likely to have vehicles)
        response = client.get("/api/v1/vehicles/county/KING")
        assert response.status_code == 200
        
        data = response.json()
        assert data["county"] == "KING"
        assert "total_count" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
        assert "vehicles" in data
        
        # Validate pagination
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert len(data["vehicles"]) <= 20
    
    def test_county_pagination(self):
        """Test pagination works"""
        response = client.get("/api/v1/vehicles/county/KING?page=1&page_size=10")
        assert response.status_code == 200
        
        data = response.json()
        assert data["page_size"] == 10
        assert len(data["vehicles"]) <= 10
    
    def test_county_not_found(self):
        """Test non-existent county returns 404"""
        response = client.get("/api/v1/vehicles/county/NONEXISTENT")
        assert response.status_code in [404, 200]  # 200 if empty, 404 preferred
    
    def test_county_filter_by_year(self):
        """Test filtering by model year"""
        response = client.get("/api/v1/vehicles/county/KING?model_year=2023")
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            # All vehicles should be from 2023
            for vehicle in data["vehicles"]:
                assert vehicle["model_year"] == 2023
    
    def test_county_sorting(self):
        """Test sorting functionality"""
        response = client.get("/api/v1/vehicles/county/KING?sort_by=make&sort_order=asc")
        assert response.status_code == 200
        
        data = response.json()
        if len(data["vehicles"]) > 1:
            makes = [v["make"] for v in data["vehicles"]]
            # Check if sorted ascending
            assert makes == sorted(makes)


class TestMakeModelsEndpoint:
    """Test /api/v1/vehicles/make/{make}/models endpoint"""
    
    def test_get_make_models_success(self):
        """Test successful make models query"""
        # TESLA is a popular make
        response = client.get("/api/v1/vehicles/make/TESLA/models")
        assert response.status_code == 200
        
        data = response.json()
        assert data["make"] == "TESLA"
        assert "total_models" in data
        assert "most_popular_model" in data
        assert "most_popular_count" in data
        assert "models" in data
        
        # Validate model statistics
        assert len(data["models"]) > 0
        for model in data["models"]:
            assert "model" in model
            assert "count" in model
            assert "average_electric_range" in model
    
    def test_make_not_found(self):
        """Test non-existent make returns 404"""
        response = client.get("/api/v1/vehicles/make/NONEXISTENTMAKE/models")
        assert response.status_code == 404
    
    def test_most_popular_model_is_first(self):
        """Test that most popular model matches first in list"""
        response = client.get("/api/v1/vehicles/make/TESLA/models")
        
        if response.status_code == 200:
            data = response.json()
            assert data["most_popular_model"] == data["models"][0]["model"]
            assert data["most_popular_count"] == data["models"][0]["count"]


class TestAnalyzeEndpoint:
    """Test /api/v1/vehicles/analyze endpoint"""
    
    def test_analyze_basic(self):
        """Test basic analyze query"""
        request_body = {
            "filters": {},
            "group_by": "make"
        }
        response = client.post("/api/v1/vehicles/analyze", json=request_body)
        assert response.status_code == 200
        
        data = response.json()
        assert data["group_by"] == "make"
        assert "total_matching_vehicles" in data
        assert "groups" in data
        assert len(data["groups"]) > 0
    
    def test_analyze_with_make_filter(self):
        """Test analyze with make filter"""
        request_body = {
            "filters": {
                "makes": ["TESLA", "CHEVROLET"]
            },
            "group_by": "county"
        }
        response = client.post("/api/v1/vehicles/analyze", json=request_body)
        assert response.status_code == 200
        
        data = response.json()
        assert data["group_by"] == "county"
    
    def test_analyze_with_year_range(self):
        """Test analyze with year range filter"""
        request_body = {
            "filters": {
                "model_years": {"start": 2020, "end": 2024}
            },
            "group_by": "model_year"
        }
        response = client.post("/api/v1/vehicles/analyze", json=request_body)
        assert response.status_code == 200
        
        data = response.json()
        # All groups should be within the year range
        for group in data["groups"]:
            year = int(group["group_value"])
            assert 2020 <= year <= 2024
    
    def test_analyze_with_min_range(self):
        """Test analyze with minimum electric range filter"""
        request_body = {
            "filters": {
                "min_electric_range": 200
            },
            "group_by": "vehicle_type"
        }
        response = client.post("/api/v1/vehicles/analyze", json=request_body)
        assert response.status_code in [200, 404]
    
    def test_analyze_group_by_options(self):
        """Test all group_by options"""
        group_by_options = ["county", "make", "model_year", "vehicle_type"]
        
        for group_by in group_by_options:
            request_body = {
                "filters": {},
                "group_by": group_by
            }
            response = client.post("/api/v1/vehicles/analyze", json=request_body)
            assert response.status_code == 200
            data = response.json()
            assert data["group_by"] == group_by


class TestTrendsEndpoint:
    """Test /api/v1/vehicles/trends endpoint"""
    
    def test_get_trends_success(self):
        """Test successful trends retrieval"""
        response = client.get("/api/v1/vehicles/trends")
        assert response.status_code == 200
        
        data = response.json()
        assert "trends" in data
        assert len(data["trends"]) > 0
        
        # Validate trend structure
        for trend in data["trends"]:
            assert "model_year" in trend
            assert "vehicle_count" in trend
            assert "average_electric_range" in trend
            assert "bev_count" in trend
            assert "phev_count" in trend
            assert "bev_percentage" in trend
            assert "phev_percentage" in trend
    
    def test_trends_sorted_by_year(self):
        """Test that trends are sorted by year"""
        response = client.get("/api/v1/vehicles/trends")
        data = response.json()
        
        years = [trend["model_year"] for trend in data["trends"]]
        assert years == sorted(years)
    
    def test_trends_percentages_sum_to_100(self):
        """Test that BEV and PHEV percentages sum to ~100"""
        response = client.get("/api/v1/vehicles/trends")
        data = response.json()
        
        for trend in data["trends"]:
            total_pct = trend["bev_percentage"] + trend["phev_percentage"]
            # Allow small rounding error
            assert 99 <= total_pct <= 101
    
    def test_trends_has_growth_rates(self):
        """Test that growth rates are calculated"""
        response = client.get("/api/v1/vehicles/trends")
        data = response.json()
        
        # Growth rates should be present if we have multiple years
        if len(data["trends"]) >= 2:
            assert "overall_growth_rate" in data
            assert "range_improvement_rate" in data


class TestErrorHandling:
    """Test error handling"""
    
    def test_invalid_page_number(self):
        """Test invalid page number"""
        response = client.get("/api/v1/vehicles/county/KING?page=0")
        assert response.status_code == 422  # Validation error
    
    def test_invalid_sort_field(self):
        """Test invalid sort field"""
        response = client.get("/api/v1/vehicles/county/KING?sort_by=invalid_field")
        assert response.status_code == 422
    
    def test_invalid_group_by(self):
        """Test invalid group_by value"""
        request_body = {
            "filters": {},
            "group_by": "invalid_field"
        }
        response = client.post("/api/v1/vehicles/analyze", json=request_body)
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
