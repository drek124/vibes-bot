import vibes
import logging
import asyncio
from vibes.ext import Extension, event_listener
from extensions.chatinteraction.assets import interactions


class chatinteraction(Extension):
    def __init__(self, client):
        self.client: vibes.Client = client

    @event_listener()
    async def on_message(self, message: vibes.Message):
        author = message.author
        if message.system or author is None or author.guest:
            return
        # Commands are never answers to an interaction
        prefixes = ('/',) + ((self.client.prefix,) if self.client.prefix else ())
        if message.content and message.content.startswith(prefixes):
            return

        # Copy the list since interactions remove themselves while running
        listeners = list(interactions.get(author.viewer_id, []))
        if not listeners:
            return

        results = await asyncio.gather(*(i.run(message) for i in listeners), return_exceptions=True)
        for res in results:
            if isinstance(res, Exception):
                logging.error("Error occurred in chat interaction callback", exc_info=res)


async def setup(client):
    await client.add_ext(chatinteraction(client))
