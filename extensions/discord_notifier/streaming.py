import vibes
import drekord
import datetime
from vibes import commands
from vibes.commands import Context
from vibes.ext import event_listener, Extension
from data import drekbase, helper, config

from drekord.ui import *

STREAMERS: dict[str, datetime.datetime] = {}

class notifier_streaming(Extension):

    def __init__(self, client):
        self.client: vibes.Client = client

    @event_listener()
    async def on_stream_online(self, stream: vibes.Stream):
        now = datetime.datetime.now()
        if (
            now - STREAMERS.get(stream.channel.id, datetime.datetime.fromtimestamp(0)) 
        ).total_seconds() < config.get('discord-notifier/new_stream_cooldown', 420):
            # Return to prevent spam from instantly restarting a stream 
            return
        
        async with drekord.Client(helper.getenv('DISCORD_BOT_TOKEN')) as c:
            channel = await c.fetch_channel(config.get("discord-notifier/channel"))
            view = LayoutView()
            container = Container(accent_color="#00a0e5")
            view.add_item(container)
            
            for i in [
                Section(TextDisplay(f"# {stream.channel} is LIVE!"), accessory=Thumbnail(stream.channel.avatar_url)),
                Separator(),
                TextDisplay(f"[{stream.channel}]({stream.channel.url}) just started streaming **{stream.title}** in the **{stream.category.name}** category!"),
                ActionRow(Button(label="Tune in!", url=stream.url)),
                TextDisplay(f"-# Want these notifications for your channel? [Add me]({config.get('bot_page_url')}/add)!")
            ]:
                container.add_item(i)

            msg = await channel.send(view=view)
        STREAMERS[stream.channel.id] = now
  

async def setup(client):
    await client.add_ext(notifier_streaming(client))