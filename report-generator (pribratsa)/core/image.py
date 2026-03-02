# -*- coding: utf-8 -*-
"""Обработка изображений: конвертация в base64, разрешение путей."""
import os
import re
import base64
from PIL import Image
import mimetypes


def image_to_base64(image_path, max_width=800):
    """Конвертирует изображение в base64, сжимая до max_width."""
    try:
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type:
            mime_type = "image/png"

        with Image.open(image_path) as img:
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

            from io import BytesIO
            buffer = BytesIO()

            if mime_type == "image/jpeg" and img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            fmt = "JPEG" if mime_type == "image/jpeg" else "PNG"
            img.save(buffer, format=fmt, optimize=True, quality=85)
            img_bytes = buffer.getvalue()

        b64 = base64.b64encode(img_bytes).decode("utf-8")
        return f"data:{mime_type};base64,{b64}"
    except Exception as e:
        print(f"Ошибка конвертации {image_path}: {e}")
        return None


def resolve_image_path(src_value, images_dir):
    """По src из JSON (например '1.png' или 'images/1.png') возвращает путь к файлу в images_dir."""
    if not src_value or not images_dir:
        return None
    name = os.path.basename(src_value)
    path = os.path.join(images_dir, name)
    return path if os.path.isfile(path) else None


def process_images_in_data(data, images_dir=None, max_width=800):
    """Заменяет src на base64. images_dir — папка с картинками (1.png, 2.png, ...)."""
    count = 0
    if not images_dir or not os.path.isdir(images_dir):
        return count
    if isinstance(data, dict):
        for key, value in data.items():
            if key == "src" and isinstance(value, str) and not value.startswith("data:"):
                image_path = resolve_image_path(value, images_dir)
                if image_path:
                    b64 = image_to_base64(image_path, max_width)
                    if b64:
                        data[key] = b64
                        count += 1
                else:
                    print(f"Изображение не найдено: {value} в {images_dir}")
            else:
                count += process_images_in_data(value, images_dir, max_width)
    elif isinstance(data, list):
        for item in data:
            count += process_images_in_data(item, images_dir, max_width)
    return count
