
# Classe Helper para chamar funcoes utils facilmente
from weblocal.models import User

class Helpers:
    """Helper para chamar funcoes utils de forma simples"""
    
    @staticmethod
    def generate_response(user_message: str, user: User) -> str:
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
