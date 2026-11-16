import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer
from supabase import create_client, Client

load_dotenv(Path(__file__).parent / ".env")

mcp = MCPServer("Supabase MCP Server")

supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))


def _error(e: Exception) -> dict[str, str]:
    return {"erro": f"{type(e).__name__}: {e}"}


@mcp.resource("config://app")
def app_config() -> str:
    """Configuração da aplicação"""
    return {
        "name": "Supabase MCP Server",
        "version": "1.0.0",
        "description": "Servidor MCP para o Supabase",
        "author": "Victor Bugueno"
    }


@mcp.prompt()
def simple_echo(message: str) -> str:
    """Um prompt simples que pede ao modelo para ecoar uma mensagem"""
    print(f"Mensagem recebida: {message}")
    return f"Por favor, repita exatamente esta mensagem: {message}"


@mcp.tool()
def get_from_table(
    table: str,
    filter: dict[str, Any]
) -> list[dict[str, Any]] | dict[str, str]:
    """Busca registros de uma tabela (o "Read" do CRUD), retornando todas as colunas.

    Args:
        table: nome da tabela, conforme retornado por `list_tables`.
        filter: filtros de igualdade, mapeando nome da coluna para o valor exato,
            ex: {"id": 1} ou {"status": "ativo", "cidade": "Recife"}.
            Todas as condições precisam ser verdadeiras (AND).
            Use {} para retornar todos os registros da tabela.

    Retorna: lista de registros encontrados, cada um como um dicionário
    coluna -> valor. Retorna lista vazia se nada casar com os filtros.
    Em caso de falha, retorna {"erro": "<descrição do erro>"}.
    """
    try:
        #_validate_table(table)
        return supabase.table(table).select("*").match(filter).execute().data
    except Exception as e:
        return _error(e)


@mcp.tool()
def insert_into_table(
    table: str,
    data: list[dict[str, Any]]
) -> list[dict[str, Any]] | dict[str, str]:
    """Insere um ou mais registros novos em uma tabela (o "Create" do CRUD).

    Args:
        table: nome da tabela, conforme retornado por `list_tables`.
        data: lista de registros a inserir, cada um mapeando nome da coluna para o valor,
            ex: [{"nome": "Ana", "email": "ana@email.com"}].
            Para inserir um único registro, envie uma lista com um elemento.
            Não informe colunas geradas automaticamente pelo banco, como `id` ou `created_at`.

    Retorna: os registros inseridos, incluindo os valores gerados pelo banco (como o `id`).
    Em caso de falha, retorna {"erro": "<descrição do erro>"}.
    """
    try:
        #_validate_table(table)
        return supabase.table(table).insert(data).execute().data
    except Exception as e:
        return _error(e)


@mcp.tool()
def update_in_table(
    table: str,
    filter: dict[str, Any],
    data: dict[str, Any]
) -> list[dict[str, Any]] | dict[str, str]:
    """Altera registros existentes de uma tabela (o "Update" do CRUD).

    Args:
        table: nome da tabela, conforme retornado por `list_tables`.
        filter: filtros de igualdade que selecionam quais registros alterar,
            ex: {"id": 1}. Todas as condições precisam ser verdadeiras (AND).
            Prefira filtrar pela chave primária. Nunca envie {}: isso alteraria
            todos os registros da tabela.
        data: colunas a alterar e seus novos valores, ex: {"status": "inativo"}.
            Colunas não informadas permanecem como estão.

    Retorna: lista dos registros alterados, já com os novos valores.
    Lista vazia significa que nenhum registro casou com os filtros.
    Em caso de falha, retorna {"erro": "<descrição do erro>"}.
    """
    try:
        #_validate_table(table)
        return supabase.table(table).update(data).match(filter).execute().data
    except Exception as e:
        return _error(e)


@mcp.tool()
def delete_from_table(
    table: str,
    filter: list[dict[str, Any]]
) -> list[dict[str, Any]] | dict[str, str]:
    """Remove permanentemente registros de uma tabela (o "Delete" do CRUD).

    Esta operação não pode ser desfeita. Antes de chamar, use `get_from_table`
    com o mesmo filtro para confirmar quais registros serão removidos.

    Args:
        table: nome da tabela, conforme retornado por `list_tables`.
        filter: filtros de igualdade que selecionam quais registros remover,
            ex: {"id": 1}. Todas as condições precisam ser verdadeiras (AND).
            Prefira filtrar pela chave primária. Nunca envie um filtro vazio:
            isso apagaria todos os registros da tabela.

    Retorna: lista dos registros removidos.
    Em caso de falha, retorna {"erro": "<descrição do erro>"}.
    """
    try:
        #_validate_table(table)
        return supabase.table(table).delete().match(filter).execute().data
    except Exception as e:
        return _error(e)


if __name__ == "__main__":
    mcp.run()