

from typing import Any, Dict, List, Optional, Tuple
import uuid
from models import Conversation, Message, MessageData
from repository import ConversationRepository


class ConversationService:
    """Serviço para gerenciar conversas e mensagens"""
    
    def __init__(self, repository: ConversationRepository):
        self.repository = repository

    def get_or_create_conversation(self, client_hub: str, channel: str, timeout_minutes: int = None) -> Tuple[Conversation, bool]:
        return self.repository.get_or_create_conversation(client_hub=client_hub, channel=channel, timeout_minutes=timeout_minutes)
    
    def add_message(self, conversation_uuid: uuid.UUID, message_data: MessageData) -> Tuple[Message, bool]:
        return self.repository.add_message(conversation_uuid=conversation_uuid, message_data=message_data)
    
    def get_conversation_history(self, client_hub: str, limit: int = 50, include_closed: bool = False) -> List[Message]:
        return self.repository.get_conversation_history(client_hub=client_hub, limit=limit, include_closed=include_closed)
    
    def get_or_create_conversation_uuid(self, client_hub: str, channel: str, timeout_minutes: int = None) -> Tuple[str, bool]:
        """Retorna UUID da conversa em vez do objeto"""
        return self.repository.get_or_create_conversation_uuid(client_hub=client_hub, channel=channel, timeout_minutes=timeout_minutes) 

    def get_active_conversation(self, client_hub: str) -> Optional[Conversation]:
        return self.repository.get_active_conversation(client_hub=client_hub)
    
    def force_close_conversation(self, client_hub: str, reason: str = "Fechada manualmente") -> bool:
        return self.repository.force_close_conversation(client_hub=client_hub, reason=reason)
    
    def extend_conversation_timeout(self, client_hub: str, additional_minutes: int) -> bool:
        return self.repository.extend_conversation_timeout(client_hub=client_hub, additional_minutes=additional_minutes)

    def get_conversation_stats(self, client_hub: str = None) -> Dict[str, Any]:
        return self.repository.get_conversation_stats(client_hub=client_hub)
    
    def cleanup_old_conversations(self, days_old: int = 30):
        return self.repository.cleanup_old_conversations(days_old=days_old)
