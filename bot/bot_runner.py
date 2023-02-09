import logging
import json
from os import path
from datetime import date

import util

from database import Database

import telebot


class BotRunner:
    default_commands = [
        telebot.types.BotCommand("termine", "Zeigt die nächsten Alfredotermine"),
        telebot.types.BotCommand("karte", "Verlinkt die Alfredokarte"),
        telebot.types.BotCommand("start", "Zeigt die Willkommensnachricht an"),
        telebot.types.BotCommand("help", "Zeigt die verfügbaren Kommandos")
    ]

    admin_commands = [
        telebot.types.BotCommand("newalfredo", "<iso-date> Umfrage für neuen Alfredotermin starten"),
        telebot.types.BotCommand("announce", "<announcement> Ankündigung in der Gruppe posten")
    ]

    def __init__(self, cfgfile, bot_invoker, dbfile):
        self.log = logging.getLogger("BotRunner")

        self.init_config(cfgfile)
        self.init_bot(bot_invoker)
        self.init_database(dbfile)

    def init_config(self, cfgfile):
        if not path.exists(cfgfile):
            raise Exception(f"{cfgfile} does not exist")

        with open(cfgfile) as c:
            cfg = json.load(c)

        for req in ["token", "group", "admins"]:
            if req not in cfg.keys():
                raise Exception(f"config key {req} not found in {cfgfile}")

        if not len(cfg["admins"]) > 0:
            raise Exception("need at least one admin")

        self.config = cfg

    def init_bot(self, invoker):
        self.bot = invoker(self.config["token"])
        self.bot.set_my_commands(self.default_commands)

        self.bot.register_message_handler(self.cmd_start, commands=['start'])
        self.bot.register_message_handler(self.cmd_help, commands=['help'])
        self.bot.register_message_handler(self.cmd_menu, commands=['karte'])
        self.bot.register_message_handler(self.cmd_show_dates, commands=["termine"])

        self.bot.register_message_handler(self.acmd_new_alfredo, commands=['newalfredo'])
        self.bot.register_message_handler(self.acmd_announce, commands=['announce'])

    def init_database(self, dbfile):
        self.db = Database(dbfile)

    def send_error(self, reply_to, errmsg):
        self.log.info(f"sending error reply message: '{errmsg}'")
        self.bot.reply_to(reply_to, f"{util.emoji('cross')} Fehler: {errmsg}")

    def user_is_admin(self, user):
        return user.id in self.config["admins"]

    def cmd_start(self, message):
        msg = "Mamma-mia!\n\n"
        msg += util.li("Verfügbare Kommandos: siehe /help")
        msg += util.li("Maintainer: @TriviaThorsten")
        msg += util.li(f"Version: {util.get_version()}")
        msg += util.li("Bugreports: https://github.com/TarEnethil/alfredo/issues")

        self.bot.reply_to(message, msg, disable_web_page_preview=True)

    def cmd_help(self, message):
        msg = "Mamma-mia!\n\n"
        msg += "Verfügbare Kommandos:\n"

        for cmd in self.default_commands:
            msg += util.li(f"/{cmd.command}: {cmd.description}")

        if self.user_is_admin(message.from_user) and message.chat.type == "private":
            msg += "\nAdminkommandos:\n"
            for cmd in self.admin_commands:
                msg += util.li(f"/{cmd.command} {cmd.description}")

        self.bot.reply_to(message, msg)

    def cmd_menu(self, message):
        url = "https://github.com/TarEnethil/alfredo/releases/latest/download/menu.pdf"

        msg = f"Link zur aktuellen Karte: [Link]({url})"
        self.bot.reply_to(message, msg, disable_web_page_preview=True, parse_mode="MarkdownV2")

    def cmd_show_dates(self, message):
        dates = self.db.get_future_dates()
        num = len(dates)

        if num == 0:
            msg = f"Es wurden keine weiteren Termine angekündigt {util.emoji('frowning')}"
        elif num == 1:
            msg = f"Der (einzige) nächste Termin ist am {util.format_date(dates[0].date)}."
        else:
            msg = f"Die nächsten {len(dates)} Termine:\n\n"

            for date_ in dates:
                msg += f"{util.emoji('bullet')} {util.format_date(date_.date)}\n"

        self.bot.reply_to(message, msg)

    def acmd_new_alfredo(self, message):
        if not self.user_is_admin(message.from_user):
            self.send_error(message, "Du bist kein Admin.")
            return

        params = message.text.strip().split(" ")

        if len(params) != 2:
            self.send_error(message, f"Befehl erwartet nur einen Parameter, geparsed wurden {len(params) - 1}")
            return

        try:
            date_ = date.fromisoformat(params[1])
        except ValueError as verr:
            self.send_error(message, f"String konnte nicht in ein Datum konvertiert werden: {verr}")
            return

        today = date.today()

        if date_ <= today:
            self.send_error(message, "Datum darf frühstens heute sein.")
            return

        if self.db.check_date_is_free(date_) is False:
            msg = f"An diesem Termin ist bereits ein Alfredo eingetragen ({util.format_date(date_)})"
            self.send_error(message, msg)
            return

        description = f"Alfredo am {util.format_date(date_)} (18:00 Uhr)"

        try:
            poll = self.bot.send_poll(
                chat_id=self.config["group"],
                question=description,
                options=["Teilnahme", "Teilnahme (+1 Gast)", "Absage"],
                is_anonymous=False,
            )
        except Exception as ex:
            self.send_error(message, f"Telegram API meldete einen Fehler: {ex}")
            return

        self.db.create_alfredo_date(date_, description, poll.message_id)

        self.bot.reply_to(message, f"Umfrage wurde erstellt {util.emoji('check')}")

    def acmd_announce(self, message):
        if not self.user_is_admin(message.from_user):
            self.send_error(message, "Du bist kein Admin.")
            return

        params = message.text.strip().split(" ")

        if len(params) < 2:
            self.send_error(message, "Befehl benötigt Parameter")
            return

        announcement = f"{util.emoji('megaphone')} {' '.join(params[1:])}"

        self.bot.send_message(
            chat_id=self.config["group"],
            text=announcement,
            disable_web_page_preview=True
        )

    def run(self):
        self.bot.infinity_polling()
