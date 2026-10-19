import vibes
import random
from decimal import Decimal
from vibes import commands
from vibes.commands import Context, Cooldown
from vibes.ext import event_listener, Extension
from data import drekbase
from extensions.economy.assets import Citizen, InsufficientFunds, money, round_money, MIGRATIONS



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
            f"You worked as a drek officer and you earned {money(profit)}",
            f"You did some of your chores and earned {money(profit)}. Good boy!",
            f"You were hired as {self.client.user} official tester and as signing bonus you earned {money(profit)}",
            f"You did some chores around the house and mommy gave you {money(profit)}",
            f"You sold OnlyDrek leaks and earned {money(profit)}",
            f"You washed the dishes. That's it. Oh by the way you earned {money(profit)}",
            f"You got fired but you looked at the floor and found {money(profit)} lying around. How convenient!",
            f"You are so dumb you couldn't work so you told everyone what a loser you are and people gave you {money(profit)} from pity",
            f"You work for the KKK and you earn {money(profit)}",
            f"you clean toilets for 2 years, congratulations on {money(profit)}",
            f"cigan take {money(profit)}",
            f"You as work a drek deputy and gain {money(profit)}.",
            f"You linked your VALORANT account to drek utilities and gained {money(profit)}!",
            f"Your unempl*yment cheque earned you {money(profit)}.",
            f"#ad You subscribed to VIBES Premium and enjoyed streaming like a pro. You made {money(profit)} from donations!",
            f"#ad You equipped the VIBES tag and earned {money(profit)} 🔥",
            f"You donated your heart for a transplant and gained {money(profit)}!",
            f"You traveled to Bahrain. free {money(profit)}.",
            f"21ketchup used your sub-botting service for {money(profit)}!",
            f"You subscribed to Hustler's University's affiliate system and gained {money(profit)}!",
            f"You went to America and won the lottery of 1,000,000d$! After the IRS robbed you, you're left with {money(profit)} rip bozo",
            f"You became black. Free {money(profit)}", 
            f"You sold N-Word passes for {money(profit)}.",
            f"You became drek's E-Kitten & gained {money(profit)}.",
            f"You became the middleman for drek bank's Auction House for {money(profit)}",
            f"You work as a professional worker and earn {money(profit)}.",
            f"You did work {money(profit)}",
            f"You assasinated Drek John Um and earned {money(profit)} as a thank you from North Drekea!",
            f"You assasinated Adolf Titler for {money(profit)}"
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

    @commands.app_command(cooldown=Cooldown(300, 1, Cooldown.USER))
    async def crime(self, ctx: Context):
        "[RISKY] Commit a crime in drek city"
        citizen = await Citizen(ctx.author).fetch()
        odds = random.randint(1, 100)

        if odds <= 30: # % loss chance
            loss = citizen.total / 3
            await citizen.remove_cash(loss)
            response = '⚠ ' + random.choice([
            f"Before you could hit the trigger, a drek officer tackled you which caused you to lose {money(loss)}",
            f"You were stopped by drek security while attempting to hack drek utilities to grant yourself more coins! You were fined {money(loss)}",
            f"You attempted to avoid getting blacklisted from drek lounge! But you failed and lost {money(loss)}",
            f"You tried to abuse drek modmail! As a punishment, you were fined {money(loss)}",
            f"You tried to post NSFW media in VIBES, but you failed and got fined {money(loss)}.",
            f"You tried to groom an E-Girl but it was 21ketchup recording a video which fined you {money(loss)}.",
            f"You tried to sexually assault a miner, however you forgot that Kris Dreksen was conveniently at the ATM behind you & you paid him {money(loss)} to let it slide.",
            ])
            await ctx.message.reply(response)
            return
        profit = random.randint(50, 200)
        await citizen.add_cash(profit)
        response = '👍 ' + random.choice([
            f"You robbed drek bank for {money(profit)}!",
            f"You hacked drek security and granted yourself {money(profit)}",
            f"You hijacked a plane and hit the twin towers for {money(profit)}",
            f"You robbed a homeless person for {money(profit)}. tf?",
            f"You hacked an OnlyDrek account and stole {money(profit)}",
        ])
        await ctx.message.reply(response)


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
    await drekbase.migrate(MIGRATIONS)
    await client.add_ext(economy_simple(client))