from mcp.server.mcpserver import MCPServer

from supabase_tools.notes_table import register as register_notes_table
from supabase_tools.telegram_users_table import register as register_telegram_users_table

mcp = MCPServer("Supabase MCP Server")

register_notes_table(mcp)
register_telegram_users_table(mcp)


@mcp.resource("config://app")
def app_config() -> dict[str, str]:
    """Configuração da aplicação"""
    return {
        "name": "Supabase MCP Server",
        "version": "1.0.0",
        "description": "Servidor MCP para a tabela public.notes no Supabase",
        "author": "Victor Bugueno",
    }


@mcp.prompt()
def simple_echo(message: str) -> str:
    """Um prompt simples que pede ao modelo para ecoar uma mensagem"""
    return f"Por favor, repita exatamente esta mensagem: {message}"

if __name__ == "__main__":
    mcp.run()
