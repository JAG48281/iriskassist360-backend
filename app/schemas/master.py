from pydantic import BaseModel

class RiskDescriptionResponse(BaseModel):
    riskDescription: str
    iibCode: str
    aiftSection: str
    occupancyType: str

    class Config:
        orm_mode = True
        from_attributes = True
