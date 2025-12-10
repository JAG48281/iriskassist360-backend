
# app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user_schema import UserCreate, UserOut
from app.utils.password_handler import hash_password, verify_password
from app.utils.jwt_handler import create_access_token
from app.utils.otp_handler import create_otp, verify_otp_code
from pydantic import BaseModel

from app.schemas.response import ResponseModel

router = APIRouter(prefix="/irisk/auth", tags=["Authentication"])


# --------------------------
#  USER REGISTRATION
# --------------------------
@router.post("/register", response_model=ResponseModel[UserOut])
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    # Must have at least email or mobile
    if not payload.email and not payload.mobile:
        raise HTTPException(
            status_code=400,
            detail="Provide either email or mobile"
        )

    # Check existing user by email
    if payload.email:
        email_exists = db.query(User).filter(User.email == payload.email).first()
        if email_exists:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )

    # Check existing user by mobile
    if payload.mobile:
        mobile_exists = db.query(User).filter(User.mobile == payload.mobile).first()
        if mobile_exists:
            raise HTTPException(
                status_code=400,
                detail="Mobile already registered"
            )

    user = User(
        email=payload.email,
        mobile=payload.mobile,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password) if payload.password else None
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return ResponseModel(success=True, message="User registered successfully", data=user)


# --------------------------
#  USER LOGIN
# --------------------------
@router.post("/login", response_model=ResponseModel[dict])
def login_user(payload: UserCreate, db: Session = Depends(get_db)):
    # Requirement → Login by Email + Password
    if not payload.email or not payload.password:
        raise HTTPException(
            status_code=400,
            detail="Email and password required"
        )

    user = db.query(User).filter(User.email == payload.email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    if not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password not set for this account"
        )

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    token = create_access_token({"user_id": user.id})

    data = {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "email": user.email
    }
    return ResponseModel(success=True, message="Login successful", data=data)

# --------------------------
#  OTP AUTHENTICATION
# --------------------------

class OtpRequest(BaseModel):
    mobile: str

class OtpVerifyRequest(BaseModel):
    mobile: str
    otp: str

@router.post("/send-otp", response_model=ResponseModel[dict])
def send_otp(payload: OtpRequest, db: Session = Depends(get_db)):
    # 1. Check if mobile is valid (basic check)
    if len(payload.mobile) != 10:
        raise HTTPException(status_code=400, detail="Invalid mobile number")
    
    # 2. Generate and Save OTP
    otp = create_otp(db, payload.mobile)
    
    # 3. "Send" OTP (Mock)
    print(f"OTP for {payload.mobile} is {otp}")
    
    return ResponseModel(success=True, message="OTP sent successfully", data={"mock_otp": otp})

@router.post("/verify-otp", response_model=ResponseModel[dict])
def verify_otp_endpoint(payload: OtpVerifyRequest, db: Session = Depends(get_db)):
    # 1. Verify OTP
    is_valid = verify_otp_code(db, payload.mobile, payload.otp)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
    # 2. Get or Create User
    user = db.query(User).filter(User.mobile == payload.mobile).first()
    if not user:
        # Auto-register if not exists
        user = User(mobile=payload.mobile)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # 3. Generate Token
    token = create_access_token({"user_id": user.id})
    
    data = {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "mobile": user.mobile
    }
    return ResponseModel(success=True, message="OTP verified successfully", data=data)
