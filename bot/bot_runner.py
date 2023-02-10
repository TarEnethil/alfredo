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
        telebot.types.BotCommand("newalfredo", "<iso-date> Umfrage für neuen Alfredotermin posten"),
        telebot.types.BotCommand("announce", "<announcement> Ankündigung in der Gruppe posten")
    ]

    def __init__(self, cfgfile, bot_invoker, dbfile):
        self.log = logging.getLogger("BotRunner")

        self.init_config(cfgfile)
        self.init_bot(bot_invoker)
        self.init_database(dbfile)

    def init_config(self, cfgfile):
        self.log.info(f"loading config from {cfgfile}")
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
        self.log.info("creating bot")
        self.bot = invoker(self.config["token"])

        self.log.debug("setting bot commands")
        self.bot.set_my_commands(self.default_commands)

        self.log.debug("registering bot message handlers")
        self.bot.register_message_handler(self.cmd_start, commands=['start'])
        self.bot.register_message_handler(self.cmd_help, commands=['help'])
        self.bot.register_message_handler(self.cmd_menu, commands=['karte'])
        self.bot.register_message_handler(self.cmd_show_dates, commands=["termine"])

        self.bot.register_message_handler(self.acmd_new_alfredo, commands=['newalfredo'])
        self.bot.register_message_handler(self.acmd_announce, commands=['announce'])

    def init_database(self, dbfile):
        self.log.info("initializing database")
        self.db = Database(dbfile)

    def log_command(self, message, admin=False):
        role = "admin" if self.user_is_admin(message.from_user) else "user"
        if admin:
            self.log.info(f"{role} {util.format_user(message.from_user)} sent admin command '{message.text}'")
        else:
            self.log.debug(f"{role} {util.format_user(message.from_user)} sent command '{message.text}'")

    def send_error(self, reply_to, errmsg):
        self.log.info(f"sending error reply message to {util.format_user(reply_to.from_user)}: '{errmsg}'")
        self.safe_exec(
            self.bot.reply_to,
            message=reply_to,
            text=f"{util.emoji('cross')} Fehler: {errmsg}"
        )

    def user_is_admin(self, user):
        return user.id in self.config["admins"]

    def safe_exec(self, func, reraise=False, **kwargs):
        self.log.debug(f"safe_exec for {func.__name__}")

        try:
            return func(**kwargs)
        except Exception as ex:
            self.log.error(f"Telegram API Exception: {ex}")

            if reraise:
                raise ex

    def cmd_start(self, message):
        self.log_command(message)

        msg = "Mamma Mia!\n\n"
        msg += "Der AlfredoBot versorgt dich mit allen Informationen rund um die beste Pizza der Welt.\n\n"
        msg += util.li("Verfügbare Kommandos: siehe /help")
        msg += util.li("Maintainer: @TriviaThorsten")
        msg += util.li(f"Version: {util.get_version()}")
        msg += util.li("Bugreports: https://github.com/TarEnethil/alfredo/issues")

        if self.user_is_admin(message.from_user) and message.chat.type == "private":
            msg += "\n\nDu bist ein Admin!"

        self.safe_exec(self.bot.reply_to, message=message, text=msg, disable_web_page_preview=True)

    def cmd_help(self, message):
        self.log_command(message)

        msg = "Verfügbare Kommandos:\n"

        for cmd in self.default_commands:
            msg += util.li(f"/{cmd.command}: {cmd.description}")

        if self.user_is_admin(message.from_user) and message.chat.type == "private":
            msg += "\nAdminkommandos:\n"
            for cmd in self.admin_commands:
                msg += util.li(f"/{cmd.command} {cmd.description}")

        self.safe_exec(self.bot.reply_to, message=message, text=msg)

    def cmd_menu(self, message):
        self.log_command(message)

        url = "https://github.com/TarEnethil/alfredo/releases/latest/download/menu.pdf"

        msg = f"Link zur aktuellen Karte: [Link]({url})"
        self.safe_exec(
           self.bot.reply_to,
           message=message,
           text=msg,
           disable_web_page_preview=True,
           parse_mode="MarkdownV2"
        )

    def cmd_show_dates(self, message):
        self.log_command(message)

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

        self.safe_exec(self.bot.reply_to, message=message, text=msg)

    def acmd_new_alfredo(self, message):
        if not self.user_is_admin(message.from_user):
            self.log_command(message)
            self.send_error(message, "Du bist kein Admin.")
            return

        self.log_command(message, admin=True)

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
            poll = self.safe_exec(
                self.bot.send_poll,
                reraise=True,
                chat_id=self.config["group"],
                question=description,
                options=["Teilnahme", "Teilnahme (+1 Gast)", "Absage"],
                is_anonymous=False,
            )
        except Exception as ex:
            self.send_error(message, f"Telegram API meldete einen Fehler: {ex}")
            return

        self.db.create_alfredo_date(date_, description, poll.message_id)

        self.safe_exec(self.bot.reply_to, message=message, text=f"Umfrage wurde erstellt {util.emoji('check')}")

    def acmd_announce(self, message):
        if not self.user_is_admin(message.from_user):
            self.log_command(message)
            self.send_error(message, "Du bist kein Admin.")
            return

        self.log_command(message, admin=True)

        params = message.text.strip().split(" ")

        if len(params) < 2:
            self.send_error(message, "Befehl benötigt Parameter")
            return

        announcement = f"{util.emoji('megaphone')} {' '.join(params[1:])}"

        try:
            self.safe_exec(
                self.bot.send_message,
                reraise=True,
                chat_id=self.config["group"],
                text=announcement,
                disable_web_page_preview=True
            )
        except Exception as ex:
            self.send_error(message, f"Telegram API meldete einen Fehler: {ex}")
            return

        self.safe_exec(self.bot.reply_to, message=message, text=f"Ankündigung wurde gesendet {util.emoji('check')}")

    def run(self):
        self.log.info("bot starts polling now")
        self.bot.infinity_polling()
