import time
from typing import Dict, Optional
from channel.models import Payload, Message, Audio, Image, User
from service import ConversationService
from models import MessageData, MessageOwner

class MessageService:
    """Serviço para processar mensagens locais similar ao WhatsApp webhook"""
    
    def __init__(self, conversation_service: ConversationService):
        self.conversation_service = conversation_service
        self.MESSAGE_EXPIRY_MINUTES = 5
        
    def is_message_too_old(self, message_timestamp: str, max_age_minutes: int = None) -> bool:
        """
        Verifica se uma mensagem é muito antiga para ser processada.
        
        Args:
            message_timestamp: Timestamp da mensagem (string ou int/float)
            max_age_minutes: Idade máxima em minutos antes de considerar muito antiga
        
        Returns:
            bool: True se a mensagem for muito antiga, False caso contrário
        """
        if max_age_minutes is None:
            max_age_minutes = self.MESSAGE_EXPIRY_MINUTES
            
        current_time = time.time()
        
        # Converter message_timestamp para float se for string
        try:
            if isinstance(message_timestamp, str):
                message_time = float(message_timestamp)
            else:
                message_time = float(message_timestamp)
        except (ValueError, TypeError):
            # Se não conseguir fazer parse do timestamp, considerar muito antigo por segurança
            return True
        
        # Calcular idade em minutos
        age_minutes = (current_time - message_time) / 60
        
        return age_minutes > max_age_minutes

    def parse_message(self, payload: Payload) -> Optional[Message]:
        """Extrai a mensagem do payload"""
        if not payload.entry[0].changes[0].value.messages:
            return None
        return payload.entry[0].changes[0].value.messages[0]

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Mock para autenticação local - você pode implementar sua lógica aqui
        Por enquanto retorna um usuário padrão
        """
        # TODO: Implementar sua lógica de autenticação local
        return User(
            id=int(user_id.replace("user_", "")) if "user_" in user_id else 1,
            first_name="Local",
            last_name="User",
            role="basic"
        )

    def transcribe_audio_local(self, audio: Audio) -> str:
        """
        Mock para transcrição de áudio local
        TODO: Implementar transcrição real se necessário
        """
        return f"[Áudio transcrito - ID: {audio.id}]"

    def process_image_local(self, image: Image) -> str:
        """
        Mock para processamento de imagem local
        TODO: Implementar processamento real se necessário
        """
        return f"[Imagem processada - ID: {image.id}]"

    def extract_message_content(self, message: Message) -> Optional[str]:
        """Extrai o conteúdo da mensagem baseado no tipo"""
        if message.type == "text" and message.text:
            return message.text.body
        elif message.type == "audio" and message.audio:
            return self.transcribe_audio_local(message.audio)
        elif message.type == "image" and message.image:
            return self.process_image_local(message.image)
        return None
    
    def generate_response(self, user_message: str, user: User) -> str:
        """
        Gera uma resposta para a mensagem do usuário
        TODO: Integrar com seus agentes de IA aqui
        """
        # Mock de resposta - substitua pela sua lógica
        responses = [
            f"Olá {user.first_name}! Recebi sua mensagem: '{user_message}'",
            "Como posso ajudá-lo hoje?",
            "Interessante! Me conte mais sobre isso.",
            "Entendi. Há mais alguma coisa que gostaria de saber?",
            "Obrigado pela mensagem. Vou processar isso para você."
        ]
        
        # Escolher resposta baseada no comprimento da mensagem (mock)
        response_index = len(user_message) % len(responses)
        return responses[response_index]

    def get_conversation_context(self, user: User, limit: int = 10) -> str:
        """Obtém o contexto da conversa para o usuário"""
        client_hub = f"user_{user.id}"
        history = self.conversation_service.get_conversation_history(
            client_hub=client_hub,
            limit=limit,
            include_closed=False
        )
        
        if not history:
            return ""
        
        context_lines = []
        for msg in history[-limit:]:  # Pegar as últimas mensagens
            role = "Usuário" if msg["owner"] == "user" else "Agente"
            context_lines.append(f"{role}: {msg['message']}")
        
        return "\n".join(context_lines)

#=========================================================================================

    def save_request(self, user: User, owner: MessageOwner, channel: str, client_hub: str, message: str, message_type: str, meta: Dict = None):
        """Salva a mensagem do usuário no sistema de conversação"""
        if user:
            client_hub = f"user_{user.id}"
        
        # Criar dados da mensagem
        message_data = MessageData(
            message=message,
            type=message_type,
            owner=owner,
            meta=meta or {},
            channel=channel
        )
        
        # Obter ou criar conversa
        conversation_uuid, is_new = self.conversation_service.get_or_create_conversation_uuid(
            client_hub=client_hub,
            channel=channel
        )
        
        # Adicionar mensagem
        message_dict, conversation_closed = self.conversation_service.add_message(
            conversation_uuid=conversation_uuid,
            message_data=message_data
        )
        
        if is_new:
            print(f"Nova conversa criada para usuário {user.first_name} {user.last_name}")
        
        print(f"Mensagem salva: {message[:50]}...")
        return conversation_uuid, message_dict
    
    def save_response(self, user: User, owner: MessageOwner, channel: str, client_hub: str, response: str, message_type: str, agent_type: str, meta: Dict = None):
        """Salva a resposta do agente no sistema de conversação"""
        if user:
            client_hub = f"user_{user.id}"
        
        # Criar dados da resposta
        message_data = MessageData(
            message=response,
            type=message_type,
            owner=owner,
            meta={
                "agent_type": agent_type,
                **(meta or {})
            },
            channel=channel
        )
        
        # Obter conversa existente
        conversation_uuid, _ = self.conversation_service.get_or_create_conversation_uuid(
            client_hub=client_hub,
            channel=channel
        )
        
        # Adicionar resposta
        message_dict, conversation_closed = self.conversation_service.add_message(
            conversation_uuid=conversation_uuid,
            message_data=message_data
        )
        
        print(f"Resposta do agente salva: {response[:50]}...")
        return message_dict
    
    def receive_and_respond_message(self, payload: Payload, channel: str = "local") -> Dict:
        """
        Processa uma mensagem local
        """
        start_time = time.time()
        
        # Parse da mensagem
        message = self.parse_message(payload)
        if not message:
            return {"status": "no_message", "error": "No message found in payload"}
        
        # Verificar se a mensagem não é muito antiga
        if self.is_message_too_old(message.timestamp):
            return {
                "status": "expired", 
                "error": "Message is too old to be processed",
                "max_age_minutes": self.MESSAGE_EXPIRY_MINUTES
            }
        
        # Obter usuário
        user = self.get_user_by_id(message.from_)
        if not user:
            return {"status": "user_not_found", "error": "User not found"}
        
        # Extrair conteúdo da mensagem
        message_content = self.extract_message_content(message)
        if not message_content:
            return {"status": "no_content", "error": "No message content found"}
        
        print(f"Mensagem recebida de {user.first_name} {user.last_name}: {message_content}")
        
        # Salvar mensagem do usuário
        conversation_uuid, user_message_dict = self.save_message(
            owner=MessageOwner.USER,
            user=user,
            message_content=message_content,
            message_type=message.type,
            channel=channel,
            meta={"original_message_id": message.id}
        )
        
        # Gerar resposta
        response = self.generate_response(message_content, user)
        
        # Salvar resposta do agente
        agent_message_dict = self.save_response(
            owner=MessageOwner.AGENT,
            user=user,
            response=response,
            channel=channel,
            meta={"response_to": message.id}
        )
        
        processing_time = round((time.time() - start_time) * 1000, 2)
        
        return {
            "status": "processed",
            "user": {
                "id": user.id,
                "name": f"{user.first_name} {user.last_name}"
            },
            "conversation_uuid": conversation_uuid,
            "user_message": user_message_dict,
            "agent_response": agent_message_dict,
            "response_text": response,
            "processing_time_ms": processing_time
        }

#=========================================================================================

    def save_user_message(self, user: User, message_content: str, message_type: str, 
                         channel: str = "local", meta: Dict = None):
        """Salva a mensagem do usuário no sistema de conversação"""
        client_hub = f"user_{user.id}"
        
        # Criar dados da mensagem
        message_data = MessageData(
            message=message_content,
            type=message_type,
            owner=MessageOwner.USER,
            meta=meta or {},
            channel=channel
        )
        
        # Obter ou criar conversa
        conversation_uuid, is_new = self.conversation_service.get_or_create_conversation_uuid(
            client_hub=client_hub,
            channel=channel
        )
        
        # Adicionar mensagem
        message_dict, conversation_closed = self.conversation_service.add_message(
            conversation_uuid=conversation_uuid,
            message_data=message_data
        )
        
        if is_new:
            print(f"Nova conversa criada para usuário {user.first_name} {user.last_name}")
        
        print(f"Mensagem salva: {message_content[:50]}...")
        return conversation_uuid, message_dict

    def save_agent_response(self, user: User, response: str, message_type: str = "text",
                           agent_type: str = "local_agent", channel: str = "local", meta: Dict = None):
        """Salva a resposta do agente no sistema de conversação"""
        client_hub = f"user_{user.id}"
        
        # Criar dados da resposta
        message_data = MessageData(
            message=response,
            type=message_type,
            owner=MessageOwner.AGENT,
            meta={
                "agent_type": agent_type,
                **(meta or {})
            },
            channel=channel
        )
        
        # Obter conversa existente
        conversation_uuid, _ = self.conversation_service.get_or_create_conversation_uuid(
            client_hub=client_hub,
            channel=channel
        )
        
        # Adicionar resposta
        message_dict, conversation_closed = self.conversation_service.add_message(
            conversation_uuid=conversation_uuid,
            message_data=message_data
        )
        
        print(f"Resposta do agente salva: {response[:50]}...")
        return message_dict

    def process_local_message(self, payload: Payload, channel: str = "local") -> Dict:
        """
        Processa uma mensagem local
        """
        start_time = time.time()
        
        # Parse da mensagem
        message = self.parse_message(payload)
        if not message:
            return {"status": "no_message", "error": "No message found in payload"}
        
        # Verificar se a mensagem não é muito antiga
        if self.is_message_too_old(message.timestamp):
            return {
                "status": "expired", 
                "error": "Message is too old to be processed",
                "max_age_minutes": self.MESSAGE_EXPIRY_MINUTES
            }
        
        # Obter usuário
        user = self.get_user_by_id(message.from_)
        if not user:
            return {"status": "user_not_found", "error": "User not found"}
        
        # Extrair conteúdo da mensagem
        message_content = self.extract_message_content(message)
        if not message_content:
            return {"status": "no_content", "error": "No message content found"}
        
        print(f"Mensagem recebida de {user.first_name} {user.last_name}: {message_content}")
        
        # Salvar mensagem do usuário
        conversation_uuid, user_message_dict = self.save_user_message(
            user=user,
            message_content=message_content,
            message_type=message.type,
            channel=channel,
            meta={"original_message_id": message.id}
        )
        
        # Gerar resposta
        response = self.generate_response(message_content, user)
        
        # Salvar resposta do agente
        agent_message_dict = self.save_agent_response(
            user=user,
            response=response,
            channel=channel,
            meta={"response_to": message.id}
        )
        
        processing_time = round((time.time() - start_time) * 1000, 2)
        
        return {
            "status": "processed",
            "user": {
                "id": user.id,
                "name": f"{user.first_name} {user.last_name}"
            },
            "conversation_uuid": conversation_uuid,
            "user_message": user_message_dict,
            "agent_response": agent_message_dict,
            "response_text": response,
            "processing_time_ms": processing_time
        }
