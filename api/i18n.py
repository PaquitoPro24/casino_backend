import json
import os
from pathlib import Path
from fastapi import Request

# Global dictionary to hold loaded translations
# Structure: {'es': {...}, 'en': {...}}
TRANSLATIONS = {}

def load_translations(locales_dir: str = "locales"):
    """
    Loads translation files from the specified directory.
    Files should be named like 'es.json', 'en.json', etc.
    """
    global TRANSLATIONS
    base_path = Path(locales_dir)
    
    if not base_path.exists():
        print(f"⚠️ i18n: Locales directory '{locales_dir}' not found.")
        return

    for file_path in base_path.glob("*.json"):
        lang_code = file_path.stem # e.g., 'es' from 'es.json'
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                TRANSLATIONS[lang_code] = json.load(f)
            print(f"✅ i18n: Loaded locale '{lang_code}'")
        except Exception as e:
            print(f"🚨 i18n: Error loading '{file_path}': {e}")

def get_locale(request: Request) -> str:
    """
    Determines the locale from the request.
    Priority:
    1. 'lang' query param (e.g. ?lang=en)
    2. 'NEXT_LOCALE' cookie (standard in some frameworks, we can use 'app_lang')
    3. Accept-Language header
    4. Default 'es'
    """
    # 1. Query Param
    query_lang = request.query_params.get("lang")
    if query_lang and query_lang in TRANSLATIONS:
        return query_lang

    # 2. Cookie
    cookie_lang = request.cookies.get("app_lang")
    if cookie_lang and cookie_lang in TRANSLATIONS:
        return cookie_lang

    # 3. Header (Simplified check)
    accept_language = request.headers.get("accept-language", "")
    if "en" in accept_language[:2]: # Very basic check
        return "en"

    # Default
    return "es"

def trans(key: str, request: Request = None, locale: str = None) -> str:
    """
    Translate a key string (e.g., 'common.welcome').
    If request is provided, auto-detects locale.
    If locale is provided, uses it.
    """
    if locale is None and request is not None:
        locale = get_locale(request)
    
    if locale is None:
        locale = "es" # Fallback

    # Navigate the dictionary (e.g., "common.welcome" -> ["common"]["welcome"])
    keys = key.split(".")
    value = TRANSLATIONS.get(locale, {})
    
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k)
        else:
            return key # Key not found structure mismatch

    if value is None:
        return key # Translation missing

    return str(value)
