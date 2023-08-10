import os
import glob
from multiprocessing.pool import ThreadPool

from yt_dlp.cookies import extract_cookies_from_browser, SUPPORTED_BROWSERS
import requests


def to_cookie_str(jar):
    items = []
    for cookie in jar:
        if cookie.domain.endswith('.bilibili.com'):
            items.append(f'{cookie.name}={cookie.value}')
    return '; '.join(items)


def validate_cookies(jar, retries=3):
    try:
        session = requests.Session()
        session.cookies = jar
        r = session.get('https://api.bilibili.com/x/web-interface/nav', timeout=5)
        if r.status_code == 200 and r.json()['code'] == 0:
            data = r.json()['data']
            return {data['mid']: (data['uname'], to_cookie_str(jar))}
        return {}
    except Exception:
        if retries > 0:
            return validate_cookies(jar, retries=retries-1)
        raise


def extract_cookies(args):
    try:
        jar = extract_cookies_from_browser(*args)
    except (FileNotFoundError, ValueError):
        return {}
    for cookie in jar:
        if cookie.domain.endswith('.bilibili.com'):
            if cookie.name == 'SESSDATA':
                return {cookie.value: jar}
    return {}


def match_misc_chromium():
    matches = []
    if os.name == 'nt' and os.environ.get('LOCALAPPDATA'):
        for layer in range(3):
            matches.extend(glob.glob(os.path.join(
                *[os.environ['LOCALAPPDATA']] + ['*'] * layer + ['User Data', '*', "Google Profile.ico"])))
    return [('chrome', os.path.dirname(match)) for match in matches]


def default_browsers():
    return [(browser,) for browser in SUPPORTED_BROWSERS]


def auto_extract_cookies():
    cookies_jars = {}
    for args in default_browsers() + match_misc_chromium():
        cookies_jars.update(extract_cookies(args))
    valid_cookies = {}
    with ThreadPool(processes=len(cookies_jars)) as pool:
        for result in pool.map(validate_cookies, cookies_jars.values()):
            valid_cookies.update(result)
    return valid_cookies


if __name__ == '__main__':
    result = auto_extract_cookies()
    print(result)
    print(result.keys())
