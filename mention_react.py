from .. import loader
from telethon import functions, types
import asyncio

TARGET_USER_ID = 8505890439

TARGET_CHATS = {
    -1002556760909,
    -1003839856024,
}

REACTION_EMOJI = "😊"
REPLY_TEXT = "Oiii"

@loader.tds
class MentionReactMod(loader.Module):
    """MentionReact seguro"""

    strings = {"name": "MentionReact"}

    async def client_ready(self, client, db):
        self.client = client
        self.me = await client.get_me()
        self.me_id = self.me.id
        self.me_username = (self.me.username or "").lower()
        self.seen = set()

    async def watcher(self, message):
        try:
            if getattr(message, "out", False):
                return

            if getattr(message, "chat_id", None) not in TARGET_CHATS:
                return

            if getattr(message, "sender_id", None) != TARGET_USER_ID:
                return

            msg_id = getattr(message, "id", None)
            if not msg_id:
                return

            key = f"{message.chat_id}:{msg_id}"
            if key in self.seen:
                return

            should_answer = False

            if getattr(message, "mentioned", False):
                should_answer = True

            text = (getattr(message, "raw_text", "") or "").lower()
            if self.me_username and f"@{self.me_username}" in text:
                should_answer = True

            if not should_answer and getattr(message, "is_reply", False):
                try:
                    replied = await message.get_reply_message()
                    if replied and (
                        getattr(replied, "sender_id", None) == self.me_id
                        or getattr(replied, "out", False)
                    ):
                        should_answer = True
                except Exception:
                    pass

            if not should_answer:
                return

            await asyncio.sleep(0.4)

            try:
                await self.client(
                    functions.messages.SendReactionRequest(
                        peer=message.chat_id,
                        msg_id=message.id,
                        reaction=[types.ReactionEmoji(emoticon=REACTION_EMOJI)],
                    )
                )
            except Exception:
                pass

            await message.reply(REPLY_TEXT)
            self.seen.add(key)

        except Exception:
            pass
