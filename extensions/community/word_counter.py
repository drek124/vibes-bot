import re
import logging
import vibes
from vibes import commands
from vibes.commands import Context
from vibes.ext import event_listener, Extension
from data import drekbase, config


# The word_counters.word column is VARCHAR(50), so longer words can't be stored
DB_MAX_WORD_LENGTH = 50
MAX_WORD_LENGTH = config.get('community/word_tracker/max_word_length', DB_MAX_WORD_LENGTH)
if MAX_WORD_LENGTH > DB_MAX_WORD_LENGTH:
    logging.warning(f"community/word_tracker/max_word_length ({MAX_WORD_LENGTH}) is higher than {DB_MAX_WORD_LENGTH}, using {DB_MAX_WORD_LENGTH}")
    MAX_WORD_LENGTH = DB_MAX_WORD_LENGTH


class community_word_counter(Extension):

    def __init__(self, client):
        self.client: vibes.Client = client

        # Cache
        self.tracked: dict[str, set[str]] = {}

    async def get_tracked(self, channel_id: str) -> set[str]:
        if channel_id not in self.tracked:
            async with drekbase.get_cursor() as c:
                await c.execute("SELECT word FROM word_counters WHERE channel_id = %s", (channel_id,))
                self.tracked[channel_id] = {row[0] for row in await c.fetchall()}
        return self.tracked[channel_id]

    @commands.app_command(name='track',
        cooldown=commands.Cooldown(10, 3, commands.Cooldown.USER),
        role=vibes.Role.MOD
    )
    @commands.describe(
        word="The word to count in chat (no spaces)"
    )
    async def track(self, ctx: Context, word: str):
        """Count how many times a word is said in this chat"""
        word = word.strip().lower()
        if not word or any(ch.isspace() for ch in word) or len(word) > MAX_WORD_LENGTH:
            await ctx.message.reply(f"Invalid word. It must be a single word, up to {MAX_WORD_LENGTH} characters.")
            return

        channel_id = str(ctx.stream.channel.id)
        tracked = await self.get_tracked(channel_id)
        if word in tracked:
            await ctx.message.reply(f"\"{word}\" is already being tracked.")
            return

        async with drekbase.get_cursor() as c:
            await c.execute("""
                INSERT IGNORE INTO word_counters (channel_id, word) VALUES (%s, %s)
            """, (channel_id, word))
        tracked.add(word)

        await ctx.message.reply(f"✅ Now tracking \"{word}\"!")

    @commands.app_command(name='untrack',
        cooldown=commands.Cooldown(10, 5, commands.Cooldown.USER),
        role=vibes.Role.MOD
    )
    @commands.describe(
        word="The tracked word to stop counting"
    )
    async def untrack(self, ctx: Context, word: str):
        """Stop counting a word in this chat"""
        word = word.strip().lower()
        channel_id = str(ctx.stream.channel.id)

        async with drekbase.get_cursor() as c:
            await c.execute("""
                DELETE FROM word_counters WHERE channel_id = %s AND word = %s
            """, (channel_id, word))
            deleted = c.rowcount
        (await self.get_tracked(channel_id)).discard(word)

        if not deleted:
            await ctx.message.reply(f"\"{word}\" isn't being tracked.")
            return
        await ctx.message.reply(f"✅ Stopped tracking \"{word}\".")

    @event_listener()
    async def on_message(self, message: vibes.Message):
        author = message.author
        if message.system or author is None or author.bot or not message.content:
            return
        # Commands (e.g. /track <word>) shouldn't count towards the word
        prefixes = ('/',) + ((self.client.prefix,) if self.client.prefix else ())
        if message.content.startswith(prefixes):
            return

        channel_id = str(message.stream.channel.id)
        tracked = await self.get_tracked(channel_id)
        if not tracked:
            return

        content = message.content.lower()

        # Copy since /track and /untrack can change the set while the loops is running
        
        for word in list(tracked):
            # Whole word matches only, so "cat" doesn't count "category" B)
            amount = len(re.findall(rf"(?<!\w){re.escape(word)}(?!\w)", content))
            if not amount:
                continue

            async with drekbase.get_cursor() as c:
                await c.execute("""
                    UPDATE word_counters SET count = count + %s
                    WHERE channel_id = %s AND word = %s
                """, (amount, channel_id, word))
                await c.execute("""
                    SELECT count FROM word_counters WHERE channel_id = %s AND word = %s
                """, (channel_id, word))
                count = await drekbase.dbfetch.one(c)

            if count is None: # Untracked in the meantime
                continue
            await message.reply(f"{word} has been said {count} time{'s' if count != 1 else ''}")


MIGRATIONS = [
    ("community_002_create_word_counters", """
        CREATE TABLE IF NOT EXISTS word_counters (
        channel_id VARCHAR(50) NOT NULL,
        word VARCHAR(50) NOT NULL,
        count BIGINT UNSIGNED NOT NULL DEFAULT 0,
        PRIMARY KEY (channel_id, word)
        )
    """),
]


async def setup(client):
    await drekbase.migrate(MIGRATIONS)
    await client.add_ext(community_word_counter(client))
