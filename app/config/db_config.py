from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from core.config import settings


engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
def reset_database():
    """Drop and recreate all tables."""
    Base.metadata.drop_all(bind=engine)  # Drop all tables
    Base.metadata.create_all(bind=engine)  # Recreate all tables
