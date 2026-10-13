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

