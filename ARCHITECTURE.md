# 🏗️ Arquitetura Detalhada - Conversation Service

Este documento contém diagramas detalhados da arquitetura do sistema.

## 📊 Diagramas de Arquitetura

### 1. Arquitetura Geral do Sistema

```mermaid
graph TB
    subgraph "External Layer"
        WA[WhatsApp Business API]
        CLI[Command Line Interface]
        USER[End Users]
    end
    
    subgraph "API Layer"
        WS[WhatsApp Server<br/>FastAPI]
        WLC[Weblocal CLI<br/>argparse]
    end
    
    subgraph "Handler Layer"
        WH[Webhook Handler]
        WLS[Weblocal Service]
    end
    
    subgraph "Business Logic Layer"
        CS[Conversation Service]
        WSS[WhatsApp Service]
    end
    
    subgraph "Data Access Layer"
        CR[Conversation Repository]
        DB[(SQLite/PostgreSQL<br/>Database)]
    end
    
    subgraph "Configuration Layer"
        SETTINGS[Settings<br/>Pydantic]
        CONFIG[Conversation Config]
        EXCEPTIONS[Custom Exceptions]
    end
    
    subgraph "Models Layer"
        WAM[WhatsApp Models<br/>Pydantic]
        WLM[Weblocal Models<br/>Pydantic]
        CM[Conversation Models<br/>SQLAlchemy]
    end
    
    USER --> WA
    USER --> CLI
    WA --> WS
    CLI --> WLC
    WS --> WH
    WLC --> WLS
    WH --> WSS
    WLS --> CS
    WSS --> CS
    CS --> CR
    CR --> DB
    SETTINGS --> CS
    CONFIG --> CS
    EXCEPTIONS --> CS
    WAM --> WSS
    WLM --> WLS
    CM --> CR
```

### 2. Fluxo de Processamento de Mensagem WhatsApp

```mermaid
sequenceDiagram
    participant U as User
    participant WA as WhatsApp API
    participant WS as WhatsApp Server
    participant WH as Webhook Handler
    participant WSS as WhatsApp Service
    participant CS as Conversation Service
    participant CR as Conversation Repository
    participant DB as Database
    participant AI as AI Response Generator
    
    U->>WA: Send Message
    WA->>WS: POST /webhook
    WS->>WH: handle_webhook()
    WH->>WSS: parse_message()
    WSS->>WSS: validate_user()
    WSS->>WSS: check_message_age()
    WSS->>CS: get_or_create_conversation()
    CS->>CR: get_or_create_conversation_uuid()
    CR->>DB: Query/Insert Conversation
    DB-->>CR: Conversation Data
    CR-->>CS: (uuid, is_new)
    CS-->>WSS: Conversation UUID
    WSS->>CS: save_request()
    CS->>CR: add_message()
    CR->>DB: Insert User Message
    DB-->>CR: Message Data
    CR-->>CS: (message_dict, closed)
    CS-->>WSS: User Message Saved
    WSS->>AI: generate_response()
    AI-->>WSS: AI Response
    WSS->>CS: save_response()
    CS->>CR: add_message()
    CR->>DB: Insert Agent Message
    DB-->>CR: Message Data
    CR-->>CS: (message_dict, closed)
    CS-->>WSS: Agent Message Saved
    WSS-->>WH: Processing Complete
    WH-->>WS: HTTP 200 OK
    WS-->>WA: Webhook Acknowledgment
```

### 3. Fluxo de Processamento Local (CLI)

