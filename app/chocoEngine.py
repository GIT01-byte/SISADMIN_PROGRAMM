import os
import sys
import subprocess
import threading


def get_choco_path():
    """Определяет, где находится choco.exe (работает и в коде, и внутри собранного .exe)"""
    try:
        # Папка, куда PyInstaller распакует файлы во время работы
        base_path = sys._MEIPASS
    except AttributeError:
        # Путь при обычном запуске скрипта main.py
        base_path = os.path.abspath(".")

    return os.path.join(base_path, "choco_files", "choco.exe")


def install_package_async(package_name, log_callback):
    """Запуск установки в фоновом потоке, чтобы GUI не зависал"""

    def run():
        choco_path = get_choco_path()

        # Важно: принудительно отключаем глобальные папки Choco,
        # чтобы он работал локально и изолированно
        os.environ["ChocolateyInstall"] = os.path.dirname(choco_path)

        # Формируем команду: локальный choco + установка + автосогласие
        command = [choco_path, "install", package_name, "-y"]

        try:
            log_callback(f"[Система]: Запуск установки {package_name}...\n")

            # Запускаем процесс и перехватываем логи
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="cp866",  # Корректный вывод кириллицы в Windows
            )

            # Читаем лог Choco в реальном времени
            for line in process.stdout:
                log_callback(line)

            process.wait()

            if process.returncode == 0:
                log_callback(f"\n[Успех]: {package_name} успешно установлен!\n")
            else:
                log_callback(f"\n[Ошибка]: Код сбоя {process.returncode}\n")

        except Exception as e:
            log_callback(f"[Критическая ошибка]: {str(e)}\n")

    # Переносим выполнение в отдельный поток
    threading.Thread(target=run, daemon=True).start()
