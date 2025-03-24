import asyncio
import logging
from base64 import b64decode

logger = logging.getLogger("bot." + __name__)


class LocalTranslated:

    def __init__(self, translator, dest_language: str, src_language: str = "en"):
        self.locker = asyncio.Lock()
        self.translator = translator
        self.dest_language = dest_language
        self.src_language = src_language
        self.languages_map = {
            b64decode("=uNC"[::-1].swapcase().encode()).decode(): dest_language,
        }
        self.t_cache = {}

    async def gettext(
        self, input_text, dest_language: str = None, src_language: str = None
    ) -> str | None:
        dest_language = (
            self.languages_map.get(dest_language, dest_language)
            if dest_language is not None
            else self.dest_language
        )
        src_language = src_language or self.src_language
        if dest_language == src_language:
            return input_text
        if input_text in self.t_cache.get(dest_language, {}):
            return self.t_cache[dest_language][input_text]
        r = await self.translator.translate(input_text, dest=dest_language)
        if r:
            async with self.locker:
                self.t_cache.setdefault(dest_language, {})[input_text] = r.text
            return r.text
