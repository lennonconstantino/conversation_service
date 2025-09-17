
import logging
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from config.settings import settings

load_dotenv()

CONFIG_DIR = Path(__file__).resolve().parent

Base = declarative_base()

# Configurar logging
logger = logging.getLogger(__name__)

class DatabaseConfig:
    def __init__(self, database_url: str, database_type="sqlite", **kwargs):
        self.database_type = database_type.lower()
        
        try:
            if self.database_type == "sqlite":
                db_path = kwargs.get("db_path", settings.DATABASE_PATH)
                self.connection_string = f"sqlite:///{db_path}"
                logger.info(f"SQLite database configured: {db_path}")
                          
            elif self.database_type == "postgresql":
                host = kwargs.get("host", "localhost")
                port = kwargs.get("port", 5432)
                database = kwargs.get("database", settings.CONVERSATION_DATABASE_NAME)
                username = kwargs.get("username", "postgres")
                password = kwargs.get("password", "")
                self.connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}"
                logger.info(f"PostgreSQL database configured: {host}:{port}/{database}")
                
            else:
                raise ValueError("Tipo de banco não suportado. Use 'sqlite' ou 'postgresql'")
                
            # Validar configuração
            self._validate_config()
            
        except Exception as e:
            logger.error(f"Error configuring database: {e}")
            raise ValueError(f"Database configuration failed: {e}")
    
    def _validate_config(self):
        """Valida a configuração do banco de dados"""
        if not self.connection_string:
            raise ValueError("Connection string cannot be empty")
        
        if self.database_type not in ["sqlite", "postgresql"]:
            raise ValueError(f"Unsupported database type: {self.database_type}")
        
        logger.debug(f"Database configuration validated: {self.database_type}")