```mermaid
sequenceDiagram
    participant U as User
    participant CLI as Weblocal CLI
    participant WLS as Weblocal Service
    participant CS as Conversation Service
    participant CR as Conversation Repository
    participant DB as Database
    
    U->>CLI: python cli.py --message "Hello"
    CLI->>CLI: parse_arguments()
    CLI->>WLS: respond_and_send_message()
    WLS->>WLS: get_user_by_id()
    WLS->>WLS: parse_message()
    WLS->>CS: get_or_create_conversation()
    CS->>CR: get_or_create_conversation_uuid()
    CR->>DB: Query/Insert Conversation
    DB-->>CR: Conversation Data
    CR-->>CS: (uuid, is_new)
    CS-->>WLS: Conversation UUID
    WLS->>CS: save_request()
    CS->>CR: add_message()
    CR->>DB: Insert User Message
    DB-->>CR: Message Data
    CR-->>CS: (message_dict, closed)
    CS-->>WLS: User Message Saved
    WLS->>WLS: generate_response()
    WLS->>CS: save_response()
    CS->>CR: add_message()
    CR->>DB: Insert Agent Message
    DB-->>CR: Message Data
    CR-->>CS: (message_dict, closed)
    CS-->>WLS: Agent Message Saved
    WLS-->>CLI: Response Data
    CLI-->>U: Display Response
```

### 4. Estrutura de Dados

```mermaid
erDiagram
    CONVERSATION {
        uuid conversation_uuid PK
        string client_hub
        string channel
        datetime created_at
        datetime updated_at
        datetime last_activity_at
        enum status
        int idle_timeout_minutes
        text closed_by_message
        datetime closed_at
    }
    
    MESSAGE {
        uuid id PK
        uuid conversation_uuid FK
        enum type
        text message
        datetime timestamp
        enum owner
        string channel
        json meta
        boolean closes_conversation
    }
    
    CONVERSATION ||--o{ MESSAGE : contains
```

### 5. Padrões de Design Implementados

```mermaid
graph LR
    subgraph "Factory Pattern"
        SF[ServiceFactory]
        WSF[WeblocalServiceFactory]
        SF --> WS[WhatsApp Service]
        SF --> CS[Conversation Service]
        WSF --> WLS[Weblocal Service]
        WSF --> CS2[Conversation Service]
    end
    
    subgraph "Repository Pattern"
        CR[Conversation Repository]
        CS3[Conversation Service]
        CR --> DB[(Database)]
        CS3 --> CR
    end
    
    subgraph "Strategy Pattern"
        CH[Channel Interface]
        WS2[WhatsApp Service]
        WLS2[Weblocal Service]
        CH <|-- WS2
        CH <|-- WLS2
    end
    
    subgraph "Configuration Pattern"
        SETTINGS[Settings]
        CONFIG[Conversation Config]
        SETTINGS --> CONFIG
    end
```

### 6. Fluxo de Configuração

```mermaid
graph TD
    ENV[Environment Variables] --> SETTINGS[Settings.py<br/>Pydantic BaseSettings]
    SETTINGS --> CONFIG[Conversation Config]
    SETTINGS --> DB_CONFIG[Database Config]
    SETTINGS --> WA_CONFIG[WhatsApp Config]
    
    CONFIG --> CS[Conversation Service]
    DB_CONFIG --> CR[Conversation Repository]
    WA_CONFIG --> WSS[WhatsApp Service]
    
    CS --> VALIDATION[Data Validation]
    CR --> DB_CONNECTION[Database Connection]
    WSS --> API_CONFIG[API Configuration]
```

### 7. Tratamento de Erros

```mermaid
graph TD
    REQUEST[Incoming Request] --> VALIDATE[Input Validation]
    VALIDATE -->|Valid| PROCESS[Process Request]
    VALIDATE -->|Invalid| VALIDATION_ERROR[ValidationError]
    
    PROCESS --> DB_OP[Database Operation]
    DB_OP -->|Success| RESPONSE[Return Response]
    DB_OP -->|Error| DB_ERROR[DatabaseError]
    
    VALIDATION_ERROR --> LOG_ERROR[Log Error]
    DB_ERROR --> LOG_ERROR
    LOG_ERROR --> ERROR_RESPONSE[Return Error Response]
    
    RESPONSE --> LOG_SUCCESS[Log Success]
    ERROR_RESPONSE --> LOG_SUCCESS
```

### 8. Sistema de Logging

