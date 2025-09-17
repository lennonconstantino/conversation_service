"""
Factory pattern para gerenciar dependências do Weblocal service
"""
import os
from conversation.db import DatabaseConfig
from conversation.repository import ConversationRepository
from conversation.service import ConversationService
from weblocal.weblocal_service import WeblocalService
from config.settings import settings

class WeblocalServiceFactory:
    """Factory singleton para criar e gerenciar instâncias de serviços weblocal"""
    
    _instance = None
    _db = None
    _repository = None
    _conversation_service = None
    _weblocal_service = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(WeblocalServiceFactory, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def get_weblocal_service(cls, db_path: str = None) -> WeblocalService:
        """Retorna instância singleton do WeblocalService"""
        if cls._weblocal_service is None or db_path:
            db_path = db_path or settings.DATABASE_PATH
            cls._db = DatabaseConfig("sqlite", db_path=db_path)
            cls._repository = ConversationRepository(cls._db)
            cls._conversation_service = ConversationService(cls._repository)
            cls._weblocal_service = WeblocalService(cls._conversation_service)
        return cls._weblocal_service
    
    @classmethod
    def get_conversation_service(cls, db_path: str = None) -> ConversationService:
        """Retorna instância singleton do ConversationService"""
        if cls._conversation_service is None or db_path:
            db_path = db_path or settings.DATABASE_PATH
            cls._db = DatabaseConfig("sqlite", db_path=db_path)
            cls._repository = ConversationRepository(cls._db)
            cls._conversation_service = ConversationService(cls._repository)
        return cls._conversation_service
    
    @classmethod
    def reset(cls):
        """Reset das instâncias (útil para testes)"""
        cls._instance = None
        cls._db = None
        cls._repository = None
        cls._conversation_service = None
        cls._weblocal_service = None
