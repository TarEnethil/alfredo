# Setup
```bash
git clone https://github.com/TarEnethil/alfredo.git
cd alfredo/bot
python3 -m venv venv
venv/bin/activate
pip install -r requirements.txt
cp config.json.template config.json
```

# Config & Bot Setup
* Create Telegram bot (@BotFather) to get API Key ("token") -> config value "token"
* Invite bot to your group and get the "chat_id" from `https://api.telegram.org/bot<TOKEN>/getUpdates` -> config value "group" (negative ID as string)
* Write one message to your bot and get your "chat_id" from `https://api.telegram.org/bot<TOKEN>/getUpdates` -> config value "admins" (list of integers)

# Run Bot
* `./bot.py`

# Autoreminder
* send SIGUSR1 to automatically send a reminder for tomorrow's date (if it exists)

# Dev
* Lint: `flake8 .`
* Tests: `./run_tests.sh`
* Coverage: `./coverage.sh <html|report>`

# TODO
* Add comments
* Add .ics