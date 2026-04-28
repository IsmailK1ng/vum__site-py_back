from asgiref.sync import sync_to_async

from main.services.telegram.bot_service import BotService


@sync_to_async
def get_message(key: str, language: str, **kwargs) -> str:
    return BotService.get_message(key, language, **kwargs)


@sync_to_async
def get_config():
    return BotService.get_config()


@sync_to_async
def read_file(path: str) -> bytes:
    with open(path, 'rb') as f:
        return f.read()