import asyncio
import logging
from video_clipper.config import load_config
from video_clipper.database import Database
from video_clipper.utils.logging_config import setup_logging

logger = logging.getLogger(__name__)

BANNER = """
╔══════════════════════════════════════╗
║        VIDEO CLIPPER v0.1.0          ║
║   Telegram → Clips → VK / Telegram  ║
╚══════════════════════════════════════╝
"""


async def main():
    # 1. Загрузить конфиг
    config = load_config()

    # 2. Настроить логирование
    setup_logging()

    # 3. Показать баннер
    print(BANNER)
    logger.info("Starting Video Clipper...")

    # 4. Показать режим
    if config.dev_mode:
        logger.info("MODE: Development")
        logger.info(f"  Mock GPU:      {config.mock_gpu}")
        logger.info(f"  Mock Selector: {config.mock_selector}")
        logger.info(f"  Mock Monitor:  {config.mock_monitor}")
    else:
        logger.info("MODE: Production")

    # 5. Инициализировать БД
    db = Database(config.db_path)
    await db.init_tables()
    logger.info(f"Database ready: {config.db_path}")

    # 6. Импортировать заглушки — проверка что всё грузится
    from video_clipper.pipeline.orchestrator import PipelineOrchestrator
    from video_clipper.pipeline.monitor import TelegramMonitor
    from video_clipper.pipeline.transcriber import WhisperTranscriber
    from video_clipper.pipeline.selector import MomentSelector
    from video_clipper.pipeline.editor import VideoEditor
    from video_clipper.pipeline.publisher import ClipPublisher
    from video_clipper.gpu.guard import GPUGuard

    logger.info("All modules loaded (stubs)")
    logger.info("Pipeline ready. Stages not yet implemented.")
    logger.info("Waiting for stage-2 implementation...")

    # 7. Держим процесс
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        await db.close()
        logger.info("Shutdown complete.")


if __name__ == "__main__":
    asyncio.run(main())
