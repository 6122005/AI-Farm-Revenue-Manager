from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.api import upload, predict, dashboard, feedback, config_api, model_routes
from app.services.data_pipeline import DataPipeline, CLEAN_DATA_PATH
from app.services.prediction_engine import prediction_engine

# Initialize SQLite database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Farmhouse AI Revenue Management System API",
    description="Commercial AI Revenue Management System predicting optimal selling prices for farmhouse inventory.",
    version="2.0.0"
)

# Enable CORS for local development & frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(upload.router)
app.include_router(predict.router)
app.include_router(dashboard.router)
app.include_router(feedback.router)
app.include_router(config_api.router)
app.include_router(model_routes.router)

@app.on_event("startup")
async def startup_event():
    """
    On app startup:
    Checks if user dataset exists; if so, loads champion model.
    By default remains blank until user uploads dataset file.
    """
    if CLEAN_DATA_PATH.exists() and DataPipeline.has_user_data():
        prediction_engine.load_champion_model()

@app.get("/")
async def root():
    return {
        "status": "online",
        "app": "Farmhouse AI Revenue Management System",
        "version": "2.0.0",
        "docs_url": "/docs"
    }
