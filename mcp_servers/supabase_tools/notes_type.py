from typing import TypedDict

class Note(TypedDict):
    id: int
    title: str
    is_done: bool
    created_at: str