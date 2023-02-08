#!/usr/bin/env python

import logging
import json
from os import path
from sys import exit
from datetime import date

import util

from database import Database

import telebot


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

config = None
bot = None
db = None


default_commands = [
    telebot.types.BotCommand("termine", "Zeigt die nächsten Alfredotermine"),
    telebot.types.BotCommand("karte", "Verlinkt die Alfredokarte"),
    telebot.types.BotCommand("start", "Zeigt die Willkommensnachricht an"),
    telebot.types.BotCommand("help", "Zeigt die verfügbaren Kommandos")
]


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
    bot.reply_to(reply_to, f"{util.emoji('cross')} error: {errmsg}")


def is_admin(user):
    return user.id in config["admins"]


if __name__ == "__main__":  # noqa: C901
    config = load_config()
    bot = telebot.TeleBot(config["token"])
    db = Database("alfredo.sqlite")

    bot.set_my_commands(default_commands)

    @bot.message_handler(commands=['start'])
    def start(message):
        msg = "Mamma-mia!\n\n"
        msg += util.li("Verfügbare Kommandos: siehe /help")
        msg += util.li("Maintainer: @TriviaThorsten")
        msg += util.li(f"Version: {util.get_version()}")
        msg += util.li("Bugreports: https://github.com/TarEnethil/alfredo/issues")

        bot.reply_to(message, msg, disable_web_page_preview=True)

    @bot.message_handler(commands=['help'])
    def help(message):
        msg = "Mamma-mia!\n\n"
        msg += "Verfügbare Kommandos:\n"

        for cmd in default_commands:
            msg += util.li(f"/{cmd.command}: {cmd.description}")

        if is_admin(message.from_user):
            msg += "\nAdminkommandos:\n"
            msg += util.li("/newalfredo 20xx-yy-zz")

        bot.reply_to(message, msg)

    @bot.message_handler(commands=['karte'])
    def menu(message):
        url = "https://github.com/TarEnethil/alfredo/releases/latest/download/menu.pdf"

        msg = f"Link zur aktuellen Karte: [Link]({url})"
        bot.reply_to(message, msg, disable_web_page_preview=True, parse_mode="MarkdownV2")

    @bot.message_handler(commands=["termine"])
    def show_dates(message):
        dates = db.get_future_dates()
        num = len(dates)

        if num == 0:
            msg = f"Es wurden keine weiteren Termine angekündigt {util.emoji('frowning')}"
        elif num == 1:
            msg = f"Der (einzige) nächste Termin ist am {util.format_date(dates[0].date)}."
        else:
            msg = f"Die nächsten {len(dates)} Termine:\n\n"

            for date_ in dates:
                msg += f"{util.emoji('bullet')} {util.format_date(date_.date)}\n"

        bot.reply_to(message, msg)

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

        today = date.today()

        if date_ <= today:
            send_error(message, "Date must be in the future")
            return

        if db.check_date_is_free(date_) is False:
            send_error(message, f"There is already an Alfredo on this date ({util.format_date(date_)})")
            return

        description = f"Alfredo am {util.format_date(date_)} (18:00 Uhr)"

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

        bot.reply_to(message, f"Poll was created {util.emoji('check')}")

    bot.infinity_polling()
