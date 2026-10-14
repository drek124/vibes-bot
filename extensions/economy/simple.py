import vibes
import random
from decimal import Decimal
from vibes import commands
from vibes.commands import Context, Cooldown
from vibes.ext import event_listener, Extension
from data import drekbase
from extensions.economy.assets import Citizen, InsufficientFunds, money, round_money, create_tables



class economy_simple(Extension):

    def __init__(self, client):
        self.client: vibes.Client = client

    @commands.app_command(cooldown=Cooldown(60, 1, Cooldown.USER))
    async def work(self, ctx: Context):
        "Work work work"
        citizen = Citizen(ctx.author)

        profit = round_money(random.uniform(3, 10))
        await citizen.add_cash(profit)
        msg = random.choice([
            f"You worked and gained {money(profit)}"
        ])
        await ctx.message.reply(msg)

    @commands.app_command(cooldown=Cooldown(10, 2, Cooldown.USER))
    @commands.describe(
        user="Whose balance to check (default: you)"
    )
    async def bal(self, ctx: Context, user: vibes.Viewer = None):
        """Check your balance, or someone else's"""
        user = user or ctx.author
        citizen = await Citizen(user).fetch()

        owner = "Your" if user == ctx.author else f"{user}'s"
        await ctx.message.reply(f"{owner} balance - Cash: {money(citizen.cash)} | Bank: {money(citizen.bank)}")

    @commands.app_command(cooldown=Cooldown(10, 3, Cooldown.USER))
    @commands.describe(
        amount="How much to deposit (default: all)"
    )
    async def dep(self, ctx: Context, amount: float = None):
        """Deposit cash into your bank"""
        citizen = await Citizen(ctx.author).fetch()
        value = citizen.cash if amount is None else round_money(amount)
        if value <= 0:
            await ctx.message.reply("Nothing to move." if amount is None else f"Amount must be at least {money(Decimal('0.01'))}.")
            return

        try:
            await citizen.deposit(value)
        except InsufficientFunds as e:
            await ctx.message.reply(f"You only have {money(e.available)} in cash.")
            return

        await ctx.message.reply(f"Deposited {money(value)}. Bank: {money(citizen.bank)}")

    @commands.app_command(name='with', cooldown=Cooldown(10, 3, Cooldown.USER))
    @commands.describe(
        amount="How much to withdraw (default: all)"
    )
    async def withdraw(self, ctx: Context, amount: float = None):
        """Withdraw money from your bank"""
        citizen = await Citizen(ctx.author).fetch()
        value = citizen.bank if amount is None else round_money(amount)
        if value <= 0:
            await ctx.message.reply("Nothing to move." if amount is None else f"Amount must be at least {money(Decimal('0.01'))}.")
            return

        try:
            await citizen.withdraw(value)
        except InsufficientFunds as e:
            await ctx.message.reply(f"You only have {money(e.available)} in the bank.")
            return

        await ctx.message.reply(f"Withdrew {money(value)}. Cash: {money(citizen.cash)}")

    @commands.app_command(name='guesser', cooldown=Cooldown(30, 1, Cooldown.USER))
    @commands.describe(
        guess="Your guess, from 1 to 4"
    )
    async def guesser(self, ctx: Context, guess: int):
        """Guess the dice roll (1-4) to win cash!"""
        if not 1 <= guess <= 4:
            await ctx.message.reply("Your guess must be between 1 and 4.")
            return

        citizen = Citizen(ctx.author)
        stake = round_money(random.uniform(30, 80))
        loss = round_money(stake / 3)

        roll = random.randint(1, 4)
        if roll == guess:
            await citizen.add_cash(stake)
            await ctx.message.reply(f"🎲 Rolled {roll}! You guessed it and won {money(stake)}!")
            return

        await citizen.remove_cash(loss)
        await ctx.message.reply(f"🎲 Rolled {roll}, you guessed {guess}. You lost {money(loss)}.")


async def setup(client):
    await create_tables()
    await client.add_ext(economy_simple(client))