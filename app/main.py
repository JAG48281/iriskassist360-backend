
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth
from app.routers.fire import uiic_fire
from app.database import Base, engine

import os

import logging
import time
from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.limiter import limiter

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("irisk_backend")

def create_app():
    app = FastAPI(title="iRiskAssist360 Backend", description="Backend API for iRiskAssist360 Flutter App", version="1.0.0")
    
    # Initialize Rate Limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Trust Proxy Headers (Railway/LoadBalancers)
    from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
    app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])

    # CORS Configuration
    # In Railway variables, set ALLOWED_ORIGINS to "https://your-netlify-app.netlify.app"
    # For multiple origins, separate by comma: "https://app.com,https://staging.app.com"
    origins_str = os.getenv("ALLOWED_ORIGINS", "*")
    origins = [origin.strip() for origin in origins_str.split(",")]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        logger.info(f"Incoming Request: {request.method} {request.url}")
        
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(f"Request Failed: {e}")
            return JSONResponse(
                status_code=500,
                content={"success": False, "message": "Internal Server Error", "data": str(e)}
            )
            
        process_time = time.time() - start_time
        logger.info(f"Request Completed: {response.status_code} in {process_time:.4f}s")
        return response

    app.include_router(auth.router)
    app.include_router(uiic_fire.router)
    
    # New Routers for Flutter App
    from app.routers.premium import router as premium_router
    from app.routers.rates import router as rates_router
    
    app.include_router(premium_router, prefix="/api/premium")
    app.include_router(rates_router, prefix="/api/rates")
    
    # Common Data Routers
    from app.routers.common.occupancies import router as occ_router
    from app.routers.common.addons import router as addon_router
    from app.routers.common.data_inspection import router as inspect_router
    from app.routers.master import risk_master
    

    app.include_router(occ_router)
    app.include_router(addon_router)
    app.include_router(inspect_router)
    app.include_router(risk_master.router, prefix="/api")

    # Rating Engine
    from app.routers.rating_engine import router as rating_router
    app.include_router(rating_router, prefix="/api/rating")

    # Debug Router
    from app.routers import debug
    app.include_router(debug.router)

    return app

app = create_app()

@app.on_event("startup")
async def verify_bgrp_configuration():
    """Ensure BGRP rates are correctly configured before traffic is accepted."""
    try:
        from app.services.rating_engine import get_terrorism_rate_per_mille
        rate = float(get_terrorism_rate_per_mille("BGRP", occupancy_code="1001", tsi=10000000.0))
        if abs(rate - 0.07) > 0.00001:
            logger.critical(f"STARTUP FAILURE: BGRP Terrorism Rate is {rate}, expected 0.07")
            raise RuntimeError("Invalid BGRP Terrorism Rate Configuration")
        logger.info("✅ Startup Check: BGRP Terrorism Rate verified as 0.07")
    except Exception as e:
        logger.critical(f"STARTUP CHECK FAILED: {e}")
        # In production, this exception will prevent the app from starting
        raise e

Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"brand": "iRiskAssist360", "status": "running"}

@app.get("/api/manual-seed")
@limiter.limit("1/hour")
def trigger_manual_seeding(request: Request):
    """Manually trigger seeding in case deployment script fails"""
    try:
        from seed import main as seed_main
        seed_main()
        return {"success": True, "message": "Seeding executed successfully."}
    except Exception as e:
        import traceback
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}

