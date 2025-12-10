import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "iRiskAssist360 Backend"
    # Updated to PostgreSQL with URL-encoded password (@ -> %40)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:Uiic%40151000@localhost:5432/iriskassist360_db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "iriskassist360_secret_key")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))

settings = Settings()
