# translator_404_bot
Telegram bot for translating messages in chats with text in another language (404)


### Installation

#### Install Python
```bash
pyton -m venv .venv
source .venv/bin/activate or .venv/Scripts/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

#### Add the Bot to the Group
 Add the bot to your group chat.
 Give it admin permissions (at least to read messages) if group is private.


#### # Your API credentials (Get from https://my.telegram.org)
Fill variables in the '.env' file by use example template 'dot_env' file.


### Run the Script
```bash
python bot.py
```

### Docker
Build and Run
```bash
cd scripts/
chmod +x *.sh
./docker_build.sh
./docker_run.sh
```

### Docker Compose
- Start:
```bash
docker compose up --build -d
```
- Stop:
```bash
docker compose down
```

### Commands of the bot

- help - Help with commands
- translate - Translate: lang text
- chat_id  - Show chat_id of group
- exclude - Exclude current user from automatically translates
- include - Include current user for automatically translates
- check - Check if included current user for automatically translates


### .env

```dotenv
API_ID="YOUR_API_ID"
API_HASH="YOUR_API_HASH"
BOT_TOKEN="YOUR_BOT_TOKEN"
FROM_USERS="@USERNAME1"
GROUPS_ID=XXXXXXXXX,YYYYYYYYY
DESTINATION_LANGUAGE=uk
EXCLUDED_LANGUAGES=""
STORAGE_PATH="storage"
USE_IPV6=False
USE_INTRO_MESSAGE=False
TRUST_TELEGRAM_LANGUAGES=True
```
- DESTINATION_LANGUAGE - Language to translate all messages to.
- EXCLUDED_LANGUAGES - Additional languages (comma separated) that should not be translated.
- GROUPS_ID - List of groups (comma separated) to limit bot to, if empty then all groups can use this bot.
- FROM_USERS - List of users (comma separated) to limit bot to.
- USE_INTRO_MESSAGE - Send intro message to all groups in list.
- TRUST_TELEGRAM_LANGUAGES - Use Telegram language settings.