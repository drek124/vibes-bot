import vibes
import random
import asyncio
import difflib
import re
import unicodedata
from decimal import Decimal
from vibes import commands
from vibes.commands import Context, Cooldown
from vibes.ext import event_listener, Extension
from data import drekbase, jsonbase
from extensions.economy.assets import Citizen, InsufficientFunds, money, round_money, MIGRATIONS
from extensions.chatinteraction.assets import *

_data: dict = jsonbase.readjson('extensions/economy/assets/flags.json')
COUNTRIES: dict[str, str] = _data['countries']
EMOJIS: dict[str, str] = _data['emojis']




async def _lose(citizen: Citizen, profit: Decimal) -> Decimal:
    loss = profit/3
    await citizen.remove_cash(loss)
    return loss

def _normalize(text: str) -> str:
    """Lowercases, strips accents & punctuation ("Åland Islands" -> "aland islands")"""
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode()
    text = text.lower().replace('&', ' and ').replace("'", '')
    return ' '.join(re.sub(r'[^a-z0-9 ]', ' ', text).split())

def _answers(name: str) -> set[str]:
    """Every accepted answer for a country; the part in brackets counts on its own
    ("Côte d'Ivoire (Ivory Coast)" -> "cote divoire", "ivory coast", "cote divoire ivory coast")
    """
    answers = {_normalize(name)}
    if match := re.fullmatch(r'(.*?)\s*\((.*)\)\s*', name):
        answers.update(_normalize(part) for part in match.groups())
    return answers - {''}

# Normalized answer -> country name
_ANSWERS: dict[str, str] = {answer: name for name in COUNTRIES.values() for answer in _answers(name)}

def _check(attempt: str, name: str, cutoff: float = 0.8) -> bool:
    """Checks if the guess is correct, allowing small typos.
    A typo only counts if the guess isn't closer to another country (e.g. "niger" won't pass for Nigeria)
    """
    attempt = _normalize(attempt)

    if attempt in _answers(name):
        return True

    closest = difflib.get_close_matches(attempt, _ANSWERS.keys(), n=1, cutoff=cutoff)
    return bool(closest) and _ANSWERS[closest[0]] == name


class economy_flag(Extension):

    def __init__(self, client):
        self.client: vibes.Client = client

    @commands.app_command(cooldown=Cooldown(30, 8, Cooldown.USER))
    async def flag(self, ctx: Context):
        """Guess the country from its flag"""
        citizen = await Citizen(ctx.author).fetch()
        profit = round_money(random.randint(20, 90))
        countdown = random.randint(5, 15)

        key, country = random.choice(list(COUNTRIES.items()))
        emoji = EMOJIS[key]
        called = False
        async def callback(event: InteractionEvent):
            nonlocal called
            called = True
            msg = event.message
            if not _check(msg.content, country):
                loss = await _lose(citizen, profit)
                await msg.reply(f"‼ You lost {money(loss)}. Answer: {country}")
                return

            # Winning
            await citizen.add_cash(profit)
            await msg.reply(f"✅ You got {money(profit)} for guessing {country}")

        interaction = ChatInteraction(ctx, timeout=countdown, callback=callback)
        await ctx.message.reply(f"[{countdown}s] Discover the country's name: {emoji}")
        await asyncio.sleep(countdown)
        if called: 
            return
        
        interaction.stop()
        loss = await _lose(citizen, profit)
        await ctx.message.reply(f'⚠ Ran out of time. Lost {money(loss)}; country: {country}')




    
async def setup(client):
    await drekbase.migrate(MIGRATIONS)
    await client.add_ext(economy_flag(client))