# -*- coding: utf-8 -*-
"""Генерация HTML-отчёта из JSON данных."""
import json
import os
from .image import process_images_in_data
from .text_processing import apply_fig_refs_in_data
from .renderer import render_html
from ..config import TEMPLATES_DIR


def load_and_merge_data(lab_json_path, base_info_path=None):
    """
    Загружает JSON лабы и при необходимости объединяет с base_info.json.
    Возвращает словарь для шаблона.
    """
    with open(lab_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if base_info_path and os.path.isfile(base_info_path):
        with open(base_info_path, "r", encoding="utf-8") as f:
            base = json.load(f)
        # Объединяем: base_info перезаписывает только отсутствующие ключи
        for key in ("university", "student", "teacher", "location"):
            if key in base and key not in data:
                data[key] = base[key]
    
    return data


def generate_report(
    json_file=None,
    output_file=None,
    max_width=800,
    data=None,
    base_info_file=None,
    images_dir=None,
    template_dir=None,
):
    """
    Генерирует HTML отчёт.
    
    Args:
        json_file: путь к JSON с данными лабы
        output_file: путь для сохранения HTML (по умолчанию 'report.html')
        max_width: максимальная ширина изображений в пикселях
        data: словарь с данными (если передан, json_file игнорируется)
        base_info_file: путь к base_info.json (универ, студент, преподаватель)
        images_dir: папка с картинками (1.png, 2.png, ...)
        template_dir: папка с шаблонами (по умолчанию из config)
    """
    if data is None:
        if not json_file:
            print("Не указан источник данных (json_file или data)")
            return False
        try:
            data = load_and_merge_data(json_file, base_info_file)
            print(f"Загружен JSON: {json_file}")
        except Exception as e:
            print(f"Ошибка загрузки JSON: {e}")
            return False
    else:
        # Если data передан напрямую, всё равно попробуем подмешать base_info
        if base_info_file and os.path.isfile(base_info_file):
            try:
                with open(base_info_file, "r", encoding="utf-8") as f:
                    base = json.load(f)
                for key in ("university", "student", "teacher", "location"):
                    if key in base and key not in data:
                        data[key] = base[key]
            except Exception as e:
                print(f"Не удалось загрузить base_info: {e}")

    # Замена (Рис. N) → как показано на Рисунке N
    apply_fig_refs_in_data(data)

    # Обработка изображений
    if images_dir:
        images_dir = os.path.abspath(images_dir)
    processed = process_images_in_data(data, images_dir=images_dir, max_width=max_width)
    if processed > 0:
        print(f"Встроено изображений: {processed}")
    elif images_dir:
        print(f"Папка с изображениями указана, но изображения не найдены: {images_dir}")

    # Рендеринг HTML
    tpl_dir = template_dir or str(TEMPLATES_DIR)
    if not os.path.isdir(tpl_dir):
        print(f"Папка шаблонов не найдена: {tpl_dir}")
        return False

    try:
        html = render_html(data, template_dir=tpl_dir)
    except Exception as e:
        print(f"Ошибка рендеринга: {e}")
        return False

    # Сохранение
    if not output_file:
        output_file = "report.html"
    out_dir = os.path.dirname(output_file)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = os.path.getsize(output_file) / 1024
    print(f"Отчёт сохранён: {output_file} ({size_kb:.2f} КБ)")
    return True
