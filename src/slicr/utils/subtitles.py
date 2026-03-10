"""
Генерация файлов субтитров в TikTok-стиле.

Создаёт SRT и ASS субтитры из word-level транскрипции.
ASS — karaoke-эффект с подсветкой слово-за-словом, pop-in анимацией,
крупным шрифтом и обводкой для вертикального видео (1080x1920).
"""

import logging

logger = logging.getLogger(__name__)

# Группировка: лимиты
_MAX_WORDS_PER_LINE = 4
_MAX_CHARS_PER_LINE = 22  # макс символов (Montserrat Bold 72pt на 1080px)
_MAX_LINE_DURATION = 2.5  # секунд

# Пунктуация — жёсткий разрыв (конец предложения): разрыв даже при 1 слове
_SENTENCE_END = {".", "!", "?"}
# Пунктуация — мягкий разрыв: разрыв при >= 2 словах
_SOFT_BREAK = {",", ":", ";", "\u2014", "\u2013", "-", "\u2026"}


def _group_text_len(group: list[dict]) -> int:
    """Длина текста группы в символах (слова через пробел, UPPER)."""
    return len(" ".join(w.get("word", "").strip().upper() for w in group))


def _group_words(words: list[dict]) -> list[list[dict]]:
    """
    Сгруппировать слова в строки субтитров.

    Правила (на основе auto-subs и лучших практик):
    - Макс символов на строку: 22 (Montserrat Bold 72pt, 1080px шир.)
    - Макс слов: 4
    - Макс длительность: 2.5 сек
    - Конец предложения (. ! ?) — жёсткий разрыв (даже 1 слово)
    - Мягкая пунктуация (, : ; —) — разрыв при >= 2 словах

    Returns:
        Список групп, каждая группа — список словарей слов.
    """
    groups: list[list[dict]] = []
    current: list[dict] = []

    for word in words:
        word_text = word.get("word", "").strip()
        if not word_text:
            continue

        if not current:
            current.append(word)
            # Жёсткий разрыв после единственного слова с точкой/восклицательным
            if word_text[-1] in _SENTENCE_END:
                groups.append(current)
                current = []
            continue

        # Проверяем, поместится ли новое слово в строку
        new_len = _group_text_len(current) + 1 + len(word_text.upper())
        group_start = current[0].get("start", 0.0)
        word_end = word.get("end", 0.0)
        duration = word_end - group_start

        should_break = (
            len(current) >= _MAX_WORDS_PER_LINE
            or new_len > _MAX_CHARS_PER_LINE
            or duration > _MAX_LINE_DURATION
        )

        if should_break:
            groups.append(current)
            current = [word]
            # Одиночное слово с концом предложения
            if word_text[-1] in _SENTENCE_END:
                groups.append(current)
                current = []
            continue

        current.append(word)

        # Пунктуация после добавления
        if word_text[-1] in _SENTENCE_END:
            # Жёсткий разрыв — конец предложения
            groups.append(current)
            current = []
        elif len(current) >= 2 and word_text[-1] in _SOFT_BREAK:
            # Мягкий разрыв — запятая и т.д. при >= 2 словах
            groups.append(current)
            current = []

    if current:
        groups.append(current)

    return groups


def _format_srt_time(seconds: float) -> str:
    """Форматировать секунды в SRT-формат: HH:MM:SS,mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _format_ass_time(seconds: float) -> str:
    """Форматировать секунды в ASS-формат: H:MM:SS.cc"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds % 1) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _build_karaoke_line(group_words: list[dict]) -> str:
    """
    Собрать текст строки ASS с karaoke `\\kf` тегами.

    Один Dialogue на группу. Тег `\\kf` даёт progressive fill
    (SecondaryColour → PrimaryColour) для каждого слова.
    Паузы между словами: невидимый `\\k` тег.

    Returns:
        Строка ASS-текста с karaoke-тегами.
    """
    parts: list[str] = []
    for i, w in enumerate(group_words):
        text = w.get("word", "").strip().upper()
        start = w.get("start", 0.0)
        end = w.get("end", 0.0)
        duration_cs = max(1, round((end - start) * 100))

        # Пауза между словами (невидимый \k)
        if i > 0:
            prev_end = group_words[i - 1].get("end", 0.0)
            gap_cs = max(0, round((start - prev_end) * 100))
            if gap_cs > 0:
                parts.append(f"{{\\k{gap_cs}}}")

        # Слово с progressive fill
        parts.append(f"{{\\kf{duration_cs}}}{text}")

        # Пробел после слова (кроме последнего)
        if i < len(group_words) - 1:
            parts.append(" ")

    return "".join(parts)


