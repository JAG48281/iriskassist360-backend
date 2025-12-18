"""
Database Health Check Router

Provides non-invasive database health monitoring.
Safe for production use - does not write to database.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import logging

from app.database import engine
from app.utils.schema_check import get_schema_status

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)

logger = logging.getLogger(__name__)


@router.get("/db")
async def database_health():
    """
    Database health check endpoint.
    
    Returns database connection status, schema validation, and row counts.
    IMPORTANT: Returns HTTP 200 even with warnings to not trigger monitoring alerts.
    
    Response:
    {
        "status": "healthy" | "degraded" | "disconnected",
        "database": "connected" | "error",
        "schema": {
            "required_tables_present": bool,
            "missing_tables": [...],
            "forbidden_tables": [...],
            "unexpected_tables": [...],
            "total_required": int,
            "total_present": int
        },
        "row_counts": {
            "table_name": count
        }
    }
    """
    response = {
        "status": "healthy",
        "database": "disconnected",
        "schema": {},
        "row_counts": {}
    }
    
    # Check database connection
    try:
        with engine.connect() as conn:
            # Simple connectivity test
            conn.execute(text("SELECT 1"))
            response["database"] = "connected"
    except SQLAlchemyError as e:
        logger.error(f"Database connection failed: {e}")
        response["database"] = "error"
        response["status"] = "disconnected"
        # Still return 200 OK but with error status
        return response
    except Exception as e:
        logger.error(f"Unexpected error during DB check: {e}")
        response["database"] = "error"
        response["status"] = "disconnected"
        return response
    
    # Get schema status (non-invasive)
    try:
        schema_status = get_schema_status()
        response["schema"] = schema_status
        
        # Adjust health status based on schema
        if not schema_status["required_tables_present"]:
            response["status"] = "degraded"
            logger.warning(f"Schema degraded - missing tables: {schema_status['missing_tables']}")
        
        if schema_status["forbidden_tables"]:
            response["status"] = "degraded"
            logger.warning(f"Forbidden tables exist: {schema_status['forbidden_tables']}")
    
    except Exception as e:
        logger.error(f"Schema status check failed: {e}")
        response["schema"] = {
            "required_tables_present": False,
            "missing_tables": [],
            "forbidden_tables": [],
            "unexpected_tables": [],
            "error": str(e)[:200]
        }
        response["status"] = "degraded"
    
    # Get row counts (safe, read-only)
    tables_to_count = [
        "lob_master",
        "occupancies",
        "fire_iib_rates",
        "fire_bsus_rates",
        "fire_stfi_rates",
        "fire_eq_rates",
        "fire_terrorism_rates",
        "fire_add_on_master",
        "fire_add_on_rates"
    ]
    
    try:
        with engine.connect() as conn:
            for table in tables_to_count:
                try:
                    # Check if table exists first
                    exists_result = conn.execute(text(f"SELECT to_regclass('public.{table}')"))
                    if exists_result.scalar() is not None:
                        # Table exists, get count
                        count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        response["row_counts"][table] = count_result.scalar()
                    else:
                        # Table doesn't exist
                        response["row_counts"][table] = None
                except SQLAlchemyError as e:
                    # Rollback to clean transaction
                    conn.rollback()
                    response["row_counts"][table] = f"error: {str(e)[:50]}"
                    logger.warning(f"Could not count {table}: {e}")
    except Exception as e:
        logger.error(f"Row count failed: {e}")
        response["row_counts"] = {"error": str(e)[:200]}
    
    # Final status summary
    if response["database"] == "disconnected":
        response["status"] = "disconnected"
    elif response["schema"].get("required_tables_present") == False:
        response["status"] = "degraded"
    elif response["schema"].get("forbidden_tables"):
        response["status"] = "degraded"
    else:
        response["status"] = "healthy"
    
    # IMPORTANT: Always return 200 OK, even with errors
    # Monitoring should check response body, not HTTP status
    return response
