import logging
import json
import signal
from os import path
from datetime import date, timedelta

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
        telebot.types.BotCommand("newalfredo", "<iso-date>: Umfrage für neuen Alfredotermin posten"),
        telebot.types.BotCommand("reminder", ": Erinnerung für den morgigen Termin posten"),
        telebot.types.BotCommand("cancel", "<iso-date>: Alfredotermin absagen"),
        telebot.types.BotCommand("announce", "<announcement>: Ankündigung in der Gruppe posten")
    ]

    def __init__(self, cfgfile, bot_invoker, dbfile, tmpdir):
        self.log = logging.getLogger("BotRunner")

        self.tmpdir = tmpdir

        self.init_config(cfgfile)
        self.init_bot(bot_invoker)
        self.init_database(dbfile)
        self.register_signal_handlers()

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
        self.bot.register_message_handler(self.acmd_reminder, commands=['reminder'])
        self.bot.register_message_handler(self.acmd_cancel, commands=['cancel'])
        self.bot.register_message_handler(self.acmd_announce, commands=['announce'])

    def init_database(self, dbfile):
        self.log.info("initializing database")
        self.db = Database(dbfile)

    def register_signal_handlers(self):
        self.log.info("registering signal handlers")
        signal.signal(signal.SIGUSR1, self.signal_usr1)

    def log_command(self, message, admincmd=False):
        role = "admin" if self.user_is_admin(message.from_user) else "user"
        if admincmd:
            self.log.info(f"{role} {util.format_user(message.from_user)} sent admin command '{message.text}'")
        else:
            self.log.debug(f"{role} {util.format_user(message.from_user)} sent command '{message.text}'")

    def send_error(self, reply_to, errmsg):
        self.log.info(f"sending error reply message to {util.format_user(reply_to.from_user)}: '{errmsg}'")
        self.safe_exec(
            self.bot.reply_to,
            message=reply_to,
            text=util.failure(f"Fehler: {errmsg}")
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

    @util.admin_command_check()
    def acmd_new_alfredo(self, message):
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

        if self.db.get_by_date(date_) is not None:
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
                is_anonymous=False
            )
        except Exception as ex:
            self.send_error(message, f"Telegram API meldete einen Fehler: {ex}")
            return

        self.db.create_alfredo_date(date_, description, poll.message_id)

        self.do_pinning()

        self.safe_exec(self.bot.reply_to, message=message, text=util.success("Umfrage wurde erstellt"))

    @util.admin_command_check()
    def acmd_reminder(self, message):
        sent = self.reminder_internal(message)

        if sent:
            self.safe_exec(self.bot.reply_to, message=message, text=util.success("Erinnerung gesendet"))

    @util.admin_command_check()
    def acmd_cancel(self, message):  # noqa: C901
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
            self.send_error(message, "Man kann nur Termine in der Zukunft absagen")
            return

        row = self.db.get_by_date(date_)
        if row is None:
            msg = f"An diesem Termin ist kein Alfredo eingetragen ({util.format_date(date_)})"
            self.send_error(message, msg)
            return

        msg = ""
        try:
            text = f"Der Alfredo am {util.format_date(row.date)} wurde leider abgesagt {util.emoji('frowning')}"
            self.safe_exec(
                self.bot.send_message,
                reraise=True,
                chat_id=self.config["group"],
                text=text,
                reply_to_message_id=row.message_id
            )
            msg += util.li(util.success("Absage gesendet"))
        except Exception as ex:
            msg += util.li(util.failure(f"Absage gesendet ({ex})"))

        try:
            self.safe_exec(
                self.bot.stop_poll,
                reraise=True,
                chat_id=self.config["group"],
                message_id=row.message_id
            )
            msg += util.li(util.success("Umfrage gestoppt"))
        except Exception as ex:
            msg += util.li(util.failure(f"Umfrage gestoppt ({ex})"))

        self.db.delete_date(row)
        msg += util.li(util.success("Aus Datenbank entfernt"))

        self.do_pinning()

        self.safe_exec(self.bot.reply_to, message=message, text=msg)

    @util.admin_command_check()
    def acmd_announce(self, message):
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

        self.safe_exec(self.bot.reply_to, message=message, text=util.success("Ankündigung gesendet"))

    def signal_usr1(self, signum, frame):
        self.log.debug(f"Received signal {signum}, triggering reminder and cleanup functions")

        sent = self.reminder_internal()
        if sent:
            self.log.info("Sent reminder for tomorrow")

        # logging inside
        self.do_pinning()

    def reminder_internal(self, message=None):
        tomorrow = date.today() + timedelta(days=1)

        row = self.db.get_by_date(tomorrow)
        if row is None:
            if message is not None:
                msg = f"Für den morgigen Tag ist kein Alfredo angekündigt ({util.format_date(tomorrow)})"
                self.send_error(message, msg)
            return False

        try:
            text = f"Attenzione!\n\n{util.get_reminder()}"
            self.safe_exec(
                self.bot.send_message,
                reraise=True,
                chat_id=self.config["group"],
                text=text,
                reply_to_message_id=row.message_id
            )
        except Exception as ex:
            if message is not None:
                self.send_error(message, f"Telegram API meldete einen Fehler: ({ex})")
            else:
                self.log.error(f"Telegram API error when sending reminder for tomorrow: ({ex})")
            return False

        return True

    def do_pinning(self):
        dates = self.db.get_future_dates()

        chat = self.safe_exec(
            self.bot.get_chat,
            reraise=False,
            chat_id=self.config["group"]
        )

        if chat is None:
            self.log.error("Pinning: could not get chat info")
            return

        unpin = False

        if len(dates) > 0:
            next_alf = dates[0]

            # unpin (last) old message if necessary
            # as get_chat only returns the last pinned message, this assumes
            # that there will always only be one pinned message at a time
            if chat.pinned_message is not None and chat.pinned_message.message_id != next_alf.message_id:
                unpin = True

            if chat.pinned_message is None or chat.pinned_message.message_id != next_alf.message_id:
                self.log.info(f"pinning message for alfredo {next_alf.date}")
                self.safe_exec(
                    self.bot.pin_chat_message,
                    reraise=False,
                    chat_id=self.config["group"],
                    message_id=dates[0].message_id,
                    disable_notification=True
                )
        # no new dates, unpin old message
        elif chat.pinned_message is not None:
            unpin = True

        if unpin:
            self.log.info(f"unpinning message {chat.pinned_message.message_id}")
            self.safe_exec(
                self.bot.unpin_chat_message,
                reraise=False,
                chat_id=self.config["group"],
                message_id=chat.pinned_message.message_id
            )

    def run(self):
        self.log.info("bot starts polling now")
        self.bot.infinity_polling()
