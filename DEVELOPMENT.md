# 🛠️ Guia de Desenvolvimento - Conversation Service

Este documento fornece informações detalhadas para desenvolvedores que trabalham no projeto.

## 🚀 Configuração do Ambiente de Desenvolvimento

### 1. Pré-requisitos

```bash
# Python 3.8+
python --version

# pip
pip --version

# Git
git --version
```

### 2. Configuração Inicial

```bash
# Clone o repositório
git clone <repository-url>
cd conversation_service

# Crie um ambiente virtual
python -m venv venv

# Ative o ambiente virtual
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Instale as dependências
pip install -r requirements.txt

# Configure as variáveis de ambiente
cp env.example .env
# Edite o arquivo .env com suas configurações
```

### 3. Estrutura de Desenvolvimento

```
conversation_service/
├── 📁 channel/                 # Interface abstrata
├── 📁 config/                  # Configurações
├── 📁 conversation/            # Núcleo do sistema
├── 📁 weblocal/               # Interface local
├── 📁 whatsapp/               # Integração WhatsApp
├── 📄 requirements.txt        # Dependências
├── 📄 env.example             # Exemplo de configuração
└── 📄 README.md               # Documentação principal
```

## 🧪 Testes e Desenvolvimento

### Executar Testes

```bash
# Teste do módulo weblocal
python weblocal/weblocal_tester.py

# Teste do módulo whatsapp
python whatsapp/whatsapp_tester.py message "Test message"

# Teste via CLI
python weblocal/cli.py --message "Test" --user test_user

# Teste de estatísticas
python weblocal/cli.py --stats

# Teste de histórico
python weblocal/cli.py --history --user test_user --limit 5
```

### Desenvolvimento Local

```bash
# Iniciar servidor em modo desenvolvimento
uvicorn whatsapp.server:app --host 0.0.0.0 --port 5001 --reload

# Acessar documentação da API
# http://localhost:5001/docs
```

### Debugging

```bash
# Ativar logs detalhados
export LOG_LEVEL=DEBUG

# Verificar configurações
python -c "from config.settings import settings; print(settings.dict())"
```

## 📝 Padrões de Código

### 1. Estrutura de Arquivos

Cada módulo segue a estrutura:

```
module_name/
├── __init__.py              # Inicialização do módulo
├── models.py                # Modelos de dados
├── service.py               # Lógica de negócio
├── repository.py            # Acesso a dados (se aplicável)
├── dependencies.py          # Factory pattern
├── exceptions.py            # Exceções customizadas (se aplicável)
└── config.py                # Configurações específicas (se aplicável)
```

### 2. Imports

```python
# Ordem de imports
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

# Imports de terceiros
from sqlalchemy import create_engine
from pydantic import BaseModel

# Imports locais
from conversation.models import MessageData
from conversation.exceptions import ConversationError
```

### 3. Logging

```python
import logging

logger = logging.getLogger(__name__)

# Diferentes níveis
logger.debug("Informação detalhada para debugging")
logger.info("Informação geral sobre operações")
logger.warning("Avisos sobre situações anômalas")
logger.error("Erros que não impedem o funcionamento")
logger.critical("Erros críticos que impedem o funcionamento")
```

### 4. Tratamento de Erros

```python
try:
    # Operação que pode falhar
    result = some_operation()
    logger.info(f"Operation successful: {result}")
    return result
except SpecificException as e:
    logger.error(f"Specific error occurred: {e}")
    raise CustomException(f"Operation failed: {e}")
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise CustomException(f"Unexpected error: {e}")
```

### 5. Validação de Dados

```python
from pydantic import BaseModel, Field, validator

class MessageData(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    type: str = Field(..., regex="^(text|audio|image)$")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    @validator('message')
    def validate_message(cls, v):
        if not v.strip():
            raise ValueError('Message cannot be empty')
        return v
```

## 🔧 Ferramentas de Desenvolvimento

### 1. Linting e Formatação

```bash
# Instalar ferramentas (opcional)
pip install black flake8 mypy

# Formatar código
black .

# Verificar estilo
flake8 .

# Verificar tipos
mypy .
```

### 2. Testes Automatizados

