import vibes
import random
from vibes import commands
from vibes.commands import Context, Cooldown
from vibes.ext import event_listener, Extension
from data import drekbase, config
from extensions.leveling.assets import Chatter, MIGRATIONS


class leveling(Extension):

    def __init__(self, client):
        self.client: vibes.Client = client

    @event_listener()
    async def on_message(self, message: vibes.Message):
        author = message.author
        if message.system or author is None or author.guest or author.bot:
            return
        if message.content.startswith(self.client.prefix):
            return

        chatter = Chatter(author)
        if await chatter.reward_message() and config.get('leveling/announce', True):
            msg = random.choice(config.get('leveling/levelup_messages', None) or ["🎉 {user} reached level {level}!"])
            await message.reply(msg.format(user=author.mention, level=chatter.level))

    @commands.app_command(cooldown=Cooldown(10, 2, Cooldown.USER))
    @commands.describe(
        user="Whose level to check (default: you)"
    )
    async def rank(self, ctx: Context, user: vibes.Viewer = None):
        """Check your level, or someone else's"""
        user = user or ctx.author
        chatter = await Chatter(user).fetch()
        current, needed = chatter.progress

        owner = "You are" if user == ctx.author else f"{user} is"
        await ctx.message.reply(f"{owner} level {chatter.level} ({current}/{needed} XP) | Rank #{await chatter.rank()}")

    @commands.app_command(name='top', cooldown=Cooldown(30, 1, Cooldown.CHAT))
    async def leaderboard(self, ctx: Context):
        """The top chatters on VIBES"""
        chatters = await Chatter.leaderboard(limit=config.get('leveling/leaderboard_size', 5))
        if not chatters:
            await ctx.message.reply("Nobody has any XP yet.")
            return

        lines = [f"#{i} {c.username or 'unknown'} (lvl {c.level})" for i, c in enumerate(chatters, 1)]
        await ctx.message.reply("🏆 " + " | ".join(lines))


async def setup(client):
    await drekbase.migrate(MIGRATIONS)
    await client.add_ext(leveling(client))
