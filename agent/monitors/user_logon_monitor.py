import wmi
import time
import pythoncom
from .base_monitor import BaseMonitor

class UserLogonMonitor(BaseMonitor):
    def run(self):
        pythoncom.CoInitialize()
        try:
            c = wmi.WMI()
            watcher = c.watch_for(notification_type='Creation', wmi_class='Win32_LogonSession', delay_secs=1)
        except wmi.x_access_denied as e:
            self.logger.error(f"Доступ запрещён при инициализации WMI : {e}")
            return
        while True:
            try:
                event = watcher()
                instance = event.TargetInstance
                logon_id = instance.LogonId
                logon_type = instance.LogonType
                start_time = instance.StartTime
                self.logger.info(f"Вход пользователя: LogonId={logon_id}, Type={logon_type}, StartTime={start_time}")
            except Exception as e:
                self.logger.error(f"Ошибка в UserLogonMonitor: {e}")
                time.sleep(1) 