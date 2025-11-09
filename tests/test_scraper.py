import sys
import os
import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from scraper import get_book_data, scrape_books, get_book_links_from_page


class TestGetBookData:
    """Тесты для функции get_book_data"""
    
    def test_returns_dict(self):
        """Проверяет, что функция возвращает словарь"""
        book_url = 'https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html'
        result = get_book_data(book_url)
        assert isinstance(result, dict)
    
    def test_has_required_keys(self):
        """Проверяет наличие всех необходимых ключей"""
        book_url = 'https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html'
        result = get_book_data(book_url)
        
        required_keys = ['title', 'price', 'rating', 'availability', 
                        'description', 'product_information', 'url']
        
        for key in required_keys:
            assert key in result
    
    def test_title_not_empty(self):
        """Проверяет, что название книги не пустое"""
        book_url = 'https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html'
        result = get_book_data(book_url)
        
        assert result['title'] is not None
        assert len(result['title']) > 0
        assert isinstance(result['title'], str)


class TestScrapeBooks:
    """Тесты для функции scrape_books"""
    
    def test_returns_list(self):
        """Проверяет, что функция возвращает список"""
        result = scrape_books(is_save=False, max_pages=1)
        assert isinstance(result, list)
    
    def test_books_count_reasonable(self):
        """Проверяет, что количество книг соответствует ожиданиям"""
        result = scrape_books(is_save=False, max_pages=1)
        assert len(result) == 20


class TestGetBookLinksFromPage:
    """Тесты для функции get_book_links_from_page"""
    
    def test_returns_list_of_links(self):
        """Проверяет, что функция возвращает список ссылок"""
        page_url = 'https://books.toscrape.com/catalogue/page-1.html'
        result = get_book_links_from_page(page_url)
        
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_links_format(self):
        """Проверяет формат возвращаемых ссылок"""
        page_url = 'https://books.toscrape.com/catalogue/page-1.html'
        result = get_book_links_from_page(page_url)
        
        for link in result[:3]:
            assert link.startswith('https://')
            assert 'index.html' in link