"""
Exceções customizadas para o módulo conversation
"""

class ConversationError(Exception):
    """Exceção base para erros do módulo conversation"""
    pass

class ConversationNotFoundError(ConversationError):
    """Exceção quando conversa não é encontrada"""
    def __init__(self, conversation_uuid: str):
        self.conversation_uuid = conversation_uuid
        super().__init__(f"Conversation {conversation_uuid} not found")

class ConversationExpiredError(ConversationError):
    """Exceção quando conversa expirou"""
    def __init__(self, conversation_uuid: str):
        self.conversation_uuid = conversation_uuid
        super().__init__(f"Conversation {conversation_uuid} has expired")

class ConversationClosedError(ConversationError):
    """Exceção quando tentativa de adicionar mensagem em conversa fechada"""
    def __init__(self, conversation_uuid: str, status: str):
        self.conversation_uuid = conversation_uuid
        self.status = status
        super().__init__(f"Cannot add message to closed conversation {conversation_uuid} (status: {status})")

class MessageValidationError(ConversationError):
    """Exceção quando mensagem não passa na validação"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(f"Message validation failed: {message}")

class DatabaseConnectionError(ConversationError):
    """Exceção quando há problema de conexão com banco"""
    def __init__(self, database_type: str, error: str):
        self.database_type = database_type
        self.error = error
        super().__init__(f"Database connection failed for {database_type}: {error}")
