# -*- coding: utf-8 -*-
"""Генерация JSON отчёта из методички через LLM."""
import json
import os
from pathlib import Path
from typing import Optional
from .client import create_client, LLMProvider
from .text_extractor import extract_text_from_file, load_lab_prompt


def generate_lab_json(
    lab_file_path: str,
    output_json_path: Optional[str] = None,
    lab_number: Optional[int] = None,
    lab_theme: Optional[str] = None,
    provider: str = "groq",
    api_key: Optional[str] = None,
    prompt_file: Optional[str] = None,
) -> dict:
    """
    Генерирует JSON отчёт из файла методички.
    
    Args:
        lab_file_path: путь к файлу методички (PDF, TXT, MD)
        output_json_path: путь для сохранения JSON (если None, создаётся рядом с исходным файлом)
        lab_number: номер лабораторной работы (если None, извлекается из текста)
        lab_theme: тема лабораторной работы (если None, извлекается из текста)
        provider: провайдер LLM ("gemini", "groq", "openai")
        api_key: API ключ (если None, берётся из config)
        prompt_file: путь к файлу с промптом (если None, используется по умолчанию)
    
    Returns:
        Словарь с данными отчёта
    """
    print(f"📄 Извлечение текста из {lab_file_path}...")
    lab_text = extract_text_from_file(lab_file_path)
    print(f"✅ Извлечено {len(lab_text)} символов")
    
    print(f"📝 Загрузка промпта...")
    lab_prompt = load_lab_prompt(prompt_file)
    
    print(f"🤖 Генерация JSON через {provider}...")
    
    # Временный костыль - получение промпта из файла для самостоятельной генерации отчёта
    path = Path(f"3. data/lab{lab_number}/prompt.txt")
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(lab_prompt, encoding="utf-8")

    client = create_client(provider, api_key)
    
    # Номер и тема будут автоматически извлечены из текста, если не указаны
    # Это происходит внутри generate_json_from_text
    
    try:
        result = client.generate_json_from_text(
            lab_text=lab_text,
            lab_prompt=lab_prompt,
            lab_number=lab_number,
            lab_theme=lab_theme,
        )
        print("✅ JSON успешно сгенерирован")
        
        # Сохраняем результат
        if output_json_path:
            os.makedirs(os.path.dirname(output_json_path) or ".", exist_ok=True)
            with open(output_json_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"💾 Сохранено в {output_json_path}")
        
        return result
    
    except Exception as e:
        print(f"❌ Ошибка генерации: {e}")
        raise
