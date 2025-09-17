
import logging
import uvicorn
from fastapi import FastAPI, Query, BackgroundTasks

from whatsapp.webhook_handler import WebhookHandler
from config.settings import settings

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Criar instância do handler
webhook_handler = WebhookHandler()

# Configurar FastAPI
app = FastAPI(
    title="WhatsApp Bot",
    version="0.1.0",
    openapi_url=f"/openapi.json" if settings.IS_DEV_ENVIRONMENT else None,
    docs_url=f"/docs" if settings.IS_DEV_ENVIRONMENT else None,
    redoc_url=f"/redoc" if settings.IS_DEV_ENVIRONMENT else None,
    swagger_ui_oauth2_redirect_url=f"/docs/oauth2-redirect" if settings.IS_DEV_ENVIRONMENT else None,
)


@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/readiness")
def readiness():
    return {"status": "ready"}

@app.get("/webhook")
def verify_webhook(
        hub_mode: str = Query("subscribe", description="The mode of the webhook", alias="hub.mode"),
        hub_challenge: int = Query(..., description="The challenge to verify the webhook", alias="hub.challenge"),
        hub_verify_token: str = Query(..., description="The verification token", alias="hub.verify_token"),
):
    """Endpoint para verificação do webhook do WhatsApp"""
    return webhook_handler.verify_webhook(hub_mode, hub_challenge, hub_verify_token)

@app.post("/webhook", status_code=200)
async def webhook(data: dict, background_tasks: BackgroundTasks):
    """Endpoint para receber webhooks do WhatsApp"""
    return await webhook_handler.handle_webhook(data, background_tasks)

if __name__ == "__main__":
    logger.info(f"Starting WhatsApp Bot on {settings.HOST}:{settings.PORT}")
    uvicorn.run(
        "whatsapp.server:app", 
        host=settings.HOST, 
        port=settings.PORT, 
        reload=settings.DEBUG
    )
