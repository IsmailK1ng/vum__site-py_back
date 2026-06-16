from django.apps import AppConfig

class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'
    
    def ready(self):
        import main.admin
        import main.signals
        # Регистрация сигналов очистки orphan-файлов
        # (старый файл удаляется при замене ImageField или удалении объекта)
        from main.signals_cleanup import register_all
        register_all()
