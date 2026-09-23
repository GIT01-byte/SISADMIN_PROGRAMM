import os
import sys
import subprocess
import threading
import logging
import traceback
import tkinter as tk

# =====================================================================
# НАСТРОЙКА КЛАССИЧЕСКОГО ЛОГИРОВАНИЯ В ФАЙЛ
# =====================================================================
# Файл app_debug.log будет создаваться в папке запуска приложения
log_file_path = os.path.join(os.path.abspath("."), "app_debug.log")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] (%(threadName)s) %(message)s",
    handlers=[
        logging.FileHandler(log_file_path, encoding="utf-8", mode="a"),
        logging.StreamHandler(sys.stdout),  # Также дублируем логи в консоль для IDE
    ],
)

logging.info("=== Запуск нового сеанса менеджера пакетов ===")
logging.info(f"Путь к файлу логов: {log_file_path}")


def _get_choco_path():
    """Находит точный путь к choco.exe с учетом режима запуска (EXE или разработка)"""
    try:
        # Режим сборки PyInstaller (.exe)
        base_path = sys._MEIPASS
        logging.debug(f"Обнаружена сборка PyInstaller. Временный путь: {base_path}")

        # В скомпилированном виде ищем сразу в корне временной папки
        raw_path = os.path.join(
            base_path, "choco_files", "tools", "chocolateyInstall", "choco.exe"
        )
    except AttributeError:
        # Режим локальной разработки (исходный код .py)
        base_path = os.path.abspath(".")
        logging.debug(f"Запуск в режиме исходного кода. Базовый путь: {base_path}")

        # Для разработки добавляем промежуточную папку "app"
        raw_path = os.path.join(
            base_path, "app", "choco_files", "tools", "chocolateyInstall", "choco.exe"
        )

    # Принудительно меняем все обратные слэши на прямые
    choco_exe = raw_path.replace("\\", "/")

    logging.debug(
        f"Сформирован целевой путь к choco.exe (с прямыми слэшами): {choco_exe}"
    )
    return choco_exe


def _run_choco_with_logs(command_args, log_widget):
    """Фоновый запуск локального Choco с расширенным выводом логов на экран и детальной записью в файл."""
    current_thread_name = threading.current_thread().name
    logging.info(
        f"Инициализация фонового потока {current_thread_name} для обработки Choco."
    )
    logging.info(f"Переданные аргументы для Choco: {command_args}")

    log_lines = ["[Система]: Инициализация локального движка Choco..."]
    MAX_LINES = 12

    def update_ui_text(new_line):
        """Обновление интерфейса."""
        log_lines.append(new_line)
        if len(log_lines) > MAX_LINES:
            log_lines.pop(0)
        full_text = "\n".join(log_lines)
        log_widget.config(text=full_text)
        log_widget.update_idletasks()

    try:
        # Сборка путей движка
        choco_path = _get_choco_path()
        choco_dir = os.path.dirname(os.path.dirname(os.path.dirname(choco_path)))

        if not os.path.exists(choco_path):
            error_msg = f"Файл choco.exe отсутствует по указанному пути: {choco_path}"
            logging.error(error_msg)
            raise FileNotFoundError(error_msg)

        # Перенаправляем домашнюю директорию Choco
        os.environ["ChocolateyInstall"] = choco_dir
        logging.debug(
            f"Переменная среды ChocolateyInstall переопределена на локальную папку: {choco_dir}"
        )

        # Склеиваем команду
        full_command = [choco_path] + command_args
        logging.info(
            f"Полная системная команда на исполнение: {' '.join(full_command)}"
        )

        update_ui_text(f"[Система]: Запуск команды: {' '.join(command_args)}")

        # Запускаем локальный процесс
        logging.debug("Запуск subprocess.Popen для чтения потока stdout.")
        process = subprocess.Popen(
            full_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="cp866",
        )

        # Построчно читаем лог движка
        for line in process.stdout:
            cleaned_line = line.strip()
            if cleaned_line:
                # На экран выводим только краткую строчку
                update_ui_text(f"[Choco]: {cleaned_line}")
                # В текстовый файл пишем абсолютно ВСЁ, что отдает Chocolatey
                logging.debug(f"[Choco Engine Output]: {cleaned_line}")

        process.wait()
        logging.info(
            f"Процесс Choco завершил работу с кодом возврата: {process.returncode}"
        )

        if process.returncode == 0:
            logging.info("Сценарий установки завершился успешно.")
            update_ui_text("\n[Успех]: Операция успешно завершена!")
        else:
            logging.warning(
                f"Сценарий установки вернул код ошибки: {process.returncode}"
            )
            update_ui_text(
                f"\n[Ошибка]: Код сбоя Choco: {process.returncode}. Подробности ищите в файле app_debug.log"
            )

    except Exception as e:
        # Перехватываем полную цепочку вызовов и определяем конкретную строку, вызвавшую падение
        error_type, error_value, error_tb = sys.exc_info()
        # Извлекаем последний кадр стека (где именно упал код)
        summary = traceback.extract_tb(error_tb)[-1]
        line_number = summary.lineno
        func_name = summary.name

        # Строим информативный отчет об ошибке для разработчика
        detailed_error = (
            f"\n=== КРИТИЧЕСКАЯ ОШИБКА ДВИЖКА ===\n"
            f"Тип исключения: {error_type.__name__}\n"
            f"Описание ошибки: {str(e)}\n"
            f"Локация сбоя: файл {os.path.basename(__file__)}, функция '{func_name}', строка {line_number}\n"
            f"Входные аргументы при падении: {command_args}\n"
            f"Полный Traceback сбоя:\n{traceback.format_exc()}"
            f"================================="
        )

        # Пишем развернутый технический дамп в файл лога
        logging.critical(detailed_error)

        # Выводим аккуратную ошибку пользователю в GUI
        log_widget.config(
            text=f"Критическая ошибка движка!\nСбой зафиксирован на строке {line_number}.\nДетали сохранены в файл app_debug.log"
        )


# --- ФУНКЦИИ ДЛЯ КНОПОК ---


def install_base_soft(log_widget):
    """Установка базового софта в фоновом потоке."""
    args = ["install", "7zip", "vlc", "googlechrome", "-y"]
    threading.Thread(
        target=_run_choco_with_logs,
        args=(args, log_widget),
        daemon=True,
        name="Thread-BaseSoft",
    ).start()


def install_developer_soft(log_widget):
    """Установка софта разработчика в фоновом потоке."""
    args = ["install", "git", "vscode", "python", "-y"]
    threading.Thread(
        target=_run_choco_with_logs,
        args=(args, log_widget),
        daemon=True,
        name="Thread-DevSoft",
    ).start()


def upgrade_all_soft(log_widget):
    """Обновление всех программ в фоновом потоке."""
    args = ["upgrade", "all", "-y"]
    threading.Thread(
        target=_run_choco_with_logs,
        args=(args, log_widget),
        daemon=True,
        name="Thread-UpgradeAll",
    ).start()
