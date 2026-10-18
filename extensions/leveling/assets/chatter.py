import vibes
import random
from data import drekbase, config


def xp_for_next(level: int) -> int:
    """XP needed to go from `level` to `level + 1`:
    `xp_per_level + xp_growth * level + xp_growth_squared * level²`
    """
    base = max(1, config.get('leveling/xp_per_level', 100)) # At least 1, or level_for() never ends
    growth = config.get('leveling/xp_growth', 50)
    growth_squared = config.get('leveling/xp_growth_squared', 5)
    return base + growth * level + growth_squared * level ** 2


def level_for(xp: int) -> int:
    """The level reached with `xp` total XP"""
    level = 0
    while xp >= xp_for_next(level):
        xp -= xp_for_next(level)
        level += 1
    return level


def xp_for_level(level: int) -> int:
    """Total XP needed to reach `level`"""
    return sum(xp_for_next(l) for l in range(level))


MIGRATIONS = [
    ("leveling_001_create_lvl_users", """
        CREATE TABLE IF NOT EXISTS lvl_users (
        user_id VARCHAR(50) NOT NULL,
        username VARCHAR(100) DEFAULT NULL,
        xp BIGINT UNSIGNED NOT NULL DEFAULT 0,
        last_xp_at DATETIME DEFAULT NULL,
        PRIMARY KEY (user_id),
        INDEX idx_xp (xp)
        )
    """),
]


class Chatter:
    """A user's leveling progress across the whole platform.

    `xp` is cached and refreshed after every write, so it always reflects
    the DB state after this object's last operation.
    Call `await chatter.fetch()` to load it before reading.
    """

    def __init__(self, user: vibes.User | str | int):
        self.id: str = str(getattr(user, 'id', user))
        self.username: str | None = getattr(user, 'username', None)
        self.xp = 0

    def __repr__(self):
        return f"<Chatter id={self.id} xp={self.xp} level={self.level}>"

    @property
    def level(self) -> int:
        return level_for(self.xp)

    @property
    def progress(self) -> tuple[int, int]:
        """(XP into the current level, XP needed for the next one)"""
        level = self.level
        return self.xp - xp_for_level(level), xp_for_next(level)

    async def _refresh(self, c):
        await c.execute("SELECT xp, username FROM lvl_users WHERE user_id = %s", (self.id,))
        row = await drekbase.dbfetch.row(c)
        if row:
            self.xp, self.username = row[0], row[1] or self.username
        else:
            self.xp = 0

    async def fetch(self) -> 'Chatter':
        """Load XP from the DB. Returns self, so `chatter = await Chatter(user).fetch()` works"""
        async with drekbase.get_cursor() as c:
            await self._refresh(c)
        return self

    async def rank(self) -> int:
        """Position on the global leaderboard, starting at 1"""
        async with drekbase.get_cursor() as c:
            await c.execute("""
                SELECT COUNT(*) + 1 FROM lvl_users
                WHERE xp > (SELECT COALESCE(MAX(xp), 0) FROM lvl_users WHERE user_id = %s)
            """, (self.id,))
            return await drekbase.dbfetch.one(c, 1)

    async def add_xp(self, amount: int):
        async with drekbase.get_cursor() as c:
            await c.execute("""
                INSERT INTO lvl_users (user_id, xp)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE xp = lvl_users.xp + VALUES(xp)
            """, (self.id, _positive(amount)))
            await self._refresh(c)

    async def set_xp(self, amount: int):
        async with drekbase.get_cursor() as c:
            await c.execute("""
                INSERT INTO lvl_users (user_id, xp)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE xp = VALUES(xp)
            """, (self.id, max(0, int(amount))))
            await self._refresh(c)

    async def reward_message(self) -> bool:
        """Give the random per-message XP, at most once per cooldown.

        Returns True if this pushed the chatter to a new level.
        """
        cooldown = config.get('leveling/cooldown', 60)
        amount = random.randint(config.get('leveling/xp_min', 15), config.get('leveling/xp_max', 25))

        async with drekbase.get_cursor() as c:
            await c.execute("""
                INSERT INTO lvl_users (user_id, username) VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE username = COALESCE(VALUES(username), lvl_users.username)
            """, (self.id, self.username))
            # Atomic cooldown check and add, no spamming allowed x)
            await c.execute("""
                UPDATE lvl_users SET xp = xp + %s, last_xp_at = NOW()
                WHERE user_id = %s
                AND (last_xp_at IS NULL OR last_xp_at <= NOW() - INTERVAL %s SECOND)
            """, (amount, self.id, cooldown))
            updated = c.rowcount
            await self._refresh(c)

        return bool(updated) and level_for(self.xp - amount) < self.level

    @staticmethod
    async def leaderboard(limit: int = 10) -> list['Chatter']:
        """The top chatters on the platform, highest XP first"""
        async with drekbase.get_cursor() as c:
            await c.execute("""
                SELECT user_id, username, xp FROM lvl_users
                WHERE xp > 0
                ORDER BY xp DESC LIMIT %s
            """, (limit,))
            rows = await c.fetchall()

        chatters = []
        for user_id, username, xp in rows:
            chatter = Chatter(user_id)
            chatter.username, chatter.xp = username, xp
            chatters.append(chatter)
        return chatters


def _positive(amount) -> int:
    amount = int(amount)
    if amount <= 0:
        raise ValueError("Amount must be positive")
    return amount
