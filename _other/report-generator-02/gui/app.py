# -*- coding: utf-8 -*-
"""GUI приложение для генерации отчётов."""
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import json
from shutil import copy2
import threading

try:
    from PIL import Image
except ImportError:
    messagebox.showerror("Ошибка", "Установите Pillow: pip install pillow")
    exit(1)

from report-generator.core.report import generate_report
from ..config import TEMPLATES_DIR, get_api_key, set_api_key, load_api_keys
from ..llm.generator import generate_lab_json


class LabReportGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Генератор отчётов лабораторных работ")
        self.root.geometry("900x750")
        self.data = None

        # Переменные для генерации отчёта
        self.json_path = tk.StringVar()
        self.base_info_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.image_width = tk.IntVar(value=500)
        self.images_dir = tk.StringVar()
        self.screenshots_source_dir = tk.StringVar()

        # Переменные для генерации JSON через LLM
        self.lab_file_path = tk.StringVar()
        self.llm_provider = tk.StringVar(value="gemini")
        self.llm_api_key = tk.StringVar()
        self.output_json_path = tk.StringVar()
        # Информация о лабе (извлекается автоматически)
        self.extracted_lab_info = tk.StringVar(value="")

        # Загружаем сохранённые API ключи при запуске
        self.load_api_key_from_config()
        
        self.create_widgets()

    def create_widgets(self):
        # Создаём notebook для вкладок
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Вкладка 1: Генерация JSON через LLM
        tab_llm = ttk.Frame(notebook, padding="10")
        notebook.add(tab_llm, text="🤖 Генерация JSON через AI")
        self.create_llm_tab(tab_llm)

        # Вкладка 2: Генерация HTML отчёта
        tab_report = ttk.Frame(notebook, padding="10")
        notebook.add(tab_report, text="📄 Генерация HTML отчёта")
        self.create_report_tab(tab_report)

    def create_llm_tab(self, parent):
        """Создаёт вкладку для генерации JSON через LLM."""
        main = ttk.Frame(parent)
        main.pack(fill=tk.BOTH, expand=True)

        # Файл методички
        ttk.Label(main, text="Файл методички (PDF/TXT/MD):").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main, textvariable=self.lab_file_path, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(main, text="Обзор...", command=self.browse_lab_file).grid(row=0, column=2, padx=5, pady=5)

        # Провайдер LLM
        ttk.Label(main, text="Провайдер AI:").grid(row=1, column=0, sticky=tk.W, pady=5)
        provider_frame = ttk.Frame(main)
        provider_frame.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Radiobutton(provider_frame, text="Gemini (Google)", variable=self.llm_provider, value="gemini", 
                       command=self.on_provider_change).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(provider_frame, text="Groq", variable=self.llm_provider, value="groq",
                       command=self.on_provider_change).pack(side=tk.LEFT, padx=5)

        # API ключ
        ttk.Label(main, text="API ключ:").grid(row=2, column=0, sticky=tk.W, pady=5)
        api_entry = ttk.Entry(main, textvariable=self.llm_api_key, width=50)
        api_entry.grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(main, text="Загрузить", command=self.load_api_key_from_config).grid(row=2, column=2, padx=5, pady=5)
        ttk.Button(main, text="Сохранить", command=self.save_api_key_to_config).grid(row=2, column=3, padx=5, pady=5)
        ttk.Label(main, text="(ключ сохраняется в .api_keys.json, не коммитится в git)", 
                 font=("TkDefaultFont", 8), foreground="gray").grid(row=3, column=1, sticky=tk.W, padx=5)

        # Информация о лабе (извлекается автоматически)
        ttk.Label(main, text="Информация о лабе:").grid(row=4, column=0, sticky=tk.W, pady=5)
        info_label = ttk.Label(main, textvariable=self.extracted_lab_info, foreground="gray", 
                               font=("TkDefaultFont", 9))
        info_label.grid(row=4, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5)
        ttk.Label(main, text="(номер и тема извлекаются автоматически из файла)", 
                 font=("TkDefaultFont", 8), foreground="gray", style="TLabel").grid(row=5, column=1, sticky=tk.W, padx=5)

        # Выходной JSON
        ttk.Label(main, text="Сохранить JSON в:").grid(row=6, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main, textvariable=self.output_json_path, width=50).grid(row=6, column=1, padx=5, pady=5)
        ttk.Button(main, text="Обзор...", command=self.browse_output_json).grid(row=6, column=2, padx=5, pady=5)

        ttk.Separator(main, orient="horizontal").grid(row=7, column=0, columnspan=3, sticky=tk.EW, pady=10)

        # Кнопка генерации
        ttk.Button(main, text="🚀 Сгенерировать JSON", command=self.generate_json_async).grid(row=8, column=0, columnspan=3, pady=20)

        self.llm_status = ttk.Label(main, text="", foreground="blue")
        self.llm_status.grid(row=9, column=0, columnspan=3, pady=5)

        # Информация о бесплатных API
        info_text = """
💡 Бесплатные API:
• Gemini: https://ai.google.dev/ - 1500 запросов/день бесплатно
• Groq: https://console.groq.com/ - очень быстрый, бесплатный tier
        """
        ttk.Label(main, text=info_text, font=("TkDefaultFont", 8), foreground="gray", justify=tk.LEFT).grid(
            row=10, column=0, columnspan=3, sticky=tk.W, pady=10
        )

    def create_report_tab(self, parent):
        """Создаёт вкладку для генерации HTML отчёта."""
        main = ttk.Frame(parent)
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

        # Папка с изображениями для отчёта
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

    # Методы для вкладки LLM
    def browse_lab_file(self):
        f = filedialog.askopenfilename(
            filetypes=[("Все поддерживаемые", "*.pdf *.txt *.md"), ("PDF", "*.pdf"), ("Текст", "*.txt"), ("Markdown", "*.md")]
        )
        if f:
            self.lab_file_path.set(f)
            # Автоматически предлагаем путь для JSON
            if not self.output_json_path.get():
                base = os.path.splitext(f)[0]
                self.output_json_path.set(base + ".json")
            # Сбрасываем информацию о лабе при выборе нового файла
            self.extracted_lab_info.set("Выберите файл и нажмите 'Сгенерировать JSON' для извлечения информации")

    def on_provider_change(self):
        """Вызывается при смене провайдера - загружает соответствующий ключ."""
        self.load_api_key_from_config()
    
    def load_api_key_from_config(self):
        """Загружает API ключ из config для выбранного провайдера."""
        provider = self.llm_provider.get()
        load_api_keys()  # Обновляем ключи из файла
        api_key = get_api_key(provider)
        if api_key:
            self.llm_api_key.set(api_key)
        else:
            self.llm_api_key.set("")
    
    def save_api_key_to_config(self):
        """Сохраняет API ключ в config."""
        provider = self.llm_provider.get()
        api_key = self.llm_api_key.get().strip()
        if not api_key:
            messagebox.showwarning("Пусто", "Введите API ключ перед сохранением")
            return
        try:
            set_api_key(provider, api_key)
            messagebox.showinfo("Успех", f"API ключ для {provider} сохранён в .api_keys.json")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить ключ: {e}")

    def browse_output_json(self):
        f = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if f:
            self.output_json_path.set(f)

    def generate_json_async(self):
        """Запускает генерацию JSON в отдельном потоке."""
        if not self.lab_file_path.get():
            messagebox.showerror("Ошибка", "Выберите файл методички")
            return
        
        provider = self.llm_provider.get()
        api_key = self.llm_api_key.get().strip() or None
        
        # Если ключ не введён, пробуем загрузить из config
        if not api_key:
            load_api_keys()
            api_key = get_api_key(provider)
        
        if not api_key:
            messagebox.showerror("Ошибка", f"Укажите API ключ для {provider} или сохраните его в настройках")
            return

        self.llm_status.config(text="Генерация... (извлечение информации о лабе и создание JSON)", foreground="blue")
        self.extracted_lab_info.set("Извлечение информации...")
        self.root.update()

        def generate():
            try:
                output_path = self.output_json_path.get().strip() or None
                
                # Номер и тема будут автоматически извлечены из файла
                result = generate_lab_json(
                    lab_file_path=self.lab_file_path.get(),
                    output_json_path=output_path,
                    lab_number=None,  # Автоматическое извлечение
                    lab_theme=None,  # Автоматическое извлечение
                    provider=provider,
                    api_key=api_key,
                )
                
                # Обновляем информацию о лабе
                lab_info = result.get("lab", {})
                lab_num = lab_info.get("number", "?")
                lab_theme = lab_info.get("theme", "не определена")
                info_text = f"Лабораторная работа №{lab_num}: {lab_theme}"
                
                self.root.after(0, lambda: self.extracted_lab_info.set(info_text))
                self.root.after(0, lambda: self.llm_status.config(
                    text=f"✅ JSON сгенерирован: {output_path or 'в памяти'}", foreground="green"
                ))
                self.root.after(0, lambda: messagebox.showinfo("Успех", 
                    f"JSON успешно сгенерирован!\n\n{info_text}\n\n{output_path or 'Результат в памяти'}"))
                
                # Автоматически заполняем путь к JSON в другой вкладке
                if output_path:
                    self.root.after(0, lambda: self.json_path.set(output_path))
            
            except Exception as e:
                error_msg = str(e)
                self.root.after(0, lambda: self.extracted_lab_info.set("Ошибка при извлечении информации"))
                self.root.after(0, lambda: self.llm_status.config(text="❌ Ошибка", foreground="red"))
                self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Не удалось сгенерировать JSON:\n{error_msg}"))

        threading.Thread(target=generate, daemon=True).start()

    # Методы для вкладки генерации отчёта (остаются без изменений)
    def browse_json(self):
        f = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if f:
            self.json_path.set(f)
            base = os.path.splitext(f)[0]
            self.output_path.set(base + ".html")
            parent = os.path.dirname(f)
            default_images = os.path.join(parent, "images")
            if not self.images_dir.get().strip():
                self.images_dir.set(default_images)
            if not self.base_info_path.get().strip():
                for folder in (parent, os.path.join(parent, "..")):
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
        """Копирует скриншоты в папку отчёта, переименовывая в 1.png, 2.png... с обработкой конфликтов."""
        src_dir = self.screenshots_source_dir.get()
        if not src_dir or not os.path.isdir(src_dir):
            messagebox.showerror("Ошибка", "Выберите папку «Подготовить скриншоты из»")
            return

        dest_dir = self.images_dir.get().strip()
        if not dest_dir:
            out = self.output_path.get().strip()
            j = self.json_path.get().strip()
            if out and out.endswith(".html"):
                base_dir = os.path.dirname(out)
            elif j:
                base_dir = os.path.dirname(j)
            else:
                base_dir = os.path.dirname(src_dir)
            dest_dir = os.path.join(base_dir, "report_images")
            self.images_dir.set(dest_dir)

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
        skipped = 0
        for i, src_path in enumerate(files, start=1):
            ext = os.path.splitext(src_path)[1].lower()
            dest_name = f"{i}{ext}"
            dest_path = os.path.join(dest_dir, dest_name)
            
            if os.path.exists(dest_path):
                base_name = str(i)
                counter = 1
                while os.path.exists(dest_path):
                    dest_name = f"{base_name}_{counter}{ext}"
                    dest_path = os.path.join(dest_dir, dest_name)
                    counter += 1
                skipped += 1
            
            try:
                copy2(src_path, dest_path)
                copied += 1
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось скопировать {src_path}: {e}")
                return

        msg = f"Скопировано {copied} файлов в:\n{dest_dir}"
        if skipped > 0:
            msg += f"\n\n⚠️ {skipped} файлов переименовано из-за конфликтов имён"
        messagebox.showinfo("Успех", msg)

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
        
        if not os.path.isdir(str(TEMPLATES_DIR)):
            messagebox.showerror("Ошибка", f"Папка шаблонов не найдена: {TEMPLATES_DIR}")
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
