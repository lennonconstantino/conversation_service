#!/usr/bin/env python3
"""
CLI robusto para o sistema Weblocal
"""
import argparse
import logging
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from weblocal.dependencies import WeblocalServiceFactory
from weblocal.builders import PayloadBuilder
from weblocal.models import User

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WeblocalCLI:
    """CLI para interagir com o sistema Weblocal"""
    
    def __init__(self):
        self.weblocal = None
        self.conversation_service = None
    
    def setup_services(self, db_path: str = None):
        """Configura os serviços"""
        try:
            self.weblocal = WeblocalServiceFactory.get_weblocal_service(db_path)
            self.conversation_service = WeblocalServiceFactory.get_conversation_service(db_path)
            logger.info("Serviços configurados com sucesso")
        except Exception as e:
            logger.error(f"Erro ao configurar serviços: {e}")
            sys.exit(1)
    
    def send_message(self, user_id: str, message: str, message_type: str = "text"):
        """Envia uma mensagem"""
        try:
            if message_type == "text":
                payload = PayloadBuilder.create_text_payload(user_id, message)
            elif message_type == "audio":
                payload = PayloadBuilder.create_audio_payload(user_id, f"audio_{user_id}", "audio/ogg")
            elif message_type == "image":
                payload = PayloadBuilder.create_image_payload(user_id, f"image_{user_id}", "image/jpeg")
            else:
                raise ValueError(f"Tipo de mensagem inválido: {message_type}")
            
            result = self.weblocal.respond_and_send_message(payload)
            
            if result['status'] == 'processed':
                print(f"✅ Mensagem processada com sucesso!")
                print(f"Resposta: {result['response_text']}")
                print(f"Tempo: {result['processing_time_ms']}ms")
                return True
            else:
                print(f"❌ Erro: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem: {e}")
            print(f"❌ Erro: {e}")
            return False
    
    def show_stats(self):
        """Mostra estatísticas"""
        try:
            stats = self.conversation_service.get_conversation_stats()
            print("\n📊 Estatísticas das Conversas:")
            print("=" * 40)
            for key, value in stats.items():
                print(f"{key}: {value}")
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            print(f"❌ Erro: {e}")
    
    def show_history(self, user_id: str, limit: int = 10):
        """Mostra histórico de conversa"""
        try:
            # Usar a mesma lógica do WeblocalService
            try:
                if "user_" in user_id:
                    user_id_num = int(user_id.replace("user_", ""))
                else:
                    user_id_num = abs(hash(user_id)) % 1000000
            except (ValueError, TypeError):
                user_id_num = 1
            
            user = User(id=user_id_num, first_name="CLI", last_name="User")
            context = self.weblocal.get_conversation_context(user, limit=limit)
            
            if context:
                print(f"\n📝 Histórico da conversa (últimas {limit} mensagens):")
                print("=" * 50)
                print(context)
            else:
                print("📝 Nenhum histórico encontrado para este usuário.")
                
        except Exception as e:
            logger.error(f"Erro ao obter histórico: {e}")
            print(f"❌ Erro: {e}")
    
    def interactive_mode(self, user_id: str):
        """Modo interativo"""
        print(f"\n💬 Modo Interativo - Usuário: {user_id}")
        print("Digite 'quit' para sair, 'help' para ajuda")
        print("-" * 50)
        
        while True:
            try:
                user_input = input(f"\n[{user_id}]: ").strip()
                
                if user_input.lower() == 'quit':
                    print("Tchau!")
                    break
                elif user_input.lower() == 'help':
                    self._show_help()
                    continue
                elif user_input.lower() == 'stats':
                    self.show_stats()
                    continue
                elif user_input.lower() == 'history':
                    self.show_history(user_id)
                    continue
                
                if not user_input:
                    continue
                
                self.send_message(user_id, user_input)
                
            except KeyboardInterrupt:
                print("\n\nChat interrompido pelo usuário.")
                break
            except Exception as e:
                logger.error(f"Erro no modo interativo: {e}")
                print(f"❌ Erro: {e}")
    
    def _show_help(self):
        """Mostra ajuda"""
        print("\n📋 Comandos disponíveis:")
        print("  quit     - Sair do chat")
        print("  stats    - Ver estatísticas")
        print("  history  - Ver histórico")
        print("  help     - Mostrar esta ajuda")

def main():
    """Função principal do CLI"""
    parser = argparse.ArgumentParser(description="CLI para sistema Weblocal")
    parser.add_argument("--db", help="Caminho do banco de dados", default=None)
    parser.add_argument("--user", help="ID do usuário", default="user_cli")
    parser.add_argument("--message", help="Mensagem para enviar")
    parser.add_argument("--type", help="Tipo da mensagem (text/audio/image)", default="text")
    parser.add_argument("--stats", action="store_true", help="Mostrar estatísticas")
    parser.add_argument("--history", action="store_true", help="Mostrar histórico")
    parser.add_argument("--interactive", action="store_true", help="Modo interativo")
    parser.add_argument("--limit", type=int, default=10, help="Limite de mensagens no histórico")
    
    args = parser.parse_args()
    
    # Criar instância do CLI
    cli = WeblocalCLI()
    cli.setup_services(args.db)
    
    try:
        if args.stats:
            cli.show_stats()
        elif args.history:
            cli.show_history(args.user, args.limit)
        elif args.interactive:
            cli.interactive_mode(args.user)
        elif args.message:
            cli.send_message(args.user, args.message, args.type)
        else:
            # Modo padrão - mostrar menu
            print("🚀 Weblocal CLI")
            print("=" * 30)
            print("Use --help para ver todas as opções")
            print("Exemplos:")
            print("  python cli.py --message 'Olá mundo'")
            print("  python cli.py --interactive --user user_123")
            print("  python cli.py --stats")
            print("  python cli.py --history --user user_123")
            
    except Exception as e:
        logger.error(f"Erro na execução: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
