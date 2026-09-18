from app.db.connection import get_pool


async def get_by_username(username: str) -> dict | None:
    pool = get_pool()
    row = await pool.fetchrow(
        "SELECT id, username, password_hash, role, created_at FROM users WHERE username = $1",
        username,
    )
    return dict(row) if row else None
