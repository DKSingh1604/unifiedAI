# Electric Vehicle Analytics

A complete data pipeline and REST API for analyzing electric vehicle population data from Washington State (270K+ records).

## 📋 Project Overview

This project implements:
- **Phase 1**: ETL data pipeline (Extract, Transform, Load)
- **Phase 2**: FastAPI REST API with 5 analytical endpoints
- **Bonus**: Comprehensive testing and caching support

## 🏗️ Architecture

```
unifiedAI/
├── app/
│   ├── api/              # API routes and endpoints
│   ├── pipeline/         # ETL pipeline
│   ├── schemas/          # Pydantic models
│   ├── config.py         # Configuration management
│   ├── database.py       # MongoDB connection and indexes
│   ├── logger.py         # Logging setup
│   └── main.py           # FastAPI application
├── scripts/              # Utility scripts
│   ├── run_pipeline.py   # Run ETL pipeline
│   └── run_server.py     # Start API server
├── tests/                # Integration tests
│   ├── test_api.py       # API endpoint tests
│   └── test_pipeline.py  # Pipeline tests
├── data/
│   └── raw/              # Place CSV file here
├── logs/                 # Application logs
├── requirements.txt      # Python dependencies
├── .env.example          # Example environment variables
└── README.md            # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- MongoDB (local installation)
- Electric Vehicle Population Data CSV file

### 1. Setup Environment

```bash
# Clone or navigate to project directory
cd unifiedAI

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
# For local setup, default values should work
```

**Key Configuration:**
- `MONGODB_URL`: MongoDB connection string (default: `mongodb://localhost:27017`)
- `CSV_SOURCE`: `local` or `s3`
- `CSV_LOCAL_PATH`: Path to CSV file (default: `./data/raw/Electric_Vehicle_Population_Data.csv`)

### 3. Setup MongoDB

