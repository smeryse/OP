#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Точка входа: запуск GUI генератора отчётов по лабораторным.
Запускайте из корня проекта:  python run_report_gui.py
"""
import os
import sys

# Корень проекта = каталог, где лежит этот файл
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SCRIPT_DIR = os.path.join(PROJECT_ROOT, "2. scripts", "script")

if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

os.chdir(PROJECT_ROOT)

from gui import main

if __name__ == "__main__":
    main()
