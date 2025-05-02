from datetime import timedelta


def next_weekday(current, weekday):
    days_ahead = weekday - current.weekday()
    if days_ahead < 0:
        days_ahead += 7
    return current + timedelta(days_ahead)
