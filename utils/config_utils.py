'''Functions for working with the config'''

from typing import Dict

from yaml import YAMLError, safe_load


def read_config(file_path: str) -> Dict[str, str | int | bool]:
    '''Read the config and return it in dictionary form'''
    with open(file_path, "r", encoding='UTF-8') as file_read:
        try:
            CONFIG = safe_load(file_read)
        except YAMLError as exc:
            raise exc
        else:
            return CONFIG
        