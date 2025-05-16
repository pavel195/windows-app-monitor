@echo off
echo Запуск мониторинга событий Windows...
start /B pythonw main.py
echo Мониторинг запущен в фоновом режиме.
echo Для просмотра логов откройте файл app.log
timeout /t 5 