from functools import wraps
from ics import Calendar, Event
from os import path
from random import choice
import arrow
import babel.dates
import logging
import datetime

log = logging.getLogger("util")

emojis = {
    "check": u'\U00002705',
    "cross": u'\U0000274C',
    "frowning": u'\U0001F641',
    "bullet": u'\U00002022',
    "megaphone": u'\U0001F4E3',
    "download": u'\U00002B07'
}

reminders = [
    "Wer heute sein Kreuz setzt, muss morgen nicht hungern!",
    "Heute votieren -> morgen dinieren!",
    "Heute schön einschreiben -> morgen dick einverleiben!",
    "Heiße Teigscheiben in deiner Umgebung suchen DICH! MELD. DICH. AN.",
    "Hunger? Muss nicht sein, meld' dich jetzt an!",
    "Letzte Chance für nette Fettigkeiten oder fette Nettigkeiten!",
    "Morgen gibt's mal wieder Pizza...",
    "Hast du auch von Pizza geträumt? Bei Alfredo werden morgen Träume Wirklichkeit!"
]


def format_date(date):
    return babel.dates.format_date(date, format='full', locale='de_DE')


def format_user(user):
    username = f"{user.username}:" if user.username else ""
    return f"{user.first_name} ({username}{user.id})"


def get_version():
    return "0.2 'Bavadin'"


def emoji(emo):
    if emo in emojis.keys():
        return emojis[emo]
    else:
        return ""


def success(msg):
    return f"{emoji('check')} {msg}"


def failure(msg):
    return f"{emoji('cross')} {msg}"


def li(string):
    return f"{emoji('bullet')} {string}\n"


def generate_ics_file(workdir, date):
    filename = f"{babel.dates.format_date(date, format='yyyy-MM-dd')}_alfredo.ics"
    filepath = path.join(workdir, filename)

    if not path.exists(filepath):
        log.debug(f"creating new ics file {filepath}")
        begin = arrow.get(date, "Europe/Berlin")
        begin = begin.replace(hour=18)

        cal = Calendar()
        ev = Event(
            name="Alfredo",
            begin=begin.to("UTC"),
            duration={"hours": 4},
            location="Z3034",
            created=datetime.datetime.now()
        )

        cal.events.add(ev)

        with open(filepath, 'w') as f:
            f.writelines(cal.serialize_iter())
    else:
        log.debug(f"serving ics file {filepath} from cache")

    return filepath


def get_reminder():
    return choice(reminders)


def admin_command_check():
    def decorator(f):
        @wraps(f)
        def decorated_function(self, *args, **kwargs):
            message = args[0]

            if not self.user_is_admin(message.from_user):
                self.log_command(message)
                self.send_error(message, "Du bist kein Admin.")
                return

            self.log_command(message, admincmd=True)
            return f(self, message)
        return decorated_function
    return decorator
