import os
import json
import time

import psutil


def look_for_wpf():
    for proc in psutil.process_iter():
        if proc.name() == 'BililiveRecorder.WPF.exe':
            return proc


def get_config_path():
    try:
        fn = os.path.join(os.environ['LOCALAPPDATA'], 'BililiveRecorder', 'path.json')
        with open(fn, 'rt') as f:
            return os.path.join(json.load(f)['Path'], 'config.json')
    except (TypeError, FileNotFoundError, json.JSONDecodeError, KeyError):
        pass


def get_path_from_proc(proc):
    for basedir in [os.path.dirname(proc.exe()), proc.cwd()]:
        try:
            with open(os.path.join(basedir, 'path.json'), 'rt') as f:
                return os.path.join(json.load(f)['Path'], 'config.json')
        except (TypeError, FileNotFoundError, json.JSONDecodeError, KeyError):
            pass


def get_path_and_proc():
    proc = look_for_wpf()
    if not proc:
        path = get_config_path()
    else:
        path = get_path_from_proc(proc)
    if path:
        if not validate_config(path):
            path = None
    return (path, proc)


def validate_config(json_fn):
    try:
        with open(json_fn, 'rt') as f:
            data = json.load(f)
        if data['version'] != 3:
            raise ValueError(f'不支持的配置版本：{data["version"]}')
        return True
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return False


def set_cookies(json_fn, cookie_str):
    with open(json_fn, 'rt', encoding='utf-8') as f:
        data = json.load(f)
    data['global'] = {
        **data.get('global', {}),
        "Cookie": {
            "HasValue": True,
            "Value": cookie_str,
        }
    }
    os.rename(json_fn, f'{os.path.splitext(json_fn)[0]}-{time.strftime("%y%m%d-%H%M%S")}.json')
    with open(json_fn, 'wt', encoding='utf-8') as f:
        json.dump(data, f)


if __name__ == '__main__':
    path, proc = get_path_and_proc()
    print(path, proc)
