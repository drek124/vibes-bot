""" ## Chat Interaction System
Create live callbacks to chat messages
"""
import datetime
import vibes

MISSING = object()


class InteractionEvent:
    def __init__(self, message: vibes.Message, original_interaction):
        self.message: vibes.Message = message
        self.interaction: ChatInteraction = original_interaction


class ChatInteraction:
    def __init__(
            self, viewer: vibes.Viewer, *,
            auto_stop: bool = True,
            timeout: float = None,
            callback = MISSING
            ):
        """Chat interaction handler
        ## Parameters
        - viewer: The stream viewer that triggers the interaction
        - auto_stop: Stops the interaction after the first response. If `False`, it keeps
            responding to every message until `stop()` is called or it times out.
        - timeout: Time in seconds until the interaction expires & stops responding
        - callback: The `async def callback(InteractionEvent)` function for the interaction
        """
        if viewer.viewer_id is None:
            raise ValueError("Chat interactions can't be created for guest viewers")

        self.viewer: vibes.Viewer = viewer
        self.key: str = viewer.viewer_id
        self.auto_stop: bool = auto_stop
        self.timeout: float = timeout
        self.responded: bool = False
        self.created_at: datetime.datetime = datetime.datetime.now()

        if callback is not MISSING:
            self.callback = callback

        self.start()

    async def callback(self, event: InteractionEvent):
        """The callback function that will be called when the interaction is triggered.
        ## Parameters
        - `event`: The interaction event & context.
        """
        return

    @property
    def active(self) -> bool:
        """Whether the interaction is currently listening for messages."""
        return self in interactions.get(self.key, [])

    @property
    def expired(self) -> bool:
        return self.timeout is not None and (datetime.datetime.now() - self.created_at).total_seconds() > self.timeout

    def start(self):
        """Starts (or restarts) listening for messages. Restarting also resets the timeout."""
        self.created_at = datetime.datetime.now()
        if not self.active:
            interactions.setdefault(self.key, []).append(self)

    def stop(self):
        """Stops the interaction from responding to any more messages."""
        listeners = interactions.get(self.key)
        if listeners and self in listeners:
            listeners.remove(self)
            if not listeners:
                del interactions[self.key]

    async def run(self, message: vibes.Message):
        """Responds to the message event"""
        if not self.active:
            return
        if self.expired:
            self.stop()
            return

        # Stop before awaiting so a second message can't trigger it while the callback runs
        if self.auto_stop:
            self.stop()
        self.responded = True
        return await self.callback(InteractionEvent(message, self))


interactions: dict[str, list[ChatInteraction]] = {}

__all__ = [
    "ChatInteraction",
    "InteractionEvent"
]