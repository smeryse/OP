#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Точка входа: запуск GUI генератора отчётов по лабораторным.
Запускайте из корня проекта: python run.py
"""
import os
import sys

# Корень проекта = папка, где лежит run.py
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Добавляем корень проекта в путь для импорта report_generator
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.chdir(PROJECT_ROOT)

from report_generator.gui import main

if __name__ == "__main__":
    main()
