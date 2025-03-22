import logging
import os
import pickle
from pathlib import Path

from telethon import TelegramClient, events
from googletrans import Translator

from dotenv import load_dotenv

from ext.language_detection import LanguageDetection

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", level=logging.INFO
)

logger = logging.getLogger("bot")
logging.getLogger("telethon").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)


load_dotenv()

__version__ = os.environ.get("VERSION", "dev")
# Your API credentials (Get from https://my.telegram.org)
api_id = int(os.environ.get("API_ID", 0))
api_hash = os.environ.get("API_HASH")
bot_token = os.environ.get("BOT_TOKEN")
assert api_id and api_hash and bot_token, "API credentials not found"
groups_id = list(map(int, os.environ.get("GROUPS_ID", "0").strip().split(",")))
from_users = os.environ.get("FROM_USERS", [])
if isinstance(from_users, str):
    from_users = [u.strip() for u in from_users.strip().split(",") if u.strip()]
destination_language = os.environ.get("DESTINATION_LANGUAGE", "uk")
storage_path = Path(os.environ.get("STORAGE_PATH", "storage"))
excluded_languages = os.environ.get("EXCLUDED_LANGUAGES", [])
if isinstance(excluded_languages, str):
    excluded_languages = [
        u.strip() for u in excluded_languages.strip().split(",") if u.strip()
    ]

use_ipv6 = os.environ.get("USE_IPV6", "False").strip().lower() == "true"
use_intro_message = (
    os.environ.get("USE_INTRO_MESSAGE", "False").strip().lower() == "true"
)
debug = os.environ.get("DEBUG", "False").strip().lower() == "true"
excluded_languages.append(destination_language)
excluded_senders_filename = ".excluded_senders.pickle"

language_detection = LanguageDetection(destination_language, excluded_languages)


if debug:
    logger.setLevel(logging.DEBUG)


excluded_senders = {}
translator = Translator()
client = TelegramClient(
    storage_path / ".bot",
    api_id,
    api_hash,
    lang_code=destination_language,
    use_ipv6=use_ipv6,
).start(bot_token=bot_token)


def add_excluded_sender(sender_id, group_id):
    excluded_senders.setdefault(group_id, set()).add(sender_id)
    save_excluded_senders()


def remove_excluded_sender(sender_id, group_id):
    if group_id in excluded_senders:
        excluded_senders[group_id].discard(sender_id)
        save_excluded_senders()


def is_excluded_sender(sender_id, group_id):
    return group_id in excluded_senders and sender_id in excluded_senders[group_id]


def save_excluded_senders(storage_file: str = excluded_senders_filename):
    if not storage_path.exists():
        storage_path.mkdir(parents=True)
    excluded_senders_path = storage_path / storage_file
    try:
        with excluded_senders_path.open("wb") as f:
            pickle.dump(excluded_senders, f)
    except Exception as e:
        logger.error(e)


def load_excluded_senders(storage_file: str = excluded_senders_filename):
    if not storage_path.exists():
        return
    result = {}
    excluded_senders_path = storage_path / storage_file
    if excluded_senders_path.exists():
        try:
            with excluded_senders_path.open("rb") as f:
                result = pickle.load(f)
        except Exception as e:
            logger.error(e)
    return result


def extract_text_from_message(message):
    if message.media:
        try:
            if poll := message.media.poll:
                question = poll.question.text
                answer = ", ".join([str(answer.text.text) for answer in poll.answers])
                return f"{question}: {answer}"
        except Exception as e:
            logger.error(e)
    return message.message


async def send_intro_message():
    try:
        for entity in groups_id:
            if entity:
                await client.send_message(
                    entity, "🚀 Bot started and ready to translate in this group!"
                )
    except Exception as e:
        logger.error(e)


@client.on(events.NewMessage(pattern=r"^/chat_id"))
async def handler_chat_id(event):
    detected_chat_id = event.chat_id
    try:
        await event.reply(f"Group ID: {detected_chat_id}")
    except Exception as e:
        logger.error(e)


@client.on(events.NewMessage(pattern=r"^/help"))
async def handler_help(event):
    help_text = (
        "/help - Help with commands\n"
        "/translate - Translate: <lang> <text>\n"
        "/chat_id - Show chat_id of group\n"
        "/exclude - Exclude current user from automatically translates\n"
        "/include - Include current user for automatically translates\n"
        "/check - Check if included current user for automatically translates\n"
        "__Version__: {version}".format(version=__version__)
    )
    try:
        await event.reply(help_text)
    except Exception as e:
        logger.error(e)


@client.on(events.NewMessage(pattern=r"^/check"))
async def handler_check(event):
    try:
        excluded = is_excluded_sender(event.sender_id, event.chat_id)
        await event.reply(
            f"You are **{'excluded' if excluded else 'included'}** for using the bot in this group."
        )
    except Exception as e:
        logger.error(e)


@client.on(events.NewMessage(pattern=r"^/exclude"))
async def handler_exclude(event):
    try:
        add_excluded_sender(event.sender_id, event.chat_id)
        await event.reply(
            "You have been **excluded** from using the bot in this group."
        )
    except Exception as e:
        logger.error(e)


@client.on(events.NewMessage(pattern=r"^/include"))
async def handler_include(event):
    try:
        remove_excluded_sender(event.sender_id, event.chat_id)
        await event.reply("You have been **included** for using the bot in this group.")
    except Exception as e:
        logger.error(e)


@client.on(events.NewMessage(pattern=r"^/translate\s+(\w+)\s+(.+)"))
async def translate_handler(event):
    match = event.pattern_match
    target_lang = match.group(1)
    text = match.group(2)

    try:
        translated = await translator.translate(text, dest=target_lang)
        await event.reply(
            f"**Translated ({language_detection.map_lang(target_lang)}):**\n{translated.text}"
        )
    except Exception as e:
        try:
            await event.reply(f"Translation failed: {e}")
        except Exception as e:
            logger.error(e)


# @client.on(events.NewMessage)
async def handler(event):
    try:
        if event.raw_text.startswith("/"):
            return
        if is_excluded_sender(event.sender_id, event.chat_id):
            return
        original_text = extract_text_from_message(event.message)

        # detected_chat_id = event.chat_id
        # print(f"[{detected_chat_id}][{sender_id}] {event.message.message=}")

        detected_language = language_detection.detect_language(original_text)
        if detected_language not in excluded_languages:
            translated_text = await translator.translate(
                original_text, dest=destination_language
            )
            await event.reply(
                f"🔄 **Translated ({language_detection.map_lang(detected_language)}):**\n{translated_text.text}"
            )

    except Exception as e:
        logger.error(e)


async def main():
    if use_intro_message:
        await send_intro_message()
    logger.info("Starting bot...")
    options = {"incoming": True, "pattern": r"^(?!/).*"}
    if from_users:
        options["from_users"] = from_users
    if groups_id:
        options["chats"] = groups_id
    client.add_event_handler(handler, events.NewMessage(**options))
    await client.run_until_disconnected()


if __name__ == "__main__":
    excluded_senders = load_excluded_senders()
    logger.debug(f"{excluded_senders=}")
    logger.debug(f"{excluded_languages=}")
    logger.debug(f"{from_users=}")

    try:
        with client:
            client.loop.run_until_complete(main())
    except KeyboardInterrupt:
        client.disconnect()
