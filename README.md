# Slicr

Automated video clip production pipeline that monitors Telegram channels, transcribes video content, selects the most engaging moments using AI, and produces short-form vertical clips.

## How it works

```
Monitor Telegram channels → Download videos → Transcribe (Whisper STT)
→ Select best moment (Claude AI) → Edit to 9:16 + subtitles (ffmpeg)
→ Human moderation → Publish
```

## Key features

- **Async pipeline** — built on asyncio, handles multiple videos concurrently
- **Smart filtering** — duration, file size, keyword whitelist/blacklist, deduplication
- **AI-powered selection** — Claude API analyzes transcripts to find the most engaging 15-60s segment
- **Speech-to-text** — faster-whisper with word-level timestamps for precise subtitle generation
- **Moderation UI** — Telegram bot with inline approve/reject buttons
- **Vertical video** — automatic 9:16 crop with styled subtitles overlay

## Tech stack

- Python 3.13, asyncio
- Telethon + aiogram (Telegram)
- faster-whisper (speech recognition)
- Claude API (content analysis)
- ffmpeg (video processing)
- SQLite + aiosqlite (database)

## Quick start

```bash
pip install -e .
cp creds.example.json creds.json  # fill in credentials
python -m slicr
```

## Project structure

```
slicr/
├── src/slicr/
│   ├── pipeline/      # Processing stages (monitor, download, transcribe, select, edit)
│   ├── bot/           # Telegram bot & moderation UI
│   ├── services/      # External API clients (Telegram, Claude, VK)
│   ├── database/      # Async SQLite layer
│   └── utils/         # Video processing helpers
└── tests/             # pytest + pytest-asyncio test suite
```

## License

Private project.
