import vibes
from vibes import commands
from vibes.commands import Context
from vibes.ext import event_listener, Extension
from data import drekbase


DISCORD_INVITE_LINK = 'https://discord.gg/'

class community(Extension):

    def __init__(self, client):
        self.client: vibes.Client = client

    @commands.app_command(name='discord',
        cooldown=commands.Cooldown(60, 2, commands.Cooldown.USER),
        role=vibes.Role.STREAMER
    )
    @commands.describe(
        link="Your discord server link"
    )
    async def register_discord(self, ctx: Context, link: str):
        """Let ppl use !discord in this stream!"""
        if not link.startswith(DISCORD_INVITE_LINK) or link.endswith(DISCORD_INVITE_LINK) or len(link) > 30:
            await ctx.message.reply("Invalid link.")
            return
        async with drekbase.get_cursor() as c:
            await c.execute("""
                INSERT INTO communities (user_id, discord) 
                VALUES (%s, %s) AS n
                ON DUPLICATE KEY UPDATE discord = n.discord;

                """, (ctx.stream.channel.id, link))

        await ctx.message.reply("✅ Done!")


    @commands.command(cooldown=commands.Cooldown(30, 2, commands.Cooldown.CHAT))
    async def discord(self, ctx: Context):
        async with drekbase.get_cursor() as c:
            await c.execute("""
                SELECT discord FROM communities WHERE user_id = %s
            """, (ctx.stream.channel.id,))
            link = await drekbase.dbfetch.one(c)

        if link is None:
            return 
        await ctx.message.reply(link)


async def setup(client):
    async with drekbase.get_cursor() as c:
        await c.execute("""
        CREATE TABLE IF NOT EXISTS communities (
        user_id VARCHAR(50) NOT NULL,
        discord VARCHAR(150) DEFAULT NULL,
        PRIMARY KEY (user_id)
        )
    """)
    await client.add_ext(community(client))