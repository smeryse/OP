#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import json
from shutil import copy2

try:
    from PIL import Image
except ImportError:
    messagebox.showerror("Ошибка", "Установите Pillow: pip install pillow")
    exit(1)
try:
    from jinja2 import Environment, FileSystemLoader
except ImportError:
    messagebox.showerror("Ошибка", "Установите Jinja2: pip install jinja2")
    exit(1)

from generate import generate_report

def _script_dir():
    return os.path.dirname(os.path.abspath(__file__))


def _templates_dir():
    return os.path.join(_script_dir(), "..", "templates")


class LabReportGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Генератор отчётов лабораторных работ")
        self.root.geometry("800x620")
        self.data = None

        self.json_path = tk.StringVar()
        self.base_info_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.image_width = tk.IntVar(value=500)
        self.images_dir = tk.StringVar()  # папка с 1.png, 2.png для отчёта
        self.screenshots_source_dir = tk.StringVar()  # откуда копировать при "Подготовить"

        self.create_widgets()

    def create_widgets(self):
        main = ttk.Frame(self.root, padding="10")
        main.pack(fill=tk.BOTH, expand=True)

        # JSON файл
        ttk.Label(main, text="JSON отчёта (лаб.):").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main, textvariable=self.json_path, width=48).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(main, text="Обзор...", command=self.browse_json).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(main, text="Загрузить", command=self.load_json).grid(row=0, column=3, padx=5, pady=5)

        # base_info (опционально)
        ttk.Label(main, text="base_info.json:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main, textvariable=self.base_info_path, width=48).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(main, text="Обзор...", command=self.browse_base_info).grid(row=1, column=2, padx=5, pady=5)
        ttk.Button(main, text="Рядом с JSON", command=self.set_base_info_next_to_json).grid(row=1, column=3, padx=5, pady=5)

        # Выходной HTML
        ttk.Label(main, text="Выходной HTML:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main, textvariable=self.output_path, width=48).grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(main, text="Обзор...", command=self.browse_output).grid(row=2, column=2, padx=5, pady=5)

        # Ширина
        ttk.Label(main, text="Макс. ширина (px):").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main, textvariable=self.image_width, width=10).grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Separator(main, orient="horizontal").grid(row=4, column=0, columnspan=4, sticky=tk.EW, pady=10)

        # Папка с изображениями для отчёта (здесь лежат 1.png, 2.png...)
        ttk.Label(main, text="Папка с картинками отчёта:").grid(row=5, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main, textvariable=self.images_dir, width=48).grid(row=5, column=1, padx=5, pady=5)
        ttk.Button(main, text="Выбрать папку", command=self.browse_images_dir).grid(row=5, column=2, padx=5, pady=5)

        # Подготовка: копировать из другой папки в папку отчёта
        ttk.Label(main, text="Подготовить скриншоты из:").grid(row=6, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main, textvariable=self.screenshots_source_dir, width=48).grid(row=6, column=1, padx=5, pady=5)
        ttk.Button(main, text="Выбрать папку", command=self.browse_screenshots_source).grid(row=6, column=2, padx=5, pady=5)
        ttk.Button(main, text="Скопировать как 1.png, 2.png…", command=self.prepare_screenshots).grid(row=6, column=3, padx=5, pady=5)

        ttk.Separator(main, orient="horizontal").grid(row=7, column=0, columnspan=4, sticky=tk.EW, pady=10)

        # Генерация
        ttk.Button(main, text="Сгенерировать отчёт", command=self.generate).grid(row=8, column=0, columnspan=4, pady=20)

        self.status = ttk.Label(main, text="", foreground="blue")
        self.status.grid(row=9, column=0, columnspan=4, pady=5)

    def browse_json(self):
        f = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if f:
            self.json_path.set(f)
            base = os.path.splitext(f)[0]
            self.output_path.set(base + ".html")
            # Папка с картинками по умолчанию — рядом с JSON, подпапка images
            parent = os.path.dirname(f)
            default_images = os.path.join(parent, "images")
            if not self.images_dir.get().strip():
                self.images_dir.set(default_images)
            if not self.base_info_path.get().strip():
                # Сначала рядом с JSON, потом на уровень выше (например 3. data/base_info.json)
                for folder in (os.path.dirname(f), os.path.join(os.path.dirname(f), "..")):
                    candidate = os.path.normpath(os.path.join(folder, "base_info.json"))
                    if os.path.isfile(candidate):
                        self.base_info_path.set(candidate)
                        break

    def browse_base_info(self):
        f = filedialog.askopenfilename(
            title="Файл base_info.json (универ, студент, преподаватель)",
            filetypes=[("JSON", "*.json")],
        )
        if f:
            self.base_info_path.set(f)

    def set_base_info_next_to_json(self):
        j = self.json_path.get().strip()
        if not j:
            messagebox.showinfo("Подсказка", "Сначала выберите JSON отчёта")
            return
        parent = os.path.dirname(j)
        path = os.path.join(parent, "base_info.json")
        if os.path.isfile(path):
            self.base_info_path.set(path)
        else:
            self.base_info_path.set(path)
            messagebox.showinfo("Подсказка", f"Путь установлен. Создайте файл, если его нет:\n{path}")

    def load_json(self):
        path = self.json_path.get()
        if not path:
            messagebox.showerror("Ошибка", "Укажите JSON файл")
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            messagebox.showinfo("Успех", "JSON загружен")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def browse_output(self):
        f = filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML", "*.html")])
        if f:
            self.output_path.set(f)

    def browse_images_dir(self):
        d = filedialog.askdirectory(title="Папка, где лежат 1.png, 2.png… для отчёта")
        if d:
            self.images_dir.set(d)

    def browse_screenshots_source(self):
        d = filedialog.askdirectory(title="Папка с исходными скриншотами")
        if d:
            self.screenshots_source_dir.set(d)

    def prepare_screenshots(self):
        """Копирует скриншоты из выбранной папки в папку с картинками отчёта, переименовывая в 1,2,3... по времени создания."""
        src_dir = self.screenshots_source_dir.get()
        dest_dir = self.images_dir.get()
        if not src_dir or not os.path.isdir(src_dir):
            messagebox.showerror("Ошибка", "Выберите папку «Подготовить скриншоты из»")
            return
        if not dest_dir:
            messagebox.showerror("Ошибка", "Укажите «Папка с картинками отчёта»")
            return

        exts = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff")
        files = [
            os.path.join(src_dir, f)
            for f in os.listdir(src_dir)
            if f.lower().endswith(exts)
        ]
        if not files:
            messagebox.showerror("Ошибка", "В папке нет изображений")
            return

        files.sort(key=lambda x: os.path.getmtime(x))
        os.makedirs(dest_dir, exist_ok=True)

        copied = 0
        for i, src_path in enumerate(files, start=1):
            ext = os.path.splitext(src_path)[1].lower()
            dest_name = f"{i}{ext}"
            dest_path = os.path.join(dest_dir, dest_name)
            try:
                copy2(src_path, dest_path)
                copied += 1
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось скопировать {src_path}: {e}")
                return

        messagebox.showinfo(
            "Успех",
            f"Скопировано {copied} файлов в папку отчёта.\n{dest_dir}",
        )

    def generate(self):
        if not self.data:
            messagebox.showerror("Ошибка", "Нет данных – загрузите JSON")
            return
        out = self.output_path.get()
        if not out:
            messagebox.showerror("Ошибка", "Укажите выходной файл")
            return
        width = self.image_width.get()
        if width <= 0:
            messagebox.showerror("Ошибка", "Ширина должна быть > 0")
            return
        if not os.path.isdir(_templates_dir()):
            messagebox.showerror("Ошибка", f"Папка шаблонов не найдена: {_templates_dir()}")
            return

        self.status.config(text="Генерация...", foreground="blue")
        self.root.update()

        base_info = self.base_info_path.get().strip() or None
        if base_info and not os.path.isfile(base_info):
            base_info = None
        images_dir = self.images_dir.get().strip() or None
        if images_dir and not os.path.isdir(images_dir):
            images_dir = None

        try:
            ok = generate_report(
                output_file=out,
                max_width=width,
                data=self.data,
                base_info_file=base_info,
                images_dir=images_dir,
                template_dir=_templates_dir(),
            )
            if ok:
                self.status.config(text=f"✅ Отчёт готов: {out}", foreground="green")
                messagebox.showinfo("Успех", f"Отчёт сохранён:\n{out}")
            else:
                self.status.config(text="❌ Ошибка при генерации", foreground="red")
        except Exception as e:
            self.status.config(text="❌ Ошибка", foreground="red")
            messagebox.showerror("Ошибка", str(e))

def main():
    root = tk.Tk()
    app = LabReportGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()