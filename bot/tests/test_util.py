from datetime import date
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

        assert util.emoji("does_not_exist") == ""

    def test_li(self):
        s = util.li("test")

        assert s.startswith(util.emoji("bullet"))
        assert "test" in s
        assert s.endswith("\n")
