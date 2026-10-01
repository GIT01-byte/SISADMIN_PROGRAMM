import os
import sys
import subprocess
import threading
from tkinter import Label, ttk
from typing import List, Optional
import shutil

import logging
import traceback

# =====================================================================
# НАСТРОЙКА КЛАССИЧЕСКОГО ЛОГИРОВАНИЯ В ФАЙЛ
# =====================================================================
# Файл app_debug.log будет создаваться в папке запуска приложения
log_file_path = os.path.join(os.path.abspath("."), "app_debug.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(threadName)s) %(message)s",
    handlers=[
        logging.FileHandler(log_file_path, encoding="utf-8", mode="a"),
        logging.StreamHandler(sys.stdout),  # Также дублируем логи в консоль для IDE
    ],
)

logging.info("=== Запуск нового сеанса менеджера пакетов ===")
logging.info(f"Путь к файлу логов: {log_file_path}")


def _get_choco_exe_path() -> str:
    """Находит точный путь к choco.exe с учетом режима запуска (EXE или разработка)"""
    try:
        # Режим сборки PyInstaller (.exe)
        base_path = sys._MEIPASS  # type: ignore
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
    choco_exe_path = raw_path.replace("\\", "/")

    logging.debug(f"Сформирован целевой путь к choco.exe: {choco_exe_path}")
    return choco_exe_path


def _get_choco_cache_path() -> str | None:
    """Находит точный путь к choco.exe с учетом режима запуска (EXE или разработка)"""
    try:
        # Режим сборки PyInstaller (.exe)
        base_path = sys._MEIPASS  # type: ignore
        logging.debug(f"Обнаружена сборка PyInstaller. Временный путь: {base_path}")

        # В скомпилированном виде ищем сразу в корне временной папки
        raw_path = os.path.join(base_path, "choco_files", ".chocolatey")
    except AttributeError:
        # Режим локальной разработки (исходный код .py)
        base_path = os.path.abspath(".")
        logging.debug(f"Запуск в режиме исходного кода. Базовый путь: {base_path}")

        # Для разработки добавляем промежуточную папку "app"
        raw_path = os.path.join(base_path, "app", "choco_files", ".chocolatey")

    # Принудительно меняем все обратные слэши на прямые
    choco_cache_path = raw_path.replace("\\", "/")

    if os.path.exists(choco_cache_path):
        logging.debug(f"Сформирован целевой путь к choco cache: {choco_cache_path}")
        return choco_cache_path

    logging.debug(f"Директорию кеша choco не существует: {choco_cache_path}")
    return None


def _run_choco_with_logs(
    command_args, log_widget: Label, progress_bar: ttk.Progressbar
):
    """Фоновый запуск локального Choco с расширенным выводом логов на экран и детальной записью в файл."""
    current_thread_name = threading.current_thread().name
    logging.info(
        f"Инициализация фонового потока {current_thread_name} для обработки Choco."
    )
    logging.info(f"Переданные аргументы для Choco: {command_args}")

    def update_ui_text(text_line: str | None, percent_value: int | None = None):
        """Обновление интерфейса."""
        # Обновляем текст (только если это не мусорный прогресс)
        if text_line:
            log_widget.after(0, lambda: log_widget.config(text=text_line))

        # Обновляем прогресс-бар, если вытащили проценты
        if percent_value is not None:
            log_widget.after(0, lambda: progress_bar.config(value=percent_value))

    try:
        # Сборка путей движка
        choco_path = _get_choco_exe_path()
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
        for line in process.stdout:  # type: ignore
            cleaned_line = line.strip()
            if cleaned_line:
                if "Progress" in cleaned_line and "%" in cleaned_line:
                    try:
                        package_name = cleaned_line

                        percent_str = cleaned_line.split("%")[0].split()[-1]
                        percent_int = int(percent_str)

                        update_ui_text(
                            text_line=package_name, percent_value=percent_int
                        )
                        continue
                    except (ValueError, IndexError):
                        continue

                # На экран выводим только краткую строчку
                update_ui_text(text_line=f"[Choco]: {cleaned_line}", percent_value=0)
                # В текстовый файл пишем абсолютно ВСЁ, что отдает Chocolatey
                logging.info(f"[Choco Engine Output]: {cleaned_line}")

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
            f"Тип исключения: {error_type.__name__}\n"  # type: ignore
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


def run_choco_command(
    action: str,
    log_widget: Label,
    progress_bar: ttk.Progressbar,
    packages: Optional[List[str]] = None,
    choco_args: Optional[List[str]] = None,
    thread_name: str = "ChocoWorker",
) -> threading.Thread:
    """
    Универсальный API-метод: собирает команду Chocolatey и запускает ее в изолированном фоне.

    Функция не блокирует поток UI, занимается только парсингом аргументов и
    возвращает объект созданного потока.
    """
    # 1. Приведение аргументов к безопасным спискам
    packages_list = packages if packages is not None else []
    choco_args_list = choco_args if choco_args is not None else []

    # Защита 1: Автосогласие
    if "-y" not in choco_args_list and "--yes" not in choco_args_list:
        choco_args_list = list(choco_args_list) + ["-y"]

    # Защита 2: Отключаем сбои профилей PowerShell для Portable-режима
    if "--ignore-powershell-home" not in choco_args_list:
        choco_args_list = list(choco_args_list) + ["--ignore-powershell-home"]

    # Собираем итоговый массив для subprocess
    full_command = [action] + packages_list + choco_args_list

    # 3. Инициализация и запуск потока
    choco_thread = threading.Thread(
        target=_run_choco_with_logs,
        args=(full_command, log_widget, progress_bar),
        daemon=True,
        name=thread_name,
    )
    choco_thread.start()

    return choco_thread


def clear_choco_cache(dir_path: str | None = None):
    choco_cache_path = dir_path if dir_path else _get_choco_cache_path()

    if not choco_cache_path or not os.path.exists(choco_cache_path):
        logging.info(
            f"[Cache Remover] Очистка не требуется: путь '{choco_cache_path}' не существует."
        )
        return

    logging.info(
        f"[Cache Remover] Начало удаления кэша Chocolatey по пути: {choco_cache_path}"
    )
    try:
        shutil.rmtree(choco_cache_path)
        logging.info("[Cache Remover] Удаление кэша завершено успешно.")
    except Exception as e:
        logging.error(f"[Cache Remover] Не удалось удалить кэш Chocolatey: {e}")
