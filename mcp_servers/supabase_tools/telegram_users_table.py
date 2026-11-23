from mcp.server.mcpserver import MCPServer
from typing import Any
from supabase_tools.common import supabase, _validate_table, _error, TABLE_TELEGRAM_USERS

def register(mcp: MCPServer) -> None:
    @mcp.tool()
    def get_telegram_user(telegram_user_id: int) -> dict[str, Any] | dict[str, str]:
        """Busca um usuário no Supabase pelo telegram_user_id (o "Read" do CRUD).

        Colunas de telegram_users:
        - id: bigint, chave primária, gerado pelo banco se omitido.
        - telegram_user_id: bigint, not null, chave única, gerada pelo bot do Telegram.
        - username: text, nullable.
        - created_at: timestamptz, not null, padrão now().

        Args:
            telegram_user_id: ID do usuário no Telegram.

        Retorna: dicionário com o usuário encontrado, ou dicionário vazio se não encontrado.
        Em caso de falha, retorna {"erro": "<descrição do erro>"}.
        """
        try:
            _validate_table(TABLE_TELEGRAM_USERS)
            user = supabase.table(TABLE_TELEGRAM_USERS).select("*").eq("telegram_user_id", telegram_user_id).execute().data
            if not user:
                return {}
            return user[0]
        except Exception as e:
            return _error(e)

    @mcp.tool()
    def create_telegram_user(
        telegram_user_id: int,
        username: str | None = None,
    ) -> dict[str, Any] | dict[str, str]:
        """Cria um usuário no Supabase pelo telegram_user_id.
        
        Colunas de telegram_users:
        - id: bigint, chave primária, gerado pelo banco se omitido.
        - telegram_user_id: bigint, not null, chave única, gerada pelo bot do Telegram.
        - username: text, nullable.
        - created_at: timestamptz, not null, padrão now().

        Args:
            telegram_user_id: ID do usuário no Telegram.
            username: nome de usuário do usuário no Telegram.

        Retorna: dicionário com o usuário criado, incluindo id, telegram_user_id, username e created_at gerados pelo banco.
        Em caso de falha, retorna {"erro": "<descrição do erro>"}.
        """
        try:
            _validate_table(TABLE_TELEGRAM_USERS)
            user = supabase.table(TABLE_TELEGRAM_USERS).insert({"telegram_user_id": telegram_user_id, "username": username}).execute().data
            if not user:
                return {"erro": "Erro ao criar usuário"}
            return user[0]
        except Exception as e:
            return _error(e)

    @mcp.tool()
    def list_telegram_users() -> list[dict[str, Any]] | dict[str, str]:
        """Lista todos os usuários no Supabase.
        
        Colunas de telegram_users:
        - id: bigint, chave primária, gerado pelo banco se omitido.
        - telegram_user_id: bigint, not null, chave única, gerada pelo bot do Telegram.
        - username: text, nullable.
        - created_at: timestamptz, not null, padrão now().

        Retorna: lista com todos os usuários, cada um como um dicionário coluna -> valor.
        Em caso de falha, retorna {"erro": "<descrição do erro>"}.
        """
        try:
            _validate_table(TABLE_TELEGRAM_USERS)
            return supabase.table(TABLE_TELEGRAM_USERS).select("*").execute().data
        except Exception as e:
            return _error(e)

    @mcp.tool()
    def remove_telegram_user(telegram_user_id: int) -> dict[str, Any] | dict[str, str]:
        """Remove um usuário no Supabase pelo telegram_user_id.
        
        Colunas de telegram_users:
        - id: bigint, chave primária, gerado pelo banco se omitido.
        - telegram_user_id: bigint, not null, chave única, gerada pelo bot do Telegram.
        - username: text, nullable.
        - created_at: timestamptz, not null, padrão now().

        Args:
            telegram_user_id: ID do usuário no Telegram.

        Retorna: dicionário com o usuário removido, com id, telegram_user_id, username e created_at.
        Em caso de falha, retorna {"erro": "<descrição do erro>"}.
        """
        try:
            _validate_table(TABLE_TELEGRAM_USERS)
            user = supabase.table(TABLE_TELEGRAM_USERS).delete().eq("telegram_user_id", telegram_user_id).execute().data
            if not user:
                return {"erro": "Erro ao remover usuário"}
            return user[0]
        except Exception as e:
            return _error(e)