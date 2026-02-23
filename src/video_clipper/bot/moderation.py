"""
Модерация клипов через Telegram inline-кнопки.

Отправляет клип на модерацию в tech-канал с кнопками Approve/Reject.
Обрабатывает callback-запросы от кнопок.

Реализация: этап 3.
"""

import logging
from video_clipper.config import Config
from video_clipper.database import Database

logger = logging.getLogger(__name__)


async def setup_moderation(dp: object, config: Config, db: Database) -> None:
    """
    Зарегистрировать обработчики inline-кнопок модерации.

    Кнопки:
        ✅ Опубликовать — одобрить и запустить публикацию
        ❌ Отклонить    — отклонить клип
        📝 Редактировать — изменить заголовок/описание
        ⏰ Отложить    — запланировать публикацию позже
    """
    logger.warning("setup_moderation() not implemented yet (stage 3)")
