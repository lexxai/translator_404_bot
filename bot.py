import logging
import os
from pathlib import Path
from typing import Any

from telethon import TelegramClient, events
from googletrans import Translator

from dotenv import load_dotenv
from telethon.errors import UserNotParticipantError
from telethon.tl.functions.channels import GetParticipantRequest

from ext.local_translated import LocalTranslated
from ext.sessions import Sessions, Category
from ext.language_detection import LanguageDetection
from utils import get_version

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", level=logging.INFO
)

logger = logging.getLogger("bot")
logging.getLogger("telethon").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

load_dotenv()

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
storage_path = Path(
    os.environ.get("STORAGE_PATH", Path(__file__).parent.joinpath("storage"))
)
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
trust_telegram_language = (
    os.environ.get("TRUST_TELEGRAM_LANGUAGE", "true").strip().lower() == "true"
)

if debug:
    logger.setLevel(logging.DEBUG)

language_detection = LanguageDetection(destination_language, excluded_languages)
sessions = Sessions(storage_path)
translator = Translator()
local_translated = LocalTranslated(translator, destination_language)

client = TelegramClient(
    storage_path / ".bot",
    api_id,
    api_hash,
    lang_code=destination_language,
    use_ipv6=use_ipv6,
).start(bot_token=bot_token)


def get_sender_language(event) -> str:
    # logger.debug(f"{event.sender.lang_code=}")
    # return "fr"
    return event.sender.lang_code


def get_command_args(event):
    match = event.pattern_match
    result = match.groups()
    # logger.debug(f"{result=}")
    return [
        x.strip() for x in result if x and x.strip() and (x.startswith("@") is False)
    ]


async def get_chat_id_from_arg(event) -> int | None:
    args = get_command_args(event)
    arg_1 = args[0] if len(args) > 0 else None
    chat_id = int(arg_1) if arg_1 else event.chat_id
    if not arg_1 and not event.is_group:
        await event.reply(
            await local_translated.gettext(
                "You must specify a group ID or join a group to use this command.",
                get_sender_language(event),
            )
        )
        return None
    return chat_id


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


async def answer_private_message(
    event, chat_id: int | None = None, sender_id: int | None = None
):
    try:
        chat_id = chat_id or event.chat_id
        sender_id = sender_id or event.sender_id
        if sessions.is_exists(Category.INFORMED, chat_id, sender_id):
            return
        await sessions.add(Category.INFORMED, chat_id, sender_id)
        group_name = await get_group_name(chat_id=chat_id)
        if group_name:
            await event.reply(
                await local_translated.gettext(
                    "I've sent the answer to you privately. Check your personal messages from this bot! This notification will only be shown to you once.",
                    get_sender_language(event),
                )
            )
    except Exception as e:
        logger.error(e)


async def is_sender_in_group(event, chat_id: int | None = None):
    chat_id = chat_id or event.chat_id
    if event and chat_id:
        try:
            # Fetch the participant information
            await client(
                GetParticipantRequest(
                    channel=chat_id,
                    participant=event.sender_id,
                )
            )
            # logger.debug(f"User {event.sender_id} is a member of the group.")
            return True
        except (UserNotParticipantError, IndexError):
            logger.debug(f"User {event.sender_id} is NOT a member of the group.")
            await event.reply(
                await local_translated.gettext(
                    "You must be a member of the group to use this command. Please join the group and try again.",
                    get_sender_language(event),
                )
            )
        except Exception as e:
            logger.error(e)
    return False


async def get_group_name(event=None, chat_id: str | int | None = None) -> str | None:
    try:
        chat_id = int(chat_id) if chat_id is not None else event.chat_id
        entity = await client.get_entity(chat_id)
        group_name = entity.title if entity and hasattr(entity, "title") else None
        return group_name
    except Exception as e:
        logger.error(e)


async def is_trusted_telegram_language(event, notify: bool = True) -> bool | None:
    sender_language = get_sender_language(event)
    if (
        trust_telegram_language
        and sender_language
        and sender_language == destination_language
    ):
        if notify:
            await client.send_message(
                event.sender_id,
                await local_translated.gettext(
                    "According to Telegram app's language settings, you are always excluded from automatic translation for this language",
                    get_sender_language(event),
                )
                + f": {destination_language}",
            )
        logger.debug(
            f"Sender language '{sender_language}' is trusted and excluded from translation."
        )
        return True


@client.on(events.NewMessage(pattern=r"^/chat_id"))
async def handler_chat_id(event):
    if not event.is_group:
        await event.reply(
            await local_translated.gettext(
                "You must join a group to use this command.", get_sender_language(event)
            )
        )
        return None
    chat_id = int(event.chat_id)
    sender_id = event.sender_id
    group_name = await get_group_name(chat_id=chat_id)
    try:
        await client.send_message(sender_id, f"Group ID: {chat_id} of '{group_name}'")
        await answer_private_message(event, chat_id, sender_id)
    except Exception as e:
        logger.error(e)


@client.on(events.NewMessage(pattern=r"^/help"))
async def handler_help(event):
    try:
        src = get_sender_language(event)
        help_text = [
            "/help - " + await local_translated.gettext("Help with commands", src),
            "/translate <lang> <text> - "
            + await local_translated.gettext(
                "Translate to desired language of entered text", src
            ),
            "/chat_id - "
            + await local_translated.gettext(" Show ", src)
            + " chat_id "
            + await local_translated.gettext("of this group", src),
            "/exclude <group_id> - "
            + await local_translated.gettext(
                " Exclude current user from automatic translations", src
            ),
            "/include <group_id> - "
            + await local_translated.gettext(
                " Include current user for automatic translations", src
            ),
            "/check <group_id> - "
            + await local_translated.gettext(
                " Check if included current user for automatic translations", src
            ),
            "",
            "__Version: {version}__".format(version=__version__),
        ]

        await event.reply("\n".join(help_text))
    except Exception as e:
        logger.error(e)


@client.on(events.NewMessage(pattern=r"^/check\s?([-0-9]*)"))
async def handler_check(event):
    try:
        chat_id = await get_chat_id_from_arg(event)
        if not chat_id:
            return None
        if not await is_sender_in_group(event, chat_id=chat_id):
            return None
        sender_id = event.sender_id
        excluded = sessions.is_exists(Category.EXCLUDED_SENDERS, chat_id, sender_id)
        group_name = await get_group_name(chat_id=chat_id)
        if not group_name:
            await event.reply(
                local_translated.gettext("Unknown group.", get_sender_language(event))
            )
            return None
        if await is_trusted_telegram_language(event):
            return
        await client.send_message(
            sender_id,
            await local_translated.gettext(
                f"You are {'excluded' if excluded else 'included'} for using the bot in group: ",
                get_sender_language(event),
            )
            + f"'{group_name}'.",
        ),
        await answer_private_message(event)
    except Exception as e:
        logger.error(e)


@client.on(events.NewMessage(pattern=r"^/exclude\s?([-0-9]*)"))
async def handler_exclude(event):
    try:
        chat_id = await get_chat_id_from_arg(event)
        if not chat_id:
            return None
        if not await is_sender_in_group(event, chat_id=chat_id):
            return None
        sender_id = event.sender_id
        if await is_trusted_telegram_language(event):
            return
        group_name = await get_group_name(chat_id=chat_id)
        if not group_name:
            await event.reply(
                await local_translated.gettext(
                    "Unknown group.", get_sender_language(event)
                )
            )
            return None
        await sessions.add(Category.EXCLUDED_SENDERS, chat_id, event.sender_id)
        await client.send_message(
            sender_id,
            await local_translated.gettext(
                f"You have been excluded from using the bot in group",
                get_sender_language(event),
            )
            + f": '{group_name}'.",
        )
        await answer_private_message(event)
    except Exception as e:
        logger.error(e)


@client.on(events.NewMessage(pattern=r"^/include\s?([-0-9]*)"))
async def handler_include(event):
    try:
        chat_id = await get_chat_id_from_arg(event)
        if not chat_id:
            return None
        if not await is_sender_in_group(event, chat_id=chat_id):
            return None
        sender_id = event.sender_id
        if await is_trusted_telegram_language(event):
            return
        group_name = await get_group_name(event, chat_id=chat_id)
        if not group_name:
            await local_translated.gettext("Unknown group.", get_sender_language(event))
            return None
        await sessions.remove(Category.EXCLUDED_SENDERS, chat_id, event.sender_id)
        await client.send_message(
            sender_id,
            await local_translated.gettext(
                f"You have been included for using the bot in group",
                get_sender_language(event),
            )
            + f": '{group_name}'.",
        )
        await answer_private_message(event)
    except Exception as e:
        logger.error(e)


@client.on(events.NewMessage(pattern=r"^/translate(?:\s+(\S+)(?:\s+(.+))?)?$"))
async def translate_handler(event):
    try:
        args = get_command_args(event)
        if len(args) == 2:
            target_lang = args[0]
            if len(target_lang) == 2 and target_lang.islower():
                text = args[1]
            else:
                target_lang = destination_language
                text = " ".join(args)
        elif len(args) == 1:
            target_lang = destination_language
            text = args[0]
        else:
            await event.reply(
                await local_translated.gettext(
                    "Missing text to translate.", get_sender_language(event)
                )
            )
            return

        translated = await translator.translate(text, dest=target_lang)
        await event.reply(
            "".join(
                [
                    "",
                    await local_translated.gettext(
                        "In translation from", get_sender_language(event)
                    ),
                    f" ({language_detection.map_lang(target_lang)}):\n{translated.text}",
                ]
            )
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
        if sessions.is_exists(
            Category.EXCLUDED_SENDERS, event.chat_id, event.sender_id
        ):
            logger.debug(f"Sender '{event.sender_id}' is excluded from translation.")
            return
        if await is_trusted_telegram_language(event, notify=False):
            return
        original_text = extract_text_from_message(event.message)
        detected_language = await language_detection.detect_language(original_text)
        if detected_language not in excluded_languages:
            translated_text = await translator.translate(
                original_text, dest=destination_language
            )
            await event.reply(
                "".join(
                    [
                        await local_translated.gettext(
                            "In translation from", get_sender_language(event)
                        ),
                        f" ({language_detection.map_lang(detected_language)}):\n{translated_text.text}",
                    ]
                )
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
    __version__: str | Any = os.environ.get("VERSION", get_version())
    logger.debug(f"Version: {__version__}")
    sessions.load()
    logger.debug(f"{excluded_languages=}")
    logger.debug(f"{trust_telegram_language=}")

    try:
        with client:
            client.loop.run_until_complete(main())
    except KeyboardInterrupt:
        client.disconnect()
