#!/usr/bin/env python3
"""
Перегенерация субтитров без API-вызовов.

Берёт существующие .ass файлы (слова + тайминги), перегенерирует
с текущим стилем из subtitles.py и прожигает на .mp4 клипы.

Использование:
  # Один клип — превью в mpv (мгновенно):
  python scripts/test_subtitles.py clip1.mp4 --preview

  # Один клип — прожиг:
  python scripts/test_subtitles.py clip1.mp4

  # Все клипы в папке — batch-прожиг:
  python scripts/test_subtitles.py "/Users/dvofis/Desktop/Slicr Output/"

  # Batch-превью (открывает каждый в mpv по очереди):
  python scripts/test_subtitles.py "/Users/dvofis/Desktop/Slicr Output/" --preview
"""

import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from slicr.utils.subtitles import generate_ass


def extract_words_from_ass(ass_path: str) -> list[dict]:
    """Извлечь слова и тайминги из .ass файла (формат \\kf)."""
    words = []

    with open(ass_path, encoding="utf-8") as f:
        for line in f:
            if not line.startswith("Dialogue:"):
                continue
            parts = line.split(",", 9)
            if len(parts) < 10:
                continue

            start = _parse_ass_time(parts[1].strip())
            text = parts[9].strip()

            # Формат \kf: извлекаем все слова из одного Dialogue
            kf_matches = re.findall(r"\{\\kf(\d+)\}(\S+)", text)
            if kf_matches:
                cursor = start
                pause_matches = re.findall(r"\{\\k(\d+)\}", text)
                pause_iter = iter(pause_matches)
                for i, (dur_cs, word_text) in enumerate(kf_matches):
                    word_dur = int(dur_cs) / 100.0
                    words.append({
                        "word": word_text,
                        "start": cursor,
                        "end": cursor + word_dur,
                    })
                    cursor += word_dur
                    if i < len(kf_matches) - 1:
                        try:
                            gap_cs = next(pause_iter)
                            cursor += int(gap_cs) / 100.0
                        except StopIteration:
                            pass

    return words


def _parse_ass_time(s: str) -> float:
    """H:MM:SS.cc → секунды."""
    parts = s.split(":")
    h = int(parts[0])
    m = int(parts[1])
    sec_parts = parts[2].split(".")
    sec = int(sec_parts[0])
    cs = int(sec_parts[1]) if len(sec_parts) > 1 else 0
    return h * 3600 + m * 60 + sec + cs / 100


def process_clip(clip_path: Path, preview: bool = False) -> bool:
    """Обработать один клип: перегенерировать .ass и прожечь/превью."""
    ass_path = clip_path.with_suffix(".ass")
    if not ass_path.exists():
        print(f"  Пропуск {clip_path.name}: нет .ass файла")
        return False

    words = extract_words_from_ass(str(ass_path))
    if not words:
        print(f"  Пропуск {clip_path.name}: 0 слов в .ass")
        return False

    # Перегенерируем .ass с текущим стилем
    new_ass = str(clip_path.with_name(f"{clip_path.stem}_v2.ass"))
    result = generate_ass(words, new_ass)
    if not result:
        print(f"  Ошибка генерации ASS для {clip_path.name}")
        return False

    print(f"  {clip_path.name}: {len(words)} слов → {Path(new_ass).name}")

    if preview:
        subprocess.run(["mpv", str(clip_path), f"--sub-file={new_ass}"])
    else:
        output = str(clip_path.with_name(f"{clip_path.stem}_v2.mp4"))
        escaped = new_ass.replace("\\", "\\\\").replace(":", "\\:")
        cmd = [
            "ffmpeg", "-y",
            "-i", str(clip_path),
            "-vf", f"ass={escaped}",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "copy",
            output,
        ]
        proc = subprocess.run(cmd, capture_output=True)
        if proc.returncode == 0:
            print(f"  → {Path(output).name}")
        else:
            print(f"  Ошибка ffmpeg: {proc.stderr.decode()[-200:]}")
            return False

    return True


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    preview = "--preview" in sys.argv
    target = Path(sys.argv[1])

    if target.is_dir():
        # Batch: все *_clip*.mp4 в папке
        clips = sorted(target.glob("*_clip*.mp4"))
        # Исключаем уже перегенерированные _v2 файлы
        clips = [c for c in clips if "_v2" not in c.stem]

        if not clips:
            print(f"Нет клипов (*_clip*.mp4) в {target}")
            sys.exit(1)

        print(f"Найдено {len(clips)} клипов в {target}")
        ok = 0
        for clip in clips:
            if process_clip(clip, preview):
                ok += 1

        print(f"\nГотово: {ok}/{len(clips)} клипов обработано")

    elif target.is_file() and target.suffix == ".mp4":
        if not process_clip(target, preview):
            sys.exit(1)
        if not preview:
            output = target.with_name(f"{target.stem}_v2.mp4")
            subprocess.run(["open", str(output)])
    else:
        print(f"Ожидается .mp4 файл или директория: {target}")
        sys.exit(1)


if __name__ == "__main__":
    main()
