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
