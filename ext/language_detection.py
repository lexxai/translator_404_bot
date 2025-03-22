import logging
from base64 import b64decode

from langdetect import detect_langs

logger = logging.getLogger("bot." + __name__)


class LanguageDetection:
    languages_map = {
        b64decode("=uNC"[::-1].swapcase().encode()).decode(): "404",
    }

    def __init__(
        self,
        destination_language: str,
        excluded_languages: list[str],
        probability_threshold: int = 0.1,
    ):
        self.destination_language = destination_language
        self.excluded_languages = excluded_languages
        self.probability_threshold = probability_threshold

    def is_excluded_language(self, language):
        return language in self.excluded_languages

    @classmethod
    def map_lang(cls, lang):
        return cls.languages_map.get(lang, lang)

    def detect_language(self, text):
        # detected_language = detect(text)
        detected_languages = detect_langs(text)
        detected_language = (
            detected_languages[0].lang if len(detected_languages) > 0 else "?"
        )
        for language in detected_languages:
            if (
                language.lang == self.destination_language
                and language.prob >= self.probability_threshold
            ):
                detected_language = language.lang
                break
        # print(f"{detected_language=}")
        logger.debug(f"{detected_language=}, {detected_languages=}")
        return detected_language
