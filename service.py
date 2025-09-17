
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple

from models import Conversation, ConversationConfig, ConversationStatus, Message, MessageData, MessageType

class ConversationService:
    """Serviço para gerenciar conversas e mensagens"""
    
    def __init__(self, session):
        self.session = session
        self.config = ConversationConfig()
    
    def _cleanup_expired_conversations(self, client_hub: str = None):
        """Limpa conversas que expiraram por timeout"""
        query = self.session.query(Conversation).filter(
            Conversation.status == ConversationStatus.ACTIVE
        )
        
        if client_hub:
            query = query.filter(Conversation.client_hub == client_hub)
        
        active_conversations = query.all()
        expired_count = 0
        
        for conv in active_conversations:
            if conv.is_expired():
                conv.close_conversation(ConversationStatus.IDLE_TIMEOUT)
                expired_count += 1
        
        if expired_count > 0:
            self.session.commit()
            print(f"Closed {expired_count} expired conversations")

    def get_or_create_conversation(self, client_hub: str, channel: str = "whatsapp", timeout_minutes: int = None) -> Tuple[Conversation, bool]:
        """
        Obtém uma conversa ativa ou cria uma nova
        Retorna (conversation, is_new)
        """
        # Primeiro, verificar e limpar conversas expiradas
        self._cleanup_expired_conversations(client_hub)
        
        # Buscar conversa ativa
        active_conversation = self.session.query(Conversation).filter(
            Conversation.client_hub == client_hub,
            Conversation.status == ConversationStatus.ACTIVE
        ).first()
        
        if active_conversation and not active_conversation.is_expired():
            return active_conversation, False
        
        # Se a conversa ativa expirou, encerra ela
        if active_conversation and active_conversation.is_expired():
            active_conversation.close_conversation(ConversationStatus.IDLE_TIMEOUT)
            self.session.commit()
        
        # Criar nova conversa
        timeout = timeout_minutes or self.config.DEFAULT_IDLE_TIMEOUT_MINUTES
        new_conversation = Conversation(
            client_hub=client_hub,
            idle_timeout_minutes=timeout,
            channel=channel
        )
        
        self.session.add(new_conversation)
        self.session.commit()
        
        return new_conversation, True
    
    def add_message(self, conversation_uuid: uuid.UUID, message_data: MessageData) -> Tuple[Message, bool]:
        """
        Adiciona uma nova mensagem à conversa
        Retorna (message, conversation_was_closed)
        """
        conversation = self.session.query(Conversation).filter(
            Conversation.conversation_uuid == conversation_uuid
        ).first()
        
        if not conversation:
            raise ValueError(f"Conversation {conversation_uuid} not found")
        
        # Verificar se a conversa não está encerrada
        if conversation.status != ConversationStatus.ACTIVE:
            raise ValueError(f"Cannot add message to closed conversation (status: {conversation.status.value})")
        
        # Verificar se a mensagem deve encerrar a conversa
        should_close = (message_data.closes_conversation or 
                       self.config.is_closing_message(message_data.message, message_data.owner))
        
        # Criar mensagem
        message = Message(
            conversation_uuid=conversation_uuid,
            type=MessageType(message_data.type),
            message=message_data.message,
            timestamp=message_data.timestamp,
            owner=message_data.owner,
            meta=message_data.meta,
            closes_conversation=should_close,
            channel=message_data.channel or "whatsapp"
        )
        
        self.session.add(message)
        
        # Atualizar atividade da conversa
        conversation.updated_at = datetime.now()
        conversation.last_activity_at = datetime.now()
        
        # Encerrar conversa se necessário
        conversation_closed = False
        if should_close:
            conversation.close_conversation(
                ConversationStatus.AGENT_CLOSED, 
                message_data.message
            )
            conversation_closed = True
        
        self.session.commit()
        return message, conversation_closed
    
    def get_conversation_history(self, client_hub: str, limit: int = 50, include_closed: bool = False) -> List[Message]:
        """Obtém o histórico de mensagens, incluindo conversas fechadas se solicitado"""
        query = self.session.query(Conversation).filter(
            Conversation.client_hub == client_hub
        )
        
        if not include_closed:
            query = query.filter(Conversation.status == ConversationStatus.ACTIVE)
        
        conversations = query.order_by(Conversation.updated_at.desc()).all()
        
        all_messages = []
        for conv in conversations:
            messages = self.session.query(Message).filter(
                Message.conversation_uuid == conv.conversation_uuid
            ).order_by(Message.timestamp.desc()).limit(limit).all()
            all_messages.extend(messages)
        
        # Ordenar por timestamp e limitar
        all_messages.sort(key=lambda x: x.timestamp)
        return all_messages[-limit:] if limit else all_messages
    
    def get_active_conversation(self, client_hub: str) -> Optional[Conversation]:
        """Retorna a conversa ativa para um cliente, se existir"""
        return self.session.query(Conversation).filter(
            Conversation.client_hub == client_hub,
            Conversation.status == ConversationStatus.ACTIVE
        ).first()
    
    def force_close_conversation(self, client_hub: str, reason: str = "Fechada manualmente") -> bool:
        """Força o encerramento de uma conversa ativa"""
        conversation = self.get_active_conversation(client_hub)
        if conversation:
            conversation.close_conversation(ConversationStatus.USER_CLOSED, reason)
            self.session.commit()
            return True
        return False
    
    def extend_conversation_timeout(self, client_hub: str, additional_minutes: int) -> bool:
        """Estende o timeout de uma conversa ativa"""
        conversation = self.get_active_conversation(client_hub)
        if conversation:
            conversation.idle_timeout_minutes += additional_minutes
            conversation.last_activity_at = datetime.now()
            self.session.commit()
            return True
        return False
    
    def get_conversation_stats(self, client_hub: str = None) -> Dict[str, Any]:
        """Obtém estatísticas das conversas"""
        base_query = self.session.query(Conversation)
        if client_hub:
            base_query = base_query.filter(Conversation.client_hub == client_hub)
        
        stats = {
            'total_conversations': base_query.count(),
            'active_conversations': base_query.filter(Conversation.status == ConversationStatus.ACTIVE).count(),
            'closed_by_timeout': base_query.filter(Conversation.status == ConversationStatus.IDLE_TIMEOUT).count(),
            'closed_by_agent': base_query.filter(Conversation.status == ConversationStatus.AGENT_CLOSED).count(),
            'average_messages_per_conversation': 0
        }
        
        # Calcular média de mensagens por conversa
        if stats['total_conversations'] > 0:
            total_messages = self.session.query(Message).join(Conversation).filter(
                Conversation.client_hub == client_hub if client_hub else True
            ).count()
            stats['average_messages_per_conversation'] = round(total_messages / stats['total_conversations'], 2)
        
        return stats
    
    def cleanup_old_conversations(self, days_old: int = 30):
        """Remove conversas antigas definitivamente"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        old_conversations = self.session.query(Conversation).filter(
            Conversation.updated_at < cutoff_date,
            Conversation.status != ConversationStatus.ACTIVE
        ).all()
        
        for conv in old_conversations:
            conv.status = ConversationStatus.EXPIRED
        
        self.session.commit()
        print(f"Marked {len(old_conversations)} old conversations as expired")
