# translator_404_bot
Telegram bot for translating messages in chats with text in another language (404)


### Installation

#### Install Python
```
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
```
python bot.py
```

### Commands of the bot

- help - Help with commands
- translate - Translate: lang text
- chat_id  - Show chat_id of group
- exclude - Exclude current user from automatically translates
- include - Include current user for automatically translates
- check - Check if included current user for automatically translates

