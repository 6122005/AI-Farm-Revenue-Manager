from app.database import engine
from app.models.db_models import PredictionLog

PredictionLog.__table__.drop(engine, checkfirst=True)
PredictionLog.__table__.create(engine, checkfirst=True)
print("Recreated PredictionLog table.")
