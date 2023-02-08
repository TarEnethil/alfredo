import babel.dates

emojis = {
    "check": u'\U00002705',
    "cross": u'\U0000274C',
    "frowning": u'\U0001F641',
    "bullet": u'\U00002022'
}


def format_date(date):
    return babel.dates.format_date(date, format='full', locale='de_DE')


def get_version():
    return "Alpha"


def emoji(emo):
    if emo in emojis.keys():
        return emojis[emo]
    else:
        return ""


def li(string):
    return f"{emoji('bullet')} {string}\n"
