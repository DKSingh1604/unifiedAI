"""
Database connection and management
"""
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, OperationFailure
from app.config import settings
from app.logger import setup_logger
from typing import Optional

logger = setup_logger(__name__)


class DatabaseManager:
    """Manages MongoDB connection and operations"""
    
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db = None
        
    def connect(self):
        """Establish connection to MongoDB"""
        try:
            self.client = MongoClient(settings.mongodb_url, serverSelectionTimeoutMS=5000)
            # Test the connection
            self.client.admin.command('ping')
            self.db = self.client[settings.mongodb_db_name]
            logger.info(f"Successfully connected to MongoDB: {settings.mongodb_db_name}")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
            
    def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
            
    def get_collection(self, collection_name: str):
        """Get a MongoDB collection"""
        if self.db is None:
            self.connect()
        return self.db[collection_name]
    
    def create_indexes(self):
        """
        Create indexes for optimal query performance
        
        Indexes are based on the queries required in Phase 2:
        - County queries: index on county
        - Make queries: index on make
        - Model year queries: index on model_year
        - Trends: index on model_year
        - Analyze: compound indexes for filtering
        """
        try:
            vehicles_collection = self.get_collection("vehicles")
            
            # Single field indexes
            vehicles_collection.create_index([("county", ASCENDING)], name="idx_county")
            vehicles_collection.create_index([("make", ASCENDING)], name="idx_make")
            vehicles_collection.create_index([("model_year", DESCENDING)], name="idx_model_year")
            vehicles_collection.create_index([("electric_vehicle_type", ASCENDING)], name="idx_ev_type")
            vehicles_collection.create_index([("electric_range", DESCENDING)], name="idx_electric_range")
            
            # Compound indexes for complex queries
            vehicles_collection.create_index(
                [("make", ASCENDING), ("model", ASCENDING)],
                name="idx_make_model"
            )
            vehicles_collection.create_index(
                [("county", ASCENDING), ("model_year", DESCENDING)],
                name="idx_county_year"
            )
            vehicles_collection.create_index(
                [("model_year", DESCENDING), ("electric_vehicle_type", ASCENDING)],
                name="idx_year_type"
            )
            
            logger.info("Successfully created all indexes")
            
        except OperationFailure as e:
            logger.error(f"Failed to create indexes: {e}")
            raise
    
    def drop_collection(self, collection_name: str):
        """Drop a collection (useful for testing/reloading data)"""
        try:
            self.db[collection_name].drop()
            logger.info(f"Dropped collection: {collection_name}")
        except Exception as e:
            logger.error(f"Failed to drop collection {collection_name}: {e}")
            raise


# Global database manager instance
db_manager = DatabaseManager()