def generate_srt(words: list[dict], output_path: str) -> str | None:
    """
    Сгенерировать SRT-субтитры из word-level транскрипции.

    Группировка: 2-3 слова на строку с учётом пунктуации.

    Args:
        words: список словарей {"word": str, "start": float, "end": float}.
        output_path: путь для сохранения .srt файла.

    Returns:
        Путь к файлу субтитров или None при ошибке.
    """
    if not words:
        logger.warning("Нет слов для генерации SRT")
        return None

    groups = _group_words(words)
    lines: list[str] = []

    for i, group in enumerate(groups, 1):
        start = _format_srt_time(group[0].get("start", 0.0))
        end = _format_srt_time(group[-1].get("end", 0.0))
        text = " ".join(w.get("word", "").strip().upper() for w in group)
        lines.append(f"{i}")
        lines.append(f"{start} --> {end}")
        lines.append(text)
        lines.append("")

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        logger.info("SRT создан: %s (%d строк)", output_path, len(groups))
        return output_path
    except OSError as e:
        logger.error("Ошибка записи SRT: %s", e)
        return None


def generate_ass(words: list[dict], output_path: str) -> str | None:
    """
    Сгенерировать ASS-субтитры в TikTok-стиле для вертикального видео.

    Karaoke-эффект: каждое слово в группе подсвечивается жёлтым
    по очереди, остальные остаются белыми. Первое слово группы
    появляется с pop-in анимацией (масштаб 120% -> 100% за 100ms).

    Стиль: Montserrat Bold 62pt, обводка 4px, тень 2px,
    нижний центр (Alignment 2), MarginV 120.

    Args:
        words: список словарей {"word": str, "start": float, "end": float}.
        output_path: путь для сохранения .ass файла.

    Returns:
        Путь к файлу субтитров или None при ошибке.
    """
    if not words:
        logger.warning("Нет слов для генерации ASS")
        return None

    groups = _group_words(words)

    # Заголовок ASS: Montserrat Bold, 72pt, karaoke-стиль.
    # PrimaryColour = жёлтый (цвет ПОСЛЕ fill) = уже произнесённые слова
    # SecondaryColour = белый (цвет ДО fill) = ещё не произнесённые слова
    # Karaoke \kf: progressive fill SecondaryColour → PrimaryColour
    header = (
        "[Script Info]\n"
        "Title: Slicr Subtitles\n"
        "ScriptType: v4.00+\n"
        "PlayResX: 1080\n"
        "PlayResY: 1920\n"
        "WrapStyle: 2\n"
        "\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: Default,Montserrat,72,&H0000FFFF,&H00FFFFFF,&H00000000,"
        "&H80000000,-1,0,0,0,100,100,0,0,1,4,2,2,30,30,120,1\n"
        "\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, "
        "MarginV, Effect, Text\n"
    )

    # Убираем перекрытия между группами
    for i in range(len(groups) - 1):
        curr_end = groups[i][-1].get("end", 0.0)
        next_start = groups[i + 1][0].get("start", 0.0)
        if curr_end > next_start:
            groups[i][-1]["end"] = next_start

    events: list[str] = []

    for group in groups:
        group_start = group[0].get("start", 0.0)
        group_end = group[-1].get("end", 0.0)

        # Защита от нулевой длительности
        if group_end <= group_start:
            group_end = group_start + 0.1

        start = _format_ass_time(group_start)
        end = _format_ass_time(group_end)

        karaoke_text = _build_karaoke_line(group)

        # Pop-in анимация для каждой группы
        prefix = (
            "{\\blur1"
            "\\fscx120\\fscy120"
            "\\t(0,100,\\fscx100\\fscy100)}"
        )

        events.append(
            f"Dialogue: 0,{start},{end},Default,,0,0,0,,"
            f"{prefix}{karaoke_text}"
        )

    total_dialogue = len(events)

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(header)
            f.write("\n".join(events))
            f.write("\n")

        # Debug-дамп: группировка, тайминги, длина строк
        debug_path = output_path.rsplit(".", 1)[0] + "_debug.txt"
        with open(debug_path, "w", encoding="utf-8") as df:
            df.write(f"Всего слов: {len(words)}, групп: {len(groups)}\n")
            df.write(f"Лимиты: {_MAX_CHARS_PER_LINE} символов, "
                     f"{_MAX_WORDS_PER_LINE} слов, {_MAX_LINE_DURATION}с\n\n")
            for i, group in enumerate(groups):
                text = " ".join(w.get("word", "").strip().upper() for w in group)
                gs = group[0].get("start", 0.0)
                ge = group[-1].get("end", 0.0)
                df.write(
                    f"[{i + 1:3d}] {gs:6.2f}-{ge:6.2f} "
                    f"({len(text):2d} символов, {len(group)} слов) "
                    f"│ {text}\n"
                )
        logger.info("Debug-дамп: %s", debug_path)

        logger.info(
            "ASS создан: %s (%d групп, %d dialogue-событий)",
            output_path, len(groups), total_dialogue,
        )
        return output_path
    except OSError as e:
        logger.error("Ошибка записи ASS: %s", e)
        return None
