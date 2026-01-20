# main/management/commands/test_urls.py

from django.core.management.base import BaseCommand
from django.test import Client


class Command(BaseCommand):
    help = 'Тестирует все URL на правильность префиксов языков'

    def handle(self, *args, **options):
        # ✅ Создаем клиента с правильным хостом
        client = Client(SERVER_NAME='127.0.0.1')
        
        self.stdout.write(self.style.WARNING('\n' + '='*60))
        self.stdout.write(self.style.WARNING('ТЕСТИРОВАНИЕ URL ПРЕФИКСОВ'))
        self.stdout.write(self.style.WARNING('='*60 + '\n'))
        
        # Тесты для УЗ (дефолт - БЕЗ префикса)
        self.test_uz_urls(client)
        
        # Тесты для РУ (С префиксом /ru/)
        self.test_ru_urls(client)
        
        # Тесты для ЕН (С префиксом /en/)
        self.test_en_urls(client)
        
        # Тесты что /uz/ НЕ работает
        self.test_uz_prefix_should_not_work(client)
        
        self.stdout.write(self.style.SUCCESS('\n✅ ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ!\n'))
    
    def test_uz_urls(self, client):
        """Тестируем УЗ URL (БЕЗ префикса)"""
        self.stdout.write(self.style.WARNING('\n--- ТЕСТ 1: УЗ URL (БЕЗ /uz/) ---\n'))
        
        uz_urls = [
            ('/', 'Главная'),
            ('/about/', 'О компании'),
            ('/products/', 'Каталог'),
            ('/products/?category=samosval', 'Каталог - Самосвалы'),
            ('/products/?category=tiger_v', 'Каталог - Tiger V'),
            ('/news/', 'Новости'),
            ('/dealers/', 'Дилеры'),
            ('/jobs/', 'Вакансии'),
        ]
        
        for url, name in uz_urls:
            # ✅ Добавляем HTTP_HOST
            response = client.get(url, HTTP_ACCEPT_LANGUAGE='uz', HTTP_HOST='127.0.0.1:8000')
            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS(f'✅ {url:40} → {name}'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ {url:40} → {name} (Код: {response.status_code})'))
    
    def test_ru_urls(self, client):
        """Тестируем РУ URL (С префиксом /ru/)"""
        self.stdout.write(self.style.WARNING('\n--- ТЕСТ 2: РУ URL (С /ru/) ---\n'))
        
        ru_urls = [
            ('/ru/', 'Главная'),
            ('/ru/about/', 'О компании'),
            ('/ru/products/', 'Каталог'),
            ('/ru/products/?category=samosval', 'Каталог - Самосвалы'),
            ('/ru/products/?category=tiger_v', 'Каталог - Tiger V'),
            ('/ru/news/', 'Новости'),
            ('/ru/dealers/', 'Дилеры'),
            ('/ru/jobs/', 'Вакансии'),
        ]
        
        for url, name in ru_urls:
            response = client.get(url, HTTP_ACCEPT_LANGUAGE='ru', HTTP_HOST='127.0.0.1:8000')
            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS(f'✅ {url:40} → {name}'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ {url:40} → {name} (Код: {response.status_code})'))
    
    def test_en_urls(self, client):
        """Тестируем ЕН URL (С префиксом /en/)"""
        self.stdout.write(self.style.WARNING('\n--- ТЕСТ 3: ЕН URL (С /en/) ---\n'))
        
        en_urls = [
            ('/en/', 'Home'),
            ('/en/about/', 'About'),
            ('/en/products/', 'Catalog'),
            ('/en/products/?category=samosval', 'Catalog - Dump Trucks'),
            ('/en/products/?category=tiger_v', 'Catalog - Tiger V'),
            ('/en/news/', 'News'),
            ('/en/dealers/', 'Dealers'),
            ('/en/jobs/', 'Jobs'),
        ]
        
        for url, name in en_urls:
            response = client.get(url, HTTP_ACCEPT_LANGUAGE='en', HTTP_HOST='127.0.0.1:8000')
            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS(f'✅ {url:40} → {name}'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ {url:40} → {name} (Код: {response.status_code})'))
    
    def test_uz_prefix_should_not_work(self, client):
        """Тестируем что /uz/ НЕ ДОЛЖЕН работать"""
        self.stdout.write(self.style.WARNING('\n--- ТЕСТ 4: /uz/ НЕ ДОЛЖЕН РАБОТАТЬ ---\n'))
        
        uz_prefix_urls = [
            ('/uz/', 'Главная с /uz/'),
            ('/uz/about/', 'О компании с /uz/'),
            ('/uz/products/', 'Каталог с /uz/'),
            ('/uz/products/?category=samosval', 'Каталог - Самосвалы с /uz/'),
        ]
        
        for url, name in uz_prefix_urls:
            response = client.get(url, HTTP_HOST='127.0.0.1:8000')
            if response.status_code == 404:
                self.stdout.write(self.style.SUCCESS(f'✅ {url:40} → 404 (ПРАВИЛЬНО!)'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ {url:40} → {name} (Код: {response.status_code}) - ОШИБКА! ДОЛЖЕН БЫТЬ 404!'))