import requests
from bs4 import BeautifulSoup
import concurrent.futures
import re
from typing import List, Dict
import time
from datetime import datetime
import schedule
import threading
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

def get_book_data(book_url: str) -> Dict:
    """Собирает данные о книге с заданной страницы."""
    try:
        response = requests.get(book_url)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')

        title = soup.find('h1').text
        price = soup.find('p', class_='price_color').text
        
        rating_tag = soup.find('p', class_='star-rating')
        rating = rating_tag['class'][1] if rating_tag else None

        availability_text = soup.find('p', class_='instock availability').text
        availability_match = re.search(r'\d+', availability_text)
        availability = int(availability_match.group()) if availability_match else 0

        description_tag = soup.find('div', id='product_description')
        description = description_tag.find_next_sibling('p').text if description_tag else ''

        product_table = soup.find('table', class_='table table-striped')
        product_info = {}
        if product_table:
            for row in product_table.find_all('tr'):
                header = row.find('th')
                value = row.find('td')
                if header and value:
                    product_info[header.text] = value.text

        return {
            'title': title,
            'price': price,
            'rating': rating,
            'availability': availability,
            'description': description,
            'product_information': product_info,
            'url': book_url
        }
    except Exception as e:
        logging.error(f"Ошибка при парсинге книги {book_url}: {e}")
        return {}

def get_book_links_from_page(page_url: str) -> List[str]:
    """Извлекает все ссылки на книги со страницы каталога."""
    try:
        response = requests.get(page_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        book_links = []
        books = soup.find_all('article', class_='product_pod')
        
        for book in books:
            link_tag = book.find('h3').find('a')
            if link_tag and 'href' in link_tag.attrs:
                relative_link = link_tag['href']
                if 'catalogue/' in relative_link:
                    absolute_link = f"https://books.toscrape.com/catalogue/{relative_link.split('catalogue/')[-1]}"
                else:
                    absolute_link = f"https://books.toscrape.com/catalogue/{relative_link}"
                book_links.append(absolute_link)
        
        return book_links
    except Exception as e:
        logging.error(f"Ошибка при получении ссылок со страницы {page_url}: {e}")
        return []

def scrape_books(is_save: bool = False, max_workers: int = 10, max_pages: int = None) -> List[Dict]:
    """Собирает данные о всех книгах с сайта."""
    base_url = "https://books.toscrape.com/catalogue/page-{}.html"
    
    all_book_links = []
    page_num = 1
    
    logging.info("Сбор ссылок на книги...")
    while True:
        if max_pages and page_num > max_pages:
            break
            
        page_url = base_url.format(page_num)
        try:
            response = requests.get(page_url)
            if response.status_code != 200:
                break
                
            book_links = get_book_links_from_page(page_url)
            if not book_links:
                break
                
            all_book_links.extend(book_links)
            logging.info(f"Страница {page_num}: найдено {len(book_links)} книг")
            page_num += 1
            
        except Exception as e:
            logging.error(f"Ошибка при обработке страницы {page_num}: {e}")
            break
    
    logging.info(f"Всего найдено ссылок на книги: {len(all_book_links)}")
    
    books_data = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(get_book_data, url): url for url in all_book_links}
        
        for i, future in enumerate(concurrent.futures.as_completed(future_to_url)):
            url = future_to_url[future]
            try:
                book_data = future.result()
                if book_data:
                    books_data.append(book_data)
                
                if (i + 1) % 10 == 0:
                    logging.info(f"Обработано {i + 1}/{len(all_book_links)} книг")
                    
            except Exception as e:
                logging.error(f"Ошибка при обработке книги {url}: {e}")
    
    if is_save:
        try:
            with open('artifacts/books_data.txt', 'w', encoding='utf-8') as f:
                for book in books_data:
                    f.write(f"Название: {book.get('title', 'N/A')}\n")
                    f.write(f"Цена: {book.get('price', 'N/A')}\n")
                    f.write(f"Рейтинг: {book.get('rating', 'N/A')}\n")
                    f.write(f"В наличии: {book.get('availability', 0)} шт.\n")
                    f.write(f"URL: {book.get('url', 'N/A')}\n")
                    f.write("-" * 30 + "\n")
            logging.info("Данные сохранены в artifacts/books_data.txt")
        except Exception as e:
            logging.error(f"Ошибка при сохранении в файл: {e}")
    
    logging.info(f"Парсинг завершен. Собрано данных о {len(books_data)} книгах")
    return books_data

def run_scheduler(schedule_time: str = "19:00"):
    """Запускает планировщик задач."""
    schedule.every().day.at(schedule_time).do(lambda: scrape_books(is_save=True))
    
    logging.info(f"Планировщик запущен. Ежедневный сбор данных в {schedule_time}")
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)
        except KeyboardInterrupt:
            logging.info("Планировщик остановлен")
            break
        except Exception as e:
            logging.error(f"Ошибка в планировщике: {e}")
            time.sleep(60)

def start_daily_scraping(background: bool = True, schedule_time: str = "19:00"):
    """Запускает ежедневный сбор данных."""
    logging.info(f"Запуск планировщика с временем: {schedule_time}")
    
    if background:
        scheduler_thread = threading.Thread(target=run_scheduler, args=(schedule_time,), daemon=True)
        scheduler_thread.start()
        return scheduler_thread
    else:
        run_scheduler(schedule_time)

def start_with_time(hours: int, minutes: int):
    """Запускает планировщик с указанным временем."""
    schedule_time = f"{hours:02d}:{minutes:02d}"
    start_daily_scraping(background=False, schedule_time=schedule_time)

if __name__ == "__main__":
    start_daily_scraping()