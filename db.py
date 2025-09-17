import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

load_dotenv()

CONFIG_DIR = Path(__file__).resolve().parent

Base = declarative_base()

class DatabaseConfig:
    def __init__(self, database_url: str, database_type="sqlite", **kwargs):
        self.database_type = database_type.lower()
        
        if self.database_type == "sqlite":
            db_path = kwargs.get("db_path", "conversations.db")
            self.connection_string = f"sqlite:///{db_path}"          
        elif self.database_type == "postgresql":
            host = kwargs.get("host", "localhost")
            port = kwargs.get("port", 5432)
            database = kwargs.get("database", "kanban")
            username = kwargs.get("username", "postgres")
            password = kwargs.get("password", "")
            self.connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}"
        else:
            raise ValueError("Tipo de banco não suportado. Use 'sqlite' ou 'postgresql'")

