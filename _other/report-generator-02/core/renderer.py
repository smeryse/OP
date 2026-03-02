# -*- coding: utf-8 -*-
"""Рендеринг HTML из шаблонов Jinja2."""
from jinja2 import Environment, FileSystemLoader
from ..config import TEMPLATES_DIR


def render_html(data: dict, template_dir=None):
    """
    Рендерит HTML из шаблона.
    
    Args:
        data: словарь с данными для шаблона
        template_dir: путь к папке с шаблонами (по умолчанию из config)
    """
    tpl_dir = template_dir or str(TEMPLATES_DIR)
    env = Environment(loader=FileSystemLoader(tpl_dir))
    template = env.get_template("base.html")
    # Передаём данные как **kwargs для шаблона
    return template.render(**data)
