#!/usr/bin/env python

import logging
from bot_runner import BotRunner

from telebot import TeleBot


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    runner = BotRunner("config.json", TeleBot, "alfredo.sqlite")
    runner.run()
