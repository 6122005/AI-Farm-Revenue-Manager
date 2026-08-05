from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from datetime import datetime
from app.database import Base

class BookingRecord(Base):
    __tablename__ = "booking_records"

    id = Column(Integer, primary_key=True, index=True)
    booking_date = Column(String, index=True) # YYYY-MM-DD
    slot_type = Column(String, index=True) # 12H Day, 12H Night, 24H Day, 24H Night
    person_count = Column(Integer)
    is_couple = Column(Boolean, default=False)
    extended_stay = Column(Boolean, default=False)
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
    slot_type = Column(String)
    person_count = Column(Integer)
    lead_days = Column(Integer)
    suggested_price = Column(Float)
    action = Column(String) # ACCEPT, OVERRIDE, REJECT
    override_price = Column(Float, nullable=True)
    status = Column(String) # OPEN, RESOLVED, REJECTED
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

class PredictionLog(Base):
    __tablename__ = "prediction_logs"

    id = Column(Integer, primary_key=True, index=True)
    prediction_timestamp = Column(DateTime, default=datetime.utcnow)
    booking_date = Column(String, index=True)
    booking_created_date = Column(String, nullable=True) # Mocked or inferred from lead days
    arrival_date = Column(String, nullable=True)
    month = Column(Integer)
    is_weekend = Column(Boolean)
    is_festival = Column(Boolean)
    is_vacation = Column(Boolean)
    commercial_slot = Column(String)
    person_count = Column(Integer)
    lead_days = Column(Integer)
    
    rag_median_price = Column(Float)
    shadow_ml_price = Column(Float)
    final_price = Column(Float)
    
    actual_selling_price = Column(Float, nullable=True)
    booking_status = Column(String, nullable=True) # Booked / Rejected / Negotiated
    negotiated_price = Column(Float, nullable=True)
    discount_given = Column(Float, nullable=True)
    booking_time = Column(DateTime, nullable=True)
    
    model_version = Column(String, nullable=True)
    feature_version = Column(String, nullable=True)
    business_rules_version = Column(String, nullable=True)
    
    prediction_confidence = Column(Float, nullable=True)
    
    validation_status = Column(String, default="PENDING") # PENDING, VALIDATED
    
    abs_error_rag = Column(Float, nullable=True)
    abs_error_ml = Column(Float, nullable=True)
    winning_model = Column(String, nullable=True) # RAG or ML
    created_at = Column(DateTime, default=datetime.utcnow)

class LeadDaysRule(Base):
    __tablename__ = "lead_days_rules"

    id = Column(Integer, primary_key=True, index=True)
    min_days = Column(Integer, index=True)
    max_days = Column(Integer, index=True) # e.g. 9999 for infinity
    adjustment_pct = Column(Float) # percentage, e.g. 20.0 for +20%
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

class SystemSetting(Base):
    __tablename__ = "system_settings"

    key = Column(String, primary_key=True, index=True)
    value = Column(String)
    description = Column(String, nullable=True)
