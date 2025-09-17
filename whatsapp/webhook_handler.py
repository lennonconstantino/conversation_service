"""
Handler para processar webhooks do WhatsApp
"""
import json
import logging
import time
from typing import Any, Dict
from fastapi import HTTPException, BackgroundTasks

from whatsapp.dependencies import ServiceFactory
from whatsapp.whatsapp_models import Payload
from config.settings import settings

# Configurar logging
logger = logging.getLogger(__name__)

class WebhookHandler:
    """Handler para processar webhooks do WhatsApp"""
    
    def __init__(self):
        self.service = ServiceFactory.get_whatsapp_service()
    
    def verify_webhook(self, hub_mode: str, hub_challenge: int, hub_verify_token: str) -> int:
        """
        Verifica o webhook do WhatsApp
        
        Args:
            hub_mode: Modo do webhook
            hub_challenge: Challenge para verificação
            hub_verify_token: Token de verificação
            
        Returns:
            int: Challenge se verificação bem-sucedida
            
        Raises:
            HTTPException: Se verificação falhar
        """
        if hub_mode == "subscribe" and hub_verify_token == settings.VERIFICATION_TOKEN:
            logger.info("Webhook verification successful")
            return hub_challenge
        
        logger.warning(f"Webhook verification failed: mode={hub_mode}, token={hub_verify_token}")
        raise HTTPException(status_code=403, detail="Invalid verification token")
    
    async def handle_webhook(self, data: Dict[Any, Any], background_tasks: BackgroundTasks) -> Dict[str, Any]:
        """
        Processa webhook do WhatsApp
        
        Args:
            data: Dados do webhook
            background_tasks: Tarefas em background do FastAPI
            
        Returns:
            Dict com status da operação
        """
        start_time = time.time()
        
        try:
            if settings.DEBUG:
                logger.info(f"Received WhatsApp message: {json.dumps(data, indent=2)}")
            
            # Parse do payload
            payload = Payload(**data)
            message = self.service.parse_message(payload)
            
            if not message:
                logger.info("No message found in payload")
                return {"status": "no_message"}
            
            # Verificar se mensagem não é muito antiga
            if self.service.is_message_too_old(message.timestamp):
                logger.warning(f"Message too old: {message.timestamp}")
                raise HTTPException(
                    status_code=422, 
                    detail={
                        "error": "message_expired",
                        "message": "Message is too old to be processed",
                        "max_age_minutes": settings.MESSAGE_EXPIRY_MINUTES
                    }
                )
            
            # Obter usuário
            user = self.service.get_current_user(message)
            if not user:
                logger.warning(f"User not found for phone: {message.from_}")
                raise HTTPException(status_code=404, detail="User not found")
            
            # Extrair conteúdo da mensagem
            user_message = self.service.message_extractor(message, self.service.parse_audio_file(message))
            image = self.service.parse_image_file(message)
            
            if not user_message and not image:
                logger.warning("No message content found")
                raise HTTPException(status_code=400, detail="No message content found")
            
            # Processar imagem
            if image:
                logger.info(f"Image received from user {user.first_name} {user.last_name}")
                return {"status": "image_received", "user_phone": user.phone}
            
            # Processar mensagem de texto/áudio
            if user_message:
                logger.info(f"Processing message from user {user.first_name} {user.last_name} ({user.phone})")
                
                # Adicionar processamento em background
                background_tasks.add_task(self.service.respond_and_send_message, payload)
                
                processing_time = round((time.time() - start_time) * 1000, 2)
                
                return {
                    "status": "accepted",
                    "type": message.type,
                    "user_phone": user.phone,
                    "processing_time_ms": processing_time
                }
            
            # Fallback (não deveria chegar aqui)
            logger.warning("Unexpected state: no action taken")
            return {"status": "no_action_taken"}
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error processing webhook: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error")
