"""
Диалог обновления в стиле лаунчера.

Показывает версию, changelog, прогресс скачивания.
Автоматически скачивает и применяет обновление.
"""

import logging
import threading

import customtkinter as ctk

import slicr
from slicr.updater import AutoUpdater, UpdateInfo

logger = logging.getLogger(__name__)


class UpdateDialog(ctk.CTkToplevel):
    """Модальное окно обновления приложения."""

    def __init__(self, master: ctk.CTk, update_info: UpdateInfo) -> None:
        super().__init__(master)
        self._update = update_info
        self._updater = AutoUpdater()
        self._downloading = False

        self.title("Обновление Slicr")
        self.geometry("500x400")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        """Собрать интерфейс диалога."""
        # Заголовок
        ctk.CTkLabel(
            self,
            text="Доступно обновление!",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(pady=(20, 5))

        # Версии
        ctk.CTkLabel(
            self,
            text=f"{slicr.__version__}  →  {self._update.version}",
            font=ctk.CTkFont(size=16),
            text_color="#4CAF50",
        ).pack(pady=(0, 10))

        # Размер файла
        size_mb = self._update.file_size / (1024 * 1024)
        ctk.CTkLabel(
            self,
            text=f"Размер: {size_mb:.1f} МБ",
            text_color="gray60",
        ).pack()

        # Changelog
        ctk.CTkLabel(
            self,
            text="Что нового:",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        ).pack(fill="x", padx=20, pady=(15, 5))

        changelog_box = ctk.CTkTextbox(self, height=120, wrap="word")
        changelog_box.pack(fill="x", padx=20)
        changelog_box.insert("1.0", self._update.changelog or "Нет описания")
        changelog_box.configure(state="disabled")

        # Прогресс-бар (скрыт изначально)
        self._progress_frame = ctk.CTkFrame(self, fg_color="transparent")

        self._progress_bar = ctk.CTkProgressBar(self._progress_frame, width=400)
        self._progress_bar.set(0)
        self._progress_bar.pack(pady=(5, 2))

        self._progress_label = ctk.CTkLabel(
            self._progress_frame, text="Подготовка...", text_color="gray60"
        )
        self._progress_label.pack()

        # Кнопки
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(15, 20))

        self._skip_btn = ctk.CTkButton(
            btn_frame,
            text="Позже",
            width=120,
            fg_color="gray40",
            hover_color="gray30",
            command=self._on_close,
        )
        self._skip_btn.pack(side="left")

        self._update_btn = ctk.CTkButton(
            btn_frame,
            text="Обновить",
            width=160,
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._on_update,
        )
        self._update_btn.pack(side="right")

    def _on_update(self) -> None:
        """Начать скачивание обновления."""
        if self._downloading:
            return
        self._downloading = True

        self._update_btn.configure(state="disabled", text="Скачивание...")
        self._skip_btn.configure(state="disabled")
        self._progress_frame.pack(fill="x", padx=20, before=self._skip_btn.master)

        threading.Thread(target=self._download_thread, daemon=True).start()

    def _download_thread(self) -> None:
        """Скачивание в отдельном потоке."""
        try:
            def _on_progress(pct: float) -> None:
                self.after(0, self._update_progress, pct)

            update_path = self._updater.download_update_sync(
                self._update, progress_callback=_on_progress
            )

            self.after(0, self._download_complete, update_path)

        except Exception as e:
            logger.error("Ошибка скачивания обновления: %s", e)
            self.after(0, self._download_failed, str(e))

    def _update_progress(self, pct: float) -> None:
        """Обновить прогресс-бар (вызов из GUI-потока)."""
        self._progress_bar.set(pct)
        downloaded_mb = pct * self._update.file_size / (1024 * 1024)
        total_mb = self._update.file_size / (1024 * 1024)
        self._progress_label.configure(
            text=f"Скачано: {downloaded_mb:.1f} / {total_mb:.1f} МБ ({pct:.0%})"
        )

    def _download_complete(self, update_path) -> None:
        """Скачивание завершено — предложить установить."""
        self._progress_bar.set(1.0)
        self._progress_label.configure(text="Скачивание завершено!")

        self._update_btn.configure(
            state="normal",
            text="Установить и перезапустить",
            command=lambda: self._apply(update_path),
        )
        self._skip_btn.configure(state="normal")

    def _download_failed(self, error: str) -> None:
        """Ошибка скачивания."""
        self._progress_label.configure(
            text=f"Ошибка: {error}", text_color="red"
        )
        self._update_btn.configure(state="normal", text="Повторить")
        self._skip_btn.configure(state="normal")
        self._downloading = False

    def _apply(self, update_path) -> None:
        """Применить обновление и перезапуститься."""
        import asyncio

        self._update_btn.configure(state="disabled", text="Установка...")
        self._skip_btn.configure(state="disabled")
        self._progress_label.configure(text="Применяем обновление...")

        try:
            asyncio.run(self._updater.apply_update(update_path))
        except Exception as e:
            logger.error("Ошибка применения обновления: %s", e)
            self._progress_label.configure(
                text=f"Ошибка установки: {e}\nФайл сохранён: {update_path}",
                text_color="red",
            )
            self._skip_btn.configure(state="normal")

    def _on_close(self) -> None:
        """Закрыть диалог."""
        if not self._downloading:
            self.grab_release()
            self.destroy()
