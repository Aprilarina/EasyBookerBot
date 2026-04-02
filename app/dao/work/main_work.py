import json
import asyncpg
from typing import List, Dict
from app.config import settings


# Функция для чтения JSON-файла
def load_json(file_path: str) -> List[Dict]:
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


# Функция для подключения к базе данных
async def get_connection():
    connection = await asyncpg.connect(
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
        host=settings.DB_HOST,
        port=settings.DB_PORT
    )
    return connection


# Функция для вставки данных о марке
async def insert_brand(connection, brand_data: Dict):
    query = """
    INSERT INTO brands (id, name, cyrillic_name, popular, country)
    VALUES ($1, $2, $3, $4, $5)
    """
    await connection.execute(
        query,
        brand_data["id"],
        brand_data["name"],
        brand_data.get("cyrillic-name"),
        brand_data["popular"],
        brand_data.get("country")
    )


# Функция для вставки данных о модели
async def insert_model(connection, model_data: Dict, mark_id: str):
    query = """
    INSERT INTO models (id, name, cyrillic_name, class, year_from, year_to, mark_id)
    VALUES ($1, $2, $3, $4, $5, $6, $7)
    """
    await connection.execute(
        query,
        model_data["id"],
        model_data["name"],
        model_data.get("cyrillic-name"),
        model_data.get("class"),
        model_data.get("year-from"),
        model_data.get("year-to"),
        mark_id
    )


# Основная функция для добавления данных из JSON
async def insert_data_from_json(file_path: str):
    # Загружаем данные из JSON
    data = load_json(file_path)

    # Подключаемся к базе данных
    connection = await get_connection()

    try:
        # Проходим по каждой марке в JSON
        for brand_data in data:
            # Вставляем данные о марке
            await insert_brand(connection, brand_data)

            # Проходим по каждой модели в марке
            for model_data in brand_data.get("models", []):
                # Вставляем данные о модели
                await insert_model(connection, model_data, brand_data["id"])

        print("Данные успешно добавлены в базу данных.")
    finally:
        # Закрываем соединение с базой данных
        await connection.close()