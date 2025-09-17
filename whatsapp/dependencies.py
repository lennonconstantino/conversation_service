"""
Factory pattern para gerenciar dependências do WhatsApp service
"""
import os
from conversation.db import DatabaseConfig
from conversation.repository import ConversationRepository
from conversation.service import ConversationService
from whatsapp.whatsapp_service import WhatsappService
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

class ServiceFactory:
    """Factory singleton para criar e gerenciar instâncias de serviços"""
    
    _instance = None
    _db = None
    _repository = None
    _conversation_service = None
    _whatsapp_service = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ServiceFactory, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def get_whatsapp_service(cls) -> WhatsappService:
        """Retorna instância singleton do WhatsappService"""
        if cls._whatsapp_service is None:
            cls._db = DatabaseConfig("sqlite", db_path="conversations.db")
            cls._repository = ConversationRepository(cls._db)
            cls._conversation_service = ConversationService(cls._repository)
            cls._whatsapp_service = WhatsappService(cls._conversation_service)
        return cls._whatsapp_service
    
    @classmethod
    def get_conversation_service(cls) -> ConversationService:
        """Retorna instância singleton do ConversationService"""
        if cls._conversation_service is None:
            cls._db = DatabaseConfig("sqlite", db_path="conversations.db")
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
        cls._whatsapp_service = None
