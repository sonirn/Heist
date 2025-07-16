"""
Database Configuration and Optimization Module
Handles MongoDB connection pooling, indexing, and query optimization
"""
import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING, TEXT
from typing import Dict, Optional, Any
import asyncio
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Optimized database manager with connection pooling and indexing"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.connection_pool_size = 100
        self.max_idle_time = 10000  # 10 seconds
        self.server_selection_timeout = 5000  # 5 seconds
        
    async def connect(self):
        """Establish optimized database connection with pooling"""
        mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
        db_name = os.getenv("DB_NAME", "script_to_video_production")
        
        try:
            # Create connection with optimized settings
            self.client = AsyncIOMotorClient(
                mongo_url,
                maxPoolSize=self.connection_pool_size,
                minPoolSize=10,
                maxIdleTimeMS=self.max_idle_time,
                serverSelectionTimeoutMS=self.server_selection_timeout,
                connectTimeoutMS=5000,
                socketTimeoutMS=10000,
                retryWrites=True,
                retryReads=True
            )
            
            self.db = self.client[db_name]
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {db_name}")
            
            # Setup indexes for performance
            await self.setup_indexes()
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    async def setup_indexes(self):
        """Create database indexes for optimal query performance"""
        try:
            # Projects collection indexes
            await self.db.projects.create_index([
                ("user_id", ASCENDING),
                ("created_at", DESCENDING)
            ])
            await self.db.projects.create_index([("status", ASCENDING)])
            await self.db.projects.create_index([("project_id", ASCENDING)])
            await self.db.projects.create_index([("title", TEXT)])
            
            # Videos collection indexes
            await self.db.videos.create_index([
                ("project_id", ASCENDING),
                ("created_at", DESCENDING)
            ])
            await self.db.videos.create_index([("status", ASCENDING)])
            await self.db.videos.create_index([("generation_id", ASCENDING)])
            
            # User sessions indexes
            await self.db.sessions.create_index([
                ("session_id", ASCENDING)
            ])
            await self.db.sessions.create_index([
                ("created_at", ASCENDING)
            ], expireAfterSeconds=3600)  # Auto-expire after 1 hour
            
            # Analytics collection indexes
            await self.db.analytics.create_index([
                ("timestamp", DESCENDING),
                ("event_type", ASCENDING)
            ])
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create database indexes: {e}")
    
    async def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("Database connection closed")
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get database performance statistics"""
        try:
            stats = {}
            collections = ["projects", "videos", "sessions", "analytics"]
            
            for collection_name in collections:
                collection = self.db[collection_name]
                stats[collection_name] = await collection.count_documents({})
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {}
    
    async def cleanup_old_data(self, days_old: int = 30):
        """Cleanup old data for storage optimization"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            # Clean old completed videos
            result = await self.db.videos.delete_many({
                "created_at": {"$lt": cutoff_date},
                "status": "completed"
            })
            
            # Clean old failed generations
            failed_result = await self.db.videos.delete_many({
                "created_at": {"$lt": cutoff_date},
                "status": "failed"
            })
            
            logger.info(f"Cleaned {result.deleted_count} old videos, {failed_result.deleted_count} failed generations")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")

# Global database manager instance
db_manager = DatabaseManager()