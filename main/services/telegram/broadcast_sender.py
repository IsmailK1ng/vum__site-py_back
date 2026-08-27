"""
Единая точка отправки одной рассылки (BotBroadcast).

Раньше эта логика — выбор получателей, цикл отправки, разбор ошибок
Telegram, обновление статуса — была продублирована почти дословно в
BotBroadcastAdmin.send_now (admin.py) и в management-команде
send_broadcasts.py. Копии успели разойтись: обе игнорировали
TelegramUser.notifications_enabled (админ выключает уведомления
конкретному пользователю — рассылка всё равно уходила), а "правильная"
версия фильтра (BotService.get_broadcast_recipients) была мёртвым кодом,
которую никто не вызывал.

Теперь и админка, и cron дёргают send_broadcast() отсюда — один источник
правды на выбор получателей, отправку и статус рассылки.
"""
import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup
from asgiref.sync import sync_to_async

from main.services.telegram.bot_service import BotService

logger = logging.getLogger('bot')

_SEND_DELAY = 0.05  # ~20 сообщений/сек — под лимитом Telegram Bot API
_GROUP_LANGUAGE = 'ru'  # у группы нет "языка пользователя" — берём деловой ru


@sync_to_async
def get_recipients(broadcast) -> list[dict]:
    """Публичная — переиспользуется command'ой send_broadcasts для --dry-run."""
    return list(
        BotService.get_broadcast_recipients(broadcast).values('telegram_id', 'language')
    )


@sync_to_async
def get_group_chat_ids(broadcast) -> list[int]:
    if not broadcast.send_to_groups:
        return []
    return BotService.get_active_group_chat_ids()


@sync_to_async
def _mark_sending(broadcast, total: int) -> None:
    BotService.mark_broadcast_sending(broadcast, total)


@sync_to_async
def _mark_done(broadcast, stats: dict) -> None:
    BotService.mark_broadcast_done(broadcast, stats)


@sync_to_async
def _mark_failed(broadcast) -> None:
    BotService.mark_broadcast_failed(broadcast)


@sync_to_async
def _mark_blocked(telegram_id: int) -> None:
    BotService.mark_user_blocked(telegram_id)


@sync_to_async
def _mark_group_removed(chat_id: int) -> None:
    BotService.deactivate_bot_group(chat_id)


@sync_to_async
def _record_delivery(broadcast, chat_id: int, message_id: int, is_group: bool) -> None:
    BotService.record_broadcast_delivery(broadcast, chat_id, message_id, is_group)


@sync_to_async
def get_revocable_deliveries(broadcast) -> list[dict]:
    """Публичная — переиспользуется admin-действием «Отозвать рассылку»."""
    return list(
        BotService.get_revocable_deliveries(broadcast).values('id', 'chat_id', 'message_id')
    )


@sync_to_async
def _mark_delivery_revoked(delivery_id: int) -> None:
    BotService.mark_delivery_revoked(delivery_id)


