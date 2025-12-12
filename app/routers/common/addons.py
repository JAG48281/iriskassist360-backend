from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.fire_models import AddOnRate
from app.schemas.response import ResponseModel

router = APIRouter(tags=["Common Data"])

@router.get("/api/add-on-rates", response_model=ResponseModel[list])
def get_addon_rates(db: Session = Depends(get_db)):
    """Fetch all add-on rates with proper field names"""
    data = db.query(AddOnRate).filter(AddOnRate.active == True).all()
    results = [
        {
            "id": r.id,
            "add_on_code": r.add_on.add_on_code if r.add_on else None,
            "product_code": r.product_code,
            "rate_type": r.rate_type,
            "rate_value": str(r.rate_value),
            "occupancy_rule": r.occupancy_type
        }
        for r in data
    ]
    return ResponseModel(success=True, message="AddOn Rates Fetched", data=results)
