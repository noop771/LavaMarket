import asyncio

from sqlalchemy import text

from app.db import engine


async def main() -> None:
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        print("Связь с PostgreSQL работает. Ответ от базы:", result.scalar())


if __name__ == "__main__":
    asyncio.run(main())