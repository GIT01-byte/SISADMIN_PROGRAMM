import tkinter as tk
from tkinter import ttk

from chocoEngine import clear_choco_cache, run_choco_command


def start():
    clear_choco_cache()  # Очищаем кеш Choco

    root = tk.Tk()
    root.title("Программа для установки программ")

    root.geometry("900x355")

    root.eval("tk::PlaceWindow . center")

    root.resizable(True, True)
    # Переводим окно в режим Fullscreen
    root.attributes("-fullscreen", True)

    def close_app():
        root.destroy()
        clear_choco_cache()

    # Кнопка закрытия приложения
    btn_exit = tk.Button(
        root,
        text="Закрыть программу",
        command=close_app,
        bg="red",
        fg="white",
        font=("Arial", 12),
    )
    btn_exit.pack(pady=30)

    # Функция переключения режимов
    def toggle_fullscreen(event=None):
        # Проверяем текущее состояние и меняем на противоположное
        current_state = root.attributes("-fullscreen")
        root.attributes("-fullscreen", not current_state)

    # Привязываем клавишу F11 к этой функции
    root.bind("<F11>", toggle_fullscreen)

    # Приветственный текст
    tk.Label(
        root,
        text="Приветствую! Эта программа предназначена для пакетной установки программ",
        font=("Arial", 16),
    ).pack(pady=10)

    tk.Label(
        root,
        text="Windows",
        font=("Arial", 24, "bold"),
    ).pack(pady=10)

    # --- БЛОК КНОПОК ---
    button_frame = tk.Frame(root)
    button_frame.pack(pady=20)

    # Кнопка 1: Базовый соф
    btn_base = tk.Button(
        button_frame,
        text="Установить Базовый софт\n(7-Zip, VLC, Chrome)",
        font=("Arial", 12),
        width=25,
        height=3,
        bd=2,
        relief="groove",
        command=lambda: run_choco_command(
            action="install",
            log_widget=status_label,
            progress_bar=progress_bar,
            packages=["7zip", "vlc", "googlechrome"],
            choco_args=["-y"],
        ),
    )
    btn_base.grid(row=0, column=0, padx=15)

    # Кнопка 2: Софт разработчика
    btn_dev = tk.Button(
        button_frame,
        text="Установить Софт разработчика\n(Git, VS Code, Python)",
        font=("Arial", 12),
        width=25,
        height=3,
        bd=2,
        relief="groove",
        command=lambda: run_choco_command(
            action="install",
            log_widget=status_label,
            progress_bar=progress_bar,
            packages=["git", "vscode", "python"],
            thread_name="Thread-DevSoft",
        ),
    )
    btn_dev.grid(row=0, column=1, padx=15)

    # Кнопка 3: Обновление системы
    btn_upgrade = tk.Button(
        button_frame,
        text="Обновить все программы\n(Очистка системы)",
        font=("Arial", 12),
        width=25,
        height=3,
        bd=2,
        relief="groove",
        command=lambda: run_choco_command(
            action="upgrade",
            log_widget=status_label,
            progress_bar=progress_bar,
            packages=["all"],
            thread_name="Thread-UpgradeAll",
        ),
    )
    btn_upgrade.grid(row=0, column=2, padx=15)

    # --- ЭЛЕМЕНТ ДЛЯ ВЫВОДА ЛОГОВ ---
    # Создаем рамку вокруг логов для красоты
    log_frame = tk.LabelFrame(
        root,
        text=" Статус выполнения и логи ",
        font=("Arial", 12, "italic"),
        padx=15,
        pady=15,
    )
    log_frame.pack(pady=30, fill="x", padx=100)

    # Сам Label, куда транслируются строчки
    status_label = tk.Label(
        log_frame,
        text="Система готова. Выберите действие выше.",
        font=("Courier New", 12),  # Моноширинный шрифт как в консоли
        fg="blue",
        justify="left",
        wraplength=800,  # Автоперенос длинных строк, чтобы не вылезали за экран
    )
    status_label.pack()

    # Прогресс бар, для отображения статуса установки программы
    progress_bar = ttk.Progressbar(
        log_frame,
        orient="horizontal",
        mode="determinate",
    )
    progress_bar.pack(fill="x", anchor="w")
    # -------------------------

    root.mainloop()


if __name__ == "__main__":
    start()
