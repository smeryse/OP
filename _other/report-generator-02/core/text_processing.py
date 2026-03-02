# -*- coding: utf-8 -*-
"""Обработка текста: замена ссылок на рисунки."""
import re


def replace_fig_refs(text):
    """(Рис. N) и (Рис N) → как показано на Рисунке N."""
    if not text or not isinstance(text, str):
        return text
    text = re.sub(r"\(Рис\.?\s*(\d+)\)", r"как показано на Рисунке \1", text, flags=re.IGNORECASE)
    return text


def apply_fig_refs_in_data(data):
    """Заменяет ссылки на рисунки в тексте шагов процедуры."""
    procedure = data.get("procedure") if isinstance(data, dict) else None
    if not procedure:
        return
    for step in procedure:
        if isinstance(step, dict) and "text" in step and step["text"]:
            step["text"] = replace_fig_refs(step["text"])
