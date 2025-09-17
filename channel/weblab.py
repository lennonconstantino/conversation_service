

from typing import Any, Dict
from channel import Channel
from models import MessageData, MessageOwner
from service import ConversationService

class Weblab(Channel):
    def __init__(self, service: ConversationService):
        self.service = service
    
    def save_request(self, owner: MessageOwner, channel: str, client_hub: str, message: str, message_type: str, meta: Dict[str, Any] = None):
        # Usar o método que retorna UUID diretamente
        conversation_uuid, is_new = self.service.get_or_create_conversation_uuid(client_hub, channel)
        
        message_data = MessageData(
            message=message,
            type=message_type,
            owner=owner,
            meta=meta,
            channel=channel
        )
        
        # conversation_uuid já é string, converter para UUID se necessário
        import uuid
        if isinstance(conversation_uuid, str):
            conversation_uuid = uuid.UUID(conversation_uuid)
        
        self.service.add_message(conversation_uuid, message_data)
        
        if is_new:
            print("New conversation created")
        print("New message")

    def save_response(self, owner: MessageOwner, channel: str, client_hub: str, response: str, message_type: str, agent_type: str, meta: Dict[str, Any] = None):
        message_data = MessageData(
            type=message_type,
            message=response,
            owner=owner,
            meta={
                "agent_type": agent_type,
                **(meta or {})
            }
        )
        
        conversation, is_new = self.service.get_or_create_conversation(client_hub=client_hub, channel=channel)
        if is_new:
            print("New message")
            
        self.service.add_message(conversation.conversation_uuid, message_data)

    def receive_message(self, channel: str, client_hub: str, message: str, message_type: str, message_meta: Dict[str, Any] = None):
        self.save_request(MessageOwner.USER, channel=channel, client_hub=client_hub, message=message, message_type=message_type, meta=message_meta)
        

    def respond_message(self, channel: str, client_hub: str, response: str, message_type: str, message_meta: Dict[str, Any] = None):

        self.save_response(MessageOwner.AGENT, channel=channel, client_hub=client_hub, response=response, message_type=message_type, agent_type="finance",
            meta={
                "message_id": "1",
                "template_used": "template",
                "status_code": 200,
                **(message_meta or {})
            })
        
        return response

    def receive_and_respond_message(self, channel: str, client_hub: str, message: str, user: str, message_type: str, message_meta: Dict[str, Any] = None):
        self.receive_message(channel=channel, client_hub=client_hub, message=message, message_type=message_type, message_meta=message_meta)

        # TODO
        # # Get conversation context
        # conversation_context = self.get_conversation_context(user.phone, limit=5)
        
        # # Enhanced message with context
        # enhanced_message = ""
        # if conversation_context:
        #     enhanced_message = f"Context:\n{conversation_context}\n\nNew message: {message}"
        response = "I am fine!!!"

        response = self.respond_message(channel=channel, client_hub=client_hub, response=response, message_type=message_type, message_meta=message_meta)

        print(f"Processed conversation for user: {user}, response: {response}")

