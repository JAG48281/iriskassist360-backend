from fastapi import APIRouter, HTTPException
from app.schemas.rating_engine import RatingRequest, RatingResponse
from app.services.rating_engine import RatingService

router = APIRouter(tags=["Rating Engine"])

@router.post("/calculate", response_model=RatingResponse)
async def calculate_premium(request: RatingRequest):
    try:
        return RatingService.calculate_premium(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
