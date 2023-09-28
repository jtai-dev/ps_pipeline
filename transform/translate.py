# Built-ins
import re
from datetime import datetime

# External packages and libraries
from unidecode import unidecode


datetime_ISO = re.compile(
    r'^\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2}(?:[\-\+]\d{2}:\d{2}|Z)?)?$')
mm_dd_yyyy = re.compile(
    r'(?P<m>\d{2})[\/|-|\.](?P<d>\d{2})[\/|-|\.](?P<Y>\d{4})')
mm_dd_yy = re.compile(
    r'(?P<m>\d{2})[\/|-|\.](?P<d>\d{2})[\/|-|\.](?P<y>\d{2})')
month_dd_yyyy = re.compile(
    r'(?P<B>[A-Za-z]{4,})\s+(?P<d>\d{2})(?:,\s*|\s+)(?P<Y>\d{4})')
smonth_dd_yyyy = re.compile(
    r'(?P<b>[A-Za-z]{3})\s+(?P<d>\d{2})(?:,\s*|\s+)(?P<Y>\d{4})')


def asciify(text): return unidecode(text)


def get_date(text):

    patterns = {
        0: datetime_ISO,
        1: mm_dd_yyyy,
        2: mm_dd_yy,
        3: month_dd_yyyy,
        4: smonth_dd_yyyy
    }
    # use finditer for date since they might be embedded within text

    for i, p in patterns.items():
        matched = list(p.finditer(text))
        for result in matched:
            if i == 0 and p.fullmatch(text):
                return str(datetime.fromisoformat(text))
            else:
                d = result.groupdict()
                params = " ".join([f"%{k}" for k in d if d[k]])
                values = " ".join([v for v in d.values() if v])
                return str(datetime.strptime(values, params))
            
    return text

