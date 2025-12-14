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
    """
    Fetch all occupancies with complete details.
    
    Returns:
        - id: Occupancy PRIMARY KEY
        - iib_code: IIB occupancy code
        - section: AIFT section
        - occupancy_type: Type of occupancy (e.g., Residential, Commercial)
        - description: Risk description
    """
    data = db.query(Occupancy).all()
    results = [
        {
            "id": r.id, 
            "iib_code": r.iib_code, 
            "section": r.section_aift,
            "occupancy_type": r.occupancy_type,
            "description": r.risk_description
        } 
        for r in data
    ]
    return ResponseModel(success=True, message="Occupancies Fetched", data=results)

