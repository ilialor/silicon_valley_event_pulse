#!/bin/bash

# Скрипт для запуска демо-версии системы Silicon Valley Event Pulse

echo "Запуск демо-версии Silicon Valley Event Pulse..."

# Создаем виртуальное окружение, если оно не существует
if [ ! -d "venv" ]; then
    echo "Создание виртуального окружения Python..."
    python3 -m venv venv
fi

# Активируем виртуальное окружение
source venv/bin/activate

# Устанавливаем зависимости
echo "Установка зависимостей..."
pip install -r requirements.txt

# Запускаем бэкенд в фоновом режиме
echo "Запуск бэкенда на порту 8000..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > backend.log 2>&1 &
BACKEND_PID=$!

# Ждем запуска бэкенда
echo "Ожидание запуска бэкенда..."
sleep 5

# Запускаем HTTP-сервер для фронтенда в фоновом режиме
echo "Запуск фронтенда на порту 8080..."
cd $(dirname "$0")
python3 -m http.server 8080 > frontend.log 2>&1 &
FRONTEND_PID=$!

echo "Демо-версия Silicon Valley Event Pulse запущена!"
echo "Бэкенд доступен по адресу: http://localhost:8000"
echo "Фронтенд доступен по адресу: http://localhost:8080"
echo ""
echo "Для остановки демо-версии используйте: kill $BACKEND_PID $FRONTEND_PID"

# Сохраняем PID процессов в файл для последующей остановки
echo "$BACKEND_PID $FRONTEND_PID" > .demo_pids

echo "Открытие фронтенда в браузере..."
if command -v xdg-open > /dev/null; then
    xdg-open http://localhost:8080
elif command -v open > /dev/null; then
    open http://localhost:8080
fi
