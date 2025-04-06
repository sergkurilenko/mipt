import pandas as pd
import os
import yadisk
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()
# Настройки
CSV_FILE_PATH = 'user_actions.csv'  # Путь к исходному CSV-файлу
XLSX_FILE_PATH = 'user_actions.xlsx'  # Путь для сохранения XLSX-файла
YANDEX_DISK_TOKEN = os.getenv('YANDEX_DISK_TOKEN')  # OAuth-токен Яндекс.Диска
YANDEX_UPLOAD_PATH = '/bot_files/user_actions.xlsx'  # Путь на Яндекс.Диске


def convert_csv_to_xlsx(csv_path, xlsx_path):
    """Конвертирует CSV файл в XLSX формат"""
    try:
        # Чтение CSV файла
        df = pd.read_csv(csv_path)

        # Запись в XLSX файл
        df.to_excel(xlsx_path, index=False, engine='openpyxl')
        print(f"Файл успешно конвертирован и сохранен как {xlsx_path}")
        return True
    except Exception as e:
        print(f"Ошибка при конвертации файла: {e}")
        return False


def upload_to_yandex_disk(file_path, yandex_path, token):
    """Загружает файл на Яндекс.Диск"""
    # Получаем URL для загрузки
    y = yadisk.YaDisk(token = YANDEX_DISK_TOKEN)
    if y.check_token():
        print("Токен действителен")
    else:
        print("Токен недействителен")

    try:
        y.upload(XLSX_FILE_PATH, YANDEX_UPLOAD_PATH, overwrite=True)
        print(f"Файл успешно загружен на Яндекс.Диск: {YANDEX_UPLOAD_PATH}")
        return True
    except Exception as e:
        print(f"Ошибка при загрузке на Яндекс.Диск: {e}")
        return False


def main():
    # Проверяем существование CSV файла
    if not os.path.exists(CSV_FILE_PATH):
        print(f"Файл {CSV_FILE_PATH} не найден!")
        return

    # Конвертируем CSV в XLSX
    if not convert_csv_to_xlsx(CSV_FILE_PATH, XLSX_FILE_PATH):
        return

    # Загружаем на Яндекс.Диск
    upload_to_yandex_disk(XLSX_FILE_PATH, YANDEX_UPLOAD_PATH, YANDEX_DISK_TOKEN)


if __name__ == "__main__":
    main()