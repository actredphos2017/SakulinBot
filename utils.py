import json
import re


def is_valid_string(s):
    return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', s))


def put_storage(key: str, data: dict):
    if not is_valid_string(key):
        raise Exception(f'Invalid key name: {key}')
    with open(f"save/{key}.sav.json", "w") as file:
        file.write(json.dumps(data))


def get_storage(key):
    try:
        with open(f"save/{key}.sav.json", "r") as file:
            data = file.read()
        return json.loads(data)
    except FileNotFoundError:
        return {}
