from weblocal.helpers import PayloadBuilder
from weblocal.message_service import MessageService
from db import DatabaseConfig
from repository import ConversationRepository
from service import ConversationService


def teste_simples():
    print()

    db = DatabaseConfig("sqlite", db_path="conversations.db")
    repository = ConversationRepository(db)
    service = ConversationService(repository)
    message_service = MessageService(service)

    user = "lennon"
    text_payload = PayloadBuilder.create_text_payload(
        user_id=user,
        message_text="Olá! Como você está?"
    )

    response = message_service.receive_and_respond_message(text_payload)

    print(f"Processed conversation for user: {user}, response: {response}")

def teste_completo():
    # Configurar o banco de dados e serviços
    db_config = DatabaseConfig("sqlite", db_path="conversations.db")
    repository = ConversationRepository(db_config)
    conversation_service = ConversationService(repository)
    message_service = MessageService(conversation_service)
    
    print("=== Sistema de Conversação Local ===\n")
    
    # Exemplo 1: Mensagem de texto
    print("1. Enviando mensagem de texto...")
    text_payload = PayloadBuilder.create_text_payload(
        user_id="user_123",
        message_text="Olá! Como você está?"
    )
    
    result = message_service.receive_and_respond_message(text_payload)
    print(f"Status: {result['status']}")
    print(f"Resposta: {result.get('response_text', 'N/A')}")
    print(f"Tempo: {result.get('processing_time_ms', 0)}ms\n")
    
    # Exemplo 2: Outra mensagem do mesmo usuário
    print("2. Enviando segunda mensagem...")
    text_payload2 = PayloadBuilder.create_text_payload(
        user_id="user_123",
        message_text="Preciso de ajuda com um problema técnico"
    )
    
    result2 = message_service.receive_and_respond_message(text_payload2)
    print(f"Status: {result2['status']}")
    print(f"Resposta: {result2.get('response_text', 'N/A')}")
    print(f"UUID da conversa: {result2.get('conversation_uuid', 'N/A')}\n")
    
    # Exemplo 3: Mensagem de áudio (mock)
    print("3. Enviando mensagem de áudio...")
    audio_payload = PayloadBuilder.create_audio_payload(
        user_id="user_123",
        audio_id="audio_456",
        mime_type="audio/ogg"
    )
    
    result3 = message_service.receive_and_respond_message(audio_payload)
    print(f"Status: {result3['status']}")
    print(f"Resposta: {result3.get('response_text', 'N/A')}\n")
    
    # Exemplo 4: Mensagem de imagem (mock)
    print("4. Enviando mensagem de imagem...")
    image_payload = PayloadBuilder.create_image_payload(
        user_id="user_123",
        image_id="image_789",
        mime_type="image/jpeg"
    )
    
    result4 = message_service.receive_and_respond_message(image_payload)
    print(f"Status: {result4['status']}")
    print(f"Resposta: {result4.get('response_text', 'N/A')}\n")
    
    # Exemplo 5: Novo usuário
    print("5. Mensagem de novo usuário...")
    new_user_payload = PayloadBuilder.create_text_payload(
        user_id="user_456",
        message_text="Primeira mensagem de um novo usuário!"
    )
    
    result5 = message_service.receive_and_respond_message(new_user_payload)
    print(f"Status: {result5['status']}")
    print(f"Nova conversa: {result5.get('conversation_uuid', 'N/A')}")
    print(f"Resposta: {result5.get('response_text', 'N/A')}\n")
    
    # Exemplo 6: Verificar histórico de conversação
    print("6. Verificando histórico da conversa...")
    from weblocal.models import User
    user = User(id=123, first_name="Local", last_name="User")
    context = message_service.get_conversation_context(user, limit=5)
    print(f"Contexto da conversa:\n{context}\n")
    
    # Exemplo 7: Estatísticas das conversas
    print("7. Estatísticas das conversas...")
    stats = conversation_service.get_conversation_stats()
    print(f"Total de conversas: {stats['total_conversations']}")
    print(f"Conversas ativas: {stats['active_conversations']}")
    print(f"Média de mensagens: {stats['average_messages_per_conversation']}")

def interactive_chat():
    """Função para chat interativo no terminal"""
    db_config = DatabaseConfig("sqlite", db_path="interactive_chat.db")
    repository = ConversationRepository(db_config)
    conversation_service = ConversationService(repository)
    message_service = MessageService(conversation_service)
    
    print("=== Chat Interativo Local ===")
    print("Digite 'quit' para sair")
    print("Digite 'stats' para ver estatísticas")
    print("Digite 'history' para ver histórico\n")
    
    user_id = input("Digite seu ID de usuário (ex: user_123): ")
    
    while True:
        user_input = input(f"\n[{user_id}]: ").strip()
        
        if user_input.lower() == 'quit':
            print("Tchau!")
            break
        elif user_input.lower() == 'stats':
            stats = conversation_service.get_conversation_stats()
            print(f"\n📊 Estatísticas:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
            continue
        elif user_input.lower() == 'history':
            from weblocal.models import User
            user = User(id=int(user_id.replace("user_", "")) if "user_" in user_id else 1, 
                       first_name="Interactive", last_name="User")
            context = message_service.get_conversation_context(user, limit=10)
            print(f"\n📝 Histórico:\n{context}")
            continue
        
        if not user_input:
            continue
            
        # Criar payload e processar
        payload = PayloadBuilder.create_text_payload(user_id, user_input)
        result = message_service.receive_and_respond_message(payload)
        
        if result['status'] == 'processed':
            print(f"🤖 Agente: {result['response_text']}")
        else:
            print(f"❌ Erro: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    teste_simples()
    teste_completo()
    #interactive_chat()

