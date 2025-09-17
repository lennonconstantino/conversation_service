import logging
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from weblocal.builders import PayloadBuilder
from weblocal.dependencies import WeblocalServiceFactory
from weblocal.weblocal_service import WeblocalService
from weblocal.models import User

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def teste_simples():
    """Teste simples de uma mensagem"""
    logger.info("=== Teste Simples ===")
    
    try:
        # Usar factory para obter serviço
        message_service = WeblocalServiceFactory.get_weblocal_service()
        
        user = "user_lennon"
        text_payload = PayloadBuilder.create_text_payload(
            user_id=user,
            message_text="Olá! Como você está?"
        )

        response = message_service.respond_and_send_message(text_payload)
        
        if response['status'] == 'processed':
            logger.info(f"✅ Processed conversation for user: {user}")
            logger.info(f"Response: {response['response_text']}")
            logger.info(f"Processing time: {response['processing_time_ms']}ms")
        else:
            logger.error(f"❌ Error processing message: {response.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"❌ Teste simples falhou: {e}", exc_info=True)

def teste_completo():
    """Teste completo com múltiplos cenários"""
    logger.info("=== Teste Completo - Sistema de Conversação Local ===")
    
    try:
        # Usar factory para obter serviço
        weblocal = WeblocalServiceFactory.get_weblocal_service()
        conversation_service = WeblocalServiceFactory.get_conversation_service()
        
        # Executar todos os testes
        _teste_mensagem_texto(weblocal)
        _teste_segunda_mensagem(weblocal)
        _teste_mensagem_audio(weblocal)
        _teste_mensagem_imagem(weblocal)
        _teste_novo_usuario(weblocal)
        _teste_historico_conversa(weblocal)
        _teste_estatisticas(conversation_service)
        
        logger.info("✅ Todos os testes completos executados com sucesso!")
        
    except Exception as e:
        logger.error(f"❌ Teste completo falhou: {e}", exc_info=True)

def _teste_mensagem_texto(weblocal):
    """Teste 1: Mensagem de texto"""
    logger.info("1. Enviando mensagem de texto...")
    
    text_payload = PayloadBuilder.create_text_payload(
        user_id="user_123",
        message_text="Olá! Como você está?"
    )
    
    result = weblocal.respond_and_send_message(text_payload)
    _log_result("Mensagem de texto", result)

def _teste_segunda_mensagem(weblocal):
    """Teste 2: Segunda mensagem do mesmo usuário"""
    logger.info("2. Enviando segunda mensagem...")
    
    text_payload2 = PayloadBuilder.create_text_payload(
        user_id="user_123",
        message_text="Preciso de ajuda com um problema técnico"
    )
    
    result2 = weblocal.respond_and_send_message(text_payload2)
    _log_result("Segunda mensagem", result2)

def _teste_mensagem_audio(weblocal):
    """Teste 3: Mensagem de áudio"""
    logger.info("3. Enviando mensagem de áudio...")
    
    audio_payload = PayloadBuilder.create_audio_payload(
        user_id="user_123",
        audio_id="audio_456",
        mime_type="audio/ogg"
    )
    
    result3 = weblocal.respond_and_send_message(audio_payload)
    _log_result("Mensagem de áudio", result3)

def _teste_mensagem_imagem(weblocal):
    """Teste 4: Mensagem de imagem"""
    logger.info("4. Enviando mensagem de imagem...")
    
    image_payload = PayloadBuilder.create_image_payload(
        user_id="user_123",
        image_id="image_789",
        mime_type="image/jpeg"
    )
    
    result4 = weblocal.respond_and_send_message(image_payload)
    _log_result("Mensagem de imagem", result4)

def _teste_novo_usuario(weblocal):
    """Teste 5: Novo usuário"""
    logger.info("5. Mensagem de novo usuário...")
    
    new_user_payload = PayloadBuilder.create_text_payload(
        user_id="user_456",
        message_text="Primeira mensagem de um novo usuário!"
    )
    
    result5 = weblocal.respond_and_send_message(new_user_payload)
    _log_result("Novo usuário", result5)

def _teste_historico_conversa(weblocal):
    """Teste 6: Histórico de conversa"""
    logger.info("6. Verificando histórico da conversa...")
    
    user = User(id=123, first_name="Local", last_name="User")
    context = weblocal.get_conversation_context(user, limit=5)
    logger.info(f"Contexto da conversa:\n{context}")

def _teste_estatisticas(conversation_service):
    """Teste 7: Estatísticas"""
    logger.info("7. Estatísticas das conversas...")
    
    stats = conversation_service.get_conversation_stats()
    logger.info(f"Total de conversas: {stats['total_conversations']}")
    logger.info(f"Conversas ativas: {stats['active_conversations']}")
    logger.info(f"Média de mensagens: {stats['average_messages_per_conversation']}")

def _log_result(test_name: str, result: dict):
    """Helper para logar resultados de teste"""
    if result['status'] == 'processed':
        logger.info(f"✅ {test_name}: {result['response_text']} ({result['processing_time_ms']}ms)")
    else:
        logger.error(f"❌ {test_name} falhou: {result.get('error', 'Unknown error')}")

def interactive_chat():
    """Chat interativo no terminal"""
    logger.info("=== Chat Interativo Local ===")
    print("Digite 'quit' para sair")
    print("Digite 'stats' para ver estatísticas")
    print("Digite 'history' para ver histórico")
    print("Digite 'help' para ver comandos disponíveis\n")
    
    try:
        # Usar factory com banco específico para chat interativo
        weblocal = WeblocalServiceFactory.get_weblocal_service("interactive_chat.db")
        conversation_service = WeblocalServiceFactory.get_conversation_service("interactive_chat.db")
        
        user_id = input("Digite seu ID de usuário (ex: user_123): ").strip()
        if not user_id:
            user_id = "user_interactive"
        
        logger.info(f"Chat iniciado para usuário: {user_id}")
        
        while True:
            user_input = input(f"\n[{user_id}]: ").strip()
            
            if user_input.lower() == 'quit':
                print("Tchau!")
                break
            elif user_input.lower() == 'help':
                _show_help()
                continue
            elif user_input.lower() == 'stats':
                _show_stats(conversation_service)
                continue
            elif user_input.lower() == 'history':
                _show_history(weblocal, user_id)
                continue
            
            if not user_input:
                continue
                
            # Processar mensagem
            payload = PayloadBuilder.create_text_payload(user_id, user_input)
            result = weblocal.respond_and_send_message(payload)
            
            if result['status'] == 'processed':
                print(f"🤖 Agente: {result['response_text']}")
                logger.info(f"Message processed: {result['processing_time_ms']}ms")
            else:
                print(f"❌ Erro: {result.get('error', 'Unknown error')}")
                logger.error(f"Error processing message: {result.get('error')}")
                
    except KeyboardInterrupt:
        print("\n\nChat interrompido pelo usuário.")
        logger.info("Chat interrompido pelo usuário")
    except Exception as e:
        logger.error(f"Erro no chat interativo: {e}", exc_info=True)
        print(f"❌ Erro: {e}")

def _show_help():
    """Mostra comandos disponíveis"""
    print("\n📋 Comandos disponíveis:")
    print("  quit     - Sair do chat")
    print("  stats    - Ver estatísticas das conversas")
    print("  history  - Ver histórico da conversa")
    print("  help     - Mostrar esta ajuda")

def _show_stats(conversation_service):
    """Mostra estatísticas"""
    try:
        stats = conversation_service.get_conversation_stats()
        print(f"\n📊 Estatísticas:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    except Exception as e:
        print(f"❌ Erro ao obter estatísticas: {e}")

def _show_history(weblocal, user_id):
    """Mostra histórico da conversa"""
    try:
        user_id_num = int(user_id.replace("user_", "")) if "user_" in user_id else 1
        user = User(id=user_id_num, first_name="Interactive", last_name="User")
        context = weblocal.get_conversation_context(user, limit=10)
        print(f"\n📝 Histórico:\n{context}")
    except Exception as e:
        print(f"❌ Erro ao obter histórico: {e}")

def main():
    """Função principal com menu de opções"""
    print("🚀 Weblocal Tester - Sistema de Conversação Local")
    print("=" * 50)
    print("1. Teste Simples")
    print("2. Teste Completo")
    print("3. Chat Interativo")
    print("4. Sair")
    print("=" * 50)
    
    while True:
        try:
            choice = input("\nEscolha uma opção (1-4): ").strip()
            
            if choice == "1":
                teste_simples()
            elif choice == "2":
                teste_completo()
            elif choice == "3":
                interactive_chat()
            elif choice == "4":
                print("Tchau!")
                break
            else:
                print("❌ Opção inválida. Escolha entre 1-4.")
                
        except KeyboardInterrupt:
            print("\n\nPrograma interrompido pelo usuário.")
            break
        except Exception as e:
            logger.error(f"Erro na função main: {e}", exc_info=True)
            print(f"❌ Erro: {e}")

if __name__ == "__main__":
    main()

