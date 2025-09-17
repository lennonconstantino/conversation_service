import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship

from db import Base

class MessageOwner(Enum):
    """Enum para identificar o proprietário da mensagem"""
    AGENT = "agent"
    TEAM = "team"
    USER = "user"  # Adicionado para mensagens do usuário

class MessageType(Enum):
    """Enum para tipos de mensagem"""
    TEXT = "text"
    AUDIO = "audio"
    IMAGE = "image"
    DOCUMENT = "document"
    TEMPLATE = "template"

class ConversationStatus(Enum):
    """Status da conversa"""
    ACTIVE = "active"
    IDLE_TIMEOUT = "idle_timeout"
    AGENT_CLOSED = "agent_closed"
    USER_CLOSED = "user_closed"
    EXPIRED = "expired"

@dataclass
class MessageData:
    """Classe para estruturar dados da mensagem antes da persistência"""
    message: str
    type: str
    timestamp: datetime = field(default_factory=datetime.now)
    owner: MessageOwner = MessageOwner.USER
    meta: Optional[Dict[str, Any]] = None
    closes_conversation: bool = False  # Flag para indicar se a mensagem encerra a conversa
    channel: Optional[str] = "whatsapp"

class ConversationConfig:
    """Configurações para gestão de conversas"""
    DEFAULT_IDLE_TIMEOUT_MINUTES = 2
    AGENT_CLOSE_KEYWORDS = [
        "conversa encerrada",
        "atendimento finalizado", 
        "pode fechar o atendimento",
        "obrigado pelo contato",
        "até a próxima",
        "/close",
        "/end"
    ]
    
    @classmethod
    def is_closing_message(cls, message: str, owner: MessageOwner) -> bool:
        """Verifica se a mensagem deve encerrar a conversa"""
        if owner != MessageOwner.AGENT:
            return False
        
        message_lower = message.lower().strip()
        return any(keyword in message_lower for keyword in cls.AGENT_CLOSE_KEYWORDS)

class Conversation(Base):
    """Modelo de conversa para persistência no banco de dados"""
    __tablename__ = 'conversations'
    
    conversation_uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_hub = Column(String(50), nullable=False, index=True)
    channel = Column(String(50), nullable=False, default="whatsapp", index=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    last_activity_at = Column(DateTime, default=datetime.now)  # Para controle de timeout
    status = Column(SQLEnum(ConversationStatus), default=ConversationStatus.ACTIVE)
    idle_timeout_minutes = Column(Integer, default=ConversationConfig.DEFAULT_IDLE_TIMEOUT_MINUTES)
    closed_by_message = Column(Text, nullable=True)  # Mensagem que encerrou a conversa
    closed_at = Column(DateTime, nullable=True)
    
    # Relacionamento com mensagens
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    def is_expired(self) -> bool:
        """Verifica se a conversa expirou por timeout"""
        if self.status != ConversationStatus.ACTIVE:
            return False
        
        timeout_threshold = self.last_activity_at + timedelta(minutes=self.idle_timeout_minutes)
        return datetime.now() > timeout_threshold
    
    def get_idle_time_minutes(self) -> float:
        """Retorna o tempo de inatividade em minutos"""
        return (datetime.now() - self.last_activity_at).total_seconds() / 60
    
    def close_conversation(self, reason: ConversationStatus, closing_message: str = None):
        """Encerra a conversa com um motivo específico"""
        self.status = reason
        self.closed_at = datetime.now()
        if closing_message:
            self.closed_by_message = closing_message
    
    def __repr__(self):
        return f"<Conversation(uuid={self.conversation_uuid}, client={self.client_hub}, channel={self.channel}, status={self.status.value})>"

class Message(Base):
    """Modelo de mensagem individual"""
    __tablename__ = 'messages'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_uuid = Column(UUID(as_uuid=True), ForeignKey('conversations.conversation_uuid'), nullable=False)
    type = Column(SQLEnum(MessageType), nullable=False, default=MessageType.TEXT)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    owner = Column(SQLEnum(MessageOwner), nullable=False, default=MessageOwner.USER)
    channel = Column(String(50), nullable=False, default="whatsapp")
    meta = Column(JSON)  # Para dados extras como mime_type, file_id, etc.
    closes_conversation = Column(Boolean, default=False)  # Marca se esta mensagem encerrou a conversa
    
    # Relacionamento com conversa
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        return f"<Message(id={self.id}, type={self.type.value}, owner={self.owner.value}, channel={self.channel})>"
