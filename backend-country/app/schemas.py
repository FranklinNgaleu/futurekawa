from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class LotCreate(BaseModel):
    lot_code: str
    country: str
    farm: str
    warehouse: str
    storage_date: datetime

class LotResponse(LotCreate):
    id: int
    status: str

    class Config:
        from_attributes = True

class MeasurementCreate(BaseModel):
    lot_id: int
    temperature: float
    humidity: float
    timestamp: Optional[datetime] = None

class MeasurementResponse(MeasurementCreate):
    id: int

    class Config:
        from_attributes = True

class AlertResponse(BaseModel):
    id: int
    country: str
    warehouse: str
    timestamp: datetime
    type: str
    message: str
    value: float
    min: Optional[float] = None
    max: Optional[float] = None

    class Config:
        from_attributes = True