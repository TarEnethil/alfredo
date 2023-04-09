import logging
from datetime import date, timedelta
import json
from fake import FakeBot, FakeUser, FakeMessage, FakeCallbackObject
from bot_runner import BotRunner
import util
import signal
from ics import Calendar

import pytest

ADMIN1 = FakeUser(42, "Armin", "DerAdmin")
ADMIN2 = FakeUser(69, "Bernhard", "b0ss")
USER = FakeUser(1337, "Dagobert", "DAU")
GROUP = "-1337"
TESTCFG = "tests/config-test.json"
DEFAULT_MESSAGE = FakeMessage(USER)


def defaultRunner(tmp_path=None):
    return BotRunner(TESTCFG, FakeBot, ":memory:", tmp_path)


def assert_num_dates(db, num):
    from models import AlfredoDate
    from sqlalchemy import select, func
    from sqlalchemy.orm import Session

    with Session(db.engine) as session:
        dates = session.scalars(select(func.count()).select_from(AlfredoDate)).first()

    assert dates == num


class TestBotRunner:
    def test_basic(self, tmp_path):
        runner = defaultRunner(tmp_path)

        # check that a handler for every command was registered
        assert len(runner.bot.handlers.keys()) == len(runner.default_commands) + len(runner.admin_commands)
        assert len(runner.bot.callback_handlers) == len(runner.callbacks)
        assert runner.bot.token == "abcdefghijklmnopqrstuvwxyz"
        assert runner.tmpdir == tmp_path

    def test_config_errors(self, tmp_path):
        tmp_cfg = tmp_path / "tmp.json"

        # case 1: config file does not exist
        with pytest.raises(Exception) as ex:
            BotRunner("does-not-exist.json", None, None, None)

        assert "does not exist" in ex.value.args[0]

        # case 2: missing key
        for k in ["token", "group", "admins"]:
            with open(TESTCFG) as c:
                cfg = json.load(c)

            del cfg[k]

            with open(tmp_cfg, "w") as out:
                json.dump(cfg, out)

            with pytest.raises(Exception) as ex:
                BotRunner(tmp_cfg, None, None, None)

            assert f"config key {k} not found" in ex.value.args[0]

        # case 3: no admins
        with open(TESTCFG) as c:
            cfg = json.load(c)

        cfg["admins"] = []

        with open(tmp_cfg, "w") as out:
            json.dump(cfg, out)

        with pytest.raises(Exception) as ex:
            BotRunner(tmp_cfg, None, None, None)

        assert "at least one admin" in ex.value.args[0]

    def test_log_command(self, caplog):
        runner = defaultRunner()

        with caplog.at_level(logging.DEBUG):
            runner.log_command(FakeMessage(USER, text="/command"))
            assert "/command" in caplog.text
            assert str(USER.id) in caplog.text
            assert USER.first_name in caplog.text
            assert USER.username in caplog.text

            caplog.clear()

            runner.log_command(FakeMessage(ADMIN1, text="/command"))
            assert "admin" in caplog.text
            assert "/command" in caplog.text
            assert str(ADMIN1.id) in caplog.text
            assert ADMIN1.first_name in caplog.text

            caplog.clear()

        with caplog.at_level(logging.INFO):
            runner.log_command(FakeMessage(USER, text="/command"))
            assert "/command" not in caplog.text
            assert str(USER.id) not in caplog.text
            assert USER.first_name not in caplog.text
            assert USER.username not in caplog.text

            caplog.clear()

            runner.log_command(FakeMessage(ADMIN1, text="/acommand"), admincmd=True)
            assert "admin" in caplog.text
            assert "/acommand" in caplog.text
            assert str(ADMIN1.id) in caplog.text
            assert ADMIN1.first_name in caplog.text

    def test_send_error(self):
        runner = defaultRunner()
        msg = DEFAULT_MESSAGE

        runner.send_error(msg, "Test")

        error = runner.bot.last_reply_text
        assert "Fehler" in error
        assert "Test" in error

    def test_user_is_admin(self):
        runner = defaultRunner()

        assert runner.user_is_admin(ADMIN1)
        assert runner.user_is_admin(ADMIN2)
        assert runner.user_is_admin(USER) is False

    def test_safe_exec(self):
        runner = defaultRunner()

        def no_raise(arg):
            assert arg == "test"
            return True

        def raise_(arg):
            assert arg == "test"
            raise Exception("Fake Test Exception")

        assert runner.safe_exec(no_raise, arg="test")
        assert runner.safe_exec(no_raise, reraise=False, arg="test")

        with pytest.raises(Exception):
            runner.safe_exec(raise_, reraise=True, arg="test")

    def test_cmds_with_execption(self):
        runner = defaultRunner()

        tomorrow = date.today() + timedelta(days=1)

        # collection of goodcases
        cmds = {
            "start": FakeMessage(USER, "channel"),
            "help": FakeMessage(USER, "channel"),
            "karte": DEFAULT_MESSAGE,
            "termine": DEFAULT_MESSAGE,
            "newalfredo": FakeMessage(ADMIN1, text=f"newalfredo {tomorrow.isoformat()}"),
            "reminder": FakeMessage(ADMIN1, text="reminder"),
            "announce": FakeMessage(ADMIN1, text="announce Test Test Test"),
            "cancel": FakeMessage(ADMIN1, text=f"cancel {tomorrow.isoformat()}")
        }

        assert len(cmds) == len(runner.default_commands) + len(runner.admin_commands)

        for cmd, msg in cmds.items():
            runner.bot.raise_on_next_action()
            runner.bot.handle_command(cmd, msg)

    def test_cmd_start(self):
        COMMAND = "start"
        runner = defaultRunner()

        no_admin_output = []
        admin_output = []

        # not an admin, public chat
        runner.bot.handle_command(COMMAND, FakeMessage(USER, "channel"))
        no_admin_output.append(runner.bot.last_reply_text)

        # not an admin, private chat
        runner.bot.handle_command(COMMAND, FakeMessage(USER, "private"))
        no_admin_output.append(runner.bot.last_reply_text)

        # admin, public chat
        runner.bot.handle_command(COMMAND, FakeMessage(ADMIN1, "channel"))
        no_admin_output.append(runner.bot.last_reply_text)

        # admin, public chat
        runner.bot.handle_command(COMMAND, FakeMessage(ADMIN1, "private"))
        admin_output.append(runner.bot.last_reply_text)

        for msg in no_admin_output + admin_output:
            for cmd in runner.default_commands:
                assert "/help" in msg
                assert "Maintainer" in msg
                assert "Version" in msg
                assert "github" in msg

        for msg in no_admin_output:
            assert "Admin" not in msg

        for msg in admin_output:
            assert "Admin" in msg

    def test_cmd_help(self):
        COMMAND = "help"
        runner = defaultRunner()

        no_admin_output = []
        admin_output = []

        # not an admin, public chat
        runner.bot.handle_command(COMMAND, FakeMessage(USER, "channel"))
        no_admin_output.append(runner.bot.last_reply_text)

        # not an admin, private chat
        runner.bot.handle_command(COMMAND, FakeMessage(USER, "private"))
        no_admin_output.append(runner.bot.last_reply_text)

        # admin, public chat
        runner.bot.handle_command(COMMAND, FakeMessage(ADMIN1, "channel"))
        no_admin_output.append(runner.bot.last_reply_text)

        # admin, public chat
        runner.bot.handle_command(COMMAND, FakeMessage(ADMIN1, "private"))
        admin_output.append(runner.bot.last_reply_text)

        for msg in no_admin_output + admin_output:
            for cmd in runner.default_commands:
                assert f"/{cmd.command}" in msg

        for msg in no_admin_output:
            assert "Adminkommandos" not in msg

        for msg in admin_output:
            assert "Adminkommandos" in msg

    def test_cmd_menu(self):
        COMMAND = "karte"
        runner = defaultRunner()

        # goodcase
        runner.bot.handle_command(COMMAND, DEFAULT_MESSAGE)
        msg = runner.bot.last_reply_text

        assert "github" in msg
        assert "menu.pdf" in msg

    def test_cmd_show_dates(self):
        COMMAND = "termine"
        runner = defaultRunner()

        runner.bot.handle_command(COMMAND, DEFAULT_MESSAGE)
        msg = runner.bot.last_reply_text
        assert "keine" in msg

        one_day = timedelta(days=1)

        today = date.today()
        yesterday = today - one_day
        # add alfredo, but in the past -> no change in output
        runner.db.create_alfredo_date(yesterday, None, 1)

        runner.bot.handle_command(COMMAND, DEFAULT_MESSAGE)
        msg = runner.bot.last_reply_text
        assert "keine" in msg

        runner.db.create_alfredo_date(today, None, 2)
        runner.bot.handle_command(COMMAND, DEFAULT_MESSAGE)
        msg = runner.bot.last_reply_text
        assert "einzige" in msg

        tomorrow = today + one_day
        overmorrow = tomorrow + one_day
        runner.db.create_alfredo_date(tomorrow, None, 3)
        runner.db.create_alfredo_date(overmorrow, None, 4)

        runner.bot.handle_command(COMMAND, DEFAULT_MESSAGE)
        msg = runner.bot.last_reply_text
        assert "nächsten 3 Termine" in msg
        assert msg.count(util.emoji('bullet')) == 3

    def test_acmd_new_alfredo(self):
        COMMAND = "newalfredo"
        runner = defaultRunner()

        # error 1: no admin
        runner.bot.handle_command(COMMAND, FakeMessage(USER, text="newalfredo 2199-01-01"))
        assert_num_dates(runner.db, 0)
        assert "kein Admin" in runner.bot.last_reply_text

        # error 2: no param, too many params
        runner.bot.handle_command(COMMAND, FakeMessage(ADMIN1, text=f"{COMMAND}"))
        assert "einen Parameter" in runner.bot.last_reply_text
        runner.bot.handle_command(COMMAND, FakeMessage(ADMIN1, text=f"{COMMAND} "))
        assert "einen Parameter" in runner.bot.last_reply_text
        runner.bot.handle_command(COMMAND, FakeMessage(ADMIN1, text=f"{COMMAND} 2199-01-01 even more text"))
        assert "einen Parameter" in runner.bot.last_reply_text
        assert_num_dates(runner.db, 0)

        # error 3: invalid date
        runner.bot.handle_command(COMMAND, FakeMessage(ADMIN1, text=f"{COMMAND} not-a-date"))
        assert "konnte nicht in ein Datum" in runner.bot.last_reply_text
        runner.bot.handle_command(COMMAND, FakeMessage(ADMIN1, text=f"{COMMAND} 30-01-01"))
        assert "konnte nicht in ein Datum" in runner.bot.last_reply_text
        assert_num_dates(runner.db, 0)

        # error 4: before today
        one_day = timedelta(days=1)
        today = date.today()
        yesterday = today - one_day

        runner.bot.handle_command(COMMAND, FakeMessage(ADMIN1, text=f"{COMMAND} 2022-01-01"))
        assert "frühstens heute" in runner.bot.last_reply_text
        runner.bot.handle_command(COMMAND, FakeMessage(ADMIN1, text=f"{COMMAND} {yesterday.isoformat()}"))
        assert "frühstens heute" in runner.bot.last_reply_text
        assert_num_dates(runner.db, 0)

        # error 5: telegram exception
        runner.bot.raise_on_next_action()
        runner.bot.handle_command(COMMAND, FakeMessage(ADMIN1, text=f"{COMMAND} 2199-01-01"))
        assert "Telegram API" in runner.bot.last_reply_text
        assert_num_dates(runner.db, 0)

        # goodcase
        runner.bot.handle_command(COMMAND, FakeMessage(ADMIN1, text=f"{COMMAND} 2199-01-01"))
        assert "Umfrage wurde erstellt" in runner.bot.last_reply_text
        assert util.emoji("check") in runner.bot.last_reply_text
        assert_num_dates(runner.db, 1)
        date_ = runner.db.get_future_dates()[0]
        assert runner.bot.last_poll_chat_id == GROUP
        assert util.format_date(date.fromisoformat("2199-01-01")) in runner.bot.last_poll_text
        assert date_.date == date.fromisoformat("2199-01-01")
        assert date_.message_id == 1
        # automatically pinned pinning
        assert runner.bot.pinned_message_id == date_.message_id

        # error 6: duplicate
        runner.bot.handle_command(COMMAND, FakeMessage(ADMIN1, text=f"{COMMAND} 2199-01-01"))
        assert "bereits ein Alfredo" in runner.bot.last_reply_text
        assert_num_dates(runner.db, 1)

    def test_acmd_reminder(self):
        COMMAND = "reminder"
        runner = defaultRunner()

        # error 1: no admin
        runner.bot.handle_command(COMMAND, FakeMessage(USER, text=COMMAND))
        assert "kein Admin" in runner.bot.last_reply_text

        # error 2: no date tomorrow
        runner.bot.handle_command(COMMAND, FakeMessage(ADMIN1, text=COMMAND))
        assert "morgigen Tag ist kein Alfredo" in runner.bot.last_reply_text

        tomorrow = date.today() + timedelta(days=1)
        runner.bot.handle_command("newalfredo", FakeMessage(ADMIN1, text=f"newalfredo {tomorrow.isoformat()}"))
        assert_num_dates(runner.db, 1)

        # error 3: telegram exception
        runner.bot.raise_on_next_action()
        runner.bot.handle_command(COMMAND, FakeMessage(ADMIN1, text=COMMAND))
        assert runner.bot.last_reply_text.count(util.emoji('cross')) == 1
        assert "Telegram API" in runner.bot.last_reply_text

        # goodcase
        runner.bot.handle_command(COMMAND, FakeMessage(ADMIN1, text=COMMAND))
        assert runner.bot.last_reply_text.count(util.emoji('check')) == 1
        assert runner.bot.last_message_chat_id == GROUP
        assert "Attenzione" in runner.bot.last_message_text

    def test_acmd_cancel(self):
        COMMAND = "cancel"
        runner = defaultRunner()

        runner.bot.handle_command("newalfredo", FakeMessage(ADMIN1, text="newalfredo 2199-01-01"))
        assert_num_dates(runner.db, 1)

        # error 1: no admin
        runner.bot.handle_command(COMMAND, FakeMessage(USER, text="cancel 2199-01-01"))
        assert_num_dates(runner.db, 1)
        assert "kein Admin" in runner.bot.last_reply_text

        # error 2: no param, too many params
        runner.bot.handle_command(COMMAND, FakeMessage(ADMIN1, text=f"{COMMAND}"))
        assert "einen Parameter" in runner.bot.last_reply_text
        runner.bot.handle_command(COMMAND, FakeMessage(ADMIN1, text=f"{COMMAND} "))
        assert "einen Parameter" in runner.bot.last_reply_text
        runner.bot.handle_command(COMMAND, FakeMessage(ADMIN1, text=f"{COMMAND} 2199-01-01 even more text"))
        assert "einen Parameter" in runner.bot.last_reply_text
        assert_num_dates(runner.db, 1)

        # error 3: invalid date
        runner.bot.handle_command(COMMAND, FakeMessage(ADMIN1, text=f"{COMMAND} not-a-date"))
        assert "konnte nicht in ein Datum" in runner.bot.last_reply_text
        runner.bot.handle_command(COMMAND, FakeMessage(ADMIN1, text=f"{COMMAND} 30-01-01"))
        assert "konnte nicht in ein Datum" in runner.bot.last_reply_text
        assert_num_dates(runner.db, 1)

        # error 4: before today
        one_day = timedelta(days=1)
        today = date.today()
        yesterday = today - one_day

        runner.bot.handle_command(COMMAND, FakeMessage(ADMIN1, text=f"{COMMAND} 2022-01-01"))
        assert "in der Zukunft" in runner.bot.last_reply_text
        runner.bot.handle_command(COMMAND, FakeMessage(ADMIN1, text=f"{COMMAND} {yesterday.isoformat()}"))
        assert "in der Zukunft" in runner.bot.last_reply_text
        assert_num_dates(runner.db, 1)

        assert runner.bot.polls[1] is True

        # error 5: telegram exception
        runner.bot.raise_on_next_action(1)
        runner.bot.handle_command(COMMAND, FakeMessage(ADMIN1, text=f"{COMMAND} 2199-01-01"))
        assert runner.bot.last_reply_text.count(util.emoji('cross')) == 1
        assert runner.bot.last_reply_text.count(util.emoji('check')) == 2
        assert runner.bot.polls[1] is False
        assert_num_dates(runner.db, 0)

        # error 5.1: 2 telegram exceptions
        runner.bot.handle_command("newalfredo", FakeMessage(ADMIN1, text="newalfredo 2199-01-01"))
        runner.bot.raise_on_next_action(2)
        runner.bot.handle_command(COMMAND, FakeMessage(ADMIN1, text=f"{COMMAND} 2199-01-01"))
        assert runner.bot.last_reply_text.count(util.emoji('cross')) == 2
        assert runner.bot.last_reply_text.count(util.emoji('check')) == 1
        assert runner.bot.polls[2] is True
        assert_num_dates(runner.db, 0)

        # goodcase
        runner.bot.handle_command("newalfredo", FakeMessage(ADMIN1, text="newalfredo 2199-01-01"))
        assert runner.bot.pinned_message_id == runner.db.get_future_dates()[0].message_id
        runner.bot.handle_command(COMMAND, FakeMessage(ADMIN1, text=f"{COMMAND} 2199-01-01"))
        assert runner.bot.last_reply_text.count(util.emoji('cross')) == 0
        assert runner.bot.last_reply_text.count(util.emoji('check')) == 3
        assert runner.bot.polls[3] is False
        assert_num_dates(runner.db, 0)
        # automatically unpinned
        assert runner.bot.pinned_message_id == 0

    def test_acmd_announce(self):
        COMMAND = "announce"
        runner = defaultRunner()

        # error 1: no admin
        runner.bot.handle_command(COMMAND, FakeMessage(USER, text="announce message"))
        assert "kein Admin" in runner.bot.last_reply_text

        # error 2: no param
        runner.bot.handle_command(COMMAND, FakeMessage(ADMIN1, text=f"{COMMAND}"))
        assert "Parameter" in runner.bot.last_reply_text
        runner.bot.handle_command(COMMAND, FakeMessage(ADMIN1, text=f"{COMMAND} "))
        assert "Parameter" in runner.bot.last_reply_text

        # error 3: telegram exception
        runner.bot.raise_on_next_action()
        runner.bot.handle_command(COMMAND, FakeMessage(ADMIN1, text=f"{COMMAND} Test Test Test"))
        assert "Telegram API" in runner.bot.last_reply_text

        # goodcase
        runner.bot.handle_command(COMMAND, FakeMessage(ADMIN1, text=f"{COMMAND} Test Test Test"))
        assert "Ankündigung gesendet" in runner.bot.last_reply_text
        assert util.emoji("check") in runner.bot.last_reply_text
        assert runner.bot.last_message_chat_id == GROUP
        assert runner.bot.last_message_text.endswith("Test Test Test")
        assert COMMAND not in runner.bot.last_message_text

    def test_callback_ics(self, tmp_path):
        runner = defaultRunner(tmp_path)

        # case 1: invalid callback message (no crash)
        cbo = FakeCallbackObject(USER, "ics", None)
        runner.bot.handle_callback(cbo)

        # case 2: no alfredo for message id (no crash)
        cbo = FakeCallbackObject(USER, "ics", FakeMessage(message_id=1337))
        runner.bot.handle_callback(cbo)

        # case 3: good case
        runner.db.create_alfredo_date(date.today(), None, 1)
        cbo = FakeCallbackObject(USER, "ics",  FakeMessage(message_id=1))
        runner.bot.handle_callback(cbo)

        ics = runner.bot.last_document.read()
        cal = Calendar(ics.decode("utf-8"))
        assert len(cal.events) == 1

        ev = list(cal.events)[0]

        # skip date validation for now
        assert ev.name == "Alfredo"
        assert ev.location == "Z3034"
        assert ev.duration == timedelta(hours=4)

        # case 4: exception (no crash / exception)
        runner.bot.raise_on_next_action()
        runner.bot.handle_callback(cbo)

    def test_signal_handler(self, caplog):
        runner = defaultRunner()

        with caplog.at_level(logging.DEBUG):
            runner.log_command(FakeMessage(USER, text="/command"))
            # error 1: no date tomorrow (silent, but no error either)
            signal.raise_signal(signal.SIGUSR1)

            tomorrow = date.today() + timedelta(days=1)
            runner.bot.handle_command("newalfredo", FakeMessage(ADMIN1, text=f"newalfredo {tomorrow.isoformat()}"))
            assert_num_dates(runner.db, 1)

            # error 2: telegram API
            runner.bot.raise_on_next_action()
            signal.raise_signal(signal.SIGUSR1)
            assert "Telegram API" in caplog.text

            caplog.clear()

            # goodcase
            signal.raise_signal(signal.SIGUSR1)
            assert runner.bot.last_reply_text.count(util.emoji('check')) == 1
            assert runner.bot.last_message_chat_id == GROUP
            assert "Attenzione" in runner.bot.last_message_text
            assert "Sent reminder" in caplog.text
            assert "pinning message"
            assert runner.bot.pinned_message_id == 1

    def test_do_pinning(self, caplog):
        runner = defaultRunner()

        with caplog.at_level(logging.DEBUG):
            assert runner.bot.pinned_message_id == 0

            # case 1: no future dates
            runner.do_pinning()
            assert runner.bot.pinned_message_id == 0

            # case 2: no chat info available
            runner.bot.raise_on_next_action()
            runner.do_pinning()
            assert runner.bot.pinned_message_id == 0
            assert "could not get chat info" in caplog.text
            caplog.clear()

            # case 3: pin next alfredo
            tomorrow = date.today() + timedelta(days=1)
            overmorrow = tomorrow + timedelta(days=1)
            runner.db.create_alfredo_date(overmorrow, None, 20)
            runner.do_pinning()
            assert runner.bot.pinned_message_id == 20

            # case 4: no error on already pinned message
            runner.do_pinning()
            assert runner.bot.pinned_message_id == 20

            # case 5: override existing pinning
            runner.db.create_alfredo_date(tomorrow, None, 15)
            runner.do_pinning()
            assert runner.bot.pinned_message_id == 15

            # case 6: telegram error on pinning (no crash)
            runner.bot.pinned_message_id = 0
            # delay 1 so get_chat works
            runner.bot.raise_on_next_action(delay_by=1)
            runner.do_pinning()
            # check get_chat() worked
            assert "could not get chat info" not in caplog.text
            caplog.clear()

            # delete existing dates -> there are no future dates
            for d in runner.db.get_future_dates():
                runner.db.delete_date(d)
            assert_num_dates(runner.db, 0)

            # case 7: unpin message
            runner.bot.pinned_message_id = 15
            runner.do_pinning()
            assert "unpinning" in caplog.text
            assert runner.bot.pinned_message_id == 0

            # case 8: telegram error on unpinning (no crash)
            runner.bot.pinned_message_id = 25
            # delay 1 so get_chat works
            runner.bot.raise_on_next_action(delay_by=1)
            runner.do_pinning()
            # check get_chat() worked
            assert "could not get chat info" not in caplog.text
            runner.bot.pinned_message_id = 25

    def test_run(self):
        runner = defaultRunner()
        runner.run()

        assert runner.bot.is_polling
