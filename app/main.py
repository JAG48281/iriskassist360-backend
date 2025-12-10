
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth
from app.routers.fire import uiic_fire
from app.database import Base, engine

import os

def create_app():
    app = FastAPI(title="iRiskAssist360 Backend")

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

    app.include_router(auth.router)
    app.include_router(uiic_fire.router)

    return app

app = create_app()

Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"brand": "iRiskAssist360", "status": "running"}
