import tkinter as tk

# Импортируем все три функции для наших кнопок
from installer import install_developer_soft, install_base_soft, upgrade_all_soft


def start():
    root = tk.Tk()
    root.title("Программа для установки программ")

    root.geometry("900x355")

    root.eval("tk::PlaceWindow . center")

    root.resizable(True, True)
    # Переводим окно в режим Fullscreen
    root.attributes("-fullscreen", True)

    def close_app():
        root.destroy()

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

    # Кнопка 1: Базовый софт (передаем status_label через lambda)
    btn_base = tk.Button(
        button_frame,
        text="Установить Базовый софт\n(7-Zip, VLC, Chrome)",
        font=("Arial", 12),
        width=25,
        height=3,
        bd=2,
        relief="groove",
        command=lambda: install_base_soft(status_label),
    )
    btn_base.grid(row=0, column=0, padx=15)

    # Кнопка 2: Софт разработчика (передаем status_label через lambda)
    btn_dev = tk.Button(
        button_frame,
        text="Установить Софт разработчика\n(Git, VS Code, Python)",
        font=("Arial", 12),
        width=25,
        height=3,
        bd=2,
        relief="groove",
        command=lambda: install_developer_soft(status_label),
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
        command=lambda: upgrade_all_soft(status_label),
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
    # -------------------------

    root.mainloop()


if __name__ == "__main__":
    start()
