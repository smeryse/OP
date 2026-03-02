# -*- coding: utf-8 -*-
"""Извлечение текста из PDF и других форматов."""
import os
from typing import Optional


def extract_text_from_file(file_path: str) -> str:
    """
    Извлекает текст из файла (PDF, TXT, MD).
    
    Args:
        file_path: путь к файлу
    
    Returns:
        Текст из файла
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == ".txt" or ext == ".md":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    
    elif ext == ".pdf":
        return extract_text_from_pdf(file_path)
    
    else:
        raise ValueError(f"Неподдерживаемый формат файла: {ext}")


def extract_text_from_pdf(pdf_path: str) -> str:
    """Извлекает текст из PDF файла."""
    try:
        import PyPDF2
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text_parts = []
            for page in reader.pages:
                text_parts.append(page.extract_text())
            return "\n".join(text_parts)
    except ImportError:
        try:
            # Альтернатива через pdfplumber (лучше работает с таблицами)
            import pdfplumber
            text_parts = []
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
            return "\n".join(text_parts)
        except ImportError:
            raise ImportError(
                "Для работы с PDF установите одну из библиотек:\n"
                "  pip install PyPDF2\n"
                "  или\n"
                "  pip install pdfplumber"
            )


def load_lab_prompt(prompt_path: Optional[str] = None) -> str:
    """Загружает промпт для генерации отчёта."""
    if prompt_path and os.path.isfile(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    
    # Пробуем найти по умолчанию
    default_paths = [
        "2. scripts/lab_prompt.txt",
        os.path.join(os.path.dirname(__file__), "..", "..", "2. scripts", "lab_prompt.txt"),
    ]
    
    for path in default_paths:
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
    
    # Возвращаем базовый промпт если файл не найден
    return """Ты должен составить отчёт по лабораторной работе, описывая каждый выполненный шаг.
Отчет должен быть строгим и формальным.

Формат JSON:
- lab: {number: <номер>, discipline: "Операционные системы", theme: "<тема>"}
- goals: "<цель работы>"
- procedure: [{text: "<текст шага>", images: [{number: <N>, src: "images/<N>.png", caption: "<описание>"}}]}]
- questions: [{question: "<вопрос>", answer: "<ответ>"}]
- conclusion: "<вывод>"

В тексте шагов используй формат "как показано на рисунке N" для ссылок на рисунки."""
