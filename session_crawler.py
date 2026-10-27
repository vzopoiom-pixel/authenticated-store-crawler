import requests
from bs4 import BeautifulSoup
import sqlite3
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_NAME = "shop_products.db"
BASE_URL = "https://quotes.toscrape.com"  # Поправили поддомен песочницы
LOGIN_URL = f"{BASE_URL}/login"
TARGET_URL = f"{BASE_URL}/"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                author TEXT,
                text TEXT,
                UNIQUE(author, text) ON CONFLICT IGNORE
            )
        ''')
        conn.commit()
    logger.info("База данных успешно проверена и готова к работе.")

def parse_store():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })

    try:
        logger.info("Получаем токен авторизации...")
        login_page = session.get(LOGIN_URL, timeout=10)
        soup = BeautifulSoup(login_page.text, "html.parser")
        
        csrf_token = soup.find("input", {"name": "csrf_token"})["value"]

        payload = {
            "username": "upwork_client",
            "password": "password123",
            "csrf_token": csrf_token
        }
        
        logger.info("Выполняем вход в личный кабинет...")
        response = session.post(LOGIN_URL, data=payload, timeout=10)
        
        if "Login" in response.text and "Logout" not in response.text:
            logger.error("Не удалось авторизоваться. Проверьте данные.")
            return

        logger.info("Авторизация прошла успешно! Парсим закрытый каталог...")

        current_url = TARGET_URL
        products_data = []

        # Обернули в цикл для прохода по ВСЕМ страницам пагинации
        while current_url:
            logger.info(f"Парсим страницу: {current_url}")
            catalog_page = session.get(current_url, timeout=10)
            catalog_soup = BeautifulSoup(catalog_page.text, "html.parser")

            elements = catalog_soup.find_all("div", class_="quote")
            for el in elements:
                text = el.find("span", class_="text").text
                author = el.find("small", class_="author").text
                
                products_data.append((
                    author.strip(), 
                    text.strip().replace("“", "").replace("”", "")
                ))

            # Ищем кнопку "Next" для перехода на следующую страницу
            next_button = catalog_soup.find("li", class_="next")
            if next_button:
                next_url = next_button.find("a")["href"]
                current_url = f"{BASE_URL}{next_url}"
            else:
                current_url = None  # Страницы закончились

        if products_data:
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()
                # Оптимизировали запись через executemany 
                cursor.executemany(
                    "INSERT OR IGNORE INTO products (author, text) VALUES (?, ?)",
                    products_data
                )
                conn.commit()
            logger.info(f" Успешно спарсено и сохранено {len(products_data)} позиций в {DB_NAME}!")
        else:
            logger.warning("Каталог пуст или структура сайта изменилась.")

    except Exception as e:
        logger.error(f"Произошла ошибка при работе скрипта: {str(e)}")

def main():
    init_db()
    parse_store()

if __name__ == "__main__":
    main()
