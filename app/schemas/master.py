from pydantic import BaseModel, ConfigDict

class RiskDescriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    occupancyId: int
    occupancyCode: str
    occupancyDescription: str
    occupancyType: str
    aiftSection: str


