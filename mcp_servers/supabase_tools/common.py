import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv(Path(__file__).parent.parent / ".env")

supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

TABLE_NOTES = "notes"
TABLE_TELEGRAM_USERS = "telegram_users"
ALLOWED_TABLES = {TABLE_NOTES, TABLE_TELEGRAM_USERS}

def _validate_table(table: str) -> None:
    if table not in ALLOWED_TABLES:
        permitidas = ", ".join(sorted(ALLOWED_TABLES))
        raise ValueError(f"Tabela '{table}' não permitida. Tabelas permitidas: {permitidas}.")

def _error(e: Exception) -> dict[str, str]:
    return {"erro": f"{type(e).__name__}: {e}"}


def _title_ilike_pattern(title: str) -> str | None:
    fragment = title.strip()
    if not fragment:
        return None
    escaped = fragment.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"