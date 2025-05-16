@echo off
echo Запуск с правами администратора...

:: Проверяем, запущен ли скрипт с правами администратора
NET SESSION >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Запуск с правами администратора...
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

:: Выполняем дальнейшие действия с правами администратора
cd /d "%~dp0"
echo Настройка доступа к журналу событий...

:: Запуск основного приложения
echo Запуск приложения мониторинга...
python main.py

pause 