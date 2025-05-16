import os
import yaml
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Функция для получения списка из строки с разделителями
def get_list_from_env(env_var, separator=','):
    value = os.getenv(env_var, '')
    if not value:
        return []
    return [item.strip() for item in value.split(separator) if item.strip()]

# Функция для получения целочисленного значения из переменных окружения
def get_int_from_env(env_var, default):
    value = os.getenv(env_var)
    if value is None or value == '':
        return default
    try:
        return int(value)
    except ValueError:
        return default

# Получаем список ID пользователей из переменной окружения
allowed_users_str = get_list_from_env('TELEGRAM_ALLOWED_USERS')
allowed_users = [int(user_id) for user_id in allowed_users_str] if allowed_users_str else []

# Получаем ID чата для отправки уведомлений
chat_id = os.getenv('TELEGRAM_CHAT_ID')
if chat_id and chat_id.strip():
    try:
        chat_id = int(chat_id.strip())
    except ValueError:
        # Если chat_id не число (например, @channelname), оставляем как есть
        chat_id = chat_id.strip()
else:
    chat_id = None

# Настройки по умолчанию с учетом переменных окружения
DEFAULT_CONFIG = {
    'telegram': {
        'bot_token': os.getenv('TELEGRAM_BOT_TOKEN', ''),  # Токен Telegram бота
        'allowed_users': allowed_users,  # Список ID пользователей, которым разрешено взаимодействие с ботом
        'chat_id': chat_id,  # ID чата для отправки уведомлений
    },
    'monitoring': {
        'log_name': os.getenv('EVENT_LOG_NAME', 'Application'),  # Имя журнала Windows для мониторинга
        'check_interval': get_int_from_env('CHECK_INTERVAL', 5),  # Интервал проверки журнала (в секундах)
        'tracked_apps': get_list_from_env('TRACKED_APPS'),  # Список приложений для отслеживания, пустой = все
    },
    'video': {
        'url': os.getenv('VIDEO_URL', 'https://www.youtube.com/watch?v=xm3YgoEiEDc&ab_channel=10Hours')  # URL видео по умолчанию
    }
}

CONFIG_FILE = 'config.yaml'

def load_config():
    """Загрузка конфигурации из файла или создание нового файла с настройками по умолчанию"""
    # Приоритет имеют переменные окружения
    config = DEFAULT_CONFIG.copy()
    
    # Если файл существует, объединяем его настройки с настройками из переменных окружения
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as file:
                file_config = yaml.safe_load(file)
                
                # Если в конфигурационном файле есть настройки, которых нет в переменных окружения,
                # используем их
                if file_config:
                    # Для настроек Telegram бота
                    if 'telegram' in file_config:
                        # Если в .env не указан токен, берем из файла
                        if not os.getenv('TELEGRAM_BOT_TOKEN') and 'bot_token' in file_config['telegram']:
                            config['telegram']['bot_token'] = file_config['telegram']['bot_token']
                        
                        # Если в .env не указаны пользователи, берем из файла
                        if not os.getenv('TELEGRAM_ALLOWED_USERS') and 'allowed_users' in file_config['telegram']:
                            config['telegram']['allowed_users'] = file_config['telegram']['allowed_users']
                            
                        # Если в .env не указан chat_id, берем из файла
                        if not os.getenv('TELEGRAM_CHAT_ID') and 'chat_id' in file_config['telegram']:
                            config['telegram']['chat_id'] = file_config['telegram']['chat_id']
                    
                    # Для настроек мониторинга
                    if 'monitoring' in file_config:
                        # Имя журнала
                        if not os.getenv('EVENT_LOG_NAME') and 'log_name' in file_config['monitoring']:
                            config['monitoring']['log_name'] = file_config['monitoring']['log_name']
                        
                        # Интервал проверки
                        if not os.getenv('CHECK_INTERVAL') and 'check_interval' in file_config['monitoring']:
                            config['monitoring']['check_interval'] = file_config['monitoring']['check_interval']
                        
                        # Отслеживаемые приложения
                        if not os.getenv('TRACKED_APPS') and 'tracked_apps' in file_config['monitoring']:
                            config['monitoring']['tracked_apps'] = file_config['monitoring']['tracked_apps']
                    
                    # Для настроек видео
                    if 'video' in file_config and not os.getenv('VIDEO_URL') and 'url' in file_config['video']:
                        config['video']['url'] = file_config['video']['url']
        except Exception as e:
            print(f"Ошибка при чтении файла конфигурации: {e}")
    
    # Сохраняем обновленную конфигурацию в файл
    save_config(config)
    return config

def save_config(config):
    """Сохранение конфигурации в файл"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as file:
            yaml.dump(config, file, default_flow_style=False, allow_unicode=True)
    except Exception as e:
        print(f"Ошибка при сохранении файла конфигурации: {e}")

# Загружаем конфигурацию
CONFIG = load_config() 