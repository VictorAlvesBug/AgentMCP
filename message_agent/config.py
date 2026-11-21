import sys
from pathlib import Path
 
from dotenv import load_dotenv
from mcp import StdioServerParameters

AGENT_FOLDER = Path(__file__).parent
SERVERS_FOLDER = AGENT_FOLDER.parent / "mcp_servers"

load_dotenv(AGENT_FOLDER / ".env")

GEMINI_MODEL = "gemini-3.8-flash"
MAX_ITERATIONS = 8
MAX_HISTORY_MESSAGES = 30

SYSTEM_PROMPT = """
Você é um assistente que conversa em português do Brasil.
Você tem acesso a um banco de dados Supabase por meio de ferramentas.
Tabelas existentes:
- notes (id, title, is_done, created_at)
Regras:
- Antes de alterar ou apagar registros, busque-os, mostre ao usuário e peça confirmação.
- Nunca use filtro vazio para alterar ou apagar.
- Se uma ferramenta retornar erro, explique o problema ao usuário de forma simples.
"""

MCP_SERVERS = {
    "supabase": StdioServerParameters(
        # Permite que o servidor use o .venv que está rodando, podendo acessar as bibliotecas dele
        command=sys.executable,
        # Diretório do servidor
        args=[str(SERVERS_FOLDER / "supabase_mcp_server.py")],
    ),
}

