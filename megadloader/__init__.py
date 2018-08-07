import base64
import functools
import re


def suppress_errors(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except:
            print('error: %s', e)

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
        url = 'https://mega.nz/' + m.group(1) + k.group(1)

    if url.startswith('https://mega'):
        return url
