### 1. Установить Redis
```bash
sudo apt update && sudo apt install -y redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
redis-cli ping  # должен ответить PONG
```

### 2. Настроить .env
```env
REDIS_URL=redis://localhost:6379/0
TIME_ZONE=Asia/Tashkent
```

### 3. Применить миграции
```bash
python manage.py migrate
```

### 4. Заполнить тексты бота
```bash
python manage.py init_bot_data --force
```

### 5. Обновить AmoCRM токены
```bash
python manage.py save_amocrm_tokens
```

### 6. Установить systemd сервис
```bash
sudo python manage.py install_bot_service
```

### 7. Настроить sudoers (для кнопок в Admin)
```bash
python manage.py install_bot_service --print-sudoers
```

### 8. Запустить бота
```bash
sudo systemctl start faw_bot
sudo systemctl status faw_bot
```

### 9. Проверить логи
```bash
journalctl -u faw_bot -f
# или
tail -f logs/bot.log
```

## Cron задачи (настроить на сервере)

```bash
crontab -e
```

Добавить строки:
Напоминания о тест-драйве — каждый день в 09:00 по Ташкенту
0 9 * * * /path/to/venv/bin/python /path/to/manage.py send_reminders
Обновление AmoCRM токенов — каждые 12 часов
0 */12 * * * /path/to/venv/bin/python /path/to/manage.py save_amocrm_tokens

## Рассылки

1. Admin → Бот → Рассылки → Добавить
2. Заполнить текст на ru/uz/en
3. Выбрать аудиторию
4. Статус → "Запланирована"
5. Отметить чекбокс → Action "Запустить рассылку сейчас"

## Управление ботом

| Действие | Команда |
|----------|---------|
| Запустить | `sudo systemctl start faw_bot` |
| Остановить | `sudo systemctl stop faw_bot` |
| Перезапустить | `sudo systemctl restart faw_bot` |
| Статус | `sudo systemctl status faw_bot` |
| Логи live | `journalctl -u faw_bot -f` |

Или через Admin → Бот → Конфигурация → кнопки Запустить/Остановить/Перезапустить.

## Обновление кода (деплой новой версии)

```bash
git pull origin main
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart faw_bot
```

## Структура handlers

| Файл | Отвечает за |
|------|-------------|
| start.py | /start, регистрация, выбор языка |
| catalog.py | Каталог, лид из каталога, избранное |
| dealers.py | Список дилеров |
| test_drive.py | Флоу записи на тест-драйв |
| leasing.py | Лизинговый калькулятор |
| lead.py | Оставить заявку из меню |
| faq.py | Вопросы и ответы |
| profile.py | Профиль, избранное, отмена тест-драйва |
| news.py | Новости и акции с навигацией |
| contacts.py | Контакты компании |
| common.py | Fallback, язык из любого состояния |

## Тексты бота

Все тексты хранятся в БД → Admin → Бот → Тексты.
Изменения применяются сразу без деплоя (кеш сбрасывается автоматически).

Сбросить все тексты к дефолту:
```bash
python manage.py init_bot_data --force
```

## Переменные окружения для бота

| Переменная | Описание |
|------------|---------|
| REDIS_URL | URL Redis для FSM (redis://localhost:6379/0) |
| TIME_ZONE | Часовой пояс (Asia/Tashkent) |

Токен бота, chat_id уведомлений — хранятся в БД через Admin → Бот → Конфигурация.

## Известные ограничения

- Кнопки Запустить/Остановить в Admin работают только на Linux с systemd
- При первом деплое обязательно запустить `init_bot_data --force`
- AmoCRM токены обновлять через `save_amocrm_tokens` при протухании