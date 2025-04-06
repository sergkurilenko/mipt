#!/bin/bash
VENV_PATH="/home/sergiusk88/bot/venv/bin/activate"  # Путь к activate виртуального окружения
SCRIPT_DIR="/home/sergiusk88/bot"     # Папка, где лежит Python-скрипт и .env

# Активируем venv
source "$VENV_PATH"

# Переходим в папку со скриптом (чтобы .env загрузился)
cd "$SCRIPT_DIR"

# Запускаем Python-скрипт
python3 loadtodisk.py

# Дективируем venv
deactivate