#!/usr/bin/env python

import logging
import json
from os import path
from sys import exit
from datetime import date

from database import Database

import babel.dates
import telebot


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

config = None
bot = None
db = None

emojis = {
    "check": u'\U00002713',
    "cross": u'\U0000274C'
}


def load_config():
    if not path.exists("config.json"):
        logger.error("config.json does not exist")
        exit(1)

    with open("config.json") as c:
        cfg = json.load(c)

    for req in ["token", "group", "admins"]:
        if req not in cfg.keys():
            logger.error(f"config key {req} not found in config.json")
            exit(1)

    if not len(cfg["admins"]) > 0:
        logger.error("need at least one admin")
        exit(1)

    return cfg


def send_error(reply_to, errmsg):
    logger.error(f"sending error reply message: '{errmsg}'")
    bot.reply_to(reply_to, f"{emojis['cross']} error: {errmsg}")


def is_admin(user):
    return user.id in config["admins"]


if __name__ == "__main__":
    config = load_config()
    bot = telebot.TeleBot(config["token"])
    db = Database("alfredo.sqlite")

    @bot.message_handler(commands=['help', 'start'])
    def send_welcome(message):
        bot.reply_to(message, "Hello.")

    @bot.message_handler(commands=['newalfredo'])
    def new_alfredo(message):
        logger.debug(message)

        if not is_admin(message.from_user):
            send_error(message, "You are not an admin.")
            return

        params = message.text.split(" ")

        if len(params) != 2:
            send_error(message, f"Invalid number of parameters, expected 1, got {len(params) - 1}")
            return

        try:
            date_ = date.fromisoformat(params[1])
        except ValueError as verr:
            send_error(message, f"Date string could not be parsed: {verr}")
            return

        # todo: check if in the future
        today = date.today()

        if date_ <= today:
            send_error(message, "Date must be in the future")
            return

        description = f"Alfredo am {babel.dates.format_date(date_, format='full', locale='de_DE')} (18:00 Uhr)"

        try:
            poll = bot.send_poll(
                chat_id=config["group"],
                question=description,
                options=["Teilnahme", "Teilnahme (+1 Gast)", "Absage"],
                is_anonymous=False,
            )
        except Exception as ex:
            send_error(message, f"Telegram API returned an error: {ex}")
            return

        db.create_alfredo_date(date_, description, poll.message_id)

        bot.reply_to(message, f"Poll was created {emojis['check']}")

    bot.infinity_polling()
