import os
import time
import io
import subprocess
import webbrowser
import ctypes
import win32gui
import win32process
import win32con
from PIL import ImageGrab
from dotenv import load_dotenv
from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)

def tail(file_path, n=10):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        return lines[-n:]
    except Exception:
        return []

async def activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_file = os.path.join('agent', 'logs', 'app_launch.log')
    max_apps_to_show = 10  # Количество уникальных приложений для отображения
    recent_unique_apps = []
    seen_apps = set()

    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
    except FileNotFoundError:
        logger.warning(f"Файл логов не найден: {log_file}")
        await update.message.reply_text('Файл логов не найден.')
        return
    except Exception as e:
        logger.error(f"Ошибка при чтении файла логов {log_file}: {e}")
        await update.message.reply_text('Произошла ошибка при чтении логов.')
        return

    if not all_lines:
        await update.message.reply_text('Нет данных об активности в логах.')
        return

    launch_marker = "Процесс запущен: "
    pid_marker = " (PID:"

    for line in reversed(all_lines):
        if len(recent_unique_apps) >= max_apps_to_show:
            break

        start_marker_idx = line.find(launch_marker)
        if start_marker_idx != -1:
            name_start_idx = start_marker_idx + len(launch_marker)
            pid_marker_idx = line.find(pid_marker, name_start_idx)
            if pid_marker_idx != -1:
                app_name = line[name_start_idx:pid_marker_idx].strip()
                if app_name and app_name not in seen_apps:  # убедиться имя приложения не пустое
                    recent_unique_apps.append(app_name)
                    seen_apps.add(app_name)
    
    if not recent_unique_apps:
        await update.message.reply_text('Не найдено информации о запуске приложений в логах.')
        return

    recent_unique_apps.reverse()

    header = '*Последние запущенные уникальные приложения:*'
    formatted_apps = [f'- {app_name}' for app_name in recent_unique_apps]
    msg = '\n'.join([header] + formatted_apps)
    await update.message.reply_text(msg, parse_mode='Markdown')

async def screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    img = ImageGrab.grab()
    bio = io.BytesIO()
    bio.name = 'screenshot.png'
    img.save(bio, 'PNG')
    bio.seek(0)
    await update.message.reply_photo(photo=bio)

def open_video(url: str):
    prog = os.environ.get('ProgramFiles', '')
    chrome = os.path.join(prog, 'Yandex', 'YandexBrowser', 'Application', 'yandexbrowser.exe')
    if os.path.exists(chrome):
        p = subprocess.Popen([chrome, '--new-window', url])
        time.sleep(1)
        bring_to_front(p.pid)
    else:
        webbrowser.open_new(url)

def bring_to_front(pid: int):
    def callback(hwnd, hwnds):
        _, p = win32process.GetWindowThreadProcessId(hwnd)
        if p == pid and win32gui.IsWindowVisible(hwnd):
            hwnds.append(hwnd)
        return True
    hwnds = []
    win32gui.EnumWindows(callback, hwnds)
    if hwnds:
        hwnd = hwnds[0]
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        user32 = ctypes.windll.user32
        user32.SetForegroundWindow(hwnd)

DEFAULT_URL = 'https://www.youtube.com/watch?v=xm3YgoEiEDc&ab_channel=10Hours'

async def rickroll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = context.args[0] if context.args else DEFAULT_URL
    await update.message.reply_text(f'Успешно зарикролен: {url}')
    open_video(url)

async def shutdown_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Выключаю ПК...')
    os.system('shutdown /s /t 1')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # команды в бота
    commands = [
        BotCommand('activity', 'Показать последнюю активность'),
        BotCommand('screenshot', 'Сделать скриншот рабочего стола'),
        BotCommand('rickroll', 'зарикролить'),
        BotCommand('shutdown', 'Выключить ПК')
    ]
    await context.bot.set_my_commands(commands)
    await update.message.reply_text(
        'Доступные команды:\n' +
        '\n'.join(f"/{cmd.command} - {cmd.description}" for cmd in commands)
    )

def main():
    load_dotenv()
    token = os.environ.get('TELEGRAM_TOKEN')
    if not token:
        print('Установите TELEGRAM_TOKEN в файле .env')
        return
    app = ApplicationBuilder().token(token).build()
    app.add_error_handler(error_handler)
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('activity', activity))
    app.add_handler(CommandHandler('screenshot', screenshot))
    app.add_handler(CommandHandler('rickroll', rickroll))
    app.add_handler(CommandHandler('shutdown', shutdown_cmd))


    print('Telegram-бот запущен')
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main() 