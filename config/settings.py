"""
Configurações centralizadas do projeto
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

class Settings:
    """Configurações centralizadas do projeto"""
    
    # WhatsApp API
    VERIFICATION_TOKEN: str = os.getenv("VERIFICATION_TOKEN", "")
    WHATSAPP_API_TOKEN: str = os.getenv("WHATSAPP_API_TOKEN", "")
    MY_BUSINESS_TELEPHONE: str = os.getenv("MY_BUSINESS_TELEPHONE", "")
    
    # Aplicação
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    IS_DEV_ENVIRONMENT: bool = os.getenv("IS_DEV_ENVIRONMENT", "True").lower() == "true"
    
    # Mensagens
    MESSAGE_EXPIRY_MINUTES: int = int(os.getenv("MESSAGE_EXPIRY_MINUTES", "5"))
    
    # Servidor
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "5001"))
    
    # Banco de dados
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "conversations.db")
    
    # Configurações do módulo conversation
    CONVERSATION_IDLE_TIMEOUT_MINUTES: int = int(os.getenv("CONVERSATION_IDLE_TIMEOUT_MINUTES", "2"))
    MAX_MESSAGE_LENGTH: int = int(os.getenv("MAX_MESSAGE_LENGTH", "4000"))
    CONVERSATION_DATABASE_NAME: str = os.getenv("CONVERSATION_DATABASE_NAME", "conversation")
    CLEANUP_DAYS_OLD: int = int(os.getenv("CLEANUP_DAYS_OLD", "30"))
    CLEANUP_BATCH_SIZE: int = int(os.getenv("CLEANUP_BATCH_SIZE", "100"))
    MAX_CONVERSATION_HISTORY: int = int(os.getenv("MAX_CONVERSATION_HISTORY", "1000"))
    ENABLE_CLEANUP_ON_OPERATION: bool = os.getenv("ENABLE_CLEANUP_ON_OPERATION", "False").lower() == "true"
    
    # Palavras-chave para encerramento de conversas (JSON string)
    AGENT_CLOSE_KEYWORDS: list = [
        "conversa encerrada",
        "atendimento finalizado", 
        "pode fechar o atendimento",
        "obrigado pelo contato",
        "até a próxima",
        "/close",
        "/end",
        "conversation ended",
        "support finished",
        "thank you for contacting",
        "see you next time"
    ]
    
    def validate(self) -> bool:
        """Valida se as configurações obrigatórias estão presentes"""
        required_vars = [
            self.VERIFICATION_TOKEN,
            self.WHATSAPP_API_TOKEN,
            self.MY_BUSINESS_TELEPHONE
        ]
        return all(var for var in required_vars)

# Instância global das configurações
settings = Settings()
