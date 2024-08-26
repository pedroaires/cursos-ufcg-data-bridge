from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from config.load_config import settings
import logging
    # logging.basicConfig()
    # logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
def reset_database():
    """Drop and recreate all tables."""
    session = SessionLocal()
    try:
        session.commit()  # Ensure any pending transactions are committed
        session.close()   # Close the session
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()   # Ensure session is closed even if an error occurs

    # Now drop and recreate the tables
    print("Dropping tables")
    Base.metadata.drop_all(bind=engine)
    print("Tables dropped")
    print("Creating Tables")
    Base.metadata.create_all(bind=engine)
    print("Tables created")
