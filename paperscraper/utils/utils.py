from datetime import datetime, timedelta
import re


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

def split_sent(text):
    text = text.strip()
    text = re.sub('\.[\.]+', '<dots>', text) # avoid dots being mixed up with periods
    splits = re.split('(。|？+|！+|\?+|!+|\.)', text)

    # Join every two elements in list, one the main sentence, one the delimeter punctuation
    splits = [''.join(x) for x in zip(splits[0::2], splits[1::2])]

    splits = [re.sub('<dots>', '...', split) for split in splits]
    return splits

def is_chinese(text):
    return len(re.findall('[\u4e00-\u9fff]+', text)) > 0

def always_true(x):
    return True

def always_false(x):
    return False