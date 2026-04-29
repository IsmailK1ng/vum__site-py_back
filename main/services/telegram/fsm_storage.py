import json
import logging
from typing import Any

from aiogram.fsm.storage.base import BaseStorage, StorageKey, StateType
from asgiref.sync import sync_to_async

logger = logging.getLogger('bot')


class DatabaseStorage(BaseStorage):

    @staticmethod
    def _make_key(key: StorageKey) -> str:
        return f'{key.bot_id}:{key.chat_id}:{key.user_id}'

    @sync_to_async
    def _get_record(self, raw_key: str):
        from main.models import BotFSMState
        try:
            return BotFSMState.objects.get(key=raw_key)
        except BotFSMState.DoesNotExist:
            return None

    @sync_to_async
    def _save_record(self, raw_key: str, state: str | None, data: str) -> None:
        from main.models import BotFSMState
        BotFSMState.objects.update_or_create(
            key=raw_key,
            defaults={'state': state, 'data': data},
        )

    @sync_to_async
    def _delete_record(self, raw_key: str) -> None:
        from main.models import BotFSMState
        BotFSMState.objects.filter(key=raw_key).delete()

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        raw_key = self._make_key(key)
        record = await self._get_record(raw_key)
        current_data = record.data if record else '{}'
        state_str = state.state if hasattr(state, 'state') else state
        await self._save_record(raw_key, state_str, current_data)

    async def get_state(self, key: StorageKey) -> str | None:
        raw_key = self._make_key(key)
        record = await self._get_record(raw_key)
        return record.state if record else None

    async def set_data(self, key: StorageKey, data: dict[str, Any]) -> None:
        raw_key = self._make_key(key)
        record = await self._get_record(raw_key)
        current_state = record.state if record else None
        await self._save_record(raw_key, current_state, json.dumps(data, ensure_ascii=False))

    async def get_data(self, key: StorageKey) -> dict[str, Any]:
        raw_key = self._make_key(key)
        record = await self._get_record(raw_key)
        if not record or not record.data:
            return {}
        try:
            return json.loads(record.data)
        except json.JSONDecodeError:
            logger.error('FSM data decode error key=%s', raw_key)
            return {}

    async def close(self) -> None:
        pass