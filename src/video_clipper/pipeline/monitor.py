"""
Монитор Telegram-каналов.

Слушает source-каналы через Telethon, фильтрует входящие видео
(duration >= 30 сек), создаёт записи в БД и уведомляет оркестратор.

Реализация: этап 2.
"""

import logging
from video_clipper.config import Config
from video_clipper.database import Database

logger = logging.getLogger(__name__)


class TelegramMonitor:
    """Мониторинг Telegram-каналов через Telethon. Заглушка для этапа 2."""

    def __init__(self, config: Config, db: Database) -> None:
        self.config = config
        self.db = db

    async def start(self) -> None:
        """Подключиться к Telegram и начать прослушивать каналы."""
        logger.warning("TelegramMonitor.start() not implemented yet (stage 2)")

    async def stop(self) -> None:
        """Отключиться от Telegram."""
        logger.warning("TelegramMonitor.stop() not implemented yet (stage 2)")
