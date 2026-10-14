"""The DB System for your bot

*auto-commit is ON*
"""
import aiomysql
import contextlib
import logging
import os
from dotenv import load_dotenv


pool: aiomysql.Pool = None

load_dotenv()
DB_USERNAME = os.getenv('DB_USERNAME')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DATABASE')

async def load_pool():
    global pool
    logging.info("Loading DB pool...")
    pool = await aiomysql.create_pool(host=DB_HOST, user=DB_USERNAME, password=DB_PASSWORD,
                                       db=DB_NAME, minsize=10, maxsize=100, autocommit=True,
                                       connect_timeout=5)

@contextlib.asynccontextmanager
async def get_cursor(*, dictcursor: bool = False):
    if pool is None:
        raise Exception("DB pool not loaded.")
    
   
    cursor_cls = [aiomysql.DictCursor] if dictcursor else []

    async with pool.acquire() as conn:
        async with conn.cursor(*cursor_cls) as cursor:
            yield cursor


async def migrate(migrations: list[tuple[str, str]]):
    """Apply any migrations that haven't run yet, in order. Each runs once per database.

    `migrations` is a list of (name, sql). Never edit or rename one that has
    already run - add a new one at the end instead.
    """
    async with get_cursor() as c:
        await c.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
            name VARCHAR(100) NOT NULL,
            applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (name)
            )
        """)
        await c.execute("SELECT name FROM schema_migrations")
        applied = {row[0] for row in await c.fetchall()}

        for name, sql in migrations:
            if name in applied:
                continue
            logging.info(f"Applying migration {name}...")
            await c.execute(sql)
            await c.execute("INSERT INTO schema_migrations (name) VALUES (%s)", (name,))


class _f:
    def __init__(self):
        pass

    async def row(self, cursor, default = None):
        result = await cursor.fetchall()
        return result[0] if result else default

    async def one(self, cursor, default = None):
        result = await cursor.fetchone()
        return result[0] if result else default


dbfetch = _f()

