import json
import os
from typing import List, Dict

DB_PATH = "memory.json"
MAX_MESSAGES = 24


async def init_db() -> None:
    if not os.path.exists(DB_PATH):
        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False)

    print("File memory initialized.")


async def close_db() -> None:
    return None


def _load_memory() -> Dict[str, List[Dict[str, str]]]:
    if not os.path.exists(DB_PATH):
        return {}

    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            return data

        return {}
    except Exception:
        return {}


def _save_memory(data: Dict[str, List[Dict[str, str]]]) -> None:
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


async def add_message(user_id: int, role: str, content: str) -> None:
    data = _load_memory()
    uid = str(user_id)

    if uid not in data:
        data[uid] = []

    data[uid].append({
        "role": role,
        "content": content
    })

    data[uid] = data[uid][-MAX_MESSAGES:]

    _save_memory(data)


async def get_history(user_id: int) -> List[Dict[str, str]]:
    data = _load_memory()
    return data.get(str(user_id), [])


async def clear_history(user_id: int) -> None:
    data = _load_memory()
    uid = str(user_id)

    if uid in data:
        del data[uid]
        _save_memory(data)
