import datetime
import os
import logging
import subprocess

from urllib.parse import urlparse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from config.load_config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def backup_database():
    logger.info("Iniciando processo de backup do BD")
    DATABASE_URL = os.getenv("DATABASE_URL")
    url = urlparse(DATABASE_URL)

    db_user = url.username
    db_password = url.password
    db_host = url.hostname
    db_port = url.port
    db_name = url.path.lstrip("/")


    backup_folder = "./backups"
    os.makedirs(backup_folder, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    backup_file_path = os.path.join(backup_folder, f"backup_{timestamp}.sql")

    backup_command = [
        "mysqldump",
        "-h", db_host,
        "-P", str(db_port),
        "-u", db_user,
        "--password={}".format(db_password),
        db_name,
        "--result-file", backup_file_path
    ]

    try:
        result = subprocess.run(backup_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if "Access denied" in result.stderr:
            logger.error(f"Falha no backup por erro de acesso negado: {result.stderr}")
            return False

        logger.info(f"Backup created successfully at {backup_file_path}")
        return True  
    except subprocess.CalledProcessError as e:
        logger.error(f"Um erro ocorreu ao efetuar o backup {e}")
        return False

def reset_database():
    """Remove e cria as tabelas"""
    session = SessionLocal()
    
    logger.info(msg='Iniciando reset do BD')
    Base.metadata.drop_all(bind=engine)
    logger.info(msg='Tabelas deletadas')
    logger.info(msg='Criando tabelas...')
    Base.metadata.create_all(bind=engine)
    logger.info(msg='Tabelas criadas')
