# Authenticated Session Scraper with Dynamic Pagination

A production-ready Python web scraper designed to extract data from websites requiring user authentication. It bypasses basic CSRF-token protections, maintains login sessions efficiently via HTTP cookies, and processes multi-page catalogs.

## ⚡ Key Features

*   **Session Persistence:** Uses `requests.Session` to maintain authorization cookies across all requests, eliminating browser overhead.
*   **CSRF Bypass:** Automatically extracts and injects dynamic CSRF tokens during the login handshake.
*   **Dynamic Pagination:** Includes a robust `while` loop architecture to automatically detect and follow "Next page" links until the catalog is fully extracted.
*   **Database Optimization:** Implements bulk data insertion using SQLite's `executemany()` to minimize disk I/O operations and maximize performance.

## ⚙️ Tech Stack

*   **Engine:** Python 3.10+
*   **HTTP Client:** Requests (Session-based)
*   **HTML Parser:** BeautifulSoup4
*   **Storage:** SQLite3 (Embedded database)

## 🛠️ Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the scraper:
   ```bash
   python auth_scraper.py
   ```

## 📊 Database Output
After execution, the script automatically creates a localized `shop_products.db` file with structured, duplicate-free data.
