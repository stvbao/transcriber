# Transcriber

A desktop transcription GUI for social scientists and qualitative researchers. Built on [whisply](https://github.com/tsmdt/whisply) and OpenAI's **Whisper large-v3-turbo**, it transcribes interviews, focus groups, and field recordings entirely on your own machine — no cloud, no data leaving your computer.

Select your audio files, configure settings, and press Start. Transcriptions are saved to a folder of your choice. If you have multiple files, they are processed in one batch run.

![Transcriber screenshot](screenshot.png)

## Features

- **Desktop GUI** — no terminal needed after setup
- **Offline** — audio never leaves your machine
- **99+ languages** — including non-Latin scripts
- **Speaker annotation** — automatically labels who is speaking
- **Multiple output formats** — `txt`, `srt`, `vtt`, `webvtt`, `json`, `html`, `rttm`
- **Batch processing** — select multiple files and process them in one run
- **Apple Silicon optimised** — uses MLX for fast transcription on M1–M5 Macs
- **Translation** — optionally translate transcriptions to English

## Requirements

- [uv](https://docs.astral.sh/uv/) — Python package manager
- [ffmpeg](https://ffmpeg.org) — audio conversion
- [whisply](https://github.com/tsmdt/whisply) — transcription backend

## Installation

**1. Install dependencies**

macOS (run each line in Terminal):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
brew install ffmpeg
uv tool install whisply
```

Windows (run each line in PowerShell):
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
winget install Gyan.FFmpeg
uv tool install whisply
```

**2. Download this app and install dependencies**

Option A — Download ZIP (no Git required):
1. Click the green **Code** button on this page → **Download ZIP**
2. Unzip the folder
3. Open a terminal, navigate to the `app/` folder inside, and run:
```bash
uv sync
```

Option B — Clone with Git:
```bash
git clone https://github.com/stvbao/transcriber
cd transcriber/app
uv sync
```

## Running

macOS — double-click `transcriber.command`

Windows — double-click `transcriber.bat`
## Speaker Annotation

Speaker annotation automatically labels each speaker (e.g. `SPEAKER_00`, `SPEAKER_01`). It requires a free HuggingFace account:

1. Create a token at [hf.co/settings/tokens](https://hf.co/settings/tokens)
2. Accept the license for both pyannote models:
   - [hf.co/pyannote/speaker-diarization-3.1](https://hf.co/pyannote/speaker-diarization-3.1)
   - [hf.co/pyannote/segmentation-3.0](https://hf.co/pyannote/segmentation-3.0)
3. Paste your token into the HF token field in the app

Models are downloaded once on first use and cached locally — fully offline after that.

## Known Issues

**Windows only — CPU transcription fails (k2 missing)**
On Windows, whisply uses WhisperX on CPU, which requires a package called `k2` that does not install correctly on Windows. This does not affect Mac users.

Workarounds:
- Use an NVIDIA GPU and set device to `gpu` (if your computer does not have an NVIDIA GPU, there is currently no solution)
- Use a Mac (MLX backend works out of the box)

## Data Privacy

- Audio files never leave your machine
- No API keys or cloud services used for transcription
- No telemetry or usage data sent anywhere
- HuggingFace is contacted once to download models — offline after that

## Credits

- [whisply](https://github.com/tsmdt/whisply) by [@tsmdt](https://github.com/tsmdt)
- [Whisper](https://github.com/openai/whisper) by OpenAI
- [pyannote.audio](https://github.com/pyannote/pyannote-audio) by pyannote
- [noScribe](https://github.com/kaixxx/noScribe) by Kai Dröge — GUI design and aesthetics inspiration
