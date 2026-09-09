"""
ThreatLens AI — Threat Monitoring Module

This package implements the core threat monitoring system that connects
AI malware predictions to detection logs, threat history, risk scoring,
MongoDB audit logging, and dashboard aggregation APIs.

Key components:
    - models.py          : SQLAlchemy ORM models (PostgreSQL) + MongoDB document schemas
    - schemas.py         : Pydantic request/response schemas for the REST API
    - repository.py      : PostgreSQL data access layer
    - mongo_connection.py: MongoDB connection manager (with graceful fallback)
    - mongo_repository.py: MongoDB data access layer for detection audit logs
    - risk_score.py      : Multi-factor risk score calculator
    - service.py         : Business logic orchestration layer
    - alert_integration.py: Bridge to the Alert & Notification module
"""
