from .. import loader
import pytesseract
from PIL import Image, ImageOps, ImageFilter
import io
import re
import asyncio

TARGET_SENDER_ID = 691070694

TARGET_CHATS = {
    -1002556760909,
    -1003839856024,
}

TRIGGER_TEXT = "escrever a palavra"

def clean_result(text):
    if not text:
        return ""

    text = re.sub(r"[^A-Za-zÀ-ÿ\s-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    words = [w for w in text.split() if len(w) >= 3 and not any(ch.isdigit() for ch in w)]

    if not words:
        return ""

    best = max(words, key=len)
    return best.upper()[:80]

def preprocess_image(image):
    image = image.convert("L")
    image = ImageOps.autocontrast(image)
    image = image.filter(ImageFilter.SHARPEN)

    w, h = image.size
    if w < 1000:
        image = image.resize((w * 2, h * 2))

    return image

@loader.tds
class GameOCRMod(loader.Module):
    """GameOCR seguro"""

    strings = {"name": "GameOCR"}

    async def client_ready(self, client, db):
        self.client = client
        self.seen = set()

    async def watcher(self, message):
        try:
            if getattr(message, "out", False):
                return

            if getattr(message, "chat_id", None) not in TARGET_CHATS:
                return

            if getattr(message, "sender_id", None) != TARGET_SENDER_ID:
                return

            msg_id = getattr(message, "id", None)
            if not msg_id:
                return

            key = f"{message.chat_id}:{msg_id}"
            if key in self.seen:
                return

            if not getattr(message, "photo", None):
                return

            caption = (getattr(message, "raw_text", "") or "").lower()
            if TRIGGER_TEXT not in caption:
                return

            file = await message.download_media(bytes)
            if not file:
                return

            image = Image.open(io.BytesIO(file))
            image = preprocess_image(image)

            text = pytesseract.image_to_string(
                image,
                lang="por+eng",
                config="--psm 6"
            )

            result = clean_result(text)
            if not result:
                return

            await asyncio.sleep(0.5)
            await self.client.send_message(message.chat_id, result)

            self.seen.add(key)

        except Exception:
            pass
