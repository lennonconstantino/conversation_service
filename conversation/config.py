"""
Configurações específicas do módulo conversation
"""
from config.settings import settings

class ConversationConfig:
    """Configurações para gestão de conversas"""
    
    # Timeouts
    DEFAULT_IDLE_TIMEOUT_MINUTES = getattr(settings, 'CONVERSATION_IDLE_TIMEOUT_MINUTES', 2)
    MAX_MESSAGE_LENGTH = getattr(settings, 'MAX_MESSAGE_LENGTH', 4000)
    
    # Palavras-chave para encerramento de conversas
    AGENT_CLOSE_KEYWORDS = getattr(settings, 'AGENT_CLOSE_KEYWORDS', [
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
    ])
    
    # Configurações de banco
    DATABASE_NAME = getattr(settings, 'CONVERSATION_DATABASE_NAME', 'conversation')
    
    # Configurações de cleanup
    CLEANUP_DAYS_OLD = getattr(settings, 'CLEANUP_DAYS_OLD', 30)
    CLEANUP_BATCH_SIZE = getattr(settings, 'CLEANUP_BATCH_SIZE', 100)
    
    # Configurações de performance
    MAX_CONVERSATION_HISTORY = getattr(settings, 'MAX_CONVERSATION_HISTORY', 1000)
    ENABLE_CLEANUP_ON_OPERATION = getattr(settings, 'ENABLE_CLEANUP_ON_OPERATION', False)
    
    @classmethod
    def is_closing_message(cls, message: str, owner: str) -> bool:
        """Verifica se a mensagem deve encerrar a conversa"""
        if owner != "agent":
            return False
        
        message_lower = message.lower().strip()
        return any(keyword in message_lower for keyword in cls.AGENT_CLOSE_KEYWORDS)
    
    @classmethod
    def validate_message_length(cls, message: str) -> bool:
        """Valida se a mensagem não excede o tamanho máximo"""
        return len(message) <= cls.MAX_MESSAGE_LENGTH
