
import json
import logging
import os
import sys
from pathlib import Path
import time
import threading
from typing import Any, Dict
import uvicorn
from dotenv import load_dotenv

# Add the project root to Python path
# project_root = Path(__file__).resolve().parents[5]  # sobe até o raiz do projeto
# sys.path.insert(0, str(project_root))

# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from conversation.db import DatabaseConfig
from conversation.repository import ConversationRepository
from conversation.service import ConversationService
from whatsapp.whatsapp_models import Payload
from whatsapp.whatsapp_service import WhatsappService
_ = load_dotenv()

from fastapi import FastAPI, Query, HTTPException, BackgroundTasks

IS_DEV_ENVIRONMENT = True
DEBUG = True
VERIFICATION_TOKEN = os.getenv("VERIFICATION_TOKEN")

app = FastAPI(
    title="WhatsApp Bot",
    version="0.1.0",
    openapi_url=f"/openapi.json" if IS_DEV_ENVIRONMENT else None,
    docs_url=f"/docs" if IS_DEV_ENVIRONMENT else None,
    redoc_url=f"/redoc" if IS_DEV_ENVIRONMENT else None,
    swagger_ui_oauth2_redirect_url=f"/docs/oauth2-redirect" if IS_DEV_ENVIRONMENT else None,
)

log = logging.getLogger(__name__)

MESSAGE_EXPIRY_MINUTES = 5  # Mensagens mais antigas que 5 minutos são descartadas


@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/readiness")
def readiness():
    return {"status": "ready"}

@app.get("/webhook")
def verify_whatsapp(
        hub_mode: str = Query("subscribe", description="The mode of the webhook", alias="hub.mode"),
        hub_challenge: int = Query(..., description="The challenge to verify the webhook", alias="hub.challenge"),
        hub_verify_token: str = Query(..., description="The verification token", alias="hub.verify_token"),
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFICATION_TOKEN:
        return hub_challenge

    raise HTTPException(status_code=403, detail="Invalid verification token")

@app.post('/webhook', status_code=200)
def whatsapp_webhook(data: Dict[Any, Any], background_tasks: BackgroundTasks):
    """
    Endpoint para receber webhooks do WhatsApp
    """
    start_time = time.time()

    if DEBUG:
        print("Received WhatsApp message:\n", json.dumps(data, indent=2))

    db = DatabaseConfig("sqlite", db_path="conversations.db")
    repository = ConversationRepository(db)
    conversation = ConversationService(repository)
    service = WhatsappService(conversation)
    
    payload = Payload(**data)
    # TODO
    message = service.parse_message(payload=payload)
    user = service.get_current_user(message)
    audio = service.parse_audio_file(message)
    user_message = service.message_extractor(message, audio)
    image = service.parse_image_file(message)

    if not user and not user_message and not image:
        # status message
        return {"status": "ok"}

    if message and service.is_message_too_old(message.timestamp):
        raise HTTPException(status_code=422, detail={
            "error": "message_expired",
            "message": "Message is too old to be processed",
            "max_age_minutes": MESSAGE_EXPIRY_MINUTES
        })
        
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user_message and not image:
        raise HTTPException(status_code=400, detail="No message content found")
    
    if image:
        return print("Image received")

    if user_message:
        print(f"Received message from user {user.first_name} {user.last_name} ({user.phone})")
        background_tasks.add_task(service.respond_and_send_message, payload)
        return {
            "status": "accepted", 
            "type": message.type,
            "user_phone": user.phone,
            "processing_time_ms": round((time.time() - start_time) * 1000, 2)
        }

    # Fallback (não deveria chegar aqui)
    return {"status": "no_action_taken"}

if __name__ == "__main__":
    # noinspection PyTypeChecker
    port = 5001 # default 8000
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)  # nosec
