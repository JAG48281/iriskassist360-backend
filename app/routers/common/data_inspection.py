from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.models.fire_models import ProductBasicRate, StfiRate, EqRate, TerrorismSlab, AddOnMaster, AddOnProductMap
from app.schemas.response import ResponseModel

router = APIRouter(tags=["Internal Data"])

@router.get("/api/product-basic-rates", response_model=ResponseModel[list])
def get_basic_rates(db: Session = Depends(get_db)):
    # Limit to 100 to prevent massive payload
    data = db.query(ProductBasicRate).limit(100).all()
    res = [{"id": r.id, "product_id": r.product_id, "rate": r.basic_rate} for r in data]
    return ResponseModel(success=True, message="Basic Rates (First 100)", data=res)

@router.get("/api/stfi-rates", response_model=ResponseModel[list])
def get_stfi_rates(db: Session = Depends(get_db)):
    data = db.query(StfiRate).limit(100).all()
    res = [{"id": r.id, "product_id": r.product_id, "rate": r.stfi_rate} for r in data]
    return ResponseModel(success=True, message="STFI Rates (First 100)", data=res)

@router.get("/api/eq-rates", response_model=ResponseModel[list])
def get_eq_rates(db: Session = Depends(get_db)):
    data = db.query(EqRate).limit(100).all()
    res = [{"id": r.id, "product_id": r.product_id, "zone": r.eq_zone, "rate": r.eq_rate} for r in data]
    return ResponseModel(success=True, message="EQ Rates (First 100)", data=res)

@router.get("/api/terrorism-slabs", response_model=ResponseModel[list])
def get_terr_slabs(db: Session = Depends(get_db)):
    data = db.query(TerrorismSlab).all()
    res = [{"id": r.id, "product_id": r.product_id, "min": r.si_min, "rate": r.rate_per_mille} for r in data]
    return ResponseModel(success=True, message="Terrorism Slabs", data=res)

@router.get("/api/add-on-master", response_model=ResponseModel[list])
def get_addon_master(db: Session = Depends(get_db)):
    data = db.query(AddOnMaster).all()
    res = [{"code": r.add_on_code, "name": r.add_on_name} for r in data]
    return ResponseModel(success=True, message="AddOn Master", data=res)

@router.get("/api/add-on-product-map", response_model=ResponseModel[list])
def get_addon_map(db: Session = Depends(get_db)):
    data = db.query(AddOnProductMap).limit(100).all()
    res = [{"product_code": r.product_code, "add_on_id": r.add_on_id} for r in data]
    return ResponseModel(success=True, message="AddOn Map (First 100)", data=res)
