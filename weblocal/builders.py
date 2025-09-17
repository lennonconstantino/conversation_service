
import uuid
import time

from weblocal.models import Audio, Change, Entry, Image, Payload, Value, Text, Message

# Classe helper para criar payloads locais facilmente
class PayloadBuilder:
    """Builder para criar payloads locais de forma simples"""
    
    @staticmethod
    def create_text_payload(user_id: str, message_text: str, messaging_product: str = "local") -> Payload:
        """Cria um payload para mensagem de texto"""
        message = Message(
            **{
                "from": user_id,
                "id": str(uuid.uuid4()),
                "timestamp": str(int(time.time())),
                "text": Text(body=message_text),
                "type": "text"
            }
        )
        
        return PayloadBuilder._build_payload(message, messaging_product)
    
    @staticmethod
    def create_audio_payload(user_id: str, audio_id: str, mime_type: str = "audio/ogg", 
                           messaging_product: str = "local") -> Payload:
        """Cria um payload para mensagem de áudio"""
        message = Message(
            **{
                "from": user_id,
                "id": str(uuid.uuid4()),
                "timestamp": str(int(time.time())),
                "audio": Audio(
                    mime_type=mime_type,
                    sha256="mock_sha256",
                    id=audio_id,
                    voice=True
                ),
                "type": "audio"
            }
        )
        
        return PayloadBuilder._build_payload(message, messaging_product)
    
    @staticmethod
    def create_image_payload(user_id: str, image_id: str, mime_type: str = "image/jpeg",
                           messaging_product: str = "local") -> Payload:
        """Cria um payload para mensagem de imagem"""
        message = Message(
            **{
                "from": user_id,
                "id": str(uuid.uuid4()),
                "timestamp": str(int(time.time())),
                "image": Image(
                    mime_type=mime_type,
                    sha256="mock_sha256",
                    id=image_id
                ),
                "type": "image"
            }
        )
        
        return PayloadBuilder._build_payload(message, messaging_product)
    
    @staticmethod
    def _build_payload(message: Message, messaging_product: str) -> Payload:
        """Constrói o payload completo"""
        return Payload(
            object="whatsapp_business_account",
            entry=[
                Entry(
                    id="local_entry",
                    changes=[
                        Change(
                            value=Value(
                                messaging_product=messaging_product,
                                messages=[message]
                            ),
                            field="messages"
                        )
                    ]
                )
            ]
        )