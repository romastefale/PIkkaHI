from .. import loader, utils
import asyncio
import unicodedata

TARGET_CHATS = {
    -1002556760909,
    -1003839856024,
}

SCAN_INTERVAL = 1
SCAN_LIMIT = 6

def normalize(text):
    if not text:
        return ""
    text = str(text).lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = " ".join(text.split())
    return text

def button_text(button):
    return normalize(
        getattr(button, "text", None)
        or getattr(button, "title", None)
        or ""
    )

def is_target_chat(message):
    return getattr(message, "chat_id", None) in TARGET_CHATS

def is_bau_message(message):
    text = normalize(
        getattr(message, "raw_text", None)
        or getattr(message, "text", None)
        or ""
    )
    return "bau" in text

async def click_resgatar(message):
    buttons = getattr(message, "buttons", None)
    if not buttons:
        return False

    for row_i, row in enumerate(buttons):
        for btn_i, button in enumerate(row):
            label = button_text(button)

            if "resgatar" not in label:
                continue

            try:
                await asyncio.sleep(0.4)
                await message.click(row_i, btn_i)
                return True
            except Exception:
                try:
                    await message.click(text=getattr(button, "text", None) or getattr(button, "title", None))
                    return True
                except Exception:
                    return False

    return False

@loader.tds
class SmartClickerMod(loader.Module):
    """SmartClicker seguro"""

    strings = {"name": "SmartClicker"}

    async def client_ready(self, client, db):
        self.client = client
        self.db = db
        self.enabled = self.db.get("SmartClicker", "enabled", False)
        self.seen = set(self.db.get("SmartClicker", "seen", []))

        if not hasattr(self, "_task") or self._task.done():
            self._task = asyncio.create_task(self._scanner())

    def save(self):
        self.db.set("SmartClicker", "enabled", self.enabled)
        self.db.set("SmartClicker", "seen", list(self.seen)[-500:])

    async def on_unload(self):
        if hasattr(self, "_task"):
            self._task.cancel()

    @loader.command()
    async def smartclick(self, message):
        args = utils.get_args_raw(message).strip().lower()

        if args not in ("on", "off"):
            status = "ligado" if self.enabled else "desligado"
            return await utils.answer(message, f"SmartClicker está {status}")

        self.enabled = args == "on"
        self.save()
        await utils.answer(message, "SmartClicker ligado" if self.enabled else "SmartClicker desligado")

    async def watcher(self, message):
        if not self.enabled:
            return
        if getattr(message, "out", False):
            return
        if not is_target_chat(message):
            return
        await self._process(message)

    async def _scanner(self):
        await asyncio.sleep(2)

        while True:
            try:
                if self.enabled:
                    for chat_id in TARGET_CHATS:
                        async for message in self.client.iter_messages(chat_id, limit=SCAN_LIMIT):
                            await self._process(message)
                    self.save()

                await asyncio.sleep(SCAN_INTERVAL)

            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(SCAN_INTERVAL)

    async def _process(self, message):
        msg_id = getattr(message, "id", None)
        chat_id = getattr(message, "chat_id", None)

        if msg_id is None or chat_id is None:
            return

        key = f"{chat_id}:{msg_id}"

        if key in self.seen:
            return

        if not is_bau_message(message):
            return

        clicked = await click_resgatar(message)

        if clicked:
            self.seen.add(key)
            self.save()
