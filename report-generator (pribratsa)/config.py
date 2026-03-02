# -*- coding: utf-8 -*-
"""Конфигурация проекта."""
from pathlib import Path
import os
import json

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "3. data"
REPORTS_DIR = BASE_DIR / "4. reports"
TEMPLATES_DIR = BASE_DIR / "2. scripts/templates"

DEFAULT_FORMAT = "html"

PAGE_MARGINS = {
    "left": "30mm",
    "right": "10mm",
    "top": "20mm",
    "bottom": "20mm"
}

# Путь к файлу с API ключами (не коммитится в git)
API_KEYS_FILE = BASE_DIR / ".api_keys.json"

# API ключи (загружаются из файла или переменных окружения)
API_KEYS = {
    "gemini": None,
    "groq": None,
    "openai": None,
}


def load_api_keys():
    """Загружает API ключи из файла или переменных окружения."""
    global API_KEYS
    
    # Сначала пробуем загрузить из файла
    if API_KEYS_FILE.exists():
        try:
            with open(API_KEYS_FILE, "r", encoding="utf-8") as f:
                file_keys = json.load(f)
                API_KEYS.update(file_keys)
        except Exception as e:
            print(f"⚠️ Не удалось загрузить API ключи из файла: {e}")
    
    # Затем проверяем переменные окружения (имеют приоритет)
    env_keys = {
        "gemini": os.getenv("GEMINI_API_KEY"),
        "groq": os.getenv("GROQ_API_KEY"),
        "openai": os.getenv("OPENAI_API_KEY"),
    }
    
    for key, value in env_keys.items():
        if value:
            API_KEYS[key] = value


def save_api_keys(keys: dict):
    """Сохраняет API ключи в файл."""
    try:
        # Загружаем существующие ключи
        existing = {}
        if API_KEYS_FILE.exists():
            with open(API_KEYS_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
        
        # Обновляем только переданные ключи
        existing.update(keys)
        
        # Сохраняем
        with open(API_KEYS_FILE, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
        
        # Обновляем глобальный словарь
        API_KEYS.update(existing)
        
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения API ключей: {e}")
        return False


def get_api_key(provider: str) -> str:
    """Получает API ключ для указанного провайдера."""
    return API_KEYS.get(provider.lower())


def set_api_key(provider: str, api_key: str):
    """Устанавливает API ключ для указанного провайдера."""
    provider = provider.lower()
    API_KEYS[provider] = api_key
    save_api_keys({provider: api_key})


# Загружаем ключи при импорте модуля
load_api_keys()
