
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

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("irisk_backend")

def create_app():
    app = FastAPI(title="iRiskAssist360 Backend", description="Backend API for iRiskAssist360 Flutter App", version="1.0.0")

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
    app.include_router(premium_router, prefix="/api/premium")
    app.include_router(rates_router, prefix="/api/rates")
    
    # Common Data Routers
    from app.routers.common.occupancies import router as occ_router
    from app.routers.common.addons import router as addon_router
    
    app.include_router(occ_router)
    app.include_router(addon_router)

    return app

app = create_app()

Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"brand": "iRiskAssist360", "status": "running"}

@app.get("/api/manual-seed")
def trigger_manual_seeding():
    """Manually trigger seeding in case deployment script fails"""
    try:
        from seed import main as seed_main
        seed_main()
        return {"success": True, "message": "Seeding executed successfully."}
    except Exception as e:
        import traceback
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}

