# -*- coding: utf-8 -*-
"""Клиент для работы с различными LLM API."""
import json
from typing import Optional, Dict, Any, Tuple
from enum import Enum
from ..config import get_api_key


class LLMProvider(Enum):
    """Поддерживаемые провайдеры LLM."""
    GEMINI = "gemini"
    GROQ = "groq"
    OPENAI = "openai"  # для совместимости


class LLMClient:
    """Универсальный клиент для работы с LLM API."""
    
    def __init__(self, provider: LLMProvider = LLMProvider.GEMINI, api_key: Optional[str] = None):
        self.provider = provider
        # Используем переданный ключ, или из config, или None
        self.api_key = api_key or get_api_key(provider.value)
        self.client = self._init_client()
    
    def _init_client(self):
        """Инициализирует клиент для выбранного провайдера."""
        if self.provider == LLMProvider.GEMINI:
            try:
                import google.generativeai as genai
                if not self.api_key:
                    raise ValueError("GEMINI_API_KEY не установлен. Получите ключ на https://ai.google.dev/")
                genai.configure(api_key=self.api_key)
                return genai.GenerativeModel('gemini-2.0-flash-exp')
            except ImportError:
                raise ImportError("Установите google-generativeai: pip install google-generativeai")
        
        elif self.provider == LLMProvider.GROQ:
            try:
                from groq import Groq
                if not self.api_key:
                    raise ValueError("GROQ_API_KEY не установлен. Получите ключ на https://console.groq.com/")
                return Groq(api_key=self.api_key)
            except ImportError:
                raise ImportError("Установите groq: pip install groq")
        
        elif self.provider == LLMProvider.OPENAI:
            try:
                from openai import OpenAI
                if not self.api_key:
                    raise ValueError("OPENAI_API_KEY не установлен")
                return OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError("Установите openai: pip install openai")
        
        else:
            raise ValueError(f"Неподдерживаемый провайдер: {self.provider}")
    
    def extract_lab_info(self, lab_text: str) -> Tuple[Optional[int], Optional[str]]:
        """
        Извлекает номер и тему лабораторной работы из текста методички.
        
        Args:
            lab_text: текст методички
        
        Returns:
            Кортеж (номер_лабы, тема) или (None, None) если не удалось определить
        """
        prompt = f"""Проанализируй текст методички лабораторной работы и определи:
1. Номер лабораторной работы (только число, например 3)
2. Тему лабораторной работы (краткое название)

Ответь ТОЛЬКО валидным JSON в формате:
{{"number": <номер или null>, "theme": "<тема или null>"}}

Текст методички:
{lab_text[:2000]}"""

        try:
            if self.provider == LLMProvider.GEMINI:
                response = self.client.generate_content(prompt)
                text = response.text.strip()
            elif self.provider == LLMProvider.GROQ:
                response = self.client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
                text = response.choices[0].message.content.strip()
            else:
                return None, None
            
            # Убираем markdown разметку если есть
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            data = json.loads(text)
            lab_number = data.get("number")
            lab_theme = data.get("theme")
            
            # Преобразуем номер в int если он есть
            if lab_number is not None:
                try:
                    lab_number = int(lab_number)
                except (ValueError, TypeError):
                    lab_number = None
            
            return lab_number, lab_theme
        
        except Exception as e:
            print(f"⚠️ Не удалось извлечь информацию о лабе: {e}")
            return None, None
    
    def generate_json_from_text(
        self,
        lab_text: str,
        lab_prompt: str,
        lab_number: Optional[int] = None,
        lab_theme: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Генерирует JSON отчёта из текста методички.
        
        Args:
            lab_text: текст методички лабораторной работы
            lab_prompt: промпт с инструкциями по форматированию
            lab_number: номер лабораторной работы (опционально, если None - извлекается из текста)
            lab_theme: тема лабораторной работы (опционально, если None - извлекается из текста)
        
        Returns:
            Словарь с данными отчёта в формате JSON
        """
        # Если номер или тема не указаны, пытаемся извлечь из текста
        if lab_number is None or lab_theme is None:
            extracted_number, extracted_theme = self.extract_lab_info(lab_text)
            if lab_number is None:
                lab_number = extracted_number
            if lab_theme is None:
                lab_theme = extracted_theme
        
        # Формируем полный промпт
        lab_info = ""
        if lab_number:
            lab_info += f"Номер лабораторной работы: {lab_number}\n"
        if lab_theme:
            lab_info += f"Тема: {lab_theme}\n"
        
        system_prompt = f"""Ты помощник для генерации отчётов по лабораторным работам.
Твоя задача — проанализировать текст методички и создать структурированный JSON отчёт.

{lab_info}

{lab_prompt}

ВАЖНО: Ответь ТОЛЬКО валидным JSON без дополнительного текста, комментариев или markdown разметки.
JSON должен содержать следующие поля:
- lab: {{"number": <номер>, "discipline": "Операционные системы", "theme": "<тема>"}}
- goals: "<цель работы>"
- procedure: [{{"text": "<текст шага>", "images": [{{"number": <N>, "src": "images/<N>.png", "caption": "<описание>"}}]}}]
- questions: [{{"question": "<вопрос>", "answer": "<ответ>"}}]
- conclusion: "<вывод>"

Если номер лабы указан выше, используй его. Если тема указана, используй её.
Все поля обязательны, кроме questions (может быть пустым массивом [])."""

        user_prompt = f"""Текст методички лабораторной работы:

{lab_text}

Создай JSON отчёт по этой методичке, следуя инструкциям выше."""

        if self.provider == LLMProvider.GEMINI:
            return self._generate_with_gemini(system_prompt, user_prompt)
        elif self.provider == LLMProvider.GROQ:
            return self._generate_with_groq(system_prompt, user_prompt)
        elif self.provider == LLMProvider.OPENAI:
            return self._generate_with_openai(system_prompt, user_prompt)
        else:
            raise ValueError(f"Генерация для {self.provider} не реализована")
    
    def _generate_with_gemini(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Генерация через Gemini API."""
        try:
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            response = self.client.generate_content(full_prompt)
            text = response.text.strip()
            
            # Убираем markdown разметку если есть
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Не удалось распарсить JSON от Gemini: {e}\nОтвет: {text[:500]}")
        except Exception as e:
            raise RuntimeError(f"Ошибка при запросе к Gemini API: {e}")
    
    def _generate_with_groq(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Генерация через Groq API."""
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            text = response.choices[0].message.content.strip()
            return json.loads(text)
        except json.JSONDecodeError as e:
            text = response.choices[0].message.content.strip() if 'response' in locals() else "Не получен"
            raise ValueError(f"Не удалось распарсить JSON от Groq: {e}\nОтвет: {text[:500]}")
        except Exception as e:
            raise RuntimeError(f"Ошибка при запросе к Groq API: {e}")
    
    def _generate_with_openai(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Генерация через OpenAI API."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # более дешёвая модель
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            text = response.choices[0].message.content.strip()
            return json.loads(text)
        except json.JSONDecodeError as e:
            text = response.choices[0].message.content.strip() if 'response' in locals() else "Не получен"
            raise ValueError(f"Не удалось распарсить JSON от OpenAI: {e}\nОтвет: {text[:500]}")
        except Exception as e:
            raise RuntimeError(f"Ошибка при запросе к OpenAI API: {e}")


def create_client(provider_name: str = "gemini", api_key: Optional[str] = None) -> LLMClient:
    """Создаёт клиент для указанного провайдера."""
    provider_map = {
        "gemini": LLMProvider.GEMINI,
        "groq": LLMProvider.GROQ,
        "openai": LLMProvider.OPENAI,
    }
    provider = provider_map.get(provider_name.lower(), LLMProvider.GEMINI)
    return LLMClient(provider=provider, api_key=api_key)
