from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Lot(Base):
    __tablename__ = "lots"

    id = Column(Integer, primary_key=True, index=True)
    lot_code = Column(String, unique=True, index=True, nullable=False)
    country = Column(String, nullable=False)
    farm = Column(String, nullable=False)
    warehouse = Column(String, nullable=False)
    storage_date = Column(DateTime, nullable=False)
    status = Column(String, default="conforme")
    shipped_at = Column(DateTime, nullable=True)

    measurements = relationship("Measurement", back_populates="lot")


class Measurement(Base):
    __tablename__ = "measurements"

    id = Column(Integer, primary_key=True, index=True)

    lot_id = Column(Integer, ForeignKey("lots.id"), nullable=True)

    country = Column(String, nullable=False)
    warehouse = Column(String, nullable=False)

    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)

    status = Column(String, default="OK")
    source = Column(String, nullable=False, default="iot")
    timestamp = Column(DateTime, default=datetime.utcnow)

    lot = relationship("Lot", back_populates="measurements")


class FallbackReading(Base):
    __tablename__ = "fallback_readings"

    id = Column(Integer, primary_key=True, index=True)
    country = Column(String, nullable=False)
    warehouse = Column(String, nullable=False, unique=True)
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    country = Column(String, nullable=False)
    warehouse = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)

    type = Column(String, nullable=False)
    message = Column(String, nullable=False)

    value = Column(Float, nullable=False)
    min = Column(Float, nullable=True)
    max = Column(Float, nullable=True)
