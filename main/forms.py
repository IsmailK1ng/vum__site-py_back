from django import forms
from .models import PageMeta
from .widgets import (
    SelectWithHelp, 
    TextInputWithHelp, 
    TextareaWithHelp, 
    URLInputWithHelp,
    FileInputWithHelp
)


class PageMetaAdminForm(forms.ModelForm):
    """
    Форма для PageMeta с иконками подсказок
    """
    
    class Meta:
        model = PageMeta
        fields = '__all__'
        widgets = {
            # ========== ИДЕНТИФИКАЦИЯ ==========
            'model': SelectWithHelp(
                help_text=(
                    "<strong>Выберите категорию страницы:</strong>"
                    "<strong>Page</strong> Статические страницы (главная, о нас, контакты)"
                    "<br>"
                    "<strong>Post</strong> Новости (каждая новость отдельно)"
                    "<br>"
                    "<strong>Product</strong> Продукты (каждый грузовик отдельно)"
                    "<br>"
                    "<strong>Vacancy</strong> Вакансии"
                    "<br>"
                    "<strong>Dealer</strong> Дилеры"
                )
            ),
            
            'key': TextInputWithHelp(
                attrs={'size': 50},
                help_text=(
                    "<strong>Уникальный идентификатор страницы:</strong>"
                    "<strong>Для статических страниц (model=Page):</strong>"
                    "• <code>home</code> = Главная страница (/)"
                    "<br>"
                    "• <code>about</code> = О нас (/about/)"
                    "<br>"
                    "• <code>contact</code> = Контакты (/contact/)"
                    "<br>"
                    "• <code>products</code> = Каталог (/products/)"
                    "<br>"
                    "• <code>dealers</code> = Дилеры (/dealers/)"
                    "<br>"
                    "• <code>jobs</code> = Вакансии (/jobs/)"
                    "<br>"
                    "• <code>lizing</code> = Лизинг (/lizing/)"
                    "<br>"
                    "• <code>become-a-dealer</code> = Стать дилером"
                    "<br>"
                    "<strong>Для динамических страниц:</strong>"
                    "<strong>Post:</strong> ID новости (например: 468)"
                    "<strong>Product:</strong> slug продукта (например: tiger-vh)"
                    "<strong>Vacancy:</strong> ID вакансии"
                )
            ),
            
            # ========== БАЗОВЫЕ META ==========
            'title': TextInputWithHelp(
                attrs={'size': 80},
                help_text=(
                    "<strong>Оптимальная длина: 50-70 символов</strong>"
                    "<span class='example-good'>Хороший title:</span>"
                    "<br>"
                    "FAW Tiger VH - Мощный грузовик | FAW Uzbekistan"
                    "<br>"
                    "<span class='example-bad'>Плохой title:</span>"
                    "<br>"
                    "Купить грузовик Tiger VH Tiger VH"
                    "<strong>Советы:</strong>"
                    "• Включайте ключевое слово"
                    "<br>"
                    "• Добавьте бренд через | или -"
                    "<br>"
                    "• Избегайте повторов"
                    "<br>"
                    "• Не пишите ЗАГЛАВНЫМИ"
                )
            ),
            
            'description': TextareaWithHelp(
                attrs={'rows': 3, 'cols': 80},
                help_text=(
                    "<strong>Оптимальная длина: 150-250 символов</strong>"
                    "<span class='example-good'>Хорошее description:</span>"
                    "<br>"
                    "Tiger VH - надежный грузовик FAW с двойным топливом. "
                    "Мощность 185 л.с., расход 17L/100km. Лизинг от 20%. Гарантия 3 года."
                    "<br>"
                    "<span class='example-bad'>Плохое description:</span>"
                    "<br>"
                    "Грузовик Tiger VH"
                    "<strong>Советы:</strong>"
                    "• Опишите что найдет пользователь"
                    "<br>"
                    "• Добавьте цифры и факты"
                    "<br>"
                    "• Призыв к действию"
                    "<br>"
                    "• Ключевые слова естественно"
                )
            ),
            
            'keywords': TextInputWithHelp(
                attrs={'size': 80},
                help_text=(
                    "<span class='example-good'>Правильно:</span>"
                    "<br>"
                    "грузовики FAW, купить грузовик, FAW Tiger VH, самосвалы"
                    "<br>"
                    "<span class='example-bad'>Неправильно:</span>"
                    "<br>"
                    "грузовик грузовик грузовик купить купить"
                    "<strong>Советы:</strong>"
                    "• 5-10 ключевых слов"
                    "<br>"
                    "• Разделяйте запятой"
                    "<br>"
                    "• Не повторяйте"
                    "<br>"
                    "• Можно оставить пустым"
                )
            ),
            
            # ========== OPEN GRAPH ==========
            'og_title': TextInputWithHelp(
                attrs={'size': 80},
                help_text=(
                    "<strong>Заголовок при шаринге в соцсетях</strong>"
                    "Можно оставить пустым - используется обычный Title"
                    "<strong>Используйте если хотите:</strong>"
                    "• Более короткий заголовок"
                    "<br>"
                    "• Другую формулировку под соцсети"
                )
            ),
            
            'og_description': TextareaWithHelp(
                attrs={'rows': 2, 'cols': 80},
                help_text=(
                    "<strong>Описание при шаринге в соцсетях</strong>"
                    "Можно оставить пустым - используется обычный Description"
                )
            ),
            
            'og_url': URLInputWithHelp(
                attrs={'size': 80},
                help_text=(
                    "<strong>Полная ссылка на страницу</strong>"
                    "Можно оставить пустым - система сгенерирует автоматически"
                    "Заполняйте только если хотите указать кастомный URL"
                )
            ),
            
            'og_type': SelectWithHelp(
                help_text=(
                    "<strong>Тип контента для соцсетей:</strong>"
                    "<strong>website</strong>  Обычный сайт" "<br>"
                    "Используйте для: главная, о нас, контакты, каталог"
                    "<strong>article</strong> Статья/новость" "<br>"
                    "Используйте для: новости, блог-посты""<br>"
                    "<strong>product</strong> Товар/продукт""<br>"
                    "Используйте для: страницы продуктов (Tiger VH, самосвалы)"
                    "<strong>profile</strong>  Профиль""<br>"
                    "Используйте для: карточки сотрудников, дилеров"
                )
            ),
            
            'og_site_name': TextInputWithHelp(
                attrs={'size': 50},
                help_text="Название вашего сайта/компании"
            ),
            
            'og_image': FileInputWithHelp(
                help_text=(
                    "<strong>Рекомендации для картинки:</strong>"
                    "• Размер: 1200x630px (соотношение 1.91:1)"
                    "<br>"
                    "• Формат: JPG или PNG"
                    "<br>"
                    "• Вес: до 8MB"
                    "<br>"
                    "• Яркая, контрастная"
                    "<br>"
                    "• Текст крупным шрифтом"
                    "Можно оставить пустым"
                )
            ),
        }