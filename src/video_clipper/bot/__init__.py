"""Telegram-бот: команды и модерация."""

from video_clipper.bot.handlers import router as handlers_router
from video_clipper.bot.moderation import router as moderation_router

__all__ = ["handlers_router", "moderation_router"]
