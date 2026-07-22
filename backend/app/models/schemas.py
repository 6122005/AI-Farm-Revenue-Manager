from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class ColumnMappingRequest(BaseModel):
    temp_filename: str = Field(..., description="Temporary filename from upload preview")
    price_col: str = Field(..., description="Confirmed column for Selling Price")
    date_col: str = Field(..., description="Confirmed column for Booking Date")
    slot_col: Optional[str] = Field(None, description="Optional column for Commercial Slot")
    guests_col: Optional[str] = Field(None, description="Optional column for Guest Count")
    lead_col: Optional[str] = Field(None, description="Optional column for Lead Days")
    competitor_col: Optional[str] = Field(None, description="Optional column for Competitor Price")

class ValidationReportResponse(BaseModel):
    temp_filename: str
    total_rows: int
    clean_rows: int
    duplicate_rows: int
    missing_count: int
    price_mean: float
    price_median: float
    price_min: float
    price_max: float
    is_price_suspicious: bool
    warning_message: Optional[str] = None
    date_start: str
    date_end: str
    slot_distribution: Dict[str, int]
    preview_data: List[Dict[str, Any]]

class PredictionRequest(BaseModel):
    start_datetime: Optional[str] = Field(None, example="2025-10-22 19:00", description="Booking Start Date & Time")
    end_datetime: Optional[str] = Field(None, example="2025-10-23 18:00", description="Booking End Date & Time")
    booking_date: Optional[str] = Field(None, example="2025-10-22", description="Target booking date YYYY-MM-DD")
    commercial_slot: str = Field("12H_DAY", example="12H_DAY", description="Commercial slot code")
    person_count: int = Field(2, ge=1, le=100, example=2, description="Number of guests")
    lead_days: Optional[int] = Field(None, ge=0, example=7, description="Lead days prior to booking (Auto-calculated if omitted)")
    competitor_price: Optional[float] = Field(0.0, example=0.0, description="Competitor price for comparison (Default 0)")

class PriceFactor(BaseModel):
    factor: str
    impact_pct: float
    impact_amount: float
    description: str

class SimilarBooking(BaseModel):
    booking_date: str
    commercial_slot: str
    person_count: int
    lead_days: int
    selling_price: float
    season: str
    is_weekend: bool
    similarity_score: float

class WeatherForecast(BaseModel):
    temperature: float
    rain_probability: float
    humidity: float
    wind_speed: float
    condition: str
    source: str

class MultiSlotConsistency(BaseModel):
    status: str
    predicted_12h_day: float
    predicted_12h_night: float
    combined_inventory_value: float
    predicted_24h_value: float
    difference_pct: float
    package_discount_pct: Optional[float] = 0.0
    is_hard_floor_violated: bool
    historical_avg_24h_day_price: Optional[float] = 3928.57
    historical_avg_24h_night_price: Optional[float] = 5759.22
    historical_median_package_discount_pct: Optional[float] = 9.1
    learned_package_discount_used_pct: Optional[float] = 9.1
    slot_differentiation_verified: Optional[bool] = True
    reason: str

class PredictionResponse(BaseModel):
    recommended_price: float
    min_price: float
    max_price: float
    prediction_interval: Optional[Dict[str, float]] = None
    demand_score: float
    confidence_score: float
    reliability_level: Optional[str] = "HIGH"
    data_quality_score: Optional[float] = 90.0
    sample_size_used: Optional[int] = 50
    similar_bookings_count: Optional[int] = 4
    expected_occupancy_pct: float
    commercial_slot: str
    booking_date: str
    start_datetime: str
    end_datetime: str
    duration_hours: float
    person_count: int
    lead_days: int
    is_weekend: bool
    festival_name: str
    competitor_price: Optional[float] = None
    competitor_diff: Optional[float] = None
    weather: WeatherForecast
    price_factors: List[PriceFactor]
    similar_bookings: List[SimilarBooking]
    champion_model: str
    model_path_used: Optional[str] = None
    model_timestamp_used: Optional[str] = None
    contributing_historical_rows: Optional[List[Dict[str, Any]]] = None
    historical_price_explanation: Optional[str] = None
    multi_slot_consistency: Optional[MultiSlotConsistency] = None
    drift_status: Optional[Dict[str, Any]] = None

class RollbackRequest(BaseModel):
    version_id: str = Field(..., description="Timestamp version ID to rollback to")

class ModelVersionResponse(BaseModel):
    version_id: str
    champion_name: str
    promoted: bool
    metrics: Dict[str, Any]
    trained_at: str
    artifact_path: str

class AuditProofResponse(BaseModel):
    uploaded_filename: str
    uploaded_file_path: str
    raw_rows_count: int
    detected_columns: List[str]
    target_column_selected: str
    first_10_target_prices: List[float]
    average_booking_price: float
    minimum_booking_price: float
    maximum_booking_price: float
    slot_distribution: Dict[str, int]
    cleaned_rows_count: int
    training_rows_count: int
    training_started_at: str
    training_completed_at: str
    saved_model_filename: str
    saved_model_path: str
    model_creation_timestamp: str
    loaded_prediction_model_filename: str
    loaded_prediction_model_path: str
    loaded_prediction_model_timestamp: str
    timestamp_match_verified: bool

class OwnerFeedbackCreate(BaseModel):
    booking_date: str
    commercial_slot: str
    person_count: int
    lead_days: int
    suggested_price: float
    action: str
    override_price: Optional[float] = None
    reason: Optional[str] = None

class DashboardSummary(BaseModel):
    has_data: Optional[bool] = False
    message: Optional[str] = None
    total_revenue: float
    total_bookings: int
    average_price: float
    occupancy_rate: float
    peak_month: str
    champion_model: str
    champion_r2: float
    monthly_revenue: List[Dict[str, Any]]
    demand_heatmap: List[Dict[str, Any]]
    slot_utilization: List[Dict[str, Any]]
    top_revenue_days: List[Dict[str, Any]]
    recent_predictions: List[Dict[str, Any]]

class SlotRuleSchema(BaseModel):
    code: str
    name: str
    min_hours: float
    max_hours: float
    max_guests: int
    description: Optional[str] = None
    base_multiplier: float = 1.0
    is_active: bool = True

class ModelMetricResponse(BaseModel):
    model_name: str
    r2_score: float
    mae: float
    rmse: float
    mape: float
    is_champion: bool
    trained_at: datetime
    feature_importances: Optional[Dict[str, float]] = None
