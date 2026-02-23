"""
Загрузчик видео из Telegram.

Скачивает видео по source_chat_id + source_message_id в директорию
storage/downloads/, обновляет статус видео в БД.

Реализация: этап 2.
"""

import logging
from video_clipper.config import Config
from video_clipper.database import Database

logger = logging.getLogger(__name__)


class VideoDownloader:
    """Загрузка видео из Telegram. Заглушка для этапа 2."""

    def __init__(self, config: Config, db: Database) -> None:
        self.config = config
        self.db = db

    async def download(self, video_id: int) -> str | None:
        """
        Скачать видео по video_id.
        Возвращает путь к файлу или None при ошибке.
        """
        logger.warning("VideoDownloader.download() not implemented yet (stage 2)")
        return None
