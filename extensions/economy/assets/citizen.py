import vibes
from decimal import Decimal, ROUND_DOWN
from data import drekbase, config


class InsufficientFunds(Exception):
    """Raised when a citizen doesn't have enough money for an action"""

    def __init__(self, citizen: 'Citizen', needed: Decimal, available: Decimal):
        self.citizen = citizen
        self.needed = needed
        self.available = available
        super().__init__(f"Needed {needed}, has {available}")

    


_SUFFIXES = ['', 'k', 'M', 'B', 'T', 'Q']


def round_money(amount) -> Decimal:
    """Convert to a Decimal with 2 decimal places (cut off, not rounded up), e.g. 1.239 -> 1.23"""
    return Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_DOWN)


def money(amount: Decimal) -> str:
    """Format an amount with the configured currency, e.g. 100010 -> "d$100.01k" """
    currency = config.get('economy/currency', 'd$')
    sign = '-' if amount < 0 else ''
    value = abs(amount)

    tier = 0
    while value >= 1000 and tier < len(_SUFFIXES) - 1:
        value /= 1000
        tier += 1
    # Rounding can push it to 1000 (999,999 -> "1000k"), so bump to the next suffix
    if round(value, 2) >= 1000 and tier < len(_SUFFIXES) - 1:
        value /= 1000
        tier += 1

    number = f"{value:.2f}".rstrip('0').rstrip('.')
    return f"{sign}{currency}{number}{_SUFFIXES[tier]}"


MIGRATIONS = [
    ("economy_001_create_eco_users", """
        CREATE TABLE IF NOT EXISTS eco_users (
        user_id VARCHAR(50) NOT NULL,
        cash DECIMAL(20, 2) NOT NULL DEFAULT 0,
        bank DECIMAL(20, 2) NOT NULL DEFAULT 0,
        PRIMARY KEY (user_id)
        )
    """),
]


async def create_tables():
    await drekbase.migrate(MIGRATIONS)


class Citizen:
    """A user in the economy.

    `cash` and `bank` are cached and refreshed after every write, so they
    always reflect the DB state after this object's last operation.
    Call `await citizen.fetch()` to load them before reading.
    """

    def __init__(self, user: vibes.User | str | int):
        self.id: str = str(getattr(user, 'id', user))
        self.cash = Decimal('0')
        self.bank = Decimal('0')

    def __repr__(self):
        return f"<Citizen id={self.id} cash={self.cash} bank={self.bank}>"

    @property
    def total(self) -> Decimal:
        return self.cash + self.bank

    async def _refresh(self, c):
        await c.execute("SELECT cash, bank FROM eco_users WHERE user_id = %s", (self.id,))
        row = await drekbase.dbfetch.row(c)
        self.cash, self.bank = row if row else (Decimal('0'), Decimal('0'))

    async def fetch(self) -> 'Citizen':
        """Load balances from the DB. Returns self, so `citizen = await Citizen(user).fetch()` works"""
        async with drekbase.get_cursor() as c:
            await self._refresh(c)
        return self

    async def _add(self, column: str, amount: Decimal):
        async with drekbase.get_cursor() as c:
            await c.execute(f"""
                INSERT INTO eco_users (user_id, {column})
                VALUES (%s, %s) AS n
                ON DUPLICATE KEY UPDATE {column} = eco_users.{column} + n.{column}
            """, (self.id, amount))
            await self._refresh(c)

    async def _remove(self, column: str, amount: Decimal):
        async with drekbase.get_cursor() as c:
            # Atomic check-and-subtract, so concurrent commands can't overdraw
            await c.execute(f"""
                UPDATE eco_users SET {column} = {column} - %s
                WHERE user_id = %s AND {column} >= %s
            """, (amount, self.id, amount))
            updated = c.rowcount
            await self._refresh(c)
        if not updated:
            raise InsufficientFunds(self, amount, getattr(self, column))

    async def add_cash(self, amount: Decimal):
        await self._add('cash', _positive(amount))

    async def remove_cash(self, amount: Decimal):
        """Cash can go negative, so this never fails. Check `citizen.cash` first if that matters"""
        await self._add('cash', -_positive(amount))

    async def add_bank(self, amount: Decimal):
        await self._add('bank', _positive(amount))

    async def remove_bank(self, amount: Decimal):
        """Raises InsufficientFunds if the citizen doesn't have enough in the bank"""
        await self._remove('bank', _positive(amount))

    async def set_cash(self, amount: Decimal):
        await self._set('cash', amount)

    async def set_bank(self, amount: Decimal):
        await self._set('bank', amount)

    async def _set(self, column: str, amount: Decimal):
        async with drekbase.get_cursor() as c:
            await c.execute(f"""
                INSERT INTO eco_users (user_id, {column})
                VALUES (%s, %s) AS n
                ON DUPLICATE KEY UPDATE {column} = n.{column}
            """, (self.id, amount))
            await self._refresh(c)

    async def deposit(self, amount: Decimal):
        """Move cash into the bank. Raises InsufficientFunds"""
        amount = _positive(amount)
        async with drekbase.get_cursor() as c:
            await c.execute("""
                UPDATE eco_users SET cash = cash - %s, bank = bank + %s
                WHERE user_id = %s AND cash >= %s
            """, (amount, amount, self.id, amount))
            updated = c.rowcount
            await self._refresh(c)
        if not updated:
            raise InsufficientFunds(self, amount, self.cash)

    async def withdraw(self, amount: Decimal):
        """Move money from the bank to cash. Raises InsufficientFunds"""
        amount = _positive(amount)
        async with drekbase.get_cursor() as c:
            await c.execute("""
                UPDATE eco_users SET bank = bank - %s, cash = cash + %s
                WHERE user_id = %s AND bank >= %s
            """, (amount, amount, self.id, amount))
            updated = c.rowcount
            await self._refresh(c)
        if not updated:
            raise InsufficientFunds(self, amount, self.bank)

    async def pay(self, other: 'Citizen', amount: Decimal):
        """Give cash to another citizen. Can leave this citizen's cash negative"""
        await self.remove_cash(amount)
        await other.add_cash(amount)


def _positive(amount) -> Decimal:
    amount = round_money(amount)
    if amount <= 0:
        raise ValueError("Amount must be positive")
    return amount
