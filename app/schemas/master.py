from pydantic import BaseModel, ConfigDict

class RiskDescriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    occupancyId: int  # PRIMARY KEY from occupancies table
    riskDescription: str
    iibCode: str
    aiftSection: str
    occupancyType: str


