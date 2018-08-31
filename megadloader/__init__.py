import base64
import functools
import re
import threading


def suppress_errors(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            print('error: %s', e)

    return wrapper


def threadlocal(func):
    prop_name = func.__name__

    def wrapper(self, *args, **kwargs):
        try:
            vals = self.__locals__
        except AttributeError:
            vals = self.__locals__ = threading.local()

        try:
            return getattr(vals, prop_name)
        except:
            val = func(self, *args, **kwargs)
            setattr(vals, prop_name, val)
            return val

    return wrapper


link_re = re.compile(r'Link:\s*(.*)')
key_re = re.compile(r'Key:\s*(.*)')
m_re = re.compile(r'M:\s*(.*)')
k_re = re.compile(r'K:\s*(.*)')


def decode_url(url: str):
    url = url.strip()

    try:
        tmp = base64.b64decode(url)
        url = tmp.decode('ascii')
    except:
        pass

    link = link_re.search(url)
    key = key_re.search(url)

    if link and key:
        link = base64.b64decode(link.group(1))
        key = base64.b64decode(key.group(1))
        url = link + key
        url = url.decode('ascii')

    m = m_re.search(url)
    k = k_re.search(url)
    if m and k:
        m = m.group(1)
        k = k.group(1)
        if 'mega.nz' not in m:
            m = 'mega.nz/' + m
        if '://' not in m:
            m = 'https://' + m
        url = m + k

    if url.startswith('https://mega'):
        return url
