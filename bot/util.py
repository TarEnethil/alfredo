from functools import wraps
import babel.dates

emojis = {
    "check": u'\U00002705',
    "cross": u'\U0000274C',
    "frowning": u'\U0001F641',
    "bullet": u'\U00002022',
    "megaphone": u'\U0001F4E3'
}


def format_date(date):
    return babel.dates.format_date(date, format='full', locale='de_DE')


def format_user(user):
    username = f"{user.username}:" if user.username else ""
    return f"{user.first_name} ({username}{user.id})"


def get_version():
    return "0.1 'Axies'"


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
