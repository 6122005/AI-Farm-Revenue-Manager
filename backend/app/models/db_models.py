from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from datetime import datetime
from app.database import Base

class BookingRecord(Base):
    __tablename__ = "booking_records"

    id = Column(Integer, primary_key=True, index=True)
    booking_date = Column(String, index=True) # YYYY-MM-DD
    commercial_slot = Column(String, index=True) # COUPLE_SLOT, 6H_SLOT, 12H_SLOT, etc.
    person_count = Column(Integer)
    lead_days = Column(Integer)
    duration_hours = Column(Float)
    selling_price = Column(Float) # Commercial slot selling price (NOT hourly)
    competitor_price = Column(Float, nullable=True)
    
    # Engineered / Contextual Features
    month = Column(Integer)
    day_of_week = Column(Integer) # 0=Monday, 6=Sunday
    is_weekend = Column(Boolean)
    is_holiday = Column(Boolean)
    is_festival = Column(Boolean)
    is_festival_eve = Column(Boolean)
    is_vacation = Column(Boolean)
    season = Column(String) # Summer, Monsoon, Winter, Peak, Off-Season
    
    # Weather
    temperature = Column(Float, nullable=True)
    rain_probability = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    weather_condition = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class SlotRule(Base):
    __tablename__ = "slot_rules"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    name = Column(String)
    min_hours = Column(Float)
    max_hours = Column(Float)
    max_guests = Column(Integer)
    description = Column(String, nullable=True)
    base_multiplier = Column(Float, default=1.0)
    is_active = Column(Boolean, default=True)

class ModelRunMetric(Base):
    __tablename__ = "model_run_metrics"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String) # XGBoost, CatBoost, LightGBM, Random Forest, Stacking
    r2_score = Column(Float)
    mae = Column(Float)
    rmse = Column(Float)
    mape = Column(Float)
    is_champion = Column(Boolean, default=False)
    trained_at = Column(DateTime, default=datetime.utcnow)
    feature_importances = Column(Text, nullable=True) # JSON string

class OwnerFeedback(Base):
    __tablename__ = "owner_feedback"

    id = Column(Integer, primary_key=True, index=True)
    booking_date = Column(String)
    commercial_slot = Column(String)
    person_count = Column(Integer)
    lead_days = Column(Integer)
    suggested_price = Column(Float)
    action = Column(String) # ACCEPT, OVERRIDE, REJECT
    override_price = Column(Float, nullable=True)
    reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
