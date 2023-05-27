from datetime import date
from os import path
import logging
import util

from fake import FakeUser


class TestUtil:
    def test_format_date(self):
        obj = date.fromisoformat("2023-01-01")
        fmt = util.format_date(obj)

        assert "Sonntag" in fmt
        assert "1. Januar" in fmt
        assert "2023" in fmt

    def test_format_user(self):
        fmt = util.format_user(FakeUser(1, "Firstname", "Username"))

        assert "1" in fmt
        assert "Firstname" in fmt
        assert "Username" in fmt

        # username is technially optional
        fmt = util.format_user(FakeUser(1, "Firstname", None))
        assert "None" not in fmt

    def test_get_version(self):
        assert util.get_version() is not None
        assert len(util.get_version()) > 0

    def test_emoji(self):
        assert util.emoji("bullet") != ""
        assert util.emoji("cross") != ""
        assert util.emoji("check") != ""
        assert util.emoji("frowning") != ""
        assert util.emoji("megaphone") != ""
        assert util.emoji("download") != ""

        assert util.emoji("does_not_exist") == ""

    def test_success(self):
        succ = util.success("Test")
        assert "Test" in succ
        assert util.emoji("check") in succ

    def test_failure(self):
        fail = util.failure("Test")
        assert "Test" in fail
        assert util.emoji("cross") in fail

    def test_li(self):
        s = util.li("test")

        assert s.startswith(util.emoji("bullet"))
        assert "test" in s
        assert s.endswith("\n")

    def test_generate_ics_file(self, tmp_path, caplog):
        with caplog.at_level(logging.DEBUG):
            d = date.fromisoformat("2023-01-01")

            name = path.join(tmp_path, "2023-01-01_alfredo.ics")
            assert not path.exists(name)

            ret = util.generate_ics_file(tmp_path, d)
            assert path.exists(ret)
            assert ret == name

            assert "creating new ics file" in caplog.text
            assert "from cache" not in caplog.text
            caplog.clear()

            ret = util.generate_ics_file(tmp_path, d)
            assert path.exists(ret)
            assert ret == name

            assert "creating new ics file" not in caplog.text
            assert "from cache" in caplog.text

    def test_get_reminder(self):
        reminders = set()

        for i in range(1000):
            reminders.add(util.get_reminder())

        assert len(reminders) == len(util.reminders)
