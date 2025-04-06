#!/usr/bin/env python
import logging
import csv
import os
from datetime import datetime
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import requests
from dotenv import load_dotenv
import psycopg2

# Загружаем переменные окружения
load_dotenv()

# Конфигурация
folder_id = os.getenv("FOLDER_ID")
OAUTH_TOKEN = os.getenv("OAUTH_TOKEN")
APP_TOKEN = os.getenv("APP_TOKEN")
CSV_FILE = "user_actions.csv"

# PostgreSQL конфигурация
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


# ================== Функции для работы с CSV ==================
def init_csv():
    """Инициализация CSV файла с заголовками"""
    try:
        with open(CSV_FILE, 'x', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["user_id", "timestamp", "action"])
        logger.info("CSV файл инициализирован")
    except FileExistsError:
        pass


def log_to_csv(user_id: int, action: str):
    """Логирование действия пользователя в CSV файл"""
    timestamp = datetime.now().strftime("%d.%m.%Y %H.%M.%S")
    try:
        with open(CSV_FILE, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([user_id, timestamp, action])
    except Exception as e:
        logger.error(f"Ошибка записи в CSV: {e}")


# ================== Функции для работы с PostgreSQL ==================
def init_postgres():
    """Инициализация таблицы в PostgreSQL"""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_actions (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                action_time TIMESTAMP NOT NULL,
                action_text TEXT NOT NULL
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Таблица PostgreSQL инициализирована")
    except Exception as e:
        logger.error(f"Ошибка инициализации PostgreSQL: {e}")


def log_to_postgres(user_id: int, action: str):
    """Логирование действия пользователя в PostgreSQL"""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO user_actions (user_id, action_time, action_text) VALUES (%s, %s, %s)",
            (user_id, datetime.now(), action)
        )

        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"Ошибка записи в PostgreSQL: {e}")


# ================== Общая функция логирования ==================
def log_user_action(user_id: int, action: str):
    """Логирование действия пользователя в оба хранилища"""
    log_to_csv(user_id, action)
    log_to_postgres(user_id, action)


# ================== Функции YandexGPT ==================
def get_iam_token():
    """Получение IAM токена для Yandex Cloud"""
    response = requests.post(
        'https://iam.api.cloud.yandex.net/iam/v1/tokens',
        json={'yandexPassportOauthToken': OAUTH_TOKEN}
    )
    response.raise_for_status()
    return response.json()['iamToken']


# ================== Обработчики команд Telegram ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user = update.effective_user
    log_user_action(user.id, "start")
    await update.message.reply_html(
        rf"Привет {user.mention_html()}! Я бот с интеграцией YandexGPT.",
        reply_markup=ForceReply(selective=True),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    log_user_action(update.effective_user.id, "help")
    await update.message.reply_text("Домашняя работа студента Куриленко С.")


async def process_message(update: Update, context) -> None:
    """Обработка текстовых сообщений с интеграцией YandexGPT"""
    user_text = update.message.text
    user = update.effective_user

    # Логируем вопрос пользователя
    log_user_action(user.id, f"Вопрос: {user_text[:200]}")  # Ограничиваем длину

    try:
        # Получаем ответ от YandexGPT
        iam_token = get_iam_token()

        response = requests.post(
            "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {iam_token}"
            },
            json={
                "modelUri": f"gpt://{folder_id}/yandexgpt",
                "completionOptions": {"temperature": 0.3, "maxTokens": 1000},
                "messages": [{"role": "user", "text": user_text}]
            }
        ).json()

        answer = response.get('result', {}).get('alternatives', [{}])[0].get('message', {}).get('text',
                                                                                                "Не удалось получить ответ")

        # Логируем ответ
        log_user_action(user.id, f"Ответ: {answer[:200]}")  # Ограничиваем длину

        await update.message.reply_text(answer)
    except Exception as e:
        logger.error(f"Ошибка обработки сообщения: {e}")
        await update.message.reply_text("Произошла ошибка при обработке запроса")


# ================== Основная функция ==================
def main() -> None:
    """Запуск бота"""
    # Инициализация хранилищ
    init_csv()
    init_postgres()

    # Создаем приложение Telegram бота
    application = Application.builder().token(APP_TOKEN).build()

    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Регистрируем обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_message))

    # Запускаем бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    logger.info("Бот запущен")


if __name__ == "__main__":
    main()