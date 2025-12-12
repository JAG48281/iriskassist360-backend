from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.fire_models import Occupancy
from app.schemas.response import ResponseModel

router = APIRouter(tags=["Common Data"])

from fastapi import Request
from app.limiter import limiter

@router.get("/api/occupancies", response_model=ResponseModel[list])
@limiter.limit("60/minute")
def get_occupancies(request: Request, db: Session = Depends(get_db)):
    """Fetch all occupancies"""
    data = db.query(Occupancy).all()
    # Return with correct field names
    results = [
        {
            "id": r.id, 
            "iib_code": r.iib_code, 
            "section": r.section_aift,
            "description": r.occupancy_description
        } 
        for r in data
    ]
    return ResponseModel(success=True, message="Occupancies Fetched", data=results)