**Local Installation:**
- **macOS**: `brew install mongodb-community@7.0 && brew services start mongodb/brew/mongodb-community@7.0`
- **Ubuntu**: `sudo apt install mongodb && sudo systemctl start mongodb`
- **Windows**: Download from [MongoDB Downloads](https://www.mongodb.com/try/download/community)

Verify MongoDB is running:
```bash
mongosh --eval "db.version()"
```

### 4. Prepare Data

Place your `Electric_Vehicle_Population_Data.csv` file in `data/raw/`:

```bash
# Create data directory if it doesn't exist
mkdir -p data/raw

# Copy your CSV file
cp /path/to/Electric_Vehicle_Population_Data.csv data/raw/
```

### 5. Run ETL Pipeline

```bash
# Run the pipeline to load data into MongoDB
python scripts/run_pipeline.py
```

**What this does:**
1. Reads CSV from configured source (local or S3)
2. Validates and transforms data using Pydantic models
3. Loads data into MongoDB with proper schema
4. Creates optimized indexes for queries
5. Generates data quality report

**Expected Output:**
```
================================================================================
Starting ETL Pipeline
================================================================================
Phase 1: Extract
Reading CSV from local path: ./data/raw/Electric_Vehicle_Population_Data.csv
Successfully loaded 270000 records from CSV

Phase 2: Transform
Validating 270000 records...
Validated 50000/270000 records
Validated 100000/270000 records
...
Validation complete: 268500 valid, 1500 invalid

Phase 3: Load
Inserting batch 1: 10000 records
Inserting batch 2: 10000 records
...
Successfully loaded 268500 records
Creating indexes...
Successfully created all indexes

================================================================================
ETL Pipeline Complete
Total Records: 270000
Valid Records: 268500
Invalid Records: 1500
================================================================================
```

### 6. Start API Server

```bash
# Start FastAPI server
python scripts/run_server.py
```

The API will be available at:
- **API Base URL**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## 📚 API Documentation

### Endpoint Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/vehicles/summary` | Dataset summary and statistics |
| GET | `/api/v1/vehicles/county/{county_name}` | Vehicles by county (paginated) |
| GET | `/api/v1/vehicles/make/{make}/models` | Models by manufacturer |
| POST | `/api/v1/vehicles/analyze` | Complex filtered analysis |
| GET | `/api/v1/vehicles/trends` | Trends over time |

### 1. Summary Endpoint

**GET** `/api/v1/vehicles/summary`

Returns overall dataset statistics.

**Response Example:**
```json
{
  "total_vehicles": 270000,
  "vehicles_by_type": [
    {"type": "BATTERY ELECTRIC VEHICLE (BEV)", "count": 180000},
    {"type": "PLUG-IN HYBRID ELECTRIC VEHICLE (PHEV)", "count": 90000}
  ],
  "top_10_makes": [
    {"make": "TESLA", "count": 120000},
    {"make": "CHEVROLET", "count": 25000},
    ...
  ],
  "average_electric_range": 156.8,
  "eligibility_summary": [
    {"eligibility": "Clean Alternative Fuel Vehicle Eligible", "count": 200000},
    ...
  ]
}
```

**cURL Example:**
```bash
curl http://localhost:8000/api/v1/vehicles/summary
```

### 2. County Endpoint

**GET** `/api/v1/vehicles/county/{county_name}`

Returns vehicles in a specific county with pagination and filtering.

**Query Parameters:**
- `page` (int, default: 1): Page number
- `page_size` (int, default: 20, max: 100): Items per page
- `model_year` (int, optional): Filter by model year
- `sort_by` (string, default: "model_year"): Sort field (model_year, make, model)
- `sort_order` (string, default: "desc"): Sort order (asc, desc)

**Response Example:**
```json
{
  "county": "KING",
  "total_count": 85000,
  "page": 1,
  "page_size": 20,
  "total_pages": 4250,
  "vehicles": [
    {
      "vin_1_10": "5YJSA1E26K",
      "county": "KING",
      "city": "SEATTLE",
      "model_year": 2023,
      "make": "TESLA",
      "model": "MODEL S",
      "electric_vehicle_type": "BATTERY ELECTRIC VEHICLE (BEV)",
      "electric_range": 405,
      ...
    },
    ...
  ]
}
```

**cURL Examples:**
```bash
# Get first page of vehicles in KING county
curl http://localhost:8000/api/v1/vehicles/county/KING

# Filter by year and sort by make
curl "http://localhost:8000/api/v1/vehicles/county/KING?model_year=2023&sort_by=make&sort_order=asc"

# Pagination
curl "http://localhost:8000/api/v1/vehicles/county/KING?page=2&page_size=50"
```

### 3. Make Models Endpoint

**GET** `/api/v1/vehicles/make/{make}/models`

Returns all models for a specific manufacturer with statistics.

**Response Example:**
```json
{
  "make": "TESLA",
  "total_models": 5,
  "most_popular_model": "MODEL 3",
  "most_popular_count": 50000,
  "models": [
    {
      "model": "MODEL 3",
      "count": 50000,
      "average_electric_range": 358.5
    },
    {
      "model": "MODEL Y",
      "count": 40000,
      "average_electric_range": 330.2
    },
    ...
  ]
}
```

**cURL Example:**
```bash
curl http://localhost:8000/api/v1/vehicles/make/TESLA/models
```

### 4. Analyze Endpoint

**POST** `/api/v1/vehicles/analyze`

Complex filtered analysis with grouping.

**Request Body:**
```json
{
  "filters": {
    "makes": ["TESLA", "CHEVROLET"],
    "model_years": {"start": 2020, "end": 2024},
    "min_electric_range": 100,
    "counties": ["KING", "PIERCE"],
    "vehicle_types": ["BATTERY ELECTRIC VEHICLE (BEV)"]
  },
  "group_by": "county"
}
```

**group_by options**: `county`, `make`, `model_year`, `vehicle_type`

**Response Example:**
```json
{
  "group_by": "county",
  "total_matching_vehicles": 25000,
  "groups": [
    {
      "group_value": "KING",
      "count": 18000,
      "average_electric_range": 285.5,
      "most_common_vehicle": "TESLA MODEL 3"
    },
    {
      "group_value": "PIERCE",
      "count": 7000,
      "average_electric_range": 268.3,
      "most_common_vehicle": "TESLA MODEL Y"
    }
  ]
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/vehicles/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "filters": {
      "makes": ["TESLA", "CHEVROLET"],
      "model_years": {"start": 2020, "end": 2024},
      "min_electric_range": 100
    },
    "group_by": "make"
  }'
```

### 5. Trends Endpoint

**GET** `/api/v1/vehicles/trends`

Returns trends over time by model year.

**Response Example:**
```json
{
  "trends": [
    {
      "model_year": 2018,
      "vehicle_count": 5000,
      "average_electric_range": 150.5,
      "bev_count": 3500,
      "phev_count": 1500,
      "bev_percentage": 70.0,
      "phev_percentage": 30.0
    },
    {
      "model_year": 2019,
      "vehicle_count": 8000,
      "average_electric_range": 175.2,
      "bev_count": 6000,
      "phev_count": 2000,
      "bev_percentage": 75.0,
      "phev_percentage": 25.0
    },
    ...
  ],
  "overall_growth_rate": 45.5,
  "range_improvement_rate": 12.3
}
```

**cURL Example:**
```bash
curl http://localhost:8000/api/v1/vehicles/trends
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api.py -v

# Run specific test
pytest tests/test_api.py::TestSummaryEndpoint::test_get_summary_success -v
```

**Test Coverage:**
- API endpoint tests (all 5 endpoints)
- Data validation tests
- Pipeline transformation tests
- Error handling tests

## 🗄️ Database Design

### MongoDB Schema

**Collection: `vehicles`**

```javascript
{
  "_id": ObjectId("..."),
  "vin_1_10": "5YJSA1E26K",
  "county": "KING",
  "city": "SEATTLE",
  "state": "WA",
  "postal_code": "98101",
  "model_year": 2023,
  "make": "TESLA",
  "model": "MODEL S",
  "electric_vehicle_type": "BATTERY ELECTRIC VEHICLE (BEV)",
  "cafv_eligibility": "Clean Alternative Fuel Vehicle Eligible",
  "electric_range": 405,
  "base_msrp": 0,
  "legislative_district": "43",
  "dol_vehicle_id": "12345678",
  "vehicle_location": "POINT (-122.3321 47.6062)",
  "electric_utility": "CITY OF SEATTLE - (WA)|CITY LIGHT DEPARTMENT",
  "census_tract_2020": "53033005302"
}
```

### Indexes

Optimized indexes for query performance:

```javascript
// Single field indexes
db.vehicles.createIndex({ "county": 1 })
db.vehicles.createIndex({ "make": 1 })
db.vehicles.createIndex({ "model_year": -1 })
db.vehicles.createIndex({ "electric_vehicle_type": 1 })
db.vehicles.createIndex({ "electric_range": -1 })

// Compound indexes
db.vehicles.createIndex({ "make": 1, "model": 1 })
db.vehicles.createIndex({ "county": 1, "model_year": -1 })
db.vehicles.createIndex({ "model_year": -1, "electric_vehicle_type": 1 })
```

**Design Rationale:**
- Single field indexes support basic filtering and sorting
- Compound indexes optimize complex queries (e.g., county + year filtering)
- Descending index on `model_year` for recent-first sorting
- All indexes support the required API endpoints

## 🔧 Design Decisions

### 1. Data Validation Strategy

**Pydantic Models**: Used for type safety and automatic validation
- Normalizes strings to uppercase for consistency
- Handles missing/NA values gracefully
- Validates year ranges (1997-2026)
- Converts empty numeric values to 0

### 2. Database Schema

**MongoDB Choice**:
- ✅ Flexible schema for evolving data
- ✅ Efficient aggregation pipeline for analytics
- ✅ Horizontal scaling capability
- ✅ JSON-like documents match API responses

### 3. API Design

**RESTful Principles**:
- Resource-based URLs
- HTTP methods match operations
- Proper status codes (200, 404, 422, 500)
- Pagination for large result sets

**Performance Optimizations**:
- Database indexes on frequently queried fields
- Aggregation pipelines for complex queries
- Pagination to limit response size
- Query optimization using MongoDB's `$match` early in pipeline

### 4. Error Handling

**Layered Approach**:
1. **Pydantic validation**: Catches invalid input at API level
2. **Database errors**: Handled with try-catch and logged
3. **Business logic errors**: Return appropriate HTTP status codes
4. **Logging**: All errors logged with context for debugging

### 5. Code Organization

**Modular Structure**:
- `app/api`: API routes (separation of concerns)
- `app/pipeline`: ETL logic (reusable for different data sources)
- `app/schemas`: Data models (single source of truth)
- `app/database`: Database connection (connection pooling)

## 📊 Data Quality

The pipeline includes comprehensive data validation:

### Validation Rules

1. **Required Fields**: VIN, county, city, make, model, year, type
2. **Year Range**: 1997-2026 (reasonable for EVs)
3. **String Normalization**: Uppercase, trimmed
4. **Numeric Handling**: NA/empty values converted to 0
5. **Type Validation**: Ensures BEV or PHEV

### Quality Report

After running the pipeline, you'll get a detailed quality report:

```
Total Records: 270000
Valid Records: 268500
Invalid Records: 1500
```

Check `logs/app.pipeline.etl.log` for detailed validation errors.

## 🚀 Deployment

### Production Deployment

For production deployment, consider:

1. **Process Management**: Use `systemd`, `supervisor`, or PM2 to keep the API running
2. **Reverse Proxy**: Use nginx or Apache as a reverse proxy
3. **Environment Variables**: Secure your `.env` file with proper permissions
4. **MongoDB**: Use MongoDB Atlas for managed cloud hosting or set up replication
5. **Monitoring**: Implement logging and monitoring (e.g., Sentry, DataDog)

Example systemd service file:

```ini
[Unit]
Description=EV Analytics API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/unifiedAI
Environment="PATH=/path/to/unifiedAI/venv/bin"
ExecStart=/path/to/unifiedAI/venv/bin/python scripts/run_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## 🎯 Performance Considerations

### Scalability

**Current Design** (270K records):
- All endpoints respond < 1 second
- Efficient indexes minimize query time
- Pagination prevents memory issues

**Scaling to 1M+ Records**:
1. **Batch Processing**: Pipeline already processes in 10K batches
2. **Connection Pooling**: MongoDB driver handles automatically
3. **Caching**: Redis support included (see bonus features)
4. **Sharding**: MongoDB supports horizontal scaling

### Optimization Techniques

1. **Index Usage**: All queries use indexes
2. **Projection**: Only fetch needed fields
3. **Aggregation**: Push filtering to database level
4. **Pagination**: Limit memory usage

## 🎁 Bonus Features

### 1. Caching (Redis)

Enable caching in `.env`:

```env
CACHE_ENABLED=true
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=3600
```

Install and start Redis:

```bash
# macOS
brew install redis
brew services start redis

# Ubuntu
sudo apt install redis-server
sudo systemctl start redis
```

### 2. S3 Support

Configure S3 data source in `.env`:

```env
CSV_SOURCE=s3
CSV_S3_BUCKET=your-bucket-name
CSV_S3_KEY=Electric_Vehicle_Population_Data.csv
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=us-west-2
```

### 3. Comprehensive Logging

All operations are logged to:
- Console: INFO level
- File (`logs/`): DEBUG level with full context

## 🐛 Troubleshooting

### Common Issues

**1. MongoDB Connection Error**
```
Error: Failed to connect to MongoDB
```
**Solution**: Ensure MongoDB is running
```bash
# Check if MongoDB is running
brew services list | grep mongodb  # macOS
sudo systemctl status mongodb  # Linux

# Start MongoDB if not running
brew services start mongodb/brew/mongodb-community@7.0  # macOS
sudo systemctl start mongodb  # Linux
```

**2. CSV File Not Found**
```
FileNotFoundError: CSV file not found
```
**Solution**: Place CSV in `data/raw/` directory
```bash
mkdir -p data/raw
cp /path/to/Electric_Vehicle_Population_Data.csv data/raw/
```

**3. Import Errors**
```
ModuleNotFoundError: No module named 'app'
```
**Solution**: Run scripts from project root
```bash
cd /Users/devkaransingh/Documents/unifiedAI
python scripts/run_pipeline.py
```

**4. Port Already in Use**
```
OSError: [Errno 48] Address already in use
```
**Solution**: Change port in `.env` or kill existing process
```bash
lsof -i :8000  # Find process using port 8000
kill -9 <PID>  # Kill the process
```

## 📝 Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MONGODB_URL` | Yes | `mongodb://localhost:27017` | MongoDB connection string |
| `MONGODB_DB_NAME` | Yes | `ev_analytics` | Database name |
| `CSV_SOURCE` | Yes | `local` | Data source: `local` or `s3` |
| `CSV_LOCAL_PATH` | If local | `./data/raw/Electric_Vehicle_Population_Data.csv` | Local CSV path |
| `CSV_S3_BUCKET` | If S3 | - | S3 bucket name |
| `CSV_S3_KEY` | If S3 | - | S3 object key |
| `AWS_ACCESS_KEY_ID` | If S3 | - | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | If S3 | - | AWS secret key |
| `AWS_REGION` | If S3 | `us-west-2` | AWS region |
| `REDIS_URL` | No | `redis://localhost:6379/0` | Redis connection string |
| `CACHE_ENABLED` | No | `true` | Enable/disable caching |
| `CACHE_TTL` | No | `3600` | Cache TTL in seconds |
| `API_HOST` | No | `0.0.0.0` | API host |
| `API_PORT` | No | `8000` | API port |
| `API_WORKERS` | No | `4` | Number of workers |

## 👥 Contributing

This is a take-home assignment project. For questions or issues, contact the assessment coordinator.

## 📄 License

This project is for assessment purposes.

## 🙏 Acknowledgments

- **Data Source**: Washington State Department of Licensing
- **Dataset**: Electric Vehicle Population Data (270K+ records)
- **Technologies**: FastAPI, MongoDB, Pydantic, Pandas

---

**Built with ❤️ for the Junior Software Engineer Take-Home Assessment**
