import sys
from pathlib import Path
 
from dotenv import load_dotenv
from mcp import StdioServerParameters

import os

AGENT_FOLDER = Path(__file__).parent
SERVERS_FOLDER = AGENT_FOLDER.parent / "mcp_servers"

load_dotenv(AGENT_FOLDER / ".env")

TELEGRAM_BOT_TOKEN = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()

aux_telegram_admin_id = (os.getenv("TELEGRAM_ADMIN_ID") or "").strip() or None

if aux_telegram_admin_id is None:
    TELEGRAM_ADMIN_ID = None
else:
    try:
        TELEGRAM_ADMIN_ID = int(aux_telegram_admin_id.strip())
    except ValueError:
        error_message = "Variável de ambiente 'TELEGRAM_ADMIN_ID' deve ser um número inteiro"
        print(error_message)
        raise ValueError(error_message)

PROVIDER = "groq" # "gemini" ou "groq"

GEMINI_MODEL = "gemini-3.5-flash-lite"

GROQ_MODEL = "openai/gpt-oss-120b"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

TELEGRAM_BASE_URL = "https://api.telegram.org/bot"

MAX_ITERATIONS = 8
MAX_HISTORY_MESSAGES = 30

SYSTEM_PROMPT = """
Você é um agente de IA que conversa em português do Brasil.
Você tem acesso a um banco de dados Supabase por meio de ferramentas.
Tabelas existentes:
- notes (id, title, is_done, created_at)
Regras:
- Antes de alterar ou apagar registros, busque-os, mostre ao usuário e peça confirmação.
- Nunca use filtro vazio para alterar ou apagar.
- Se uma ferramenta retornar erro, explique o problema ao usuário de forma simples.
- Sempre que a lista de notas sofrer alterações, exiba as notas atualizadas.
- Sempre exiba um descritivo inicial, e então liste as notas como um checklist: "<✅ ou ⬜> - <id>. <titulo>", sempre em texto livre, sem utilizar markdown.
- Exemplo:
Estas são suas notas:
✅ - 1. Comprar leite
⬜ - 2. Comprar pão
⬜ - 3. Comprar café
"""

MCP_SERVERS = {
    "supabase": StdioServerParameters(
        # Permite que o servidor use o .venv que está rodando, podendo acessar as bibliotecas dele
        command=sys.executable,
        # Diretório do servidor
        args=[str(SERVERS_FOLDER / "supabase_mcp_server.py")],
    ),
}