```mermaid
graph LR
    subgraph "Application Components"
        WS[WhatsApp Server]
        WLS[Weblocal Service]
        CS[Conversation Service]
        CR[Conversation Repository]
    end
    
    subgraph "Logging Levels"
        DEBUG[DEBUG<br/>Detailed Info]
        INFO[INFO<br/>General Info]
        WARNING[WARNING<br/>Warnings]
        ERROR[ERROR<br/>Errors]
    end
    
    WS --> DEBUG
    WLS --> INFO
    CS --> WARNING
    CR --> ERROR
    
    DEBUG --> LOG_FILE[Log File]
    INFO --> LOG_FILE
    WARNING --> LOG_FILE
    ERROR --> LOG_FILE
```

### 9. Fluxo de Cleanup de Conversas

```mermaid
graph TD
    START[Start Cleanup] --> CHECK_CONFIG{Cleanup Enabled?}
    CHECK_CONFIG -->|No| SKIP[Skip Cleanup]
    CHECK_CONFIG -->|Yes| QUERY[Query Active Conversations]
    
    QUERY --> LOOP[For Each Conversation]
    LOOP --> CHECK_EXPIRED{Is Expired?}
    CHECK_EXPIRED -->|No| NEXT[Next Conversation]
    CHECK_EXPIRED -->|Yes| CLOSE[Close Conversation]
    
    CLOSE --> UPDATE_STATUS[Update Status to IDLE_TIMEOUT]
    UPDATE_STATUS --> COMMIT[Commit Changes]
    COMMIT --> NEXT
    
    NEXT --> MORE{More Conversations?}
    MORE -->|Yes| LOOP
    MORE -->|No| LOG_RESULT[Log Cleanup Result]
    
    LOG_RESULT --> END[End Cleanup]
    SKIP --> END
```

### 10. Validação de Dados

```mermaid
graph TD
    INPUT[Input Data] --> PYDANTIC[Pydantic Validation]
    PYDANTIC -->|Valid| BUSINESS_RULES[Business Rules Validation]
    PYDANTIC -->|Invalid| PYDANTIC_ERROR[PydanticError]
    
    BUSINESS_RULES --> MESSAGE_LENGTH{Message Length OK?}
    MESSAGE_LENGTH -->|No| LENGTH_ERROR[MessageTooLongError]
    MESSAGE_LENGTH -->|Yes| USER_EXISTS{User Exists?}
    
    USER_EXISTS -->|No| USER_ERROR[UserNotFoundError]
    USER_EXISTS -->|Yes| CONVERSATION_ACTIVE{Conversation Active?}
    
    CONVERSATION_ACTIVE -->|No| CONVERSATION_ERROR[ConversationClosedError]
    CONVERSATION_ACTIVE -->|Yes| SUCCESS[Validation Success]
    
    PYDANTIC_ERROR --> LOG_ERROR[Log Error]
    LENGTH_ERROR --> LOG_ERROR
    USER_ERROR --> LOG_ERROR
    CONVERSATION_ERROR --> LOG_ERROR
    SUCCESS --> PROCESS[Process Request]
```

## 🔧 Componentes Técnicos

### Tecnologias Utilizadas

- **FastAPI**: Framework web moderno e rápido
- **SQLAlchemy**: ORM para Python
- **Pydantic**: Validação de dados e configurações
- **SQLite/PostgreSQL**: Banco de dados
- **Uvicorn**: Servidor ASGI
- **Python 3.8+**: Linguagem de programação

### Padrões de Arquitetura

1. **Layered Architecture**: Separação em camadas
2. **Repository Pattern**: Abstração de acesso a dados
3. **Factory Pattern**: Criação de objetos
4. **Strategy Pattern**: Diferentes implementações de canais
5. **Configuration Pattern**: Configurações centralizadas
6. **Exception Handling**: Tratamento específico de erros

### Princípios SOLID

- **S**: Single Responsibility - Cada classe tem uma responsabilidade
- **O**: Open/Closed - Aberto para extensão, fechado para modificação
- **L**: Liskov Substitution - Substituição de implementações
- **I**: Interface Segregation - Interfaces específicas
- **D**: Dependency Inversion - Dependência de abstrações

---

Este documento fornece uma visão detalhada da arquitetura do sistema, facilitando a compreensão e manutenção do código.
