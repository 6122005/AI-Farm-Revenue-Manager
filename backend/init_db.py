from app.database import engine
from app.models.db_models import Base

Base.metadata.create_all(bind=engine)
print("DB Initialized")
