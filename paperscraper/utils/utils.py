from datetime import datetime, timedelta
import re
import time
from urllib.request import urlopen
from urllib.error import HTTPError
from socket import error as SocketError


ERROR_BACKOFF_RATE = 2

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

def try_urlopen(req, sleep_t, failed_attempts=0):
    fail_t = sleep_t * (ERROR_BACKOFF_RATE ** failed_attempts)
    try:
        response = urlopen(req)
    except HTTPError as e:
        if e.code == 503:
            to = int(e.hdrs.get('retry-after', 30))
            print('Got {}. Retrying after {} seconds.'.format(e.code, fail_t))
            time.sleep(fail_t)
            return False, None
        else:
            print('HTTPError:', e)
            time.sleep(fail_t)
            return False, None
    except SocketError as e:
        if e.errno == 104:
            print('Got {}. Retrying after {} seconds.'.format(e.errno, fail_t))
            time.sleep(fail_t)
            return False, None
        else:
            print('SocketError:', e)
            time.sleep(fail_t)
            return False, None
    except Exception as e:
        print('Exception:', e)
        time.sleep(fail_t)
        return False, None
    return True, response