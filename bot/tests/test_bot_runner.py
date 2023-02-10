from datetime import date, timedelta
import json
from fake import FakeBot, FakeUser, FakeMessage
from bot_runner import BotRunner
import util

import pytest

ADMIN1 = 42
ADMIN2 = 69
GROUP = "-1337"
TESTCFG = "tests/config-test.json"


def defaultRunner():
    return BotRunner(TESTCFG, FakeBot, ":memory:")


class TestBotRunner:
    def test_basic(self):
        runner = defaultRunner()

        # check that a handler for every command was registered
        assert len(runner.bot.handlers.keys()) == len(runner.default_commands) + len(runner.admin_commands)
        assert runner.bot.token == "abcdefghijklmnopqrstuvwxyz"

    def test_config_errors(self, tmp_path):
        tmp_cfg = tmp_path / "tmp.json"

        # case 1: config file does not exist
        with pytest.raises(Exception) as ex:
            BotRunner("does-not-exist.json", None, None)

        assert "does not exist" in ex.value.args[0]

        # case 2: missing key
        for k in ["token", "group", "admins"]:
            with open(TESTCFG) as c:
                cfg = json.load(c)

            del cfg[k]

            with open(tmp_cfg, "w") as out:
                json.dump(cfg, out)

            with pytest.raises(Exception) as ex:
                BotRunner(tmp_cfg, None, None)

            assert f"config key {k} not found" in ex.value.args[0]

        # case 3: no admins
        with open(TESTCFG) as c:
            cfg = json.load(c)

        cfg["admins"] = []

        with open(tmp_cfg, "w") as out:
            json.dump(cfg, out)

        with pytest.raises(Exception) as ex:
            BotRunner(tmp_cfg, None, None)

        assert "at least one admin" in ex.value.args[0]

    def test_send_error(self):
        runner = defaultRunner()
        msg = FakeMessage()

        runner.send_error(msg, "Test")

        error = runner.bot.last_reply
        assert "Fehler" in error
        assert "Test" in error

    def test_user_is_admin(self):
        runner = defaultRunner()

        admin = FakeUser(ADMIN1)
        admin2 = FakeUser(ADMIN2)
        user = FakeUser(1337)

        assert runner.user_is_admin(admin)
        assert runner.user_is_admin(admin2)
        assert runner.user_is_admin(user) is False

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

    def test_cms_with_execption(self):
        runner = defaultRunner()

        # collection of goodcases
        cmds = {
            "start": FakeMessage(FakeUser(1), "channel"),
            "help": FakeMessage(FakeUser(1), "channel"),
            "karte": FakeMessage(),
            "termine": FakeMessage(),
            "newalfredo": FakeMessage(FakeUser(ADMIN1), text="newalfredo 2199-01-01"),
            "announce": FakeMessage(FakeUser(ADMIN1), text="announce Test Test Test")
        }

        assert len(cmds) == len(runner.default_commands) + len(runner.admin_commands)

        for cmd, msg in cmds.items():
            runner.bot.raise_on_next_action()
            runner.bot.handle_command(cmd, msg)

    def test_cmd_start(self):
        runner = defaultRunner()

        no_admin_output = []
        admin_output = []

        # not an admin, public chat
        runner.bot.handle_command("start", FakeMessage(FakeUser(1), "channel"))
        no_admin_output.append(runner.bot.last_reply)

        # not an admin, private chat
        runner.bot.handle_command("start", FakeMessage(FakeUser(1), "private"))
        no_admin_output.append(runner.bot.last_reply)

        # admin, public chat
        runner.bot.handle_command("start", FakeMessage(FakeUser(ADMIN1), "channel"))
        no_admin_output.append(runner.bot.last_reply)

        # admin, public chat
        runner.bot.handle_command("start", FakeMessage(FakeUser(ADMIN1), "private"))
        admin_output.append(runner.bot.last_reply)

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
        runner = defaultRunner()

        no_admin_output = []
        admin_output = []

        # not an admin, public chat
        runner.bot.handle_command("help", FakeMessage(FakeUser(1), "channel"))
        no_admin_output.append(runner.bot.last_reply)

        # not an admin, private chat
        runner.bot.handle_command("help", FakeMessage(FakeUser(1), "private"))
        no_admin_output.append(runner.bot.last_reply)

        # admin, public chat
        runner.bot.handle_command("help", FakeMessage(FakeUser(ADMIN1), "channel"))
        no_admin_output.append(runner.bot.last_reply)

        # admin, public chat
        runner.bot.handle_command("help", FakeMessage(FakeUser(ADMIN1), "private"))
        admin_output.append(runner.bot.last_reply)

        for msg in no_admin_output + admin_output:
            for cmd in runner.default_commands:
                assert f"/{cmd.command}" in msg

        for msg in no_admin_output:
            assert "Adminkommandos" not in msg

        for msg in admin_output:
            assert "Adminkommandos" in msg

    def test_cmd_menu(self):
        runner = defaultRunner()

        # goodcase
        runner.bot.handle_command("karte", FakeMessage())
        msg = runner.bot.last_reply

        assert "github" in msg
        assert "menu.pdf" in msg

    def test_cmd_show_dates(self):
        runner = defaultRunner()

        runner.bot.handle_command("termine", FakeMessage())
        msg = runner.bot.last_reply
        assert "keine" in msg

        one_day = timedelta(days=1)

        today = date.today()
        yesterday = today - one_day
        # add alfredo, but in the past -> no change in output
        runner.db.create_alfredo_date(yesterday, None, 1)

        runner.bot.handle_command("termine", FakeMessage())
        msg = runner.bot.last_reply
        assert "keine" in msg

        runner.db.create_alfredo_date(today, None, 2)
        runner.bot.handle_command("termine", FakeMessage())
        msg = runner.bot.last_reply
        assert "einzige" in msg

        tomorrow = today + one_day
        overmorrow = tomorrow + one_day
        runner.db.create_alfredo_date(tomorrow, None, 3)
        runner.db.create_alfredo_date(overmorrow, None, 4)

        runner.bot.handle_command("termine", FakeMessage())
        msg = runner.bot.last_reply
        assert "nächsten 3 Termine" in msg
        assert msg.count(util.emoji('bullet')) == 3

    def test_acmd_new_alfredo(self):
        def num_dates(db):
            from models import AlfredoDate
            from sqlalchemy import select, func
            from sqlalchemy.orm import Session

            with Session(db.engine) as session:
                return session.scalars(select(func.count()).select_from(AlfredoDate)).first()

        runner = defaultRunner()

        # error 1: no admin
        runner.bot.handle_command("newalfredo", FakeMessage(FakeUser(1), text="newalfredo 2199-01-01"))
        assert num_dates(runner.db) == 0
        assert "kein Admin" in runner.bot.last_reply

        # error 2: no param, too many params
        runner.bot.handle_command("newalfredo", FakeMessage(FakeUser(ADMIN1), text="newalfredo"))
        assert "einen Parameter" in runner.bot.last_reply
        runner.bot.handle_command("newalfredo", FakeMessage(FakeUser(ADMIN1), text="newalfredo "))
        assert "einen Parameter" in runner.bot.last_reply
        runner.bot.handle_command("newalfredo", FakeMessage(FakeUser(ADMIN1), text="newalfredo 2199-01-01 even more text"))
        assert "einen Parameter" in runner.bot.last_reply
        assert num_dates(runner.db) == 0

        # error 3: invalid date
        runner.bot.handle_command("newalfredo", FakeMessage(FakeUser(ADMIN1), text="newalfredo not-a-date"))
        assert "konnte nicht in ein Datum" in runner.bot.last_reply
        runner.bot.handle_command("newalfredo", FakeMessage(FakeUser(ADMIN1), text="newalfredo 30-01-01"))
        assert "konnte nicht in ein Datum" in runner.bot.last_reply
        assert num_dates(runner.db) == 0

        # error 4: before today
        one_day = timedelta(days=1)
        today = date.today()
        yesterday = today - one_day

        runner.bot.handle_command("newalfredo", FakeMessage(FakeUser(ADMIN1), text="newalfredo 2022-01-01"))
        assert "frühstens heute" in runner.bot.last_reply
        runner.bot.handle_command("newalfredo", FakeMessage(FakeUser(ADMIN1), text=f"newalfredo {yesterday.isoformat()}"))
        assert "frühstens heute" in runner.bot.last_reply
        assert num_dates(runner.db) == 0

        # error 5: telegram exception
        runner.bot.raise_on_next_action()
        runner.bot.handle_command("newalfredo", FakeMessage(FakeUser(ADMIN1), text="newalfredo 2199-01-01"))
        assert "Telegram API" in runner.bot.last_reply
        assert num_dates(runner.db) == 0

        # goodcase
        runner.bot.handle_command("newalfredo", FakeMessage(FakeUser(ADMIN1), text="newalfredo 2199-01-01"))
        assert "Umfrage wurde erstellt" in runner.bot.last_reply
        assert num_dates(runner.db) == 1
        date_ = runner.db.get_future_dates()[0]
        assert runner.bot.last_chat_id == GROUP
        assert util.format_date(date.fromisoformat("2199-01-01")) in runner.bot.last_text
        assert date_.date == date.fromisoformat("2199-01-01")
        assert date_.message_id == 1

        # error 6: duplicate
        runner.bot.handle_command("newalfredo", FakeMessage(FakeUser(ADMIN1), text="newalfredo 2199-01-01"))
        assert "bereits ein Alfredo" in runner.bot.last_reply
        assert num_dates(runner.db) == 1

    def test_acmd_announce(self):
        runner = defaultRunner()

        # error 1: no admin
        runner.bot.handle_command("announce", FakeMessage(FakeUser(1), text="announce message"))
        assert "kein Admin" in runner.bot.last_reply

        # error 2: no param
        runner.bot.handle_command("announce", FakeMessage(FakeUser(ADMIN1), text="announce"))
        assert "Parameter" in runner.bot.last_reply
        runner.bot.handle_command("announce", FakeMessage(FakeUser(ADMIN1), text="announce "))
        assert "Parameter" in runner.bot.last_reply

        # error 3: telegram exception
        runner.bot.raise_on_next_action()
        runner.bot.handle_command("announce", FakeMessage(FakeUser(ADMIN1), text="announce Test Test Test"))
        assert "Telegram API" in runner.bot.last_reply

        # goodcase
        runner.bot.handle_command("announce", FakeMessage(FakeUser(ADMIN1), text="announce Test Test Test"))
        assert runner.bot.last_chat_id == GROUP
        assert runner.bot.last_text.endswith("Test Test Test")
        assert "announce" not in runner.bot.last_text

    def test_run(self):
        runner = defaultRunner()
        runner.run()

        assert runner.bot.is_polling
