import os
import glob
from typing import Optional, Tuple, Any
from collections import defaultdict
from multiprocessing.pool import ThreadPool
import traceback

from yt_dlp.cookies import extract_cookies_from_browser, SUPPORTED_BROWSERS
from yt_dlp.cookies import _get_chromium_based_browser_settings, CHROMIUM_BASED_BROWSERS
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


def extract_cookies(args) -> Tuple[Optional[Tuple[str, Any]], dict]:
    try:
        jar = extract_cookies_from_browser(*args)
    except (FileNotFoundError, ValueError):
        return None, {}
    except (PermissionError):
        if args[0] in ['chrome', 'edge', 'chromium']:
            if len(args) > 1:
                return ('chrome read permission error', args[1]), {}
            return ('chrome read permission error', args[0]), {}
        return None, {}
    for cookie in jar:
        if cookie.domain.endswith('.bilibili.com'):
            if cookie.name == 'SESSDATA':
                return None, {cookie.value: jar}
    return None, {}


def match_misc_chromium():
    exclude_paths = {_get_chromium_based_browser_settings(browser)['browser_dir']
                     for browser in CHROMIUM_BASED_BROWSERS}
    matches = []
    if os.name == 'nt' and os.environ.get('LOCALAPPDATA'):
        for layer in range(3):
            items = map(os.path.dirname, glob.glob(os.path.join(
                *[os.environ['LOCALAPPDATA']] + ['*'] * layer + ['User Data', '*', 'History'])))
            matches.extend([i for i in items if os.path.exists(os.path.join(i, 'Network', 'Cookies'))])
    browser_paths = {os.path.dirname(match) for match in matches} - exclude_paths
    return [('chrome', path) for path in browser_paths]


def default_browsers():
    return [(browser,) for browser in SUPPORTED_BROWSERS]


def auto_extract_cookies():
    cookies_jars = {}
    known_errors = defaultdict(set)
    misc_errors = []
    for args in default_browsers() + match_misc_chromium():
        try:
            error_msg, extract_result = extract_cookies(args)
            if error_msg:
                known_errors[error_msg[0]].add(error_msg[1])
            cookies_jars.update(extract_result)
        except Exception:
            misc_errors.append(traceback.format_exc())
    valid_cookies = {}
    if cookies_jars:
        with ThreadPool(processes=len(cookies_jars)) as pool:
            for result in pool.map(validate_cookies, cookies_jars.values()):
                valid_cookies.update(result)
    return {'known': known_errors, 'misc': misc_errors}, valid_cookies


if __name__ == '__main__':
    errors, result = auto_extract_cookies()
    print(result)
    print(errors)
    print(result.keys())
