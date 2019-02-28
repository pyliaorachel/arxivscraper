from datetime import datetime, timedelta


def get_date_chunks(date_from, date_until, intv=30):
    start = datetime.strptime(date_from, '%Y-%m-%d')
    end = datetime.strptime(date_until, '%Y-%m-%d')
    intv = timedelta(intv)

    s = start
    while s + intv < end:
        yield (s.strftime('%Y-%m-%d'), (s + intv).strftime('%Y-%m-%d'))
        s += intv + timedelta(1)
    yield (s.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))