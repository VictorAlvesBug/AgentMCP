from mcp.server.mcpserver import MCPServer
from typing import Any
from supabase_tools.common import supabase, _validate_table, _error, TABLE_NOTES

def register(mcp: MCPServer) -> None:
    @mcp.tool()
    def get_notes(
        id: int | None = None,
        is_done: bool | None = None,
        title: str | None = None,
    ) -> list[dict[str, Any]] | dict[str, str]:
        """Busca registros da tabela public.notes (o "Read" do CRUD), retornando todas as colunas.

        Colunas de notes:
        - id: bigint, chave primária, gerado pelo banco se omitido.
        - title: text, not null, padrão ''.
        - is_done: boolean, not null, padrão false.
        - created_at: timestamptz, not null, padrão now().

        Args:
            id: se informado, restringe à nota com essa chave primária.
            is_done: se informado, restringe a notas concluídas (true) ou pendentes (false).
            title: se informado, restringe a notas cujo title contém esse trecho
                (substring, sem diferenciar maiúsculas). Não é igualdade exata.
                Valor vazio ou só espaços é ignorado. Os caracteres %, _ e \\
                no trecho são tratados como texto literal.

        Sem nenhum critério, retorna todas as notas. Se mais de um critério vier
        preenchido, todos precisam ser verdadeiros (AND).

        Retorna: lista de notas encontradas, cada uma como um dicionário
        coluna -> valor. Retorna lista vazia se nada casar com os filtros.
        Em caso de falha, retorna {"erro": "<descrição do erro>"}.
        """
        try:
            _validate_table(TABLE_NOTES)
            query = supabase.table(TABLE_NOTES).select("*")
            if id is not None:
                query = query.eq("id", id)
            if is_done is not None:
                query = query.eq("is_done", is_done)
            if title is not None:
                pattern = _title_ilike_pattern(title)
                if pattern is not None:
                    query = query.ilike("title", pattern)
            return query.execute().data
        except Exception as e:
            return _error(e)


    @mcp.tool()
    def create_note(
        title: str,
    ) -> list[dict[str, Any]] | dict[str, str]:
        """Insere uma única nota na tabela public.notes (o "Create" do CRUD).

        Colunas de notes:
        - id: bigint, chave primária, gerado pelo banco se omitido.
        - title: text, not null, padrão ''.
        - is_done: boolean, not null, padrão false.
        - created_at: timestamptz, not null, padrão now().

        Args:
            title: texto da nota. Pode ser string vazia; a coluna aceita ''.
                id, is_done e created_at não são enviados: o banco preenche
                os padrões (id gerado, is_done false, created_at now()).

        Retorna: lista com a nota inserida, incluindo id, is_done e created_at
        gerados pelo banco.
        Em caso de falha, retorna {"erro": "<descrição do erro>"}.
        """
        try:
            _validate_table(TABLE_NOTES)
            return supabase.table(TABLE_NOTES).insert({"title": title}).execute().data
        except Exception as e:
            return _error(e)


    @mcp.tool()
    def check_note(
        id: int,
    ) -> list[dict[str, Any]] | dict[str, str]:
        """Marca uma nota como concluída, definindo is_done como true. Não aceita filtro.

        Colunas de notes:
        - id: bigint, chave primária, gerado pelo banco se omitido.
        - title: text, not null, padrão ''.
        - is_done: boolean, not null, padrão false.
        - created_at: timestamptz, not null, padrão now().

        Args:
            id: chave primária da nota a marcar. A alteração atinge só esse registro.

        Retorna: lista com a nota alterada, já com is_done true.
        Lista vazia significa que nenhuma nota tem esse id.
        Em caso de falha, retorna {"erro": "<descrição do erro>"}.
        """
        try:
            _validate_table(TABLE_NOTES)
            return supabase.table(TABLE_NOTES).update({"is_done": True}).eq("id", id).execute().data
        except Exception as e:
            return _error(e)


    @mcp.tool()
    def uncheck_note(
        id: int,
    ) -> list[dict[str, Any]] | dict[str, str]:
        """Desmarca uma nota, definindo is_done como false. Não aceita filtro.

        Colunas de notes:
        - id: bigint, chave primária, gerado pelo banco se omitido.
        - title: text, not null, padrão ''.
        - is_done: boolean, not null, padrão false.
        - created_at: timestamptz, not null, padrão now().

        Args:
            id: chave primária da nota a desmarcar. A alteração atinge só esse registro.

        Retorna: lista com a nota alterada, já com is_done false.
        Lista vazia significa que nenhuma nota tem esse id.
        Em caso de falha, retorna {"erro": "<descrição do erro>"}.
        """
        try:
            _validate_table(TABLE_NOTES)
            return supabase.table(TABLE_NOTES).update({"is_done": False}).eq("id", id).execute().data
        except Exception as e:
            return _error(e)


    @mcp.tool()
    def remove_note(
        id: int,
    ) -> list[dict[str, Any]] | dict[str, str]:
        """Remove permanentemente uma nota pelo id (o "Delete" do CRUD). Não aceita filtro.

        Colunas de notes: id (bigint, chave primária), title (text),
        is_done (boolean), created_at (timestamptz).

        Esta operação não pode ser desfeita. Antes de chamar, use `get_notes`
        com id=<id> para confirmar qual nota será removida.

        Args:
            id: chave primária da nota a remover. A remoção atinge só esse registro.

        Retorna: lista com a nota removida, com id, title, is_done e created_at.
        Em caso de falha, retorna {"erro": "<descrição do erro>"}.
        """
        try:
            _validate_table(TABLE_NOTES)
            return supabase.table(TABLE_NOTES).delete().eq("id", id).execute().data
        except Exception as e:
            return _error(e)