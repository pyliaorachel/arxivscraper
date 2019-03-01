from datetime import datetime, timedelta


def get_date_chunks(date_from, date_until, intv=30, reverse=True):
    start = datetime.strptime(date_from, '%Y-%m-%d')
    end = datetime.strptime(date_until, '%Y-%m-%d')
    intv = timedelta(intv)

    if reverse:
        e = end
        while e - intv > start:
            yield ((e - intv).strftime('%Y-%m-%d'), e.strftime('%Y-%m-%d'))
            e -= intv + timedelta(1)
        yield (start.strftime('%Y-%m-%d'), e.strftime('%Y-%m-%d'))
    else:
        while s + intv < end:
            yield (s.strftime('%Y-%m-%d'), (s + intv).strftime('%Y-%m-%d'))
            s += intv + timedelta(1)
        yield (s.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))
