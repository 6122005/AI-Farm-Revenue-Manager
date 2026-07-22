export interface WeatherForecast {
  temperature: number;
  rain_probability: number;
  humidity: number;
  wind_speed: number;
  condition: string;
  source: string;
}

export interface PriceFactor {
  factor: string;
  impact_pct: number;
  impact_amount: number;
  description: string;
}

export interface SimilarBooking {
  booking_date: string;
  commercial_slot: string;
  person_count: number;
  lead_days: number;
  selling_price: number;
  season: string;
  is_weekend: boolean;
  similarity_score: number;
}

export interface PredictionRequest {
  start_datetime?: string;
  end_datetime?: string;
  booking_date?: string;
  commercial_slot: string;
  person_count: number;
  lead_days: number;
  competitor_price?: number;
}

export interface MultiSlotConsistency {
  status: 'VALID' | 'JUSTIFIED_DEVIATION' | 'AUTOMATICALLY_CORRECTED';
  predicted_12h_day: number;
  predicted_12h_night: number;
  combined_inventory_value: number;
  predicted_24h_value: number;
  difference_pct: number;
  package_discount_pct?: number;
  is_hard_floor_violated: boolean;
  historical_avg_24h_day_price?: number;
  historical_avg_24h_night_price?: number;
  historical_median_package_discount_pct?: number;
  learned_package_discount_used_pct?: number;
  slot_differentiation_verified?: boolean;
  reason: string;
}

export interface PredictionResponse {
  recommended_price: number;
  min_price: number;
  max_price: number;
  prediction_interval?: {
    min_price: number;
    max_price: number;
  };
  demand_score: number;
  confidence_score: number;
  reliability_level?: 'HIGH' | 'MEDIUM' | 'LOW';
  data_quality_score?: number;
  sample_size_used?: number;
  similar_bookings_count?: number;
  expected_occupancy_pct: number;
  commercial_slot: string;
  booking_date: string;
  start_datetime: string;
  end_datetime: string;
  duration_hours: number;
  person_count: number;
  lead_days: number;
  is_weekend: boolean;
  festival_name: string;
  competitor_price?: number;
  competitor_diff?: number;
  weather: WeatherForecast;
  price_factors: PriceFactor[];
  similar_bookings: SimilarBooking[];
  champion_model: string;
  model_path_used?: string;
  model_timestamp_used?: string;
  contributing_historical_rows?: Array<{
    row_id: string;
    booking_date: string;
    commercial_slot: string;
    person_count: number;
    lead_days: number;
    selling_price: number;
    similarity_score: number;
    contribution_note: string;
  }>;
  historical_price_explanation?: string;
  multi_slot_consistency?: MultiSlotConsistency;
  drift_status?: {
    drift_detected: boolean;
    overall_drift_score?: number;
    drifted_features?: string[];
    recommendation?: string;
  };
}

export interface ModelVersion {
  version_id: string;
  champion_name: string;
  promoted: boolean;
  metrics: {
    r2: number;
    mae: number;
    rmse: number;
    mape: number;
    prediction_interval_coverage?: number;
  };
  trained_at: string;
  artifact_path: string;
}

export interface AuditProof {
  uploaded_filename: string;
  uploaded_file_path: string;
  raw_rows_count: number;
  detected_columns: string[];
  target_column_selected: string;
  first_10_target_prices: number[];
  average_booking_price: number;
  minimum_booking_price: number;
  maximum_booking_price: number;
  slot_distribution: Record<string, number>;
  cleaned_rows_count: number;
  training_rows_count: number;
  training_started_at: string;
  training_completed_at: string;
  saved_model_filename: string;
  saved_model_path: string;
  model_creation_timestamp: string;
  loaded_prediction_model_filename: string;
  loaded_prediction_model_path: string;
  loaded_prediction_model_timestamp: string;
  timestamp_match_verified: boolean;
}

export interface DashboardSummary {
  has_data?: boolean;
  message?: string;
  total_revenue: number;
  total_bookings: number;
  average_price: number;
  occupancy_rate: number;
  peak_month: string;
  champion_model: string;
  champion_r2: number;
  monthly_revenue: Array<{ month: string; revenue: number; bookings: number }>;
  demand_heatmap: Array<Record<string, any>>;
  slot_utilization: Array<{ slot: string; bookings: number; revenue: number }>;
  top_revenue_days: Array<{ date: string; slot: string; price: number; guests: number }>;
  recent_predictions: Array<any>;
}

export interface OwnerFeedbackCreate {
  booking_date: string;
  commercial_slot: string;
  person_count: number;
  lead_days: number;
  suggested_price: number;
  action: 'ACCEPT' | 'OVERRIDE' | 'REJECT';
  override_price?: number;
  reason?: string;
}

export interface OwnerFeedbackItem extends OwnerFeedbackCreate {
  id: number;
  created_at: string;
}

export interface SlotRule {
  code: string;
  name: string;
  min_hours: number;
  max_hours: number;
  max_guests: number;
  description?: string;
  base_multiplier: number;
  is_active: boolean;
}

export interface ModelMetric {
  model_name: string;
  r2_score: number;
  mae: number;
  rmse: number;
  mape: number;
  is_champion: boolean;
  trained_at: string;
  feature_importances?: Record<string, number>;
}
