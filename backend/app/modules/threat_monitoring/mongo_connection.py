"""
MongoDB connection manager for the Threat Monitoring module.

Provides a MongoDB client and database reference for high-volume detection
audit logging. Gracefully degrades if MongoDB is unavailable — the rest of
the platform continues to work with PostgreSQL only.

Usage:
    from app.modules.threat_monitoring.mongo_connection import get_mongo_db, mongo_available

    if mongo_available():
        db = get_mongo_db()
        db.detection_logs.insert_one(document)
"""

import os
import logging
from typing import Optional

logger = logging.getLogger("threat_monitoring.mongo")

# ---------------------------------------------------------------------------
# MongoDB Connection State
# ---------------------------------------------------------------------------

_mongo_client = None
_mongo_db = None
_mongo_is_available = False


def init_mongo_connection(
    uri: Optional[str] = None,
    database_name: str = "threatlens_monitoring",
) -> bool:
    """
    Initialise the MongoDB connection.

    Args:
        uri: MongoDB connection URI. Defaults to MONGODB_URI env var or
             'mongodb://localhost:27017'.
        database_name: Name of the MongoDB database.

    Returns:
        True if the connection was established successfully, False otherwise.
    """
    global _mongo_client, _mongo_db, _mongo_is_available

    if uri is None:
        uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")

    try:
        from pymongo import MongoClient
        from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

        _mongo_client = MongoClient(
            uri,
            serverSelectionTimeoutMS=3000,  # 3-second timeout for fast startup
            connectTimeoutMS=3000,
        )

        # Verify connectivity with a ping
        _mongo_client.admin.command("ping")

        _mongo_db = _mongo_client[database_name]
        _mongo_is_available = True

        # Create indexes for common queries
        _create_indexes()

        logger.info(
            "MongoDB connection established: %s / %s",
            uri.split("@")[-1] if "@" in uri else uri,  # hide credentials
            database_name,
        )
        return True

    except ImportError:
        logger.warning(
            "pymongo is not installed. MongoDB logging is disabled. "
            "Install with: pip install pymongo"
        )
        _mongo_is_available = False
        return False

    except Exception as e:
        logger.warning(
            "Could not connect to MongoDB (%s). "
            "MongoDB logging is disabled. The system will continue using PostgreSQL only.",
            str(e),
        )
        _mongo_is_available = False
        return False


def _create_indexes():
    """Create MongoDB indexes for common query patterns."""
    if _mongo_db is None:
        return

    try:
        collection = _mongo_db["detection_logs"]
        collection.create_index("threat_id")
        collection.create_index("filename")
        collection.create_index("prediction")
        collection.create_index("logged_at")
        collection.create_index("risk_level")
        collection.create_index([("logged_at", -1)])  # descending for recent-first queries
        logger.info("MongoDB indexes created/verified for detection_logs collection.")
    except Exception as e:
        logger.warning("Could not create MongoDB indexes: %s", str(e))


def get_mongo_db():
    """
    Return the MongoDB database instance.

    Returns:
        pymongo Database instance, or None if MongoDB is unavailable.
    """
    return _mongo_db


def get_mongo_client():
    """Return the raw MongoClient instance (for health checks, etc.)."""
    return _mongo_client


def mongo_available() -> bool:
    """Check if MongoDB is connected and available."""
    return _mongo_is_available


def close_mongo_connection():
    """Gracefully close the MongoDB connection."""
    global _mongo_client, _mongo_db, _mongo_is_available

    if _mongo_client:
        try:
            _mongo_client.close()
            logger.info("MongoDB connection closed.")
        except Exception as e:
            logger.warning("Error closing MongoDB connection: %s", str(e))
        finally:
            _mongo_client = None
            _mongo_db = None
            _mongo_is_available = False
