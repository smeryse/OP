# -*- coding: utf-8 -*-
"""Утилиты для работы с путями."""
from pathlib import Path
from report_generator.config import DATA_DIR


def get_lab_json_path(lab_number: int):
    """Возвращает путь к JSON файлу лабораторной работы."""
    return DATA_DIR / f"lab{lab_number}" / f"lab{lab_number}.json"


def get_lab_images_dir(lab_number: int):
    """Возвращает путь к папке с изображениями лабораторной работы."""
    return DATA_DIR / f"lab{lab_number}" / "images"
