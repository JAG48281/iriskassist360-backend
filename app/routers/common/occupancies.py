from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.fire_models import Occupancy
from app.schemas.response import ResponseModel

router = APIRouter(tags=["Common Data"])

@router.get("/api/occupancies", response_model=ResponseModel[list])
def get_occupancies(db: Session = Depends(get_db)):
    """Fetch all occupancies"""
    data = db.query(Occupancy).all()
    # Simple serialization
    results = [
        {
            "id": r.id, 
            "iib_code": r.iib_code, 
            "occupancy_type": r.occupancy_type,
            "description": r.occupancy_description
        } 
        for r in data
    ]
    return ResponseModel(success=True, message="Occupancies Fetched", data=results)
