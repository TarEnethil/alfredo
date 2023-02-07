import babel.dates


def format_date(date):
    return babel.dates.format_date(date, format='full', locale='de_DE')


def get_version():
    return "Alpha"
