def localize_month(month):
    serialized_month = int(month) + 1
    ru_month = [
        'января',
        'февраля',
        'марта',
        'апреля',
        'мая',
        'июня',
        'июля',
        'августа',
        'сентября',
        'октября',
        'ноября',
        'декабря',
    ]
    return ru_month[serialized_month]