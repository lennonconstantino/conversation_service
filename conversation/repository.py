import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from conversation.db import DatabaseConfig, Base
from conversation.models import Conversation, ConversationStatus, Message, MessageData, MessageType
from conversation.config import ConversationConfig
from conversation.exceptions import (
    ConversationNotFoundError, 
    ConversationExpiredError, 
    ConversationClosedError,
    DatabaseConnectionError
)

# Configurar logging
logger = logging.getLogger(__name__)

class ConversationRepository:
    """Serviço para gerenciar conversas e mensagens"""
    
    def __init__(self, database: DatabaseConfig):
        self.config = ConversationConfig()
        self.database = database
        
        try:
            self.engine = create_engine(
                database.connection_string,
                echo=False,  # Mude para True para ver as queries SQL
                pool_pre_ping=True if database.database_type == "postgresql" else False
            )
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            self._create_tables()
            logger.info(f"Database connection established: {database.database_type}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise DatabaseConnectionError(database.database_type, str(e))
    
    def _create_tables(self):
        """Cria todas as tabelas no banco de dados"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info(f"Tables created in {self.database.database_type} database")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise DatabaseConnectionError(self.database.database_type, f"Table creation failed: {e}")

    def get_session(self) -> Session:
        """Retorna uma sessão do banco de dados"""
        return self.SessionLocal()

    def _cleanup_expired_conversations(self, client_hub: str = None):
        """Limpa conversas que expiraram por timeout"""
        if not ConversationConfig.ENABLE_CLEANUP_ON_OPERATION:
            return
            
        try:
            with self.get_session() as session:
                query = session.query(Conversation).filter(
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
                    session.commit()
                    logger.info(f"Closed {expired_count} expired conversations")
                    
        except SQLAlchemyError as e:
            logger.error(f"Error during cleanup: {e}")
            # Não re-raise para não interromper operações principais

    def get_or_create_conversation_uuid(self, client_hub: str, channel: str = "whatsapp", timeout_minutes: int = None) -> Tuple[str, bool]:
        """
        Obtém uma conversa ativa ou cria uma nova
        Retorna (conversation_uuid, is_new) seguindo o padrão do KanbanRepository
        """
        try:
            with self.get_session() as session:
                # Primeiro, verificar e limpar conversas expiradas
                self._cleanup_expired_conversations(client_hub)
                
                # Buscar conversa ativa
                active_conversation = session.query(Conversation).filter(
                    Conversation.client_hub == client_hub,
                    Conversation.status == ConversationStatus.ACTIVE
                ).first()
                
                if active_conversation and not active_conversation.is_expired():
                    logger.debug(f"Found active conversation for client {client_hub}")
                    return str(active_conversation.conversation_uuid), False
                
                # Se a conversa ativa expirou, encerra ela
                if active_conversation and active_conversation.is_expired():
                    logger.info(f"Closing expired conversation for client {client_hub}")
                    active_conversation.close_conversation(ConversationStatus.IDLE_TIMEOUT)
                    session.commit()
                
                # Criar nova conversa
                timeout = timeout_minutes or self.config.DEFAULT_IDLE_TIMEOUT_MINUTES
                new_conversation = Conversation(
                    client_hub=client_hub,
                    idle_timeout_minutes=timeout,
                    channel=channel
                )
                
                session.add(new_conversation)
                session.commit()
                session.refresh(new_conversation)
                
                logger.info(f"Created new conversation for client {client_hub}")
                return str(new_conversation.conversation_uuid), True
                
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_or_create_conversation_uuid: {e}")
            raise DatabaseConnectionError(self.database.database_type, str(e))
    
    def add_message(self, conversation_uuid: str, message_data: MessageData) -> Tuple[dict, bool]:
        """
        Adiciona uma nova mensagem à conversa
        Retorna (message_dict, conversation_was_closed) seguindo padrão do KanbanRepository
        """
        try:
            with self.get_session() as session:
                # Converter string UUID para objeto UUID
                uuid_obj = uuid.UUID(conversation_uuid) if isinstance(conversation_uuid, str) else conversation_uuid
                
                conversation = session.query(Conversation).filter(
                    Conversation.conversation_uuid == uuid_obj
                ).first()
                
                if not conversation:
                    raise ConversationNotFoundError(conversation_uuid)
                
                # Verificar se a conversa não está encerrada
                if conversation.status != ConversationStatus.ACTIVE:
                    raise ConversationClosedError(conversation_uuid, conversation.status.value)
                
                # Verificar se a conversa expirou
                if conversation.is_expired():
                    raise ConversationExpiredError(conversation_uuid)
                
                # Verificar se a mensagem deve encerrar a conversa
                should_close = (message_data.closes_conversation or 
                            self.config.is_closing_message(message_data.message, message_data.owner.value))
                
                # Criar mensagem
                message = Message(
                    conversation_uuid=uuid_obj,
                    type=MessageType(message_data.type),
                    message=message_data.message,
                    timestamp=message_data.timestamp,
                    owner=message_data.owner,
                    meta=message_data.meta,
                    closes_conversation=should_close,
                    channel=message_data.channel or "whatsapp"
                )
                
                session.add(message)
                
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
                    logger.info(f"Conversation {conversation_uuid} closed by message")
                
                session.commit()
                session.refresh(message)
                
                logger.debug(f"Message added to conversation {conversation_uuid}")
                
                # Retornar dados serializados como no KanbanRepository
                message_dict = {
                    "id": str(message.id),
                    "conversation_uuid": str(message.conversation_uuid),
                    "type": message.type.value,
                    "message": message.message,
                    "timestamp": message.timestamp,
                    "owner": message.owner.value,
                    "channel": message.channel,
                    "meta": message.meta,
                    "closes_conversation": message.closes_conversation
                }
                
                return message_dict, conversation_closed
                
        except (ConversationNotFoundError, ConversationClosedError, ConversationExpiredError):
            # Re-raise exceções específicas
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error in add_message: {e}")
            raise DatabaseConnectionError(self.database.database_type, str(e))
    
    def get_conversation_history(self, client_hub: str, limit: int = 50, include_closed: bool = False) -> List[dict]:
        """Obtém o histórico de mensagens, retornando dados serializados"""
        with self.get_session() as session:
            query = session.query(Conversation).filter(
                Conversation.client_hub == client_hub
            )
            
            if not include_closed:
                query = query.filter(Conversation.status == ConversationStatus.ACTIVE)
            
            conversations = query.order_by(Conversation.updated_at.desc()).all()
            
            all_messages = []
            for conv in conversations:
                messages = session.query(Message).filter(
                    Message.conversation_uuid == conv.conversation_uuid
                ).order_by(Message.timestamp.desc()).limit(limit).all()
                
                for message in messages:
                    message_dict = {
                        "id": str(message.id),
                        "conversation_uuid": str(message.conversation_uuid),
                        "type": message.type.value,
                        "message": message.message,
                        "timestamp": message.timestamp,
                        "owner": message.owner.value,
                        "channel": message.channel,
                        "meta": message.meta,
                        "closes_conversation": message.closes_conversation
                    }
                    all_messages.append(message_dict)
            
            # Ordenar por timestamp e limitar
            all_messages.sort(key=lambda x: x['timestamp'])
            return all_messages[-limit:] if limit else all_messages
    
    def get_active_conversation_data(self, client_hub: str) -> Optional[dict]:
        """Retorna dados da conversa ativa para um cliente, se existir"""
        with self.get_session() as session:
            conversation = session.query(Conversation).filter(
                Conversation.client_hub == client_hub,
                Conversation.status == ConversationStatus.ACTIVE
            ).first()
            
            if not conversation:
                return None
            
            return {
                "conversation_uuid": str(conversation.conversation_uuid),
                "client_hub": conversation.client_hub,
                "channel": conversation.channel,
                "created_at": conversation.created_at,
                "last_activity_at": conversation.last_activity_at,
                "status": conversation.status.value,
                "idle_timeout_minutes": conversation.idle_timeout_minutes
            }
    
    def force_close_conversation(self, client_hub: str, reason: str = "Fechada manualmente") -> bool:
        """Força o encerramento de uma conversa ativa"""
        with self.get_session() as session:
            conversation = session.query(Conversation).filter(
                Conversation.client_hub == client_hub,
                Conversation.status == ConversationStatus.ACTIVE
            ).first()
            
            if conversation:
                conversation.close_conversation(ConversationStatus.USER_CLOSED, reason)
                session.commit()
                return True
            return False
    
    def extend_conversation_timeout(self, client_hub: str, additional_minutes: int) -> bool:
        """Estende o timeout de uma conversa ativa"""
        with self.get_session() as session:
            conversation = session.query(Conversation).filter(
                Conversation.client_hub == client_hub,
                Conversation.status == ConversationStatus.ACTIVE
            ).first()
            
            if conversation:
                conversation.idle_timeout_minutes += additional_minutes
                conversation.last_activity_at = datetime.now()
                session.commit()
                return True
            return False
    
    def get_conversation_stats(self, client_hub: str = None) -> Dict[str, Any]:
        """Obtém estatísticas das conversas"""
        with self.get_session() as session:
            base_query = session.query(Conversation)
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
                total_messages = session.query(Message).join(Conversation).filter(
                    Conversation.client_hub == client_hub if client_hub else True
                ).count()
                stats['average_messages_per_conversation'] = round(total_messages / stats['total_conversations'], 2)
            
            return stats
    
    def cleanup_old_conversations(self, days_old: int = None):
        """Remove conversas antigas definitivamente"""
        days_old = days_old or ConversationConfig.CLEANUP_DAYS_OLD
        
        try:
            with self.get_session() as session:
                cutoff_date = datetime.now() - timedelta(days=days_old)
                
                old_conversations = session.query(Conversation).filter(
                    Conversation.updated_at < cutoff_date,
                    Conversation.status != ConversationStatus.ACTIVE
                ).limit(ConversationConfig.CLEANUP_BATCH_SIZE).all()
                
                for conv in old_conversations:
                    conv.status = ConversationStatus.EXPIRED
                
                session.commit()
                logger.info(f"Marked {len(old_conversations)} old conversations as expired")
                return len(old_conversations)
                
        except SQLAlchemyError as e:
            logger.error(f"Error during cleanup of old conversations: {e}")
            raise DatabaseConnectionError(self.database.database_type, str(e))
