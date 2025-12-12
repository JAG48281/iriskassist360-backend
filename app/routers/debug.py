from fastapi import APIRouter, Request
from app.schemas.response import ResponseModel
from app.limiter import limiter

router = APIRouter(tags=["Debug"])

@router.get("/api/debug/rate-limit-check", response_model=ResponseModel[dict])
@limiter.limit("1/minute")
def rate_limit_check(request: Request):
    """
    Debug endpoint with strict 1/minute limit to verify rate limiting 
    in multi-worker environments.
    """
    return ResponseModel(
        success=True, 
        message="Request allowed", 
        data={"client_host": request.client.host}
    )
