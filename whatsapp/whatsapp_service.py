
import os
import json
import time
import logging
from fastapi import Depends
from typing_extensions import Annotated
import requests
from typing import BinaryIO, Dict, Optional

from channel.channel import Channel
from conversation.models import MessageData, MessageOwner

from dotenv import load_dotenv

from conversation.service import ConversationService
from whatsapp.whatsapp_models import Audio, Image, Message, Payload, User
from config.settings import settings

_ = load_dotenv() # forcar a execucao

# Configurar logging
logger = logging.getLogger(__name__)

WHATSAPP_API_KEY = settings.WHATSAPP_API_TOKEN
MY_BUSINESS_TELEPHONE = settings.MY_BUSINESS_TELEPHONE

class WhatsappService(Channel):
    def __init__(self,  conversation_service: ConversationService, llm = None):
        self.llm = llm
        self.conversation_service = conversation_service
        self.MESSAGE_EXPIRY_MINUTES = 5

    def parse_message(self, payload: Payload) -> Message | None:
        if not payload.entry[0].changes[0].value.messages:
            return None
        return payload.entry[0].changes[0].value.messages[0]

    def get_current_user(self, message: Annotated[Message, Depends(parse_message)]) -> User | None:
        if not message:
            return None
        return self.authenticate_user_by_phone_number(message.from_)

    def parse_audio_file(self, message: Annotated[Message, Depends(parse_message)]) -> Audio | None:
        if message and message.type == "audio":
            return message.audio
        return None

    def parse_image_file(self, message: Annotated[Message, Depends(parse_message)]) -> Image | None:
        if message and message.type == "image":
            return message.image
        return None

    def message_extractor(
            self, 
            message: Annotated[Message, Depends(parse_message)],
            audio: Annotated[Audio, Depends(parse_audio_file)],
    ):
        if audio:
            return self.transcribe_audio(audio)
        if message and message.text:
            return message.text.body
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

    def transcribe_audio_file(self, audio_file: BinaryIO) -> str:
        if not audio_file:
            return "No audio file provided"
        
        if self.llm is None:
            return "No transcribe actived"
        
        try:
            transcription = self.llm.audio.transcriptions.create(
                file=audio_file,
                model="whisper-1",
                response_format="text"
            )
            return transcription
        except Exception as e:
            raise ValueError("Error transcribing audio") from e

    def transcribe_audio(self, audio: Audio) -> str:
        file_path = self.download_file_from_facebook(audio.id, "audio", audio.mime_type)
        with open(file_path, 'rb') as audio_binary:
            transcription = self.transcribe_audio_file(audio_binary)
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Failed to delete file: {e}")
        return transcription

    def download_file_from_facebook(self, file_id: str, file_type: str, mime_type: str) -> str | None:
        # First GET request to retrieve the download URL
        url = f"https://graph.facebook.com/v22.0/{file_id}"
        headers = {"Authorization": f"Bearer {WHATSAPP_API_KEY}"}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            download_url = response.json().get('url')

            # Second GET request to download the file
            response = requests.get(download_url, headers=headers)

            if response.status_code == 200:
                file_extension = mime_type.split('/')[-1].split(';')[0]  # Extract file extension from mime_type
                file_path = f"{file_id}.{file_extension}"
                with open(file_path, 'wb') as file:
                    file.write(response.content)
                if file_type == "image" or file_type == "audio":
                    return file_path

            raise ValueError(f"Failed to download file. Status code: {response.status_code}")
        raise ValueError(f"Failed to retrieve download URL. Status code: {response.status_code}")

    def authenticate_user_by_phone_number(self, phone_number: str) -> User | None:
        # TODO
        with open('allowed_users.json', 'r', encoding='utf-8') as file:
            allowed_users =  json.load(file)
                
        for user in allowed_users:
            if user["phone"] == phone_number:
                print("authenticate_user_by_phone_number - got")
                return User(**user)
        print("authenticate_user_by_phone_number - None")
        return None

    def send_whatsapp_message(self, to, message, template=True):
        url = f"https://graph.facebook.com/v22.0/{MY_BUSINESS_TELEPHONE}/messages"
        headers = {
            "Authorization": f"Bearer " + WHATSAPP_API_KEY,
            "Content-Type": "application/json"
        }
        if not template:
            data = {
                "messaging_product": "whatsapp",
                "preview_url": False,
                "recipient_type": "individual",
                "to": to,
                "type": "text",
                "text": {
                    "body": message
                }
            }
        else:
            data = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "template",
                "template": {
                    "name": "hello_world",
                    "language": {
                        "code": "en_US"
                    }
                }
            }

        response = requests.post(url, headers=headers, data=json.dumps(data))
        return response.json()

    def get_user_by_phone(self, phone_number: str) -> Optional[User]:
        """
        Obtém usuário por número de telefone (método unificado)
        """
        return self.authenticate_user_by_phone_number(phone_number)

    def extract_message_content(self, message: Message) -> Optional[str]:
        """Extrai o conteúdo da mensagem baseado no tipo"""
        if message.type == "text" and message.text:
            return message.text.body
        elif message.type == "audio" and message.audio:
            return self.transcribe_audio(message.audio)
        elif message.type == "image" and message.image:
            return self.process_image(message.image)
        return None

    def save_request(self, user: User, owner: MessageOwner, channel: str, client_hub: str, message: str, message_type: str, meta: Dict = None):
        """Salva a mensagem do usuário no sistema de conversação"""
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
    
    def save_response(self, user: User, owner: MessageOwner, channel: str, client_hub: str, response: str, message_type: str, agent_type: str = "local_agent" , meta: Dict = None):
        """Salva a resposta do agente no sistema de conversação"""
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

    def respond_and_send_message(self, payload: Payload, channel: str = "whatsapp"):
        """
        Processa uma mensagem e gera resposta
        """
        start_time = time.time()
        
        try:
            # Parse da mensagem
            message = self.parse_message(payload)
            if not message:
                logger.warning("No message found in payload")
                return {"status": "no_message", "error": "No message found in payload"}
            
            # Verificar se a mensagem não é muito antiga
            if self.is_message_too_old(message.timestamp):
                logger.warning(f"Message too old: {message.timestamp}")
                return {
                    "status": "expired", 
                    "error": "Message is too old to be processed",
                    "max_age_minutes": self.MESSAGE_EXPIRY_MINUTES
                }
            
            # Obter usuário
            user = self.get_current_user(message)
            if not user:
                logger.warning(f"User not found for phone: {message.from_}")
                return {"status": "user_not_found", "error": "User not found"}
            
            # Extrair conteúdo da mensagem
            message_content = self.extract_message_content(message)
            if not message_content:
                logger.warning("No message content found")
                return {"status": "no_content", "error": "No message content found"}
            
            logger.info(f"Mensagem recebida de {user.first_name} {user.last_name}: {message_content}")
            
            # Salvar mensagem do usuário
            conversation_uuid, user_message_dict = self.save_request(
                user=user,
                owner=MessageOwner.USER,
                channel=channel,
                client_hub="todo",
                message=message_content,
                message_type=message.type,
                meta={"original_message_id": message.id}
            )
            
            # Gerar resposta
            response = self.generate_response(message_content, user)
            
            # Salvar resposta do agente
            agent_message_dict = self.save_response(
                user=user,
                owner=MessageOwner.AGENT,
                channel=channel,
                client_hub="todo",
                message_type=message.type,
                response=response,
                meta={"response_to": message.id}
            )
            
            processing_time = round((time.time() - start_time) * 1000, 2)
            
            logger.info(f"Processed message for user {user.first_name} {user.last_name} in {processing_time}ms")

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
            
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return {"status": "error", "message": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error processing message: {e}", exc_info=True)
            return {"status": "error", "message": "Internal server error"}
