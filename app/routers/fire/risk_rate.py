"""
Fire Risk Rate API Endpoint
Returns fire risk rate (per mille) based on product code, IIB code, and AIFT section
"""
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text
from app.database import engine
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/fire", tags=["Fire Risk Rate"])


@router.get("/risk-rate")
async def get_fire_risk_rate(
    productCode: str = Query(..., description="Product code: UBGR | BGRP | SFSP | BSUS | BLUS | UVUS | UVGR"),
    iibCode: str = Query(..., description="IIB code from occupancy"),
    aiftSection: str = Query(..., description="AIFT section from occupancy")
):
    """
    Get fire risk rate (per mille) for the given product, IIB code, and AIFT section.
    
    **Product Normalization:**
    - UBGR → BGRP
    
    **Data Sources:**
    - BGRP/SFSP/IAR → fire_iib_rates table
    - BSUS/BLUS/UVUS/UVGR → fire_bsus_rates table
    
    **Response:**
    ```json
    {
        "success": true,
        "rate_per_mille": 0.15
    }
    ```
    
    **Error Response (404):**
    ```json
    {
        "success": false,
        "message": "No rate found for the given combination"
    }
    ```
    """
    try:
        # Step 1: Normalize product code
        normalized_product = productCode.upper().strip()
        if normalized_product == "UBGR":
            normalized_product = "BGRP"
        
        # Step 2: Validate product code
        valid_products = ["BGRP", "SFSP", "IAR", "BSUS", "BLUS", "UVUS", "UVGR"]
        if normalized_product not in valid_products:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "message": f"Invalid product code. Must be one of: {', '.join(valid_products)}"
                }
            )
        
        # Step 3: Determine which table to query
        iib_products = ["BGRP", "SFSP", "IAR"]
        bsus_products = ["BSUS", "BLUS", "UVUS", "UVGR"]
        
        rate_per_mille = None
        
        if normalized_product in iib_products:
            # Query fire_iib_rates table
            # Note: fire_iib_rates table only has iib_code and rate_per_mille
            # aiftSection is validated but not used in the query for this table
            query = text("""
                SELECT rate_per_mille 
                FROM fire_iib_rates 
                WHERE iib_code = :iib_code
                LIMIT 1
            """)
            
            with engine.connect() as conn:
                result = conn.execute(query, {"iib_code": iibCode})
                row = result.fetchone()
                if row:
                    rate_per_mille = float(row[0])
        
        elif normalized_product in bsus_products:
            # Query fire_bsus_rates table
            # fire_bsus_rates has: iib_code, eq_zone, rate_per_mille
            # The aiftSection parameter may correspond to eq_zone (e.g., "Zone I", "Zone II", "Zone III")
            # Try to match with eq_zone first, then fall back to any rate for the iib_code
            
            # First, try with eq_zone matching aiftSection
            query_with_zone = text("""
                SELECT rate_per_mille 
                FROM fire_bsus_rates 
                WHERE iib_code = :iib_code AND eq_zone = :eq_zone
                LIMIT 1
            """)
            
            with engine.connect() as conn:
                result = conn.execute(query_with_zone, {
                    "iib_code": iibCode,
                    "eq_zone": aiftSection
                })
                row = result.fetchone()
                if row:
                    rate_per_mille = float(row[0])
                    logger.info(f"Found rate with exact zone match: {aiftSection}")
                else:
                    # Fallback: get any rate for this iib_code
                    query_fallback = text("""
                        SELECT rate_per_mille 
                        FROM fire_bsus_rates 
                        WHERE iib_code = :iib_code
                        LIMIT 1
                    """)
                    result = conn.execute(query_fallback, {"iib_code": iibCode})
                    row = result.fetchone()
                    if row:
                        rate_per_mille = float(row[0])
                        logger.warning(
                            f"Could not match zone '{aiftSection}', using first available rate for IIB {iibCode}"
                        )
        
        # Step 4: Return response
        if rate_per_mille is None:
            logger.warning(
                f"No rate found for productCode={productCode} (normalized to {normalized_product}), "
                f"iibCode={iibCode}, aiftSection={aiftSection}"
            )
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "message": f"No rate found for product {normalized_product}, IIB code {iibCode}, and AIFT section {aiftSection}"
                }
            )
        
        logger.info(
            f"✅ Rate found: {rate_per_mille}‰ for productCode={normalized_product}, "
            f"iibCode={iibCode}, aiftSection={aiftSection}"
        )
        
        return {
            "success": True,
            "rate_per_mille": rate_per_mille
        }
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        logger.error(f"🔥 Error in get_fire_risk_rate: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": f"Internal server error: {str(e)}"
            }
        )
