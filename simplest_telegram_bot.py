import requests
import threading
import webbrowser
import time
import logging
from config import CONFIG

# Настройка логирования
logger = logging.getLogger(__name__)

class SimplestTelegramBot:
    def __init__(self):
        """Инициализация простого Telegram бота"""
        self.token = CONFIG['telegram']['bot_token']
        self.allowed_users = CONFIG['telegram']['allowed_users']
        self.chat_id = CONFIG['telegram']['chat_id']
        self.video_url = CONFIG['video']['url']
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.running = False
        self.check_thread = None
        
    def start_bot(self):
        """Запуск простого бота"""
        if not self.token:
            logger.error("Токен Telegram бота не указан в конфигурации")
            return False
        
        try:
            # Проверяем соединение с API Telegram
            response = requests.get(f"{self.base_url}/getMe")
            if response.status_code != 200:
                logger.error(f"Не удалось подключиться к API Telegram: {response.text}")
                return False
            
            bot_info = response.json()
            if not bot_info.get('ok'):
                logger.error(f"Ошибка при получении информации о боте: {bot_info}")
                return False
            
            logger.info(f"Бот {bot_info['result']['username']} успешно подключен")
            
            # Запускаем фоновую проверку новых сообщений
            self.running = True
            self.check_thread = threading.Thread(target=self._check_messages)
            self.check_thread.daemon = True
            self.check_thread.start()
            
            logger.info("Telegram бот запущен")
            return True
        except Exception as e:
            logger.error(f"Ошибка при запуске бота: {e}")
            return False
        
    def stop_bot(self):
        """Остановка бота"""
        self.running = False
        if self.check_thread:
            self.check_thread.join(timeout=2)
        logger.info("Telegram бот остановлен")
        
    def _check_messages(self):
        """Проверка новых сообщений"""
        last_update_id = 0
        
        while self.running:
            try:
                # Получаем обновления
                params = {'offset': last_update_id + 1, 'timeout': 30}
                response = requests.get(f"{self.base_url}/getUpdates", params=params)
                
                if response.status_code == 200:
                    updates = response.json()
                    if updates.get('ok'):
                        results = updates.get('result', [])
                        
                        for update in results:
                            # Обновляем ID последнего сообщения
                            if update.get('update_id', 0) > last_update_id:
                                last_update_id = update.get('update_id')
                            
                            # Обрабатываем сообщение
                            if 'message' in update and 'text' in update['message']:
                                user_id = update['message']['from']['id']
                                
                                # Проверяем, разрешено ли пользователю взаимодействие с ботом
                                if self._is_user_allowed(user_id):
                                    message_text = update['message']['text']
                                    chat_id = update['message']['chat']['id']
                                    
                                    self._process_command(chat_id, message_text)
                            
                            # Обрабатываем callback запросы (от кнопок)
                            if 'callback_query' in update:
                                user_id = update['callback_query']['from']['id']
                                
                                # Проверяем, разрешено ли пользователю взаимодействие с ботом
                                if self._is_user_allowed(user_id):
                                    callback_data = update['callback_query']['data']
                                    callback_id = update['callback_query']['id']
                                    chat_id = update['callback_query']['message']['chat']['id']
                                    message_id = update['callback_query']['message']['message_id']
                                    
                                    self._process_callback(callback_id, chat_id, message_id, callback_data)
            except Exception as e:
                logger.error(f"Ошибка при проверке сообщений: {e}")
            
            # Пауза между проверками
            time.sleep(1)
    
    def _is_user_allowed(self, user_id):
        """Проверка, разрешено ли пользователю взаимодействие с ботом"""
        # Если список разрешенных пользователей пуст, разрешаем всем
        if not self.allowed_users:
            return True
        return user_id in self.allowed_users
    
    def _process_command(self, chat_id, text):
        """Обработка команды от пользователя"""
        if text == '/start':
            self._send_message(chat_id, "Привет! Я бот для мониторинга запуска приложений Windows. Используйте /help для получения списка команд.")
        elif text == '/help':
            self._send_message(chat_id, "Доступные команды:\n/start - Начало работы с ботом\n/help - Список команд\n/video - Показать кнопку для открытия видео")
        elif text == '/video':
            # Отправляем сообщение с кнопкой
            keyboard = {
                'inline_keyboard': [
                    [{'text': 'Открыть видео в браузере', 'callback_data': 'open_video'}]
                ]
            }
            self._send_message(chat_id, "Нажмите кнопку, чтобы открыть видео:", keyboard)
    
    def _process_callback(self, callback_id, chat_id, message_id, callback_data):
        """Обработка нажатия на кнопку"""
        # Отправляем уведомление о нажатии
        requests.post(f"{self.base_url}/answerCallbackQuery", json={'callback_query_id': callback_id})
        
        if callback_data == 'open_video':
            try:
                # Открываем видео в браузере
                webbrowser.open(self.video_url)
                # Обновляем сообщение
                self._edit_message(chat_id, message_id, "Видео открыто в браузере!")
            except Exception as e:
                self._edit_message(chat_id, message_id, f"Ошибка при открытии видео: {str(e)}")
    
    def _send_message(self, chat_id, text, reply_markup=None):
        """Отправка сообщения"""
        try:
            data = {'chat_id': chat_id, 'text': text}
            if reply_markup:
                data['reply_markup'] = reply_markup
            
            response = requests.post(f"{self.base_url}/sendMessage", json=data)
            if response.status_code != 200:
                logger.error(f"Ошибка при отправке сообщения: {response.text}")
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения: {e}")
    
    def _edit_message(self, chat_id, message_id, text, reply_markup=None):
        """Редактирование сообщения"""
        try:
            data = {'chat_id': chat_id, 'message_id': message_id, 'text': text}
            if reply_markup:
                data['reply_markup'] = reply_markup
            
            response = requests.post(f"{self.base_url}/editMessageText", json=data)
            if response.status_code != 200:
                logger.error(f"Ошибка при редактировании сообщения: {response.text}")
        except Exception as e:
            logger.error(f"Ошибка при редактировании сообщения: {e}")
    
    def send_app_launch_notification(self, event_info):
        """
        Отправка уведомления о запуске приложения
        
        Args:
            event_info (dict): Информация о событии запуска приложения
        """
        if not self.running or not event_info:
            return
        
        message = (
            f"🚀 Запущено приложение: {event_info['app_name']}\n"
            f"⏰ Время: {event_info['time']}\n"
            f"🔹 Источник: {event_info['source']}"
        )
        
        # Добавляем кнопку для открытия видео
        keyboard = {
            'inline_keyboard': [
                [{'text': 'Открыть видео в браузере', 'callback_data': 'open_video'}]
            ]
        }
        
        try:
            # Если указан конкретный chat_id, отправляем только туда
            if self.chat_id:
                self._send_message(self.chat_id, message, keyboard)
                logger.info(f"Уведомление отправлено в чат {self.chat_id}")
            # Иначе отправляем всем разрешенным пользователям
            elif self.allowed_users:
                for user_id in self.allowed_users:
                    self._send_message(user_id, message, keyboard)
                    logger.info(f"Уведомление отправлено пользователю {user_id}")
            else:
                logger.warning("Не указан chat_id или allowed_users для отправки уведомлений")
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления: {e}") 