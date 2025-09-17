from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class Channel(ABC):
    @abstractmethod
    def respond_and_send_message(self, payload: Any, channel: str = "default") -> Dict:
        """Processa uma mensagem e retorna resultado"""
        pass

    @abstractmethod
    def extract_message_content(self, message: Any) -> Optional[str]:
        pass