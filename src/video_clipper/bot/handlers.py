"""
Обработчики команд Telegram-бота.

Регистрирует команды /start, /status, /sources для aiogram Dispatcher.
Показывает текущее состояние pipeline, список источников и статистику.

Реализация: этап 3.
"""

import logging
from video_clipper.config import Config
from video_clipper.database import Database

logger = logging.getLogger(__name__)


async def setup_handlers(dp: object, config: Config, db: Database) -> None:
    """
    Зарегистрировать обработчики команд бота.

    Команды:
        /start   — приветствие и статус системы
        /status  — состояние pipeline и очереди
        /sources — список активных каналов-источников
    """
    logger.warning("setup_handlers() not implemented yet (stage 3)")