async def send_broadcast(bot: Bot, broadcast) -> dict:
    """
    Отправляет одну рассылку — персональным получателям (по target)
    и, если включён send_to_groups, во все активные группы бота
    (см. BotGroup / handlers/group_membership.py). Возвращает статистику
    {'total', 'sent', 'failed', 'blocked'}. Обновляет статус broadcast
    в БД по ходу (sending -> done, либо failed при краше на середине).
    """
    recipients = await get_recipients(broadcast)
    group_chat_ids = await get_group_chat_ids(broadcast)

    # Единый список получателей: (chat_id, язык, признак "это группа")
    # — группе при блокировке снимаем is_active у BotGroup, а не
    # TelegramUser.is_blocked.
    targets = [
        (r['telegram_id'], r['language'] or 'ru', False) for r in recipients
    ] + [
        (chat_id, _GROUP_LANGUAGE, True) for chat_id in group_chat_ids
    ]

    total = len(targets)
    await _mark_sending(broadcast, total)

    if not targets:
        stats = {'total': 0, 'sent': 0, 'failed': 0, 'blocked': 0}
        await _mark_done(broadcast, stats)
        return stats

    reply_markup = None
    if broadcast.button_text and broadcast.button_url:
        reply_markup = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text=broadcast.button_text, url=broadcast.button_url)
        ]])

    # broadcast.image.url — относительный путь (/media/...), Telegram по
    # такому URL ничего скачать не может ("URL host is empty"). Первый раз
    # шлём сам файл с диска (FSInputFile), а полученный от Telegram file_id
    # переиспользуем для всех остальных получателей — иначе на каждую
    # отправку файл заново читался бы и заливался с нуля.
    photo_source = FSInputFile(broadcast.image.path) if broadcast.image else None

    sent = failed = blocked = 0

    try:
        for chat_id, lang, is_group in targets:
            text = broadcast.get_text(lang)

            if not text:
                failed += 1
                continue

            try:
                if photo_source is not None:
                    msg = await bot.send_photo(
                        chat_id=chat_id,
                        photo=photo_source,
                        caption=text,
                        reply_markup=reply_markup,
                    )
                    if isinstance(photo_source, FSInputFile):
                        photo_source = msg.photo[-1].file_id
                else:
                    msg = await bot.send_message(
                        chat_id=chat_id,
                        text=text,
                        reply_markup=reply_markup,
                    )
                sent += 1
                await _record_delivery(broadcast, chat_id, msg.message_id, is_group)

            except TelegramForbiddenError:
                blocked += 1
                if is_group:
                    await _mark_group_removed(chat_id)
                else:
                    await _mark_blocked(chat_id)

            except TelegramBadRequest as exc:
                logger.warning('Broadcast bad request chat_id=%s: %s', chat_id, exc)
                failed += 1

            except Exception as exc:
                logger.error('Broadcast send error chat_id=%s: %s', chat_id, exc)
                failed += 1

            await asyncio.sleep(_SEND_DELAY)

    except Exception:
        # Крашнулись на середине цикла — не оставляем рассылку висеть в
        # статусе "sending" навсегда, помечаем как failed и пробрасываем
        # дальше, чтобы вызывающий код (admin/cron) тоже узнал об ошибке.
        logger.error('send_broadcast crashed mid-run, broadcast#%s', broadcast.pk, exc_info=True)
        await _mark_failed(broadcast)
        raise

    stats = {'total': total, 'sent': sent, 'failed': failed, 'blocked': blocked}
    await _mark_done(broadcast, stats)
    return stats


async def revoke_broadcast(bot: Bot, broadcast) -> dict:
    """
    Удаляет уже отправленные сообщения этой рассылки у всех получателей
    (Telegram deleteMessage) — на случай, если ушла неверная информация.

    Работает только по доставкам, записанным через BroadcastDelivery —
    т.е. только для рассылок, отправленных ПОСЛЕ появления этого учёта.
    Более старые рассылки отозвать нечем: message_id для них нигде не
    сохранён.

    Ограничение — не этого проекта, а самого Telegram Bot API: удалить
    можно только сообщение, отправленное не позднее 48 часов назад.
    Возвращает {'total', 'revoked', 'failed'}.
    """
    deliveries = await get_revocable_deliveries(broadcast)
    total = len(deliveries)
    revoked = failed = 0

    for d in deliveries:
        try:
            await bot.delete_message(chat_id=d['chat_id'], message_id=d['message_id'])
            await _mark_delivery_revoked(d['id'])
            revoked += 1

        except Exception as exc:
            logger.warning(
                'Revoke failed delivery#%s chat_id=%s message_id=%s: %s',
                d['id'], d['chat_id'], d['message_id'], exc,
            )
            failed += 1

        await asyncio.sleep(_SEND_DELAY)

    return {'total': total, 'revoked': revoked, 'failed': failed}
