"""
Обёртка над Telethon для мониторинга Telegram-каналов.

Управляет подключением, сессией и передачей событий в monitor.py.
Переиспользует паттерн из TGForwardez.

Реализация: этап 2.
"""

import logging
from video_clipper.config import Config
from video_clipper.database import Database

logger = logging.getLogger(__name__)


class TelegramClientWrapper:
    """Обёртка над Telethon. Заглушка для этапа 2."""

    def __init__(self, config: Config, db: Database) -> None:
        self.config = config
        self.db = db

    async def connect(self) -> None:
        """Подключиться к Telegram через Telethon."""
        logger.warning("TelegramClientWrapper.connect() not implemented yet (stage 2)")

    async def disconnect(self) -> None:
        """Отключиться от Telegram."""
        logger.warning("TelegramClientWrapper.disconnect() not implemented yet (stage 2)")
