import os

from telethon import TelegramClient, events
from googletrans import Translator
from langdetect import detect_langs
from dotenv import load_dotenv


load_dotenv()

# Your API credentials (Get from https://my.telegram.org)
api_id = int(os.environ.get("API_ID", 0))
api_hash = os.environ.get("API_HASH")
bot_token = os.environ.get("BOT_TOKEN")
group_id = int(os.environ.get("GROUP_ID", 0))
from_users = os.environ.get("FROM_USERS")
destination_language = os.environ.get("DESTINATION_LANGUAGE", "uk")


translator = Translator()
client = TelegramClient(".bot", api_id, api_hash, lang_code=destination_language).start(
    bot_token=bot_token
)
excluded_users = set()


async def send_intro_message():
    await client.send_message(group_id, "🚀 Bot started and ready to translate!")


def detect_language(text, probability_threshold=0.2):
    # detected_language = detect(text)
    detected_languages = detect_langs(text)
    detected_language = (
        detected_languages[0].lang if len(detected_languages) > 0 else "?"
    )
    for language in detected_languages:
        if (
            language.lang == destination_language
            and language.prob >= probability_threshold
        ):
            detected_language = language.lang
    # print(f"{detected_language=}")
    # print(f"{detected_languages=}")
    return detected_language


def extract_text_from_message(message):
    if message.media:
        try:
            if poll := message.media.poll:
                question = poll.question.text
                answer = ", ".join([str(answer.text.text) for answer in poll.answers])
                return f"{question}: {answer}"
        except Exception as e:
            print(f"Error: {e}")
    return message.message


@client.on(events.NewMessage(pattern=r"^/chat_id"))
async def handler_chat_id(event):
    detected_chat_id = event.chat_id
    try:
        await event.reply(f"Group ID: {detected_chat_id}")
    except Exception as e:
        print(f"Error: {e}")


@client.on(events.NewMessage(pattern=r"^/help"))
async def handler_help(event):
    help_text = (
        "/help - Help with commands\n"
        "/translate - Translate: <lang> <text>\n"
        "/chat_id - Show chat_id of group\n"
        "/exclude - Exclude current user from automatically translates\n"
        "/include - Include current user for automatically translates\n"
        "/check - Check if included current user for automatically translates\n"
    )
    try:
        await event.reply(help_text)
    except Exception as e:
        print(f"Error: {e}")


@client.on(events.NewMessage(pattern=r"^/check"))
async def handler_check(event):
    try:
        sender_id = event.sender_id
        included = sender_id not in excluded_users
        await event.reply(
            f"You are {'included' if included else 'excluded'} for using the bot."
        )
    except Exception as e:
        print(f"Error: {e}")


@client.on(events.NewMessage(pattern=r"^/exclude"))
async def handler_exclude(event):
    try:
        sender_id = event.sender_id
        excluded_users.add(sender_id)
        await event.reply(f"You have been excluded from using the bot.")
    except Exception as e:
        print(f"Error: {e}")


@client.on(events.NewMessage(pattern=r"^/include"))
async def handler_include(event):
    try:
        sender_id = event.sender_id
        excluded_users.discard(sender_id)
        await event.reply(f"You have been included for using the bot.")
    except Exception as e:
        print(f"Error: {e}")


@client.on(events.NewMessage(pattern=r"^/translate\s+(\w+)\s+(.+)"))
async def translate_handler(event):
    match = event.pattern_match
    target_lang = match.group(1)
    text = match.group(2)

    try:
        translated = await translator.translate(text, dest=target_lang)
        await event.reply(f"**Translated ({target_lang}):**\n{translated.text}")
    except Exception as e:
        await event.reply(f"Translation failed: {e}")


# @client.on(events.NewMessage)
async def handler(event):
    try:
        original_text = extract_text_from_message(event.message)
        if original_text.startswith("/"):
            return
        sender_id = event.sender_id
        if sender_id in excluded_users:
            return
        detected_chat_id = event.chat_id
        # print(f"[{detected_chat_id}][{sender_id}] {event.message.message=}")

        detected_language = detect_language(original_text)
        if detected_language != destination_language:
            translated_text = await translator.translate(
                original_text, dest=destination_language
            )
            await event.reply(
                f"🔄 *Translated from '{detected_language}':*\n{translated_text.text}",
                parse_mode="markdown",
            )

    except Exception as e:
        print(f"Error: {e}")


async def main():
    # await send_intro_message()
    # print("Bot started successfully!")
    options = {"incoming": True, "pattern": r"^(?!/).*"}
    if from_users:
        options["from_users"] = from_users
    if group_id:
        options["chats"] = group_id
    client.add_event_handler(handler, events.NewMessage(**options))
    await client.run_until_disconnected()  # Keep bot running


if __name__ == "__main__":
    try:
        with client:
            client.loop.run_until_complete(main())
    except KeyboardInterrupt:
        client.disconnect()