```bash
# Instalar pytest (opcional)
pip install pytest pytest-asyncio

# Executar testes
pytest tests/
```

### 3. Monitoramento

```bash
# Verificar logs em tempo real
tail -f logs/conversation_service.log

# Monitorar performance
python -c "
import time
from weblocal.cli import WeblocalCLI
cli = WeblocalCLI()
start = time.time()
cli.send_message('user_test', 'Performance test')
print(f'Time: {time.time() - start:.2f}s')
"
```

## 🏗️ Arquitetura e Design Patterns

### 1. Factory Pattern

```python
class ServiceFactory:
    _instance = None
    _services = {}
    
    @classmethod
    def get_service(cls, service_type: str):
        if service_type not in cls._services:
            cls._services[service_type] = cls._create_service(service_type)
        return cls._services[service_type]
```

### 2. Repository Pattern

```python
class ConversationRepository:
    def __init__(self, database: DatabaseConfig):
        self.database = database
    
    def get_or_create_conversation_uuid(self, client_hub: str) -> Tuple[str, bool]:
        # Implementação específica do repositório
        pass
```

### 3. Service Layer

```python
class ConversationService:
    def __init__(self, repository: ConversationRepository):
        self.repository = repository
    
    def get_or_create_conversation_uuid(self, client_hub: str) -> Tuple[str, bool]:
        # Validações e lógica de negócio
        return self.repository.get_or_create_conversation_uuid(client_hub)
```

## 🐛 Debugging e Troubleshooting

### 1. Problemas Comuns

**Erro de Importação:**
```bash
# Verificar se o PYTHONPATH está correto
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Erro de Banco de Dados:**
```bash
# Verificar se o arquivo de banco existe
ls -la conversations.db

# Verificar permissões
chmod 664 conversations.db
```

**Erro de Configuração:**
```bash
# Verificar variáveis de ambiente
python -c "import os; print(os.getenv('VERIFICATION_TOKEN'))"
```

### 2. Logs de Debug

```python
# Ativar logs detalhados
import logging
logging.basicConfig(level=logging.DEBUG)

# Logs específicos por módulo
logger = logging.getLogger('conversation.service')
logger.setLevel(logging.DEBUG)
```

### 3. Testes de Conectividade

```bash
# Testar conexão com WhatsApp API
python -c "
import requests
import os
token = os.getenv('WHATSAPP_API_TOKEN')
response = requests.get(f'https://graph.facebook.com/v17.0/me?access_token={token}')
print(response.json())
"
```

## 📊 Performance e Otimização

### 1. Monitoramento de Performance

```python
import time
import logging

def monitor_performance(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        logger.info(f"{func.__name__} executed in {execution_time:.2f}s")
        return result
    return wrapper
```

### 2. Otimização de Queries

```python
# Usar eager loading para relacionamentos
from sqlalchemy.orm import joinedload

query = session.query(Conversation).options(
    joinedload(Conversation.messages)
)
```

### 3. Cache de Configurações

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_conversation_config():
    return ConversationConfig()
```

## 🔒 Segurança

### 1. Validação de Entrada

```python
# Sempre validar entrada do usuário
def validate_user_input(data: dict) -> bool:
    required_fields = ['message', 'user_id']
    return all(field in data for field in required_fields)
```

### 2. Sanitização de Dados

```python
import html

def sanitize_message(message: str) -> str:
    return html.escape(message.strip())
```

### 3. Logs de Segurança

```python
# Log tentativas de acesso não autorizado
logger.warning(f"Unauthorized access attempt from {client_ip}")
```

## 📚 Recursos Adicionais

### Documentação

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)

### Ferramentas Úteis

- **Postman**: Para testar APIs
- **DB Browser for SQLite**: Para visualizar banco de dados
- **VS Code**: Editor recomendado com extensões Python

### Comandos Úteis

```bash
# Verificar dependências
pip list

# Atualizar dependências
pip install -r requirements.txt --upgrade

# Limpar cache Python
find . -type d -name "__pycache__" -delete

# Verificar sintaxe
python -m py_compile *.py
```

---

Este guia deve ser atualizado conforme o projeto evolui. Para dúvidas específicas, consulte a documentação dos módulos individuais.
