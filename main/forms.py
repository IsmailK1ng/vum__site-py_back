from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from .models import PageMeta, DealerProfile, SparePart, SparePartType, normalize_type_name
from .widgets import (
    SelectWithHelp,
    TextInputWithHelp,
    TextareaWithHelp,
    URLInputWithHelp,
    FileInputWithHelp
)


class PageMetaAdminForm(forms.ModelForm):
    class Meta:
        model = PageMeta
        fields = '__all__'
        widgets = {
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


# ========== ФОРМЫ ДЛЯ ДИЛЕРОВ ==========

class DealerProfileAdminForm(forms.ModelForm):
    """Форма создания/редактирования дилера в админке.
    Объединяет поля User (логин, пароль) и DealerProfile (имя, аватар).
    При создании пароль обязателен, при редактировании — опционален.
    """
    username = forms.CharField(
        label='Логин',
        max_length=150,
        help_text='Латиница, цифры, символы @/./+/-/_',
    )
    password1 = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(render_value=False),
        required=False,
        help_text='Минимум 8 символов. При редактировании оставьте пустым, чтобы не менять.',
    )
    password2 = forms.CharField(
        label='Повторите пароль',
        widget=forms.PasswordInput(render_value=False),
        required=False,
    )

    class Meta:
        model = DealerProfile
        fields = ['role', 'name', 'avatar', 'company_name', 'inn', 'contract_number', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields['username'].initial = self.instance.user.username
            self.fields['username'].disabled = True
            self.fields['username'].help_text = 'Логин нельзя изменить после создания.'
        else:
            self.fields['password1'].required = True
            self.fields['password2'].required = True

    def clean(self):
        cleaned = super().clean()
        role = cleaned.get('role') or DealerProfile.ROLE_DEALER

        # Юр.данные обязательны ТОЛЬКО для дилеров — у них формируются счета.
        # Сервису и бухгалтеру эти поля не нужны.
        if role == DealerProfile.ROLE_DEALER:
            for field in ('company_name', 'inn', 'contract_number'):
                if not (cleaned.get(field) or '').strip():
                    self.add_error(field, 'Обязательно для роли «Дилер».')

        # Пароль (как было)
        pwd1 = cleaned.get('password1')
        pwd2 = cleaned.get('password2')
        if pwd1 or pwd2:
            if pwd1 != pwd2:
                self.add_error('password2', 'Пароли не совпадают.')
            else:
                try:
                    validate_password(pwd1)
                except forms.ValidationError as e:
                    self.add_error('password1', e)
        return cleaned

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if self.instance and self.instance.pk:
            return self.instance.user.username
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('Пользователь с таким логином уже существует.')
        return username

    def clean_inn(self):
        inn = (self.cleaned_data.get('inn') or '').strip()
        # Пустой ИНН допустим для не-дилеров — на обязательность проверит clean() по роли.
        if not inn:
            return ''
        if not inn.isdigit():
            raise forms.ValidationError('ИНН должен содержать только цифры.')
        if len(inn) < 5 or len(inn) > 15:
            raise forms.ValidationError('ИНН должен быть длиной от 5 до 15 цифр.')
        return inn


class DealerPasswordChangeForm(forms.Form):
    """Смена пароля из дилерского кабинета. Текущий пароль обязателен."""
    current_password = forms.CharField(
        label='Текущий пароль',
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}),
    )
    new_password = forms.CharField(
        label='Новый пароль',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        help_text='Минимум 8 символов.',
    )
    new_password_confirm = forms.CharField(
        label='Повторите новый пароль',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_current_password(self):
        pwd = self.cleaned_data.get('current_password', '')
        if not self.user or not self.user.check_password(pwd):
            raise forms.ValidationError('Текущий пароль неверный.')
        return pwd

    def clean(self):
        cleaned = super().clean()
        new1 = cleaned.get('new_password')
        new2 = cleaned.get('new_password_confirm')
        if new1 and new2:
            if new1 != new2:
                self.add_error('new_password_confirm', 'Пароли не совпадают.')
            else:
                try:
                    validate_password(new1, user=self.user)
                except forms.ValidationError as e:
                    self.add_error('new_password', e)
        return cleaned


class DealerLoginForm(forms.Form):
    """Форма входа дилера. Намеренно простая, чтобы избежать утечек:
    при неверном логине/пароле возвращаем одинаковую ошибку (не намекаем существует ли юзер).
    """
    username = forms.CharField(
        label='Логин',
        max_length=150,
        widget=forms.TextInput(attrs={
            'autocomplete': 'username',
            'autofocus': True,
            'class': 'dealer-login__input',
        }),
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'current-password',
            'class': 'dealer-login__input',
        }),
    )


