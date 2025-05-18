import wmi
import time
import pythoncom
import os
from .base_monitor import BaseMonitor

class ProcessMonitor(BaseMonitor):
    def __init__(self, name: str, logger):
        super().__init__(name, logger)
        self.current_user = os.environ.get('USERNAME', '').lower()
        self.program_files = os.environ.get('ProgramFiles', '').lower()
        self.program_files_x86 = os.environ.get('ProgramFiles(x86)', '').lower()
        self.seen_paths = set()

    def run(self):
        pythoncom.CoInitialize()
        try:
            c = wmi.WMI()
            watcher = c.Win32_ProcessStartTrace.watch_for()
        except wmi.x_access_denied as e:
            self.logger.error(f"Доступ запрещён при инициализации WMI или подписке: {e}")
            return
        while True:
            try:
                event = watcher()
                name = event.ProcessName
                pid = event.ProcessID
                if name.lower() == 'docker.exe':
                    continue
                try:
                    proc_list = c.Win32_Process(ProcessId=pid)
                    if not proc_list:
                        continue
                    proc = proc_list[0]
                    owner_res = proc.GetOwner()
                    if not owner_res or len(owner_res) < 3:
                        continue
                    domain = owner_res[1] or ''
                    user = owner_res[2].lower() if owner_res[2] else ''
                    if user != self.current_user:
                        continue
                    exe_path = proc.ExecutablePath or ''
                    exe_lower = exe_path.lower()
                    allowed = []
                    if self.program_files:
                        allowed.append(self.program_files)
                    if self.program_files_x86:
                        allowed.append(self.program_files_x86)
                    if allowed and not any(exe_lower.startswith(a) for a in allowed):
                        continue
                    if exe_lower in self.seen_paths:
                        continue
                    self.seen_paths.add(exe_lower)
                except Exception as pe:
                    self.logger.error(f"Не удалось получить данные процесса {pid}: {pe}")
                    continue
                self.logger.info(f"Процесс запущен: {name} (PID: {pid}), Пользователь: {user}@{domain}, Путь: {exe_path}")
            except Exception as e:
                self.logger.error(f"Ошибка в ProcessMonitor: {e}")
                time.sleep(1) 