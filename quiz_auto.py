from .. import loader
import asyncio

TARGET_CHATS = {
    -1002556760909,
    -1003839856024,
}

@loader.tds
class QuizAutoMod(loader.Module):
    """QuizAuto seguro"""

    strings = {"name": "QuizAuto"}

    async def client_ready(self, client, db):
        self.client = client
        self.seen = set()

    async def watcher(self, message):
        try:
            if getattr(message, "out", False):
                return

            if getattr(message, "chat_id", None) not in TARGET_CHATS:
                return

            msg_id = getattr(message, "id", None)
            if not msg_id:
                return

            key = f"{message.chat_id}:{msg_id}"
            if key in self.seen:
                return

            has_poll = False

            if getattr(message, "poll", None):
                has_poll = True

            media = getattr(message, "media", None)
            if media and getattr(media, "poll", None):
                has_poll = True

            if not has_poll:
                return

            await asyncio.sleep(0.5)

            try:
                await message.click(0)
                self.seen.add(key)
            except Exception:
                return

            if len(self.seen) > 300:
                self.seen = set(list(self.seen)[-200:])

        except Exception:
            pass
