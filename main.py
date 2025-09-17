from channel.weblab import Weblab
from db import DatabaseConfig
from repository import ConversationRepository
from service import ConversationService


def main():
    print()

    db = DatabaseConfig("sqlite", db_path="conversations_example.db")
    repository = ConversationRepository(db)
    service = ConversationService(repository)
    weblab = Weblab(service)

    weblab.receive_and_respond_message("weblab", "teste_hub", "Hello!!!", "lennon", "text")

if __name__ == "__main__":
    main()
