"""
УНИВЕРСАЛЬНАЯ КОМАНДА: python manage.py setup_seo

Выполняет ВСЕ операции по настройке SEO:
1. Создает статические страницы
2. Создает SEO для существующих новостей/продуктов
3. Исправляет og_url
4. Обновляет key_order
"""

from django.core.management.base import BaseCommand
from main.models import News, Product, PageMeta


class Command(BaseCommand):
    help = 'Полная настройка SEO системы (все в одном)'
    
    def handle(self, *args, **options):
        
        self.stdout.write('=' * 70)
        self.stdout.write(self.style.HTTP_INFO('ПОЛНАЯ НАСТРОЙКА SEO СИСТЕМЫ'))
        self.stdout.write('=' * 70 + '\n')
        
        # ========== 1. СТАТИЧЕСКИЕ СТРАНИЦЫ ==========
        self.stdout.write(self.style.HTTP_INFO('ЭТАП 1: СОЗДАНИЕ СТАТИЧЕСКИХ СТРАНИЦ'))
        self.stdout.write('-' * 70)
        
        static_pages = [
            ('home', 'Главная страница'),
            ('about', 'О нас'),
            ('contact', 'Контакты'),
            ('services', 'Сервис'),
            ('lizing', 'Лизинг'),
            ('become-a-dealer', 'Стать дилером'),
            ('jobs', 'Вакансии'),
            ('news', 'Список новостей'),
            ('dealers', 'Список дилеров'),
            ('products_samosval', 'Каталог самосвалов'),
            ('products_maxsus', 'Каталог спецтехники'),
            ('products_furgon', 'Каталог фургонов'),
            ('products_shassi', 'Каталог шасси'),
            ('products_tiger_v', 'Каталог Tiger V'),
            ('products_tiger_vh', 'Каталог Tiger VH'),
            ('products_tiger_vr', 'Каталог Tiger VR'),
        ]
        
        static_created = 0
        static_existed = 0
        
        for key, description in static_pages:
            obj, created = PageMeta.objects.get_or_create(
                model='Page',
                key=key,
                defaults={
                    'is_active': False,
                    'title': '',
                    'description': '',
                    'keywords': '',
                    'og_type': 'website',
                }
            )
            
            if created:
                static_created += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ {key} - {description}'))
            else:
                static_existed += 1
        
        self.stdout.write(f'\nИтог: создано {static_created}, уже было {static_existed}\n')
        
        # ========== 2. НОВОСТИ ==========
        self.stdout.write(self.style.HTTP_INFO('ЭТАП 2: СОЗДАНИЕ SEO ДЛЯ НОВОСТЕЙ'))
        self.stdout.write('-' * 70)
        
        all_news = News.objects.all().order_by('id')
        news_created = 0
        news_existed = 0
        
        for news in all_news:
            obj, created = PageMeta.objects.get_or_create(
                model='Post',
                key=str(news.id),
                defaults={
                    'is_active': False,
                    'title': '',
                    'description': '',
                    'keywords': '',
                    'og_type': 'article',
                }
            )
            
            if created:
                news_created += 1
        
        news_existed = all_news.count() - news_created
        self.stdout.write(f'Обработано новостей: {all_news.count()}')
        self.stdout.write(self.style.SUCCESS(f'  ✓ Создано: {news_created}'))
        if news_existed > 0:
            self.stdout.write(self.style.WARNING(f'  ○ Уже было: {news_existed}'))
        self.stdout.write('')
        
        # ========== 3. ПРОДУКТЫ ==========
        self.stdout.write(self.style.HTTP_INFO('ЭТАП 3: СОЗДАНИЕ SEO ДЛЯ ПРОДУКТОВ'))
        self.stdout.write('-' * 70)
        
        all_products = Product.objects.all().order_by('id')
        product_created = 0
        product_existed = 0
        
        for product in all_products:
            obj, created = PageMeta.objects.get_or_create(
                model='Product',
                key=str(product.id),
                defaults={
                    'is_active': False,
                    'title': '',
                    'description': '',
                    'keywords': '',
                    'og_type': 'product',
                }
            )
            
            if created:
                product_created += 1
        
        product_existed = all_products.count() - product_created
        self.stdout.write(f'Обработано продуктов: {all_products.count()}')
        self.stdout.write(self.style.SUCCESS(f'  ✓ Создано: {product_created}'))
        if product_existed > 0:
            self.stdout.write(self.style.WARNING(f'  ○ Уже было: {product_existed}'))
        self.stdout.write('')
        
        # ========== 4. ОБНОВЛЕНИЕ key_order ==========
        self.stdout.write(self.style.HTTP_INFO('ЭТАП 4: ОБНОВЛЕНИЕ key_order'))
        self.stdout.write('-' * 70)
        
        all_records = PageMeta.objects.all()
        updated = 0
        
        for record in all_records:
            old_order = record.key_order
            
            if record.key.isdigit():
                record.key_order = int(record.key)
            else:
                record.key_order = 999999
            
            if old_order != record.key_order:
                record.save()
                updated += 1
        
        self.stdout.write(f'Обновлено записей: {updated}\n')
        
        # ========== 5. ИСПРАВЛЕНИЕ og_url ==========
        self.stdout.write(self.style.HTTP_INFO('ЭТАП 5: ИСПРАВЛЕНИЕ og_url'))
        self.stdout.write('-' * 70)
        
        url_updated = 0
        
        for meta in all_records:
            old_url = meta.og_url
            meta.og_url = None
            new_url = meta.get_full_url()
            meta.og_url = new_url
            
            if old_url != new_url:
                meta.save()
                url_updated += 1
        
        self.stdout.write(f'Обновлено URL: {url_updated}\n')
        
        # ========== ИТОГОВАЯ СТАТИСТИКА ==========
        self.stdout.write('=' * 70)
        self.stdout.write(self.style.SUCCESS('НАСТРОЙКА ЗАВЕРШЕНА'))
        self.stdout.write('=' * 70)
        self.stdout.write(f'Статические страницы: {static_created} создано, {static_existed} было')
        self.stdout.write(f'Новости: {news_created} создано, {news_existed} было')
        self.stdout.write(f'Продукты: {product_created} создано, {product_existed} было')
        self.stdout.write(f'Обновлено key_order: {updated}')
        self.stdout.write(f'Обновлено og_url: {url_updated}')
        self.stdout.write('\n' + self.style.SUCCESS(f'ВСЕГО создано SEO записей: {static_created + news_created + product_created}'))
        self.stdout.write('=' * 70 + '\n')
