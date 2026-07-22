import shutil
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse

from app.config import DATA_DIR, MODELS_DIR
from app.models.schemas import ColumnMappingRequest, ValidationReportResponse
from app.services.data_pipeline import DataPipeline, SAMPLE_EXCEL_PATH, CLEAN_DATA_PATH
from app.services.ml_trainer import MLTrainer, CHAMPION_MODEL_PATH
from app.services.prediction_engine import prediction_engine

router = APIRouter(prefix="/api/upload", tags=["Upload Validation Wizard"])

@router.post("/preview")
async def preview_upload_file(file: UploadFile = File(...)):
    """
    Step 1: Upload Excel/CSV file to preview columns & sample rows.
    Training is NOT started automatically!
    """
    if not file.filename.endswith((".xlsx", ".xls", ".csv")):
        raise HTTPException(status_code=400, detail="Only Excel (.xlsx, .xls) or CSV files are supported.")

    temp_filename = f"preview_{file.filename}"
    temp_path = DATA_DIR / temp_filename

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        df = DataPipeline.load_raw_dataframe(temp_path)
        if df.empty:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        columns = [str(c) for c in df.columns]
        
        suggested_price = next((c for c in columns if any(k in c.lower() for k in ["selling_price", "price", "rent", "farm_price", "booked_price", "booking_amount"])), columns[0])
        suggested_date = next((c for c in columns if any(k in c.lower() for k in ["date", "check_in", "booking_date", "checkin"])), columns[0])
        suggested_slot = next((c for c in columns if any(k in c.lower() for k in ["slot", "timing", "type"])), None)
        suggested_guests = next((c for c in columns if any(k in c.lower() for k in ["guest", "person", "pax", "count"])), None)

        preview_rows = df.head(5).fillna("").to_dict(orient="records")

        return {
            "status": "success",
            "temp_filename": temp_filename,
            "columns": columns,
            "total_rows": len(df),
            "suggested": {
                "price_col": suggested_price,
                "date_col": suggested_date,
                "slot_col": suggested_slot,
                "guests_col": suggested_guests
            },
            "preview_data": preview_rows
        }
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to preview dataset: {str(e)}")

@router.post("/validate", response_model=ValidationReportResponse)
async def validate_dataset_mapping(mapping: ColumnMappingRequest):
    """
    Step 2: Generate Dataset Health Report & Price Sanity Check using selected columns.
    """
    temp_path = DATA_DIR / mapping.temp_filename
    if not temp_path.exists():
        raise HTTPException(status_code=404, detail="Uploaded temporary preview file expired or not found. Please upload again.")

    try:
        df = DataPipeline.load_raw_dataframe(temp_path)
        
        if mapping.price_col not in df.columns:
            raise HTTPException(status_code=400, detail=f"Price column '{mapping.price_col}' not found.")
        if mapping.date_col not in df.columns:
            raise HTTPException(status_code=400, detail=f"Date column '{mapping.date_col}' not found.")

        prices = pd.to_numeric(df[mapping.price_col], errors="coerce").dropna()
        prices = prices[prices > 0]

        if prices.empty:
            raise HTTPException(status_code=400, detail="No valid positive numerical prices found in selected column.")

        price_mean = float(prices.mean())
        price_median = float(prices.median())
        price_min = float(prices.min())
        price_max = float(prices.max())

        is_suspicious = False
        warning_msg = None
        if price_mean > 50000.0 or price_median > 45000.0:
            is_suspicious = True
            warning_msg = f"⚠️ Price Sanity Alert: Average booking price (₹{price_mean:,.0f}) appears unusually high for a standard farmhouse slot. Verify that '{mapping.price_col}' is individual booking price and not total revenue or non-currency metric."
        elif price_min < 500.0:
            is_suspicious = True
            warning_msg = f"⚠️ Price Sanity Alert: Minimum booking price (₹{price_min:,.0f}) is below standard operational thresholds."

        dates = pd.to_datetime(df[mapping.date_col], errors="coerce").dropna()
        date_start = dates.min().strftime("%Y-%m-%d") if not dates.empty else "N/A"
        date_end = dates.max().strftime("%Y-%m-%d") if not dates.empty else "N/A"

        slot_dist = {}
        if mapping.slot_col and mapping.slot_col in df.columns:
            slot_counts = df[mapping.slot_col].astype(str).value_counts().to_dict()
            slot_dist = {str(k): int(v) for k, v in slot_counts.items()}
        else:
            slot_dist = {"12H_DAY": len(df)}

        total_rows = len(df)
        clean_rows = len(prices)
        missing_count = int(df[[mapping.price_col, mapping.date_col]].isna().sum().sum())
        duplicate_rows = int(df.duplicated().sum())

        preview = df.head(5).fillna("").to_dict(orient="records")

        return ValidationReportResponse(
            temp_filename=mapping.temp_filename,
            total_rows=total_rows,
            clean_rows=clean_rows,
            duplicate_rows=duplicate_rows,
            missing_count=missing_count,
            price_mean=round(price_mean, 2),
            price_median=round(price_median, 2),
            price_min=round(price_min, 2),
            price_max=round(price_max, 2),
            is_price_suspicious=is_suspicious,
            warning_message=warning_msg,
            date_start=date_start,
            date_end=date_end,
            slot_distribution=slot_dist,
            preview_data=preview
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@router.post("/confirm-and-train")
async def confirm_mapping_and_train_models(mapping: ColumnMappingRequest):
    """
    Step 3: Owner confirms manual column mapping & sanity report.
    Executes full 17-item transparency audit & timestamp integrity assertion.
    """
    temp_path = DATA_DIR / mapping.temp_filename
    if not temp_path.exists():
        raise HTTPException(status_code=404, detail="Preview file expired. Please re-upload dataset.")

    try:
        raw_df = DataPipeline.load_raw_dataframe(temp_path)
        raw_rows_count = len(raw_df)
        detected_columns = [str(c) for c in raw_df.columns]
        
        raw_target_prices = pd.to_numeric(raw_df[mapping.price_col], errors="coerce").dropna().tolist()
        first_10_target_prices = [float(p) for p in raw_target_prices[:10]]

        # 1. Process and clean dataframe with confirmed explicit mappings
        enriched_df = DataPipeline.process_with_explicit_mapping(
            file_path=temp_path,
            price_col=mapping.price_col,
            date_col=mapping.date_col,
            slot_col=mapping.slot_col,
            guests_col=mapping.guests_col,
            lead_col=mapping.lead_col,
            competitor_col=mapping.competitor_col
        )

        cleaned_rows_count = len(enriched_df)
        clean_prices = pd.to_numeric(enriched_df["selling_price"], errors="coerce").dropna()
        avg_price = float(clean_prices.mean()) if not clean_prices.empty else 0.0
        min_price = float(clean_prices.min()) if not clean_prices.empty else 0.0
        max_price = float(clean_prices.max()) if not clean_prices.empty else 0.0

        slot_dist = enriched_df["commercial_slot"].value_counts().to_dict()
        slot_dist_clean = {str(k): int(v) for k, v in slot_dist.items()}

        # 2. Train models (Purges old model cache & records timestamps)
        champion_artifact = MLTrainer.train_and_select_champion(enriched_df)
        
        saved_model_path = str(CHAMPION_MODEL_PATH.absolute())
        model_creation_timestamp = champion_artifact.get("trained_at", datetime.now().isoformat())
        training_started_at = champion_artifact.get("training_started_at", model_creation_timestamp)

        # 3. Force reload champion model in prediction engine
        prediction_engine.reload_model()

        loaded_model_path = prediction_engine.loaded_model_path
        loaded_model_timestamp = prediction_engine.loaded_model_timestamp

        # 4. STRICT TIMESTAMP & PATH INTEGRITY ASSERTION
        if loaded_model_timestamp != model_creation_timestamp:
            raise ValueError(f"TIMESTAMP MISMATCH ERROR: Prediction engine loaded timestamp '{loaded_model_timestamp}' does not match newly trained model timestamp '{model_creation_timestamp}'!")

        print(f"\n=======================================================")
        print(f"📊 FULL TRANSPARENCY UPLOAD AUDIT PROOF REPORT")
        print(f"=======================================================")
        print(f"Absolute Path of Uploaded File: {temp_path.absolute()}")
        print(f"Absolute Path of Model Saved: {saved_model_path}")
        print(f"Absolute Path of Prediction Model Loaded: {loaded_model_path}")
        print(f"-------------------------------------------------------")
        print(f"1. Uploaded Filename: {mapping.temp_filename}")
        print(f"2. Number of Rows Loaded: {raw_rows_count}")
        print(f"3. Column Names Detected: {detected_columns}")
        print(f"4. Target Column Selected: '{mapping.price_col}'")
        print(f"5. First 10 Values from Target Price Column: {first_10_target_prices}")
        print(f"6. Average Booking Price: ₹{avg_price:,.2f}")
        print(f"7. Minimum Booking Price: ₹{min_price:,.2f}")
        print(f"8. Maximum Booking Price: ₹{max_price:,.2f}")
        print(f"9. Number of Bookings per Commercial Slot: {slot_dist_clean}")
        print(f"10. Number of Bookings after Cleaning: {cleaned_rows_count}")
        print(f"11. Number of Rows Used for Model Training: {cleaned_rows_count}")
        print(f"12. Training Started: {training_started_at}")
        print(f"13. Training Completed: {model_creation_timestamp}")
        print(f"14. Saved Model Filename: {CHAMPION_MODEL_PATH.name}")
        print(f"15. Model Creation Timestamp: {model_creation_timestamp}")
        print(f"16. Prediction Model Filename Currently Loaded: {Path(loaded_model_path).name if loaded_model_path else 'N/A'}")
        print(f"17. Prediction Model Timestamp: {loaded_model_timestamp}")
        print(f"✅ Timestamp Match Verified: TRUE")
        print(f"=======================================================\n")

        return {
            "status": "success",
            "message": f"Successfully trained models on '{cleaned_rows_count}' validated records! Champion: '{champion_artifact['champion_name']}'.",
            "champion_model": champion_artifact["champion_name"],
            "r2_score": champion_artifact["metrics"]["r2"],
            "mae": champion_artifact["metrics"]["mae"],
            "audit_proof": {
                "uploaded_filename": mapping.temp_filename,
                "uploaded_file_path": str(temp_path.absolute()),
                "raw_rows_count": raw_rows_count,
                "detected_columns": detected_columns,
                "target_column_selected": mapping.price_col,
                "first_10_target_prices": first_10_target_prices,
                "average_booking_price": round(avg_price, 2),
                "minimum_booking_price": round(min_price, 2),
                "maximum_booking_price": round(max_price, 2),
                "slot_distribution": slot_dist_clean,
                "cleaned_rows_count": cleaned_rows_count,
                "training_rows_count": cleaned_rows_count,
                "training_started_at": training_started_at,
                "training_completed_at": model_creation_timestamp,
                "saved_model_filename": CHAMPION_MODEL_PATH.name,
                "saved_model_path": saved_model_path,
                "model_creation_timestamp": model_creation_timestamp,
                "loaded_prediction_model_filename": Path(loaded_model_path).name if loaded_model_path else "N/A",
                "loaded_prediction_model_path": loaded_model_path,
                "loaded_prediction_model_timestamp": loaded_model_timestamp,
                "timestamp_match_verified": True
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to train models: {str(e)}")
    finally:
        if temp_path.exists():
            temp_path.unlink()

@router.post("")
@router.post("/")
async def upload_booking_dataset_direct(file: UploadFile = File(...)):
    if not file.filename.endswith((".xlsx", ".xls", ".csv")):
        raise HTTPException(status_code=400, detail="Only Excel (.xlsx, .xls) or CSV files are supported.")

    temp_path = DATA_DIR / f"uploaded_{file.filename}"
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        raw_df = DataPipeline.load_raw_dataframe(temp_path)
        raw_rows_count = len(raw_df)
        detected_columns = [str(c) for c in raw_df.columns]

        price_col = next((c for c in detected_columns if any(k in c.lower() for k in ["selling_price", "price", "rent", "farm_price", "booked_price", "booking_amount"])), detected_columns[0])
        raw_target_prices = pd.to_numeric(raw_df[price_col], errors="coerce").dropna().tolist()
        first_10_target_prices = [float(p) for p in raw_target_prices[:10]]

        enriched_df = DataPipeline.load_and_process_file(temp_path)
        cleaned_rows_count = len(enriched_df)
        clean_prices = pd.to_numeric(enriched_df["selling_price"], errors="coerce").dropna()
        avg_price = float(clean_prices.mean()) if not clean_prices.empty else 0.0
        min_price = float(clean_prices.min()) if not clean_prices.empty else 0.0
        max_price = float(clean_prices.max()) if not clean_prices.empty else 0.0

        slot_dist = enriched_df["commercial_slot"].value_counts().to_dict()
        slot_dist_clean = {str(k): int(v) for k, v in slot_dist.items()}

        champion_artifact = MLTrainer.train_and_select_champion(enriched_df)
        saved_model_path = str(CHAMPION_MODEL_PATH.absolute())
        model_creation_timestamp = champion_artifact.get("trained_at", datetime.now().isoformat())
        training_started_at = champion_artifact.get("training_started_at", model_creation_timestamp)

        prediction_engine.reload_model()
        loaded_model_path = prediction_engine.loaded_model_path
        loaded_model_timestamp = prediction_engine.loaded_model_timestamp

        if loaded_model_timestamp != model_creation_timestamp:
            raise ValueError(f"TIMESTAMP MISMATCH ERROR: Prediction engine loaded timestamp '{loaded_model_timestamp}' does not match newly trained model timestamp '{model_creation_timestamp}'!")

        print(f"\n=======================================================")
        print(f"📊 FULL TRANSPARENCY UPLOAD AUDIT PROOF REPORT (DIRECT)")
        print(f"=======================================================")
        print(f"Absolute Path of Uploaded File: {temp_path.absolute()}")
        print(f"Absolute Path of Model Saved: {saved_model_path}")
        print(f"Absolute Path of Prediction Model Loaded: {loaded_model_path}")
        print(f"-------------------------------------------------------")
        print(f"1. Uploaded Filename: {file.filename}")
        print(f"2. Number of Rows Loaded: {raw_rows_count}")
        print(f"3. Column Names Detected: {detected_columns}")
        print(f"4. Target Column Selected: '{price_col}'")
        print(f"5. First 10 Values from Target Price Column: {first_10_target_prices}")
        print(f"6. Average Booking Price: ₹{avg_price:,.2f}")
        print(f"7. Minimum Booking Price: ₹{min_price:,.2f}")
        print(f"8. Maximum Booking Price: ₹{max_price:,.2f}")
        print(f"9. Number of Bookings per Commercial Slot: {slot_dist_clean}")
        print(f"10. Number of Bookings after Cleaning: {cleaned_rows_count}")
        print(f"11. Number of Rows Used for Model Training: {cleaned_rows_count}")
        print(f"12. Training Started: {training_started_at}")
        print(f"13. Training Completed: {model_creation_timestamp}")
        print(f"14. Saved Model Filename: {CHAMPION_MODEL_PATH.name}")
        print(f"15. Model Creation Timestamp: {model_creation_timestamp}")
        print(f"16. Prediction Model Filename Currently Loaded: {Path(loaded_model_path).name if loaded_model_path else 'N/A'}")
        print(f"17. Prediction Model Timestamp: {loaded_model_timestamp}")
        print(f"✅ Timestamp Match Verified: TRUE")
        print(f"=======================================================\n")

        return {
            "status": "success",
            "message": f"Successfully processed '{file.filename}', cleaned {cleaned_rows_count} records, and trained champion model '{champion_artifact['champion_name']}'.",
            "champion_model": champion_artifact["champion_name"],
            "r2_score": champion_artifact["metrics"]["r2"],
            "mae": champion_artifact["metrics"]["mae"],
            "record_count": cleaned_rows_count,
            "audit_proof": {
                "uploaded_filename": file.filename,
                "uploaded_file_path": str(temp_path.absolute()),
                "raw_rows_count": raw_rows_count,
                "detected_columns": detected_columns,
                "target_column_selected": price_col,
                "first_10_target_prices": first_10_target_prices,
                "average_booking_price": round(avg_price, 2),
                "minimum_booking_price": round(min_price, 2),
                "maximum_booking_price": round(max_price, 2),
                "slot_distribution": slot_dist_clean,
                "cleaned_rows_count": cleaned_rows_count,
                "training_rows_count": cleaned_rows_count,
                "training_started_at": training_started_at,
                "training_completed_at": model_creation_timestamp,
                "saved_model_filename": CHAMPION_MODEL_PATH.name,
                "saved_model_path": saved_model_path,
                "model_creation_timestamp": model_creation_timestamp,
                "loaded_prediction_model_filename": Path(loaded_model_path).name if loaded_model_path else "N/A",
                "loaded_prediction_model_path": loaded_model_path,
                "loaded_prediction_model_timestamp": loaded_model_timestamp,
                "timestamp_match_verified": True
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process dataset: {str(e)}")
    finally:
        if temp_path.exists():
            temp_path.unlink()

@router.get("/sample-excel")
async def download_sample_excel():
    if not SAMPLE_EXCEL_PATH.exists():
        DataPipeline.generate_synthetic_historical_data(500)

    return FileResponse(
        path=SAMPLE_EXCEL_PATH,
        filename="Farm_Booking_Data_Sample.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
