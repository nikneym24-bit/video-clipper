"""
Фоновая обработка видео для GUI.

ProcessingWorker запускается в отдельном потоке и вызывает
VideoProcessor — единую точку входа обработки.
"""

import asyncio
import logging
import os
import threading
from collections.abc import Callable
from slicr.config import Config, load_config
from slicr.services.processor import ProcessingOptions, VideoProcessor

logger = logging.getLogger(__name__)


class ProcessingWorker(threading.Thread):
    """Фоновый обработчик видео через VideoProcessor."""

    def __init__(
        self,
        file_paths: list[str],
        output_dir: str,
        crop_enabled: bool = True,
        crop_x_offset: float = 0.5,
        max_clip_duration: int = 60,
        subtitles_enabled: bool = True,
        external_subtitle_paths: list[str] | None = None,
        on_progress: Callable[[float, str], None] | None = None,
        on_complete: Callable[[list[str]], None] | None = None,
        on_error: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(daemon=True)
        self._file_paths = file_paths
        self._output_dir = output_dir
        self._external_subtitle_paths = external_subtitle_paths or []
        self._base_options = ProcessingOptions(
            crop_enabled=crop_enabled,
            crop_x_offset=crop_x_offset,
            subtitles_enabled=subtitles_enabled,
            ai_select_enabled=not self._external_subtitle_paths,
            max_clip_duration=max_clip_duration,
        )
        self._on_progress = on_progress
        self._on_complete = on_complete
        self._on_error = on_error

        # Индекс .ass файлов по стему для быстрого сопоставления
        self._ass_lookup: dict[str, str] = {}
        for ass_path in self._external_subtitle_paths:
            stem = os.path.splitext(os.path.basename(ass_path))[0]
            self._ass_lookup[stem] = ass_path

    def _report_progress(self, pct: float, msg: str) -> None:
        """Отправить прогресс в GUI (thread-safe через callback)."""
        if self._on_progress:
            self._on_progress(pct, msg)

    def _report_error(self, msg: str) -> None:
        """Отправить ошибку в GUI."""
        if self._on_error:
            self._on_error(msg)

    def run(self) -> None:
        """Обработать все видеофайлы."""
        os.makedirs(self._output_dir, exist_ok=True)
        results: list[str] = []
        total = len(self._file_paths)

        # Загружаем конфиг (API-ключи для Groq, Claude)
        try:
            config = load_config()
        except Exception as e:
            logger.warning("Не удалось загрузить конфиг: %s. Работаем без API.", e)
            config = Config()

        for idx, input_path in enumerate(self._file_paths):
            name = os.path.basename(input_path)
            pct_base = idx / total

            self._report_progress(
                pct_base, f"Обработка {idx + 1}/{total}: {name}"
            )

            try:
                output_paths = self._process_single(config, input_path, idx, total)
                if output_paths:
                    results.extend(output_paths)
                    logger.info("Готово: %s → %d клипов", name, len(output_paths))
                else:
                    logger.warning("Не удалось обработать: %s", name)
                    self._report_error(f"Ошибка обработки: {name}")
            except Exception as e:
                logger.error("Ошибка при обработке %s: %s", name, e)
                self._report_error(f"Ошибка: {name} — {e}")

            self._report_progress(
                (idx + 1) / total,
                f"Завершено {idx + 1}/{total}",
            )

        self._report_progress(1.0, f"Готово! Обработано: {len(results)}/{total}")

        if self._on_complete:
            self._on_complete(results)

    def _find_matching_ass(self, video_path: str) -> str | None:
        """Найти .ass файл, соответствующий видео по имени."""
        video_stem = os.path.splitext(os.path.basename(video_path))[0]
        # Точное совпадение: clip1.mp4 → clip1.ass
        if video_stem in self._ass_lookup:
            return self._ass_lookup[video_stem]
        # Частичное: clip1.mp4 → clip1_v2.ass (или наоборот)
        for ass_stem, ass_path in self._ass_lookup.items():
            if ass_stem.startswith(video_stem) or video_stem.startswith(ass_stem):
                return ass_path
        return None

    def _process_single(
        self, config: Config, input_path: str, idx: int, total: int
    ) -> list[str]:
        """Обработать один видеофайл через VideoProcessor."""

        def _on_step_progress(pct: float, msg: str) -> None:
            overall = (idx + pct) / total
            self._report_progress(overall, msg)

        # Сопоставляем .ass файл с этим видео
        matched_ass = self._find_matching_ass(input_path) if self._external_subtitle_paths else None
        options = ProcessingOptions(
            crop_enabled=self._base_options.crop_enabled,
            crop_x_offset=self._base_options.crop_x_offset,
            subtitles_enabled=self._base_options.subtitles_enabled,
            ai_select_enabled=self._base_options.ai_select_enabled,
            max_clip_duration=self._base_options.max_clip_duration,
            external_subtitle_path=matched_ass,
        )

        if matched_ass:
            logger.info(
                "Видео %s → .ass: %s",
                os.path.basename(input_path),
                os.path.basename(matched_ass),
            )

        async def _run() -> list[str]:
            processor = VideoProcessor(config)
            try:
                result = await processor.process(
                    input_path=input_path,
                    output_dir=self._output_dir,
                    options=options,
                    on_progress=_on_step_progress,
                )
                return [clip.final_path for clip in result.clips]
            finally:
                await processor.close()

        return asyncio.run(_run())
