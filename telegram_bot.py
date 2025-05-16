import threading
import webbrowser
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from config import CONFIG

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        """Инициализация Telegram бота"""
        self.token = CONFIG['telegram']['bot_token']
        self.allowed_users = CONFIG['telegram']['allowed_users']
        self.chat_id = CONFIG['telegram']['chat_id']
        self.video_url = CONFIG['video']['url']
        self.application = None
        self.bot_thread = None
        self.loop = None
        
    def start_bot(self):
        """Запуск бота в отдельном потоке"""
        if not self.token:
            logger.error("Токен Telegram бота не указан в конфигурации")
            return False
        
        # Создаем новый event loop для асинхронной работы в отдельном потоке
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # Запускаем бота в отдельном потоке
        self.bot_thread = threading.Thread(target=self._run_bot)
        self.bot_thread.daemon = True
        self.bot_thread.start()
        
        logger.info("Telegram бот запущен")
        return True
    
    def _run_bot(self):
        """Запуск асинхронного бота"""
        asyncio.set_event_loop(self.loop)
        
        # Создаем приложение
        self.application = Application.builder().token(self.token).build()
        
        # Регистрация обработчиков команд
        self.application.add_handler(CommandHandler("start", self._start_command))
        self.application.add_handler(CommandHandler("help", self._help_command))
        self.application.add_handler(CommandHandler("video", self._video_command))
        self.application.add_handler(CallbackQueryHandler(self._button_callback))
        
        # Запускаем бота
        self.application.run_polling(stop_signals=None)
        
    def stop_bot(self):
        """Остановка бота"""
        if self.application and self.loop:
            async def stop_app():
                await self.application.stop()
                await self.application.shutdown()
            
            future = asyncio.run_coroutine_threadsafe(stop_app(), self.loop)
            future.result(timeout=5)  # Ждем до 5 секунд для остановки
            
            logger.info("Telegram бот остановлен")
    
    def _is_user_allowed(self, user_id):
        """Проверка, разрешено ли пользователю взаимодействие с ботом"""
        # Если список разрешенных пользователей пуст, разрешаем всем
        if not self.allowed_users:
            return True
        return user_id in self.allowed_users
    
    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user_id = update.effective_user.id
        if not self._is_user_allowed(user_id):
            await update.message.reply_text("У вас нет доступа к этому боту.")
            return
        
        await update.message.reply_text(
            f"Привет, {update.effective_user.first_name}! Я бот для мониторинга запуска приложений Windows. "
            "Используйте /help для получения списка команд."
        )
    
    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        user_id = update.effective_user.id
        if not self._is_user_allowed(user_id):
            await update.message.reply_text("У вас нет доступа к этому боту.")
            return
        
        await update.message.reply_text(
            "Доступные команды:\n"
            "/start - Начало работы с ботом\n"
            "/help - Список команд\n"
            "/video - Показать кнопку для открытия видео"
        )
    
    async def _video_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /video"""
        user_id = update.effective_user.id
        if not self._is_user_allowed(user_id):
            await update.message.reply_text("У вас нет доступа к этому боту.")
            return
        
        keyboard = [
            [InlineKeyboardButton("Открыть видео в браузере", callback_data='open_video')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Нажмите кнопку, чтобы открыть видео:", reply_markup=reply_markup)
    
    async def _button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатия на кнопку"""
        query = update.callback_query
        user_id = query.from_user.id
        
        if not self._is_user_allowed(user_id):
            await query.answer("У вас нет доступа к этому боту.")
            return
        
        await query.answer()  # Отправляем уведомление о нажатии
        
        if query.data == 'open_video':
            # Открываем URL в браузере на компьютере, где запущен скрипт
            try:
                webbrowser.open(self.video_url)
                await query.edit_message_text(text="Видео открыто в браузере!")
            except Exception as e:
                await query.edit_message_text(text=f"Ошибка при открытии видео: {str(e)}")
    
    def send_app_launch_notification(self, event_info):
        """
        Отправка уведомления о запуске приложения
        
        Args:
            event_info (dict): Информация о событии запуска приложения
        """
        if not self.application or not event_info:
            return
        
        message = (
            f"🚀 Запущено приложение: {event_info['app_name']}\n"
            f"⏰ Время: {event_info['time']}\n"
            f"🔹 Источник: {event_info['source']}"
        )
        
        # Добавляем кнопку для открытия видео
        keyboard = [
            [InlineKeyboardButton("Открыть видео в браузере", callback_data='open_video')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        async def send_message(target_id):
            try:
                await self.application.bot.send_message(
                    chat_id=target_id,
                    text=message,
                    reply_markup=reply_markup
                )
                logger.info(f"Уведомление отправлено в чат {target_id}")
            except Exception as e:
                logger.error(f"Ошибка при отправке сообщения в чат {target_id}: {e}")
        
        # Отправляем сообщения
        if self.loop:
            # Если указан конкретный chat_id, отправляем только туда
            if self.chat_id:
                asyncio.run_coroutine_threadsafe(send_message(self.chat_id), self.loop)
            # Иначе отправляем всем разрешенным пользователям
            elif self.allowed_users:
                for user_id in self.allowed_users:
                    asyncio.run_coroutine_threadsafe(send_message(user_id), self.loop)
            else:
                logger.warning("Не указан chat_id или allowed_users для отправки уведомлений") 