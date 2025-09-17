import logging
from typing import Any, Dict, List, Optional, Tuple
from conversation.models import MessageData
from conversation.repository import ConversationRepository
from conversation.exceptions import ConversationError
from conversation.config import ConversationConfig

# Configurar logging
logger = logging.getLogger(__name__)


class ConversationService():
    """Serviço para gerenciar conversas e mensagens"""
    
    def __init__(self, repository: ConversationRepository):
        self.repository = repository
        self.config = ConversationConfig()
        logger.info("ConversationService initialized")
    
    def get_or_create_conversation_uuid(self, client_hub: str, channel: str, timeout_minutes: int = None) -> Tuple[str, bool]:
        """Retorna UUID da conversa em vez do objeto"""
        try:
            if not client_hub or not client_hub.strip():
                raise ValueError("client_hub cannot be empty")
            
            if not channel or not channel.strip():
                raise ValueError("channel cannot be empty")
            
            logger.debug(f"Getting or creating conversation for client {client_hub} on channel {channel}")
            result = self.repository.get_or_create_conversation_uuid(
                client_hub=client_hub, 
                channel=channel, 
                timeout_minutes=timeout_minutes
            )
            
            conversation_uuid, is_new = result
            logger.info(f"Conversation {'created' if is_new else 'retrieved'} for client {client_hub}: {conversation_uuid}")
            return result
            
        except Exception as e:
            logger.error(f"Error in get_or_create_conversation_uuid: {e}")
            raise ConversationError(f"Failed to get or create conversation: {e}") 
    
    def add_message(self, conversation_uuid: str, message_data: MessageData) -> Tuple[dict, bool]:
        """Adiciona mensagem e retorna dados serializados"""
        try:
            if not conversation_uuid or not conversation_uuid.strip():
                raise ValueError("conversation_uuid cannot be empty")
            
            if not message_data:
                raise ValueError("message_data cannot be None")
            
            logger.debug(f"Adding message to conversation {conversation_uuid}")
            result = self.repository.add_message(conversation_uuid=conversation_uuid, message_data=message_data)
            
            message_dict, conversation_closed = result
            logger.info(f"Message added to conversation {conversation_uuid}. Conversation closed: {conversation_closed}")
            return result
            
        except Exception as e:
            logger.error(f"Error in add_message: {e}")
            raise ConversationError(f"Failed to add message: {e}")
    
    def get_conversation_history(self, client_hub: str, limit: int = 50, include_closed: bool = False) -> List[dict]:
        """Retorna histórico com dados serializados"""
        try:
            if not client_hub or not client_hub.strip():
                raise ValueError("client_hub cannot be empty")
            
            # Validar limite
            if limit > ConversationConfig.MAX_CONVERSATION_HISTORY:
                limit = ConversationConfig.MAX_CONVERSATION_HISTORY
                logger.warning(f"Limit capped to {ConversationConfig.MAX_CONVERSATION_HISTORY}")
            
            logger.debug(f"Getting conversation history for client {client_hub}, limit: {limit}")
            result = self.repository.get_conversation_history(client_hub=client_hub, limit=limit, include_closed=include_closed)
            logger.info(f"Retrieved {len(result)} messages for client {client_hub}")
            return result
            
        except Exception as e:
            logger.error(f"Error in get_conversation_history: {e}")
            raise ConversationError(f"Failed to get conversation history: {e}")

    def get_active_conversation_data(self, client_hub: str) -> Optional[dict]:
        """Retorna dados da conversa ativa"""
        try:
            if not client_hub or not client_hub.strip():
                raise ValueError("client_hub cannot be empty")
            
            logger.debug(f"Getting active conversation data for client {client_hub}")
            result = self.repository.get_active_conversation_data(client_hub=client_hub)
            
            if result:
                logger.info(f"Found active conversation for client {client_hub}")
            else:
                logger.info(f"No active conversation found for client {client_hub}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in get_active_conversation_data: {e}")
            raise ConversationError(f"Failed to get active conversation data: {e}")
    
    def force_close_conversation(self, client_hub: str, reason: str = "Fechada manualmente") -> bool:
        """Força o encerramento de uma conversa"""
        try:
            if not client_hub or not client_hub.strip():
                raise ValueError("client_hub cannot be empty")
            
            logger.info(f"Force closing conversation for client {client_hub}: {reason}")
            result = self.repository.force_close_conversation(client_hub=client_hub, reason=reason)
            
            if result:
                logger.info(f"Conversation successfully closed for client {client_hub}")
            else:
                logger.warning(f"No active conversation found to close for client {client_hub}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in force_close_conversation: {e}")
            raise ConversationError(f"Failed to force close conversation: {e}")
    
    def extend_conversation_timeout(self, client_hub: str, additional_minutes: int) -> bool:
        """Estende o timeout de uma conversa"""
        try:
            if not client_hub or not client_hub.strip():
                raise ValueError("client_hub cannot be empty")
            
            if additional_minutes <= 0:
                raise ValueError("additional_minutes must be positive")
            
            logger.info(f"Extending conversation timeout for client {client_hub} by {additional_minutes} minutes")
            result = self.repository.extend_conversation_timeout(client_hub=client_hub, additional_minutes=additional_minutes)
            
            if result:
                logger.info(f"Conversation timeout extended for client {client_hub}")
            else:
                logger.warning(f"No active conversation found to extend timeout for client {client_hub}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in extend_conversation_timeout: {e}")
            raise ConversationError(f"Failed to extend conversation timeout: {e}")

    def get_conversation_stats(self, client_hub: str = None) -> Dict[str, Any]:
        """Retorna estatísticas das conversas"""
        try:
            logger.debug(f"Getting conversation stats for client {client_hub or 'all'}")
            result = self.repository.get_conversation_stats(client_hub=client_hub)
            logger.info(f"Retrieved conversation stats: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in get_conversation_stats: {e}")
            raise ConversationError(f"Failed to get conversation stats: {e}")
    
    def cleanup_old_conversations(self, days_old: int = None) -> int:
        """Limpa conversas antigas"""
        try:
            days_old = days_old or ConversationConfig.CLEANUP_DAYS_OLD
            logger.info(f"Starting cleanup of conversations older than {days_old} days")
            
            result = self.repository.cleanup_old_conversations(days_old=days_old)
            logger.info(f"Cleanup completed: {result} conversations marked as expired")
            return result
            
        except Exception as e:
            logger.error(f"Error in cleanup_old_conversations: {e}")
            raise ConversationError(f"Failed to cleanup old conversations: {e}")
