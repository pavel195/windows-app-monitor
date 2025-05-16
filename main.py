import logging
import threading
import time
import sys
import os
from event_monitor import EventMonitor
from simplest_telegram_bot import SimplestTelegramBot
from config import CONFIG

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def handle_app_launch_event(event_info):
    """
    Обработчик события запуска приложения
    
    Args:
        event_info: Информация о запущенном приложении
    """
    try:
        logger.info(f"Обнаружен запуск приложения: {event_info['app_name']}")
        # Отправка уведомления через Telegram
        telegram_bot.send_app_launch_notification(event_info)
    except Exception as e:
        logger.error(f"Ошибка при обработке события запуска приложения: {e}")

def check_config():
    """Проверка конфигурации перед запуском"""
    # Проверяем, что токен бота задан
    if not CONFIG['telegram']['bot_token']:
        logger.error("Токен Telegram бота не указан. Пожалуйста, добавьте его в .env файл или config.yaml.")
        logger.error("Пример настройки в .env файле: TELEGRAM_BOT_TOKEN=your_token_here")
        return False
    return True

def main():
    try:
        # Проверяем конфигурацию
        if not check_config():
            sys.exit(1)
        
        # Запуск Telegram бота
        global telegram_bot
        telegram_bot = SimplestTelegramBot()
        if not telegram_bot.start_bot():
            logger.error("Не удалось запустить Telegram бота. Проверьте токен.")
            sys.exit(1)
        
        # Запуск монитора событий журнала Windows
        monitor = EventMonitor(callback=handle_app_launch_event)
        
        # Создаем и запускаем поток для монитора событий
        monitor_thread = threading.Thread(target=monitor.start_monitoring)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        logger.info("Приложение запущено. Нажмите Ctrl+C для завершения.")
        
        # Держим главный поток активным
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Получен сигнал завершения работы.")
        finally:
            # Остановка всех компонентов
            monitor.stop_monitoring()
            telegram_bot.stop_bot()
    
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 