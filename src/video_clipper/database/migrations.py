import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from video_clipper.database.models import Database

logger = logging.getLogger(__name__)

CURRENT_VERSION = 1


async def run_migrations(db: "Database") -> None:
    """
    Выполняет автомиграции базы данных.
    Версия схемы хранится в таблице settings по ключу 'schema_version'.
    Версия 1 — начальная схема (init_tables).
    """
    version_str = await db.get_setting("schema_version", "0")
    version = int(version_str)
    logger.info(f"Current schema version: {version}, target: {CURRENT_VERSION}")

    if version < 1:
        logger.info("Applying migration v1: initial schema")
        await db.init_tables()
        await db.set_setting("schema_version", "1")
        logger.info("Migration v1 applied")

    if version == CURRENT_VERSION:
        logger.debug("Database schema is up to date")
