from .. import loader
from telethon import events, functions, types
import asyncio
import time

TARGET_USER_ID = 8505890439

TARGET_CHATS = {
    -1002556760909,
    -1003839856024,
}

REACTION_EMOJI = "😊"
REPLY_TEXT = "Oiii"

COOLDOWN = 86400  # 1 dia


@loader.tds
class MentionReactMod(loader.Module):
    """Reage 1x por dia quando o usuário alvo menciona ou responde você."""

    strings = {"name": "MentionReact"}

    async def client_ready(self, client, db):
        self.client = client
        self.db = db
        self.me = await client.get_me()
        self.me_id = self.me.id
        self.me_username = (self.me.username or "").lower()

        self.last_trigger = self.db.get("MentionReact", "last_trigger", 0)

        if getattr(self, "_handler_added", False):
            return

        self._handler_added = True

        @client.on(events.NewMessage(incoming=True))
        async def handler(event):
            try:
                if event.chat_id not in TARGET_CHATS:
                    return

                if event.sender_id != TARGET_USER_ID:
                    return

                now = int(time.time())

                if now - self.last_trigger < COOLDOWN:
                    return

                msg = event.message

                should_answer = False

                if getattr(msg, "mentioned", False):
                    should_answer = True

                text = (getattr(msg, "raw_text", None) or "").lower()
                if self.me_username and f"@{self.me_username}" in text:
                    should_answer = True

                if not should_answer and getattr(msg, "is_reply", False):
                    try:
                        replied = await msg.get_reply_message()
                        if replied and (
                            getattr(replied, "sender_id", None) == self.me_id
                            or getattr(replied, "out", False)
                        ):
                            should_answer = True
                    except:
                        pass

                if not should_answer:
                    return

                await asyncio.sleep(0.4)

                try:
                    await self.client(
                        functions.messages.SendReactionRequest(
                            peer=event.chat_id,
                            msg_id=msg.id,
                            reaction=[types.ReactionEmoji(emoticon=REACTION_EMOJI)],
                            big=False,
                            add_to_recent=True,
                        )
                    )
                except:
                    pass

                try:
                    await event.reply(REPLY_TEXT)
                except:
                    pass

                self.last_trigger = now
                self.db.set("MentionReact", "last_trigger", now)

            except Exception as e:
                print("MentionReact erro:", e)
