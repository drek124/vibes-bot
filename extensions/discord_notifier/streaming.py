import vibes
import drekord
from vibes import commands
from vibes.commands import Context
from vibes.ext import event_listener, Extension
from data import drekbase, helper, config

from drekord.ui import *

class notifier_streaming(Extension):

    def __init__(self, client):
        self.client: vibes.Client = client

    @event_listener()
    async def on_stream_online(self, stream: vibes.Stream):
        async with drekord.Client(helper.getenv('DISCORD_BOT_TOKEN')) as c:
            channel = await c.fetch_channel(config.get("discord-notifier/channel"))
            view = LayoutView()
            container = Container(accent_color="#00a0e5")
            view.add_item(container)
            
            for i in [
                Section(TextDisplay(f"# {stream.channel} is LIVE!"), accessory=Thumbnail(stream.channel.avatar_url)),
                Separator(),
                TextDisplay(f"[{stream.channel}]({stream.channel.url}) just started streaming **{stream.title}** in the **{stream.category.name}** category!"),
                # MediaGallery(MediaGalleryItem(stream.thumbnail_url)),
                ActionRow(Button(label="Tune in!", url=stream.url)),
                TextDisplay(f"-# Want these notifications for your channel? [Add me]({config.get('bot_page_url')}/add)!")
            ]:
                container.add_item(i)

            await channel.send(view=view)
  

async def setup(client):
    await client.add_ext(notifier_streaming(client))