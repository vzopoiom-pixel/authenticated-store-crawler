import logging
import sqlite3
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DB_NAME = "shop_products.db"
BASE_URL = "https://quotes.toscrape.com"
LOGIN_URL = f"{BASE_URL}/login"
TARGET_URL = f"{BASE_URL}/"


def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                author TEXT,
                text TEXT,
                UNIQUE(author, text) ON CONFLICT IGNORE
            )
        """
        )
        conn.commit()
    logger.info("Database initialized successfully.")


def parse_store():
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    )

    try:
        logger.info("Extracting CSRF authentication token...")
        login_page = session.get(LOGIN_URL, timeout=10)
        soup = BeautifulSoup(login_page.text, "html.parser")

        csrf_input = soup.find("input", {"name": "csrf_token"})
        if not csrf_input:
            logger.error("Could not find CSRF token on login page.")
            return

        csrf_token = csrf_input["value"]
        payload = {
            "username": "upwork_client",
            "password": "password123",
            "csrf_token": csrf_token,
        }

        logger.info("Authenticating user session...")
        response = session.post(LOGIN_URL, data=payload, timeout=10)

        if "Login" in response.text and "Logout" not in response.text:
            logger.error("Authentication failed. Please verify credentials.")
            return

        logger.info("Session authenticated successfully! Scraping catalog...")
        current_url = TARGET_URL
        items_data = []

        # Traverse through all pagination pages
        while current_url:
            logger.info(f"Scraping page: {current_url}")
            catalog_page = session.get(current_url, timeout=10)
            catalog_soup = BeautifulSoup(catalog_page.text, "html.parser")
            elements = catalog_soup.find_all("div", class_="quote")

            for el in elements:
                text_el = el.find("span", class_="text")
                author_el = el.find("small", class_="author")
                if text_el and author_el:
                    clean_text = text_el.text.strip().replace("“", "").replace("”", "")
                    items_data.append((author_el.text.strip(), clean_text))

            next_button = catalog_soup.find("li", class_="next")
            if next_button and next_button.find("a"):
                next_url = next_button.find("a")["href"]
                current_url = f"{BASE_URL}{next_url}"
            else:
                current_url = None

        if items_data:
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()
                cursor.executemany(
                    "INSERT OR IGNORE INTO products (author, text) VALUES (?, ?)",
                    items_data,
                )
                conn.commit()
            logger.info(
                f"Successfully parsed and stored {len(items_data)} items into {DB_NAME}!"
            )
        else:
            logger.warning("No items found or layout has changed.")

    except Exception as e:
        logger.error(f"Scraping process encountered an error: {str(e)}")


def main():
    init_db()
    parse_store()


if __name__ == "__main__":
    main()
