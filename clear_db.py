"""
Очистка базы данных
"""

import asyncio
import config
from database_postgres import DatabasePostgres

async def clear_database():
    db = DatabasePostgres(config.POSTGRES_DSN)
    await db.init_pool()
    
    print("⚠️  Очистка базы данных...")
    
    async with db.pool.acquire() as conn:
        # Удаляем все данные из таблиц
        await conn.execute('TRUNCATE TABLE spam_messages CASCADE')
        await conn.execute('TRUNCATE TABLE achievements CASCADE')
        await conn.execute('TRUNCATE TABLE winners CASCADE')
        await conn.execute('TRUNCATE TABLE participants CASCADE')
        await conn.execute('TRUNCATE TABLE contests CASCADE')
        await conn.execute('TRUNCATE TABLE referrals CASCADE')
        await conn.execute('TRUNCATE TABLE user_stats CASCADE')
    
    print("✅ База данных очищена!")
    
    await db.close_pool()

if __name__ == "__main__":
    asyncio.run(clear_database())