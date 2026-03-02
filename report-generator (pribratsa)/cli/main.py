# -*- coding: utf-8 -*-
"""CLI интерфейс для генерации отчётов."""
import argparse
import os
from report_generator.core.report import generate_report
from report_generator.io.paths import get_lab_json_path
from report_generator.config import DATA_DIR


def main():
    parser = argparse.ArgumentParser(description="Генератор отчётов по лабораторным работам")
    parser.add_argument("--lab", type=int, help="Номер лабораторной работы")
    parser.add_argument("--json", type=str, help="Путь к JSON файлу с данными лабы")
    parser.add_argument("-o", "--output", type=str, help="Выходной HTML файл")
    parser.add_argument("--base-info", type=str, help="Путь к base_info.json")
    parser.add_argument("--images", type=str, help="Папка с изображениями")
    parser.add_argument("--width", type=int, default=500, help="Максимальная ширина изображений (px)")
    
    args = parser.parse_args()

    if not args.lab and not args.json:
        parser.error("Укажите либо --lab <номер>, либо --json <путь>")

    if args.lab:
        json_file = str(get_lab_json_path(args.lab))
        if not os.path.isfile(json_file):
            print(f"Ошибка: файл не найден: {json_file}")
            return
        if not args.output:
            args.output = f"lab{args.lab}.html"
        if not args.base_info:
            base_info_candidate = str(DATA_DIR / "base_info.json")
            if os.path.isfile(base_info_candidate):
                args.base_info = base_info_candidate
    else:
        json_file = args.json
        if not args.output:
            args.output = os.path.splitext(json_file)[0] + ".html"

    generate_report(
        json_file=json_file,
        output_file=args.output,
        max_width=args.width,
        base_info_file=args.base_info,
        images_dir=args.images,
    )


if __name__ == "__main__":
    main()
