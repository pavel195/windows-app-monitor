import win32evtlog
import win32evtlogutil
import win32con
import time
import datetime
import logging
from config import CONFIG

# Настройка логирования
logger = logging.getLogger(__name__)

class EventMonitor:
    def __init__(self, callback=None):
        """
        Инициализация монитора событий журнала Windows
        
        Args:
            callback: Функция обратного вызова для обработки событий
        """
        self.log_name = CONFIG['monitoring']['log_name']
        self.check_interval = CONFIG['monitoring']['check_interval']
        self.tracked_apps = CONFIG['monitoring']['tracked_apps']
        self.callback = callback
        self.last_record_number = self._get_last_record_number()
        self.running = False
        
    def _get_last_record_number(self):
        """Получение номера последней записи в журнале"""
        try:
            # Открываем журнал событий только для чтения
            server = None  # Локальный компьютер
            h = win32evtlog.OpenEventLog(server, self.log_name)
            try:
                # Получаем количество записей
                num_records = win32evtlog.GetNumberOfEventLogRecords(h)
                if num_records == 0:
                    return 0
                    
                # Читаем последнюю запись для получения ее номера
                flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
                events = win32evtlog.ReadEventLog(h, flags, 0)
                if events and len(events) > 0:
                    return events[0].RecordNumber
                return 0
            finally:
                if h:
                    try:
                        win32evtlog.CloseEventLog(h)
                    except Exception as e:
                        logger.error(f"Ошибка при закрытии дескриптора журнала: {e}")
        except Exception as e:
            logger.error(f"Ошибка при получении номера последней записи: {e}")
            return 0
    
    def _process_event(self, event):
        """
        Обработка события запуска приложения
        
        Args:
            event: Событие журнала Windows
        """
        # Получаем данные о событии
        try:
            event_category = event.EventCategory
            event_id = event.EventID & 0xFFFF  # Маска для получения ID без флагов
            
            # Получаем имя приложения из сообщения события
            try:
                event_data = win32evtlogutil.SafeFormatMessage(event, self.log_name)
                
                # Проверяем, является ли событие запуском приложения
                # Event ID 1000 часто используется для запуска приложений
                if event_id == 1000:
                    app_name = None
                    
                    # Пытаемся извлечь имя приложения из сообщения
                    if event_data:
                        lines = event_data.split('\n')
                        if len(lines) > 0:
                            # Обычно имя находится в первой строке
                            app_name = lines[0].strip()
                    
                    if not app_name:
                        # Если не удалось извлечь из сообщения, используем SourceName
                        app_name = event.SourceName
                    
                    # Если у нас есть список отслеживаемых приложений и
                    # это приложение не в списке, пропускаем его
                    if self.tracked_apps and app_name not in self.tracked_apps:
                        return
                    
                    # Создаем информацию о событии
                    event_info = {
                        'app_name': app_name,
                        'time': datetime.datetime.fromtimestamp(
                            int(event.TimeGenerated)
                        ).strftime('%Y-%m-%d %H:%M:%S'),
                        'source': event.SourceName,
                        'event_id': event_id,
                        'message': event_data
                    }
                    
                    # Вызываем функцию обратного вызова, если она определена
                    if self.callback:
                        self.callback(event_info)
            except Exception as e:
                logger.error(f"Ошибка при обработке данных события: {e}")
        except Exception as e:
            logger.error(f"Ошибка при обработке события: {e}")
    
    def start_monitoring(self):
        """Запуск мониторинга событий журнала"""
        self.running = True
        logger.info(f"Начинаю мониторинг журнала {self.log_name}...")
        
        try:
            while self.running:
                h = None
                try:
                    # Открываем журнал событий Windows в каждой итерации
                    server = None  # Локальный компьютер
                    flags = win32evtlog.EVENTLOG_FORWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
                    
                    h = win32evtlog.OpenEventLog(server, self.log_name)
                    if not h:
                        logger.error("Не удалось открыть журнал событий")
                        time.sleep(self.check_interval)
                        continue
                    
                    # Получаем все доступные события
                    events = win32evtlog.ReadEventLog(h, flags, 0)
                    
                    if events and len(events) > 0:
                        for event in events:
                            if event.RecordNumber > self.last_record_number:
                                self._process_event(event)
                                self.last_record_number = event.RecordNumber
                except Exception as e:
                    logger.error(f"Ошибка при чтении журнала: {e}")
                finally:
                    # Закрываем дескриптор в каждой итерации
                    if h:
                        try:
                            win32evtlog.CloseEventLog(h)
                        except Exception as e:
                            logger.error(f"Ошибка при закрытии дескриптора журнала: {e}")
                
                # Ждем перед следующей проверкой
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logger.info("Мониторинг прерван пользователем")
        except Exception as e:
            logger.error(f"Критическая ошибка в мониторинге: {e}")
        finally:
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """Остановка мониторинга событий журнала"""
        self.running = False
        logger.info("Мониторинг журнала остановлен") 