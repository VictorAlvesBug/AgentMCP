import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from mcp import StdioServerParameters

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

aux_notion_token = (os.getenv("NOTION_TOKEN") or "").strip() or None

if aux_notion_token is None:
    NOTION_TOKEN = None
    error_message = "Variável de ambiente 'NOTION_TOKEN' deve ser preenchida"
    print(error_message)
    raise ValueError(error_message)
else:
    NOTION_TOKEN = aux_notion_token.strip()

PROVIDER = "groq" # "gemini" ou "groq"

GEMINI_MODEL = "gemini-3.5-flash-lite"

GROQ_MODEL = "openai/gpt-oss-120b"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

TELEGRAM_BASE_URL = "https://api.telegram.org/bot"

MAX_ITERATIONS = 8
MAX_HISTORY_MESSAGES = 30

SYSTEM_PROMPT = """
Você é um agente de IA que conversa em português do Brasil.

MCPs disponíveis:
- Supabase
- Notion

Tabelas Supabase existentes:
- notes (id, title, is_done, created_at)

Regras gerais:
- Antes de alterar ou apagar registros, busque-os, mostre ao usuário e peça confirmação.
- Nunca use filtro vazio para alterar ou apagar.
- Se uma ferramenta retornar erro, explique o problema ao usuário de forma simples.

Regras Supabase:
- Sempre que a lista de notas sofrer alterações, exiba as notas atualizadas.
- Sempre exiba um descritivo inicial, e então liste as notas como um checklist em texto livre.
- Exemplo:
    Estas são suas notas:
    ✅ - 1. Comprar leite
    ⬜ - 2. Comprar pão
    ⬜ - 3. Comprar café

Regras Notion:
- Para buscar uma página, procure primeiro pelo nome, depois pelo conteúdo.
- Antes de criar uma página, informe seu nome, caminho e resumo do conteúdo.
- Antes de editar uma página, informe o que mudará e peça confirmação.
"""

MCP_SERVERS = {
    "supabase": StdioServerParameters(
        # Permite que o servidor use o .venv que está rodando, podendo acessar as bibliotecas dele
        command=sys.executable,
        # Diretório do servidor
        args=[str(SERVERS_FOLDER / "supabase_mcp_server.py")],
    ),
    "notion": StdioServerParameters(
        command="cmd",
        args=["/c", "npx", "-y", "@notionhq/notion-mcp-server"],
        env={"NOTION_TOKEN": NOTION_TOKEN},
    ),
}

TOOLS_VISIBLE_BY_MODEL = [
    # --- Supabase Tools ---
    "supabase__get_notes",
    "supabase__create_note",
    "supabase__check_note",
    "supabase__uncheck_note",
    "supabase__remove_note",

    # --- Notion Tools ---
    "notion__API-post-search",
    "notion__API-retrieve-page-markdown",
    "notion__API-post-page",
    "notion__API-update-page-markdown",
]
