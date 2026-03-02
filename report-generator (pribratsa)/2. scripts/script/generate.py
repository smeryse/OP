import json
import os
import base64
from jinja2 import Environment, FileSystemLoader
from PIL import Image
import mimetypes

def image_to_base64(image_path, max_width=800):
    """Конвертирует изображение в base64, сжимая до max_width"""
    try:
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type:
            mime_type = 'image/png'

        with Image.open(image_path) as img:
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

            from io import BytesIO
            buffer = BytesIO()

            if mime_type == 'image/jpeg' and img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            fmt = 'JPEG' if mime_type == 'image/jpeg' else 'PNG'
            img.save(buffer, format=fmt, optimize=True, quality=85)
            img_bytes = buffer.getvalue()

        b64 = base64.b64encode(img_bytes).decode('utf-8')
        return f"data:{mime_type};base64,{b64}"
    except Exception as e:
        print(f"❌ Ошибка конвертации {image_path}: {e}")
        return None

def _resolve_image_path(src_value, images_dir):
    """По src из JSON (например '1.png' или 'images/1.png') возвращает путь к файлу в images_dir."""
    if not src_value or not images_dir:
        return None
    name = os.path.basename(src_value)
    path = os.path.join(images_dir, name)
    return path if os.path.isfile(path) else None


def _replace_fig_refs(text):
    """(Рис. N) и (Рис N) → как показано на Рисунке N."""
    if not text or not isinstance(text, str):
        return text
    text = re.sub(r"\(Рис\.?\s*(\d+)\)", r"как показано на Рисунке \1", text, flags=re.IGNORECASE)
    return text


def _apply_fig_refs_in_data(data):
    """Заменяет ссылки на рисунки в тексте шагов процедуры."""
    procedure = data.get("procedure") if isinstance(data, dict) else None
    if not procedure:
        return
    for step in procedure:
        if isinstance(step, dict) and "text" in step and step["text"]:
            step["text"] = _replace_fig_refs(step["text"])


def process_images_in_data(data, images_dir='images', max_width=800):
    """Заменяет src на base64. images_dir — папка с картинками (1.png, 2.png, ...)."""
    count = 0
    if not images_dir or not os.path.isdir(images_dir):
        return count
    if isinstance(data, dict):
        for key, value in data.items():
            if key == 'src' and isinstance(value, str) and not value.startswith('data:'):
                image_path = _resolve_image_path(value, images_dir)
                if image_path:
                    b64 = image_to_base64(image_path, max_width)
                    if b64:
                        data[key] = b64
                        count += 1
                else:
                    print(f"⚠️  Изображение не найдено: {value} в {images_dir}")
            else:
                count += process_images_in_data(value, images_dir, max_width)
    elif isinstance(data, list):
        for item in data:
            count += process_images_in_data(item, images_dir, max_width)
    return count

def generate_report(
    json_file=None,
    output_file=None,
    max_width=800,
    data=None,
    base_info=None,
    base_info_file=None,
    images_dir="images",
    template_dir=None,
):
    """Генерирует HTML, встраивая изображения через base64.
    images_dir и template_dir — абсолютные или относительные пути (от cwd).
    """
    if data is None:
        if not json_file:
            print("❌ Не указан источник данных")
            return False
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"✅ Загружен JSON: {json_file}")
        except Exception as e:
            print(f"❌ Ошибка загрузки JSON: {e}")
            return False

    # Подмешиваем base_info (универ, студент, преподаватель)
    if base_info_file and os.path.isfile(base_info_file):
        try:
            with open(base_info_file, "r", encoding="utf-8") as f:
                base_info = json.load(f)
        except Exception as e:
            print(f"⚠️ Не удалось загрузить base_info: {e}")
    if base_info:
        for key in ("university", "student", "teacher", "location"):
            if key in base_info and key not in data:
                data[key] = base_info[key]

    # Замена (Рис. N) → как показано на Рисунке N
    _apply_fig_refs_in_data(data)

    if images_dir:
        images_dir = os.path.abspath(images_dir)
    processed = process_images_in_data(data, images_dir=images_dir, max_width=max_width)
    print(f"🖼️  Встроено изображений: {processed}")

    if template_dir is None:
        template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
    template_dir = os.path.abspath(template_dir)
    if not os.path.isdir(template_dir):
        print(f"❌ Папка шаблонов не найдена: {template_dir}")
        return False

    env = Environment(loader=FileSystemLoader(template_dir))
    try:
        template = env.get_template('base.html')
    except Exception as e:
        print(f"❌ Ошибка загрузки шаблона: {e}")
        return False

    try:
        html = template.render(**data)
    except Exception as e:
        print(f"❌ Ошибка рендеринга: {e}")
        return False

    if not output_file:
        output_file = 'report.html'
    out_dir = os.path.dirname(output_file)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    size_kb = os.path.getsize(output_file) / 1024
    print(f"✅ Отчёт сохранён: {output_file} ({size_kb:.2f} КБ)")
    return True

# Для прямого запуска из командной строки (опционально)
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print(
            "Использование: python generate.py data.json [-o output.html] [--width 800] "
            "[--images DIR] [--base-info base_info.json] [--templates DIR]"
        )
        sys.exit(1)
    json_file = sys.argv[1]
    out = None
    width = 800
    images_dir = "images"
    base_info_file = None
    template_dir = None
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "-o" and i + 1 < len(sys.argv):
            out = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--width" and i + 1 < len(sys.argv):
            width = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == "--images" and i + 1 < len(sys.argv):
            images_dir = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--base-info" and i + 1 < len(sys.argv):
            base_info_file = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--templates" and i + 1 < len(sys.argv):
            template_dir = sys.argv[i + 1]
            i += 2
        else:
            i += 1
    generate_report(
        json_file=json_file,
        output_file=out,
        max_width=width,
        images_dir=images_dir,
        base_info_file=base_info_file,
        template_dir=template_dir,
    )