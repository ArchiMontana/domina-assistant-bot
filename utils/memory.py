import asyncpg
from typing import List, Dict, Optional
from config import DATABASE_URL

_pool: Optional[asyncpg.Pool] = None

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS chat_messages (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_chat_messages_user_time
  ON chat_messages(user_id, created_at);
"""


async def init_db() -> None:
    global _pool
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set. Configure Postgres for persistent memory.")

    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
        async with _pool.acquire() as conn:
            for stmt in [s.strip() for s in CREATE_TABLE_SQL.split(";") if s.strip()]:
                await conn.execute(stmt)


async def close_db() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def add_message(user_id: int, role: str, content: str) -> None:
    if _pool is None:
        await init_db()

    async with _pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO chat_messages(user_id, role, content) VALUES($1, $2, $3)",
            int(user_id), role, content,
        )

        # Keep last 24 messages per user
        await conn.execute(
            """
            DELETE FROM chat_messages
            WHERE id IN (
              SELECT id FROM chat_messages
              WHERE user_id = $1
              ORDER BY created_at DESC
              OFFSET 24
            )
            """,
            int(user_id),
        )


async def get_history(user_id: int) -> List[Dict[str, str]]:
    if _pool is None:
        await init_db()

    async with _pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT role, content
            FROM chat_messages
            WHERE user_id = $1
            ORDER BY created_at ASC
            """,
            int(user_id),
        )

    return [{"role": r["role"], "content": r["content"]} for r in rows]


async def clear_history(user_id: int) -> None:
    if _pool is None:
        await init_db()

    async with _pool.acquire() as conn:
        await conn.execute("DELETE FROM chat_messages WHERE user_id = $1", int(user_id))