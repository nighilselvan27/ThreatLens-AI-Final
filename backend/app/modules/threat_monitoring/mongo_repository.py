"""
MongoDB data access layer for high-volume detection audit logging.

This repository writes detailed detection event documents to MongoDB's
`detection_logs` collection. These logs capture the full raw payload
from each scan — information that would be too verbose or unstructured
for the PostgreSQL schema.

If MongoDB is unavailable, all methods gracefully return empty results
or silently skip writes, logging a warning.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, List

from app.modules.threat_monitoring.mongo_connection import get_mongo_db, mongo_available

logger = logging.getLogger("threat_monitoring.mongo_repo")

# Collection name in MongoDB
COLLECTION_NAME = "detection_logs"


class MongoThreatLogger:
    """MongoDB data access for detection audit logs."""

    # ------------------------------------------------------------------
    # WRITE
    # ------------------------------------------------------------------

    @staticmethod
    def log_detection(
        *,
        threat_id: str,
        filename: str,
        prediction: str,
        confidence: float,
        risk_score: int,
        risk_level: str,
        detection_engine: Optional[str] = None,
        file_hash_md5: Optional[str] = None,
        file_hash_sha256: Optional[str] = None,
        file_size: Optional[int] = None,
        file_type: Optional[str] = None,
        yara_matches: Optional[list] = None,
        static_analysis_results: Optional[dict] = None,
        suspicious_indicators: Optional[dict] = None,
        raw_payload: Optional[dict] = None,
        detected_by_user_id: Optional[int] = None,
    ) -> Optional[str]:
        """
        Insert a detection event document into MongoDB.

        Returns:
            The inserted document's _id as a string, or None if MongoDB is unavailable.
        """
        if not mongo_available():
            logger.debug("MongoDB unavailable — skipping detection log for %s", filename)
            return None

        db = get_mongo_db()
        if db is None:
            return None

        document = {
            "threat_id": threat_id,
            "filename": filename,
            "prediction": prediction,
            "confidence": confidence,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "detection_engine": detection_engine,
            "file_hash_md5": file_hash_md5,
            "file_hash_sha256": file_hash_sha256,
            "file_size": file_size,
            "file_type": file_type,
            "yara_matches": yara_matches or [],
            "static_analysis_results": static_analysis_results or {},
            "suspicious_indicators": suspicious_indicators or {},
            "raw_payload": raw_payload or {},
            "detected_by_user_id": detected_by_user_id,
            "logged_at": datetime.now(timezone.utc),
        }

        try:
            result = db[COLLECTION_NAME].insert_one(document)
            logger.info("MongoDB detection log saved: %s (threat_id=%s)", result.inserted_id, threat_id)
            return str(result.inserted_id)
        except Exception as e:
            logger.error("Failed to write detection log to MongoDB: %s", str(e))
            return None

    # ------------------------------------------------------------------
    # READ
    # ------------------------------------------------------------------

    @staticmethod
    def get_logs(
        *,
        prediction: Optional[str] = None,
        risk_level: Optional[str] = None,
        filename: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple:
        """
        Query detection logs with optional filters.

        Returns:
            Tuple of (list of documents, total count).
        """
        if not mongo_available():
            return [], 0

        db = get_mongo_db()
        if db is None:
            return [], 0

        collection = db[COLLECTION_NAME]

        # Build filter
        query_filter = {}
        if prediction:
            query_filter["prediction"] = {"$regex": prediction, "$options": "i"}
        if risk_level:
            query_filter["risk_level"] = risk_level
        if filename:
            query_filter["filename"] = {"$regex": filename, "$options": "i"}

        try:
            total = collection.count_documents(query_filter)
            cursor = (
                collection.find(query_filter)
                .sort("logged_at", -1)
                .skip(offset)
                .limit(limit)
            )
            items = []
            for doc in cursor:
                doc["id"] = str(doc.pop("_id"))
                # Convert datetime for JSON serialisation
                if "logged_at" in doc and isinstance(doc["logged_at"], datetime):
                    doc["logged_at"] = doc["logged_at"].isoformat()
                items.append(doc)

            return items, total

        except Exception as e:
            logger.error("Failed to query MongoDB detection logs: %s", str(e))
            return [], 0

    @staticmethod
    def get_log_by_id(log_id: str) -> Optional[dict]:
        """Retrieve a single detection log by its MongoDB _id."""
        if not mongo_available():
            return None

        db = get_mongo_db()
        if db is None:
            return None

        try:
            from bson import ObjectId
            doc = db[COLLECTION_NAME].find_one({"_id": ObjectId(log_id)})
            if doc:
                doc["id"] = str(doc.pop("_id"))
                if "logged_at" in doc and isinstance(doc["logged_at"], datetime):
                    doc["logged_at"] = doc["logged_at"].isoformat()
            return doc
        except Exception as e:
            logger.error("Failed to retrieve MongoDB log %s: %s", log_id, str(e))
            return None

    @staticmethod
    def get_logs_by_threat_id(threat_id: str) -> List[dict]:
        """Retrieve all detection logs for a specific threat."""
        if not mongo_available():
            return []

        db = get_mongo_db()
        if db is None:
            return []

        try:
            cursor = (
                db[COLLECTION_NAME]
                .find({"threat_id": threat_id})
                .sort("logged_at", -1)
            )
            items = []
            for doc in cursor:
                doc["id"] = str(doc.pop("_id"))
                if "logged_at" in doc and isinstance(doc["logged_at"], datetime):
                    doc["logged_at"] = doc["logged_at"].isoformat()
                items.append(doc)
            return items
        except Exception as e:
            logger.error("Failed to query MongoDB logs for threat %s: %s", threat_id, str(e))
            return []

    @staticmethod
    def get_detection_stats(days: int = 30) -> dict:
        """
        Aggregation pipeline to compute detection statistics over a time window.

        Returns:
            Dict with keys: total_logs, by_prediction, by_risk_level.
        """
        if not mongo_available():
            return {"total_logs": 0, "by_prediction": {}, "by_risk_level": {}}

        db = get_mongo_db()
        if db is None:
            return {"total_logs": 0, "by_prediction": {}, "by_risk_level": {}}

        try:
            from datetime import timedelta
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            collection = db[COLLECTION_NAME]

            total = collection.count_documents({"logged_at": {"$gte": cutoff}})

            # Group by prediction
            pipeline_prediction = [
                {"$match": {"logged_at": {"$gte": cutoff}}},
                {"$group": {"_id": "$prediction", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
            ]
            by_prediction = {
                doc["_id"]: doc["count"]
                for doc in collection.aggregate(pipeline_prediction)
            }

            # Group by risk level
            pipeline_risk = [
                {"$match": {"logged_at": {"$gte": cutoff}}},
                {"$group": {"_id": "$risk_level", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
            ]
            by_risk_level = {
                doc["_id"]: doc["count"]
                for doc in collection.aggregate(pipeline_risk)
            }

            return {
                "total_logs": total,
                "by_prediction": by_prediction,
                "by_risk_level": by_risk_level,
            }

        except Exception as e:
            logger.error("Failed to compute MongoDB detection stats: %s", str(e))
            return {"total_logs": 0, "by_prediction": {}, "by_risk_level": {}}