# ========== МАГАЗИН — ЗАПЧАСТИ ==========

class _TypeAutocompleteWidget(forms.TextInput):
    """Кастомный autocomplete: input + видимый dropdown с существующими типами.
    HTML5 <datalist> отказались — браузер рисует его уродливым нативным UI,
    тут полный контроль над стилями + понятное выпадение на focus/click.
    """

    def render(self, name, value, attrs=None, renderer=None):
        attrs = dict(attrs) if attrs else {}
        attrs.setdefault('autocomplete', 'off')
        attrs.setdefault('placeholder', 'Введите новый тип или выберите из списка')
        attrs['class'] = (attrs.get('class', '') + ' part-type-autocomplete__input').strip()

        input_html = super().render(name, value, attrs, renderer)

        # Только типы с заполненным name_ru
        types = (
            SparePartType.objects
            .exclude(name_ru__isnull=True).exclude(name_ru='')
            .only('name_ru')
            .order_by('name_ru')
        )
        options_html = format_html_join(
            '',
            '<li class="part-type-autocomplete__option" data-value="{0}">{0}</li>',
            ((t.name_ru,) for t in types),
        )

        # Inline CSS+JS — самодостаточный widget, не требует подключения media.
        # Selector .part-type-autocomplete__input находит свой dropdown через next sibling.
        widget_html = format_html(
            '<div class="part-type-autocomplete">{input}'
            '<button type="button" class="part-type-autocomplete__toggle" tabindex="-1" '
                'aria-label="Показать список">▾</button>'
            '<ul class="part-type-autocomplete__dropdown" hidden>{options}'
            '<li class="part-type-autocomplete__empty" hidden>Совпадений нет — будет создан новый тип</li>'
            '</ul></div>',
            input=input_html,
            options=options_html,
        )

        # CSS — мелкая стилизация в стиле Django admin
        css = """
        <style>
        .part-type-autocomplete { position: relative; display: inline-block; width: 100%; max-width: 540px; }
        .part-type-autocomplete__input { width: 100% !important; padding-right: 32px !important; }
        .part-type-autocomplete__toggle {
            position: absolute; right: 4px; top: 50%; transform: translateY(-50%);
            background: transparent; border: none; cursor: pointer; padding: 4px 8px;
            color: #666; font-size: 12px; line-height: 1;
        }
        .part-type-autocomplete__dropdown {
            position: absolute; top: 100%; left: 0; right: 0; z-index: 1000;
            margin: 2px 0 0; padding: 4px 0;
            background: #fff; border: 1px solid #ccc; border-radius: 4px;
            max-height: 260px; overflow-y: auto;
            list-style: none;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }
        .part-type-autocomplete__option {
            padding: 8px 14px; cursor: pointer; font-size: 13px; color: #1a1a1a;
        }
        .part-type-autocomplete__option:hover,
        .part-type-autocomplete__option.is-active {
            background: #e9f3ff;
        }
        .part-type-autocomplete__empty {
            padding: 10px 14px; color: #888; font-size: 12px; font-style: italic;
        }
        [data-theme="dark"] .part-type-autocomplete__dropdown,
        body.dark-mode .part-type-autocomplete__dropdown {
            background: #2b2b2b; border-color: #444; color: #ddd;
        }
        [data-theme="dark"] .part-type-autocomplete__option,
        body.dark-mode .part-type-autocomplete__option { color: #ddd; }
        [data-theme="dark"] .part-type-autocomplete__option:hover,
        body.dark-mode .part-type-autocomplete__option:hover { background: #3a4a60; }
        </style>
        """

        # JS — связывает input с его dropdown через ближайший родитель .part-type-autocomplete.
        # Делегирование событий — без зависимостей.
        js = """
        <script>
        (function(){
          if (window.__partTypeAutocompleteInit) return;
          window.__partTypeAutocompleteInit = true;
          document.addEventListener('focusin', function(e){
            if (!e.target.classList.contains('part-type-autocomplete__input')) return;
            openDropdown(e.target);
            filterOptions(e.target);
          });
          document.addEventListener('input', function(e){
            if (!e.target.classList.contains('part-type-autocomplete__input')) return;
            openDropdown(e.target);
            filterOptions(e.target);
          });
          document.addEventListener('click', function(e){
            // Клик по стрелке-toggle
            if (e.target.classList.contains('part-type-autocomplete__toggle')) {
              var wrap = e.target.closest('.part-type-autocomplete');
              var input = wrap.querySelector('.part-type-autocomplete__input');
              var dd = wrap.querySelector('.part-type-autocomplete__dropdown');
              if (dd.hasAttribute('hidden')) {
                openDropdown(input);
                filterOptions(input);
                input.focus();
              } else {
                closeDropdown(wrap);
              }
              return;
            }
            // Клик по опции
            if (e.target.classList.contains('part-type-autocomplete__option')) {
              var wrap = e.target.closest('.part-type-autocomplete');
              var input = wrap.querySelector('.part-type-autocomplete__input');
              input.value = e.target.dataset.value;
              closeDropdown(wrap);
              return;
            }
            // Клик вне — закрыть все
            document.querySelectorAll('.part-type-autocomplete').forEach(function(w){
              if (!w.contains(e.target)) closeDropdown(w);
            });
          });
          // Esc закрывает
          document.addEventListener('keydown', function(e){
            if (e.key !== 'Escape') return;
            if (!e.target.classList.contains('part-type-autocomplete__input')) return;
            closeDropdown(e.target.closest('.part-type-autocomplete'));
          });

          function openDropdown(input){
            var dd = input.parentElement.querySelector('.part-type-autocomplete__dropdown');
            if (dd) dd.removeAttribute('hidden');
          }
          function closeDropdown(wrap){
            var dd = wrap.querySelector('.part-type-autocomplete__dropdown');
            if (dd) dd.setAttribute('hidden', '');
          }
          function filterOptions(input){
            var wrap = input.parentElement;
            var dd = wrap.querySelector('.part-type-autocomplete__dropdown');
            var q = input.value.trim().toLowerCase();
            var visible = 0, exact = false;
            wrap.querySelectorAll('.part-type-autocomplete__option').forEach(function(opt){
              var val = opt.dataset.value.toLowerCase();
              var match = !q || val.indexOf(q) !== -1;
              opt.style.display = match ? '' : 'none';
              if (match) visible++;
              if (val === q) exact = true;
            });
            // Подсказка "будет создан новый" — когда есть текст, нет совпадений, не точное совпадение
            var empty = dd.querySelector('.part-type-autocomplete__empty');
            if (empty) {
              if (q && visible === 0) empty.removeAttribute('hidden');
              else empty.setAttribute('hidden', '');
            }
          }
        })();
        </script>
        """

        return mark_safe(css + widget_html + js)


class SparePartAdminForm(forms.ModelForm):
    """Форма SparePart с гибридным полем 'тип':
    - Пользователь либо выбирает существующий тип из datalist,
    - либо вводит новое название (case-insensitive дедуп через get_or_create_normalized).
    Поле обязательное. Перевод типа (UZ/EN) редактируется отдельно в админке типов.
    """

    # Подмена FK на CharField — у пользователя одно текстовое поле с автодополнением
    type = forms.CharField(
        label='Тип запчасти',
        max_length=100,
        required=True,
        widget=_TypeAutocompleteWidget(),
        help_text='Введите новый тип или выберите из подсказок. Регистр не важен — '
                  '"Двигатель" и "двигатель" сохранятся как один тип. '
                  'UZ/EN-перевод добавляется в разделе «Магазин — Типы запчастей».',
    )

    class Meta:
        model = SparePart
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # При редактировании Django через model_to_dict кладёт в self.initial['type']
        # ID грузовика (число), а у нас CharField — нужно подменить на текстовое имя.
        # Перезаписываем именно self.initial, а не self.fields['type'].initial —
        # второе игнорируется когда ключ уже есть в self.initial.
        if self.instance and self.instance.pk and self.instance.type_id:
            self.initial['type'] = (
                self.instance.type.name_ru or self.instance.type.name
            )

    def clean_type(self):
        """Возвращает уже готовый SparePartType instance.
        Делаем дедуп+создание прямо здесь, чтоб construct_instance() получил FK-объект,
        а не строку (иначе ValueError на присвоение строки в FK).
        """
        raw = self.cleaned_data.get('type', '')
        normalized = normalize_type_name(raw)
        if not normalized:
            raise forms.ValidationError('Тип запчасти обязателен.')
        return SparePartType.get_or_create_normalized(normalized)