import json
import os
from functools import lru_cache

TRANSLATIONS_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'translations')
SUPPORTED_LANGUAGES = ['en', 'hi']

_cache = {}

def load_translations(language: str) -> dict:
    if language not in SUPPORTED_LANGUAGES:
        language = 'en'
    if language in _cache:
        return _cache[language]
    path = os.path.join(TRANSLATIONS_DIR, f'{language}.json')
    if not os.path.exists(path):
        path = os.path.join(TRANSLATIONS_DIR, 'en.json')
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    _cache[language] = data
    return data

def translate(key: str, language: str = 'en', **kwargs) -> str:
    translations = load_translations(language)
    text = translations.get(key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, ValueError):
            pass
    return text

def get_all_translations(language: str) -> dict:
    return load_translations(language)
