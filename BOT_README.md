
## Стек
- Python 3.13, Django 5.2.6, PostgreSQL
- aiogram 3.17.0
- FSM Storage: PostgreSQL (DatabaseStorage — без Redis)
- AmoCRM интеграция

## Архитектура
```
handlers → BotService → Django ORM
                ↓
         _fire_and_forget (daemon thread)
                ↓
    LeadSender (AmoCRM) + TelegramNotificationSender
```

FSM состояния хранятся в таблице `main_botfsmstate` (PostgreSQL).
При перезапуске бота состояния сохраняются — пользователи продолжают с того же места.

---

## Первый деплой на сервер

### 1. Подключиться к серверу
```bash
ssh golang@IP_СЕРВЕРА
cd ~/vum__site-py_back
source venv/bin/activate
```

### 2. Подтянуть код
```bash
git pull origin main
```

### 3. Установить зависимости
```bash
pip install -r requirements.txt
```

### 4. Проверить .env
Убедись что в `.env` есть:
```env
TIME_ZONE=Asia/Tashkent
DEBUG=False
```
Redis не нужен — FSM хранится в PostgreSQL.

### 5. Применить миграции
```bash
python manage.py migrate
```
Применятся миграции 0018_bot_models, 0019_bot_fsm_state и другие.

### 6. Заполнить тексты бота
```bash
python manage.py init_bot_data --force
```
Заполняет таблицу BotMessage (141 запись на 3 языках).
Запускать один раз при первом деплое.

### 7. Создать BotConfig в Admin
Открыть `https://faw.uz/admin/main/botconfig/` → Добавить:
- Токен бота (из @BotFather)
- Username бота
- Chat ID для уведомлений
- Поставить галочку "Бот активен"
- URL сайта: https://faw.uz


### 9. Установить systemd сервис
```bash
sudo python manage.py install_bot_service
```
Создаёт `/etc/systemd/system/faw_bot.service` — автозапуск при старте сервера.

### 10. Настроить sudoers (для кнопок в Admin)
```bash
python manage.py install_bot_service --print-sudoers
```
Скопировать вывод и добавить через `sudo visudo`.

### 11. Запустить бота
```bash
sudo systemctl start faw_bot
sudo systemctl status faw_bot
```
Должно показать `active (running)`.

### 12. Проверить логи
```bash
journalctl -u faw_bot -f
# или
tail -f logs/bot.log
```
Должно быть:
```
Bot initialized successfully
Starting polling...
```

### 13. Настроить cron
```bash
crontab -e
```
Добавить (заменить путь на реальный):
```
# Напоминания о тест-драйве — каждый день в 09:00 по Ташкенту
0 9 * * * /home/golang/vum__site-py_back/venv/bin/python /home/golang/vum__site-py_back/manage.py send_reminders >> /home/golang/vum__site-py_back/logs/cron.log 2>&1

# Обновление AmoCRM токенов — каждые 12 часов
0 */12 * * * /home/golang/vum__site-py_back/venv/bin/python /home/golang/vum__site-py_back/manage.py save_amocrm_tokens >> /home/golang/vum__site-py_back/logs/cron.log 2>&1
```

### 14. Перезапустить gunicorn
```bash
sudo systemctl restart gunicorn
```

---

## Обновление кода (деплой новой версии)

```bash
cd ~/vum__site-py_back
source venv/bin/activate
git pull origin main
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart faw_bot
sudo systemctl restart gunicorn
```

---

## Управление ботом

| Действие | Команда |
|----------|---------|
| Запустить | `sudo systemctl start faw_bot` |
| Остановить | `sudo systemctl stop faw_bot` |
| Перезапустить | `sudo systemctl restart faw_bot` |
| Статус | `sudo systemctl status faw_bot` |
| Логи live | `journalctl -u faw_bot -f` |

Или через Admin → Бот → Конфигурация → кнопки Запустить/Остановить/Перезапустить.

---

## Рассылки

1. Admin → Бот → Рассылки → Добавить
2. Заполнить текст на ru/uz/en
3. Выбрать аудиторию
4. Статус → "Запланирована"
5. Отметить чекбокс → Action "Запустить рассылку сейчас"

---

## Management commands

| Команда | Когда запускать |
|---------|----------------|
| `python manage.py run_bot` | Запуск бота (на проде через systemd) |
| `python manage.py init_bot_data --force` | Первый деплой или сброс текстов |
| `python manage.py send_broadcasts` | Резервный запуск рассылок через терминал |
| `python manage.py send_reminders` | Запускается автоматически через cron |
| `python manage.py save_amocrm_tokens` | Когда протухли токены AmoCRM |
| `python manage.py install_bot_service` | Один раз при первом деплое |
| `python manage.py prod_health_check` | После деплоя для проверки |

---

## Структура handlers

| Файл | Отвечает за |
|------|-------------|
| start.py | /start, регистрация, выбор языка |
| catalog.py | Каталог, скачать PDF, лид из каталога, избранное |
| dealers.py | Список дилеров |
| test_drive.py | Флоу записи на тест-драйв |
| leasing.py | Лизинговый калькулятор |
| lead.py | Оставить заявку из меню |
| faq.py | Вопросы и ответы |
| profile.py | Профиль, избранное, отмена тест-драйва |
| news.py | Новости и акции с навигацией |
| contacts.py | Контакты компании |
| common.py | Fallback, смена языка из любого состояния |

---

## Тексты бота

Все тексты хранятся в БД → Admin → Бот → Тексты.
Изменения применяются сразу без деплоя (post_save сигнал сбрасывает кеш).

Сбросить все тексты к дефолту:
```bash
python manage.py init_bot_data --force
```

---

## Переменные окружения

| Переменная | Описание |
|------------|---------|
| `TIME_ZONE` | Часовой пояс (Asia/Tashkent) |
| `DEBUG` | False на проде |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD` | PostgreSQL |

Токен бота, chat_id уведомлений — хранятся в БД через Admin → Бот → Конфигурация.
Redis не используется — FSM хранится в PostgreSQL.

---

## Известные особенности

- Кнопки Запустить/Остановить в Admin работают только на Linux с systemd
- При первом деплое обязательно запустить `init_bot_data --force`
- AmoCRM токены обновлять через `save_amocrm_tokens` при протухании
- Фото каталога читаются с диска напрямую — nginx сервит media/ директорию
- FSM состояния в таблице `main_botfsmstate` — очищать не нужно, Django ORM управляет автоматически
```

Потом:

```bash
git add BOT_README.md
git commit -m "docs: update BOT_README — remove Redis, add DatabaseStorage"
git push origin main
```