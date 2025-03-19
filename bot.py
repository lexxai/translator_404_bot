from telethon import TelegramClient, events
from googletrans import Translator
from langdetect import detect

# Your API credentials (Get from https://my.telegram.org)
api_id = "YOUR_API_ID"
api_hash = "YOUR_API_HASH"
bot_token = "YOUR_BOT_TOKEN"
group_id = -100
XXXXXXXXXX  # Replace with your group chat ID

translator = Translator()
client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)


@client.on(events.NewMessage(chats=group_id))
async def handler(event):
    original_text = event.message.message

    try:
        detected_language = detect(original_text)

        if detected_language != 'en':  # Change 'en' to your preferred language
            translated_text = translator.translate(original_text, dest='en').text
            await event.reply(f"🔄 *Translated:* {translated_text}", parse_mode="Markdown")

    except Exception as e:
        print(f"Error: {e}")


client.run_until_disconnected()
