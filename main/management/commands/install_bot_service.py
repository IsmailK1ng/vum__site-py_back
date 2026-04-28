import os
import subprocess
import sys
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


BOT_SERVICE_NAME = 'faw_bot'

SYSTEMD_DIR = Path('/etc/systemd/system')

SERVICE_TEMPLATE = """\
[Unit]
Description=FAW.UZ Telegram Bot
Documentation=https://faw.uz
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User={user}
Group={group}
WorkingDirectory={work_dir}

# Полный путь к python в venv — НЕ менять на системный python
ExecStart={python_path} manage.py run_bot

# Перезапуск при падении. НЕ перезапускать при намеренной остановке (exit 0)
Restart=on-failure
RestartSec=10
StartLimitIntervalSec=60
StartLimitBurst=3

# Логирование в journald
StandardOutput=journal
StandardError=journal
SyslogIdentifier={service_name}

# Переменные окружения из .env файла
EnvironmentFile={env_file}

# Безопасность
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
"""

SUDOERS_TEMPLATE = """\
# Разрешить {user} управлять ботом без пароля
# Файл: /etc/sudoers.d/faw_bot
# Создан командой: python manage.py install_bot_service
{user} ALL=(ALL) NOPASSWD: \\
    /bin/systemctl start {service_name}, \\
    /bin/systemctl stop {service_name}, \\
    /bin/systemctl restart {service_name}, \\
    /bin/systemctl status {service_name}
"""


class Command(BaseCommand):
    help = (
        'Устанавливает systemd сервис для Telegram бота. '
        'Запускать от root или через sudo.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            default='www-data',
            help='Пользователь от которого запускается сервис (default: www-data)',
        )
        parser.add_argument(
            '--group',
            default='www-data',
            help='Группа пользователя (default: www-data)',
        )
        parser.add_argument(
            '--env-file',
            default=None,
            help='Путь к .env файлу (default: <project_dir>/.env)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать что будет создано без реального создания файлов',
        )
        parser.add_argument(
            '--print-sudoers',
            action='store_true',
            help='Вывести строку для sudoers (не устанавливать автоматически)',
        )

    def handle(self, *args, **options):
        # ── Проверки ──────────────────────────────────────────────

        if sys.platform != 'linux':
            raise CommandError(
                f'systemd доступен только на Linux. '
                f'Текущая платформа: {sys.platform}'
            )

        if not SYSTEMD_DIR.exists():
            raise CommandError(
                f'Директория {SYSTEMD_DIR} не найдена. '
                f'Убедитесь что systemd установлен.'
            )

        # ── Пути ──────────────────────────────────────────────────

        # Директория проекта — где manage.py
        work_dir = Path(settings.BASE_DIR)

        # Python из текущего venv
        python_path = Path(sys.executable)

        # .env файл
        env_file = options['env_file']
        if env_file is None:
            env_file = work_dir / '.env'
        else:
            env_file = Path(env_file)

        if not env_file.exists():
            self.stdout.write(
                self.style.WARNING(
                    f'Предупреждение: .env файл не найден по пути {env_file}. '
                    f'Сервис будет создан, но переменные окружения не загрузятся.'
                )
            )

        service_file = SYSTEMD_DIR / f'{BOT_SERVICE_NAME}.service'
        user  = options['user']
        group = options['group']

        # ── Генерация контента ────────────────────────────────────

        service_content = SERVICE_TEMPLATE.format(
            service_name=BOT_SERVICE_NAME,
            user=user,
            group=group,
            work_dir=work_dir,
            python_path=python_path,
            env_file=env_file,
        )

        # ── Dry run ───────────────────────────────────────────────

        if options['dry_run']:
            self.stdout.write(self.style.SUCCESS('\n=== DRY RUN ===\n'))
            self.stdout.write(f'Файл сервиса: {service_file}\n')
            self.stdout.write('─' * 60)
            self.stdout.write(service_content)
            self.stdout.write('─' * 60)
            self.stdout.write('\nКоманды которые будут выполнены:')
            self.stdout.write(f'  systemctl daemon-reload')
            self.stdout.write(f'  systemctl enable {BOT_SERVICE_NAME}')
            return

        # ── Sudoers вывод ─────────────────────────────────────────

        if options['print_sudoers']:
            sudoers = SUDOERS_TEMPLATE.format(
                user=user,
                service_name=BOT_SERVICE_NAME,
            )
            self.stdout.write(self.style.SUCCESS('\n=== SUDOERS ==='))
            self.stdout.write('Добавьте в /etc/sudoers.d/faw_bot:')
            self.stdout.write('─' * 60)
            self.stdout.write(sudoers)
            self.stdout.write('─' * 60)
            self.stdout.write(
                'Команда: sudo visudo -f /etc/sudoers.d/faw_bot'
            )
            return

        # ── Проверка прав ─────────────────────────────────────────

        if os.geteuid() != 0:
            raise CommandError(
                'Нет прав на запись в /etc/systemd/system/. '
                'Запустите с sudo: sudo python manage.py install_bot_service'
            )

        # ── Создание файла сервиса ────────────────────────────────

        if service_file.exists():
            self.stdout.write(
                self.style.WARNING(
                    f'Файл {service_file} уже существует. Перезаписываем...'
                )
            )

        try:
            service_file.write_text(service_content, encoding='utf-8')
            # Права: root читает/пишет, остальные только читают
            service_file.chmod(0o644)
        except PermissionError as exc:
            raise CommandError(f'Ошибка записи файла: {exc}')

        self.stdout.write(
            self.style.SUCCESS(f'Файл сервиса создан: {service_file}')
        )

        # ── systemctl daemon-reload ───────────────────────────────

        try:
            result = subprocess.run(
                ['systemctl', 'daemon-reload'],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                self.stdout.write(self.style.SUCCESS('daemon-reload выполнен'))
            else:
                self.stdout.write(
                    self.style.ERROR(f'daemon-reload ошибка: {result.stderr}')
                )
        except subprocess.TimeoutExpired:
            raise CommandError('daemon-reload завис (timeout 30s)')

        # ── systemctl enable ──────────────────────────────────────

        try:
            result = subprocess.run(
                ['systemctl', 'enable', BOT_SERVICE_NAME],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if result.returncode == 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Сервис {BOT_SERVICE_NAME} включён в автозапуск'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'enable предупреждение: {result.stderr}'
                    )
                )
        except subprocess.TimeoutExpired:
            self.stdout.write(self.style.WARNING('enable timeout — пропущен'))

        # ── Итог ─────────────────────────────────────────────────

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== Установка завершена ==='))
        self.stdout.write(f'Сервис:     {BOT_SERVICE_NAME}')
        self.stdout.write(f'Python:     {python_path}')
        self.stdout.write(f'Директория: {work_dir}')
        self.stdout.write(f'.env файл:  {env_file}')
        self.stdout.write('')
        self.stdout.write('Следующие шаги:')
        self.stdout.write(
            f'  1. sudo systemctl start {BOT_SERVICE_NAME}'
        )
        self.stdout.write(
            f'  2. sudo systemctl status {BOT_SERVICE_NAME}'
        )
        self.stdout.write(
            f'  3. Добавить sudoers (для управления из Admin):'
        )
        self.stdout.write(
            f'     python manage.py install_bot_service --print-sudoers'
        )
        self.stdout.write(
            f'  4. Управление: Django Admin -> Бот -> Конфигурация'
        )
        self.stdout.write('')
        self.stdout.write('Просмотр логов:')
        self.stdout.write(
            f'  journalctl -u {BOT_SERVICE_NAME} -f'
        )