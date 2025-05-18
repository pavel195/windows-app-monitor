#!/usr/bin/env python3
import os
import sys
import ctypes
import time
from .logger import LoggerFactory
from .monitors.process_monitor import ProcessMonitor
from .monitors.user_logon_monitor import UserLogonMonitor


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() == 1
    except Exception:
        return False


def main():
    if not is_admin():
        print("Требуются права администратора для работы с WMI. Запуск от имени администратора.")
        sys.exit(1)
    base_dir = os.path.dirname(__file__)
    log_dir = os.path.join(base_dir, 'logs')
    factory = LoggerFactory(log_dir)
    process_logger = factory.get_logger('app_launch', 'app_launch.log')
    user_logger = factory.get_logger('user_login', 'user_login.log')

    monitors = [
        ProcessMonitor(name='ProcessMonitor', logger=process_logger),
        UserLogonMonitor(name='UserLogonMonitor', logger=user_logger)
    ]
    for monitor in monitors:
        monitor.start()

    print("Сбор логов запущен. Ctrl+C для остановки.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Сбор логов остановлен.")


if __name__ == '__main__':
    main() 