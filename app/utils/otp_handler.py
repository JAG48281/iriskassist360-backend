import random
import string
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.otp import Otp

def generate_otp(length=4):
    return ''.join(random.choices(string.digits, k=length))

def create_otp(db: Session, mobile: str):
    otp_code = generate_otp()
    # 5 minutes expiry
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    
    # Check if entry exists
    db_otp = db.query(Otp).filter(Otp.mobile == mobile).first()
    if db_otp:
        db_otp.otp_code = otp_code
        db_otp.expires_at = expires_at
    else:
        db_otp = Otp(mobile=mobile, otp_code=otp_code, expires_at=expires_at)
        db.add(db_otp)
    
    db.commit()
    db.refresh(db_otp)
    return otp_code

def verify_otp_code(db: Session, mobile: str, otp_code: str):
    db_otp = db.query(Otp).filter(Otp.mobile == mobile).first()
    if not db_otp:
        return False
    
    if db_otp.otp_code != otp_code:
        return False
        
    if db_otp.expires_at < datetime.utcnow():
        return False
        
    return True
