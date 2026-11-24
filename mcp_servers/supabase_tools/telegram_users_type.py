from typing import TypedDict

class TelegramUser(TypedDict):
    id: int
    telegram_user_id: int
    username: str | None
    created_at: str