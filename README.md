# Overview

A batch transcription tool for social scientists and qualitative researchers. Built on [whisply](https://github.com/tsmdt/whisply) and OpenAI's **Whisper large-v3-turbo**, it transcribes interviews, focus groups, and field recordings entirely on your own machine — no cloud, no data leaving your computer.

Drop `transcribe.py` into your audio folder, run it, get transcriptions.

This is a thin wrapper around [whisply](https://github.com/tsmdt/whisply) for researchers who are not familiar with command-line tools. It handles configuration, skips already processed files, and removes temporary files whisply leaves behind — so you only need to edit a few lines at the top of the script and run one command. If you are comfortable with the terminal, you can also use whisply directly for more control.


## Features
- **Automated Transcription**: Uses OpenAI's Whisper model for accurate speech recognition
- **Speaker annotation** — automatically identifies and labels each speaker (e.g. `SPEAKER_00`, `SPEAKER_01`), useful for interviews and focus groups with multiple participants
- **Multiple output formats** — `txt` for plain text, `srt` / `vtt` / `webvtt` for subtitles with timestamps, `json` for structured data, `html` for qualitative analysis tools, `rttm` for speaker timing data
- **Fully offline** — no internet connection needed after the initial setup and model download
- **99+ languages** — supports a wide range of languages including non-Latin scripts such as Chinese, Japanese, Arabic, and more
- **Batch processing** — transcribes all audio files in the folder in one run, skipping any already transcribed
- **noScribe compatible** — HTML output works directly with [noScribe](https://github.com/kaixxx/noScribe), a dedicated qualitative research transcript editor
- **Configurable** — set language, model, export format, subtitle length, and more from the top of the script

## Model

This tool uses OpenAI's [Whisper](https://github.com/openai/whisper) `large-v3-turbo` model by default — a state-of-the-art speech recognition model that performs well across a wide range of conditions, including accented speech, mixed-language audio, and recordings with background noise. It strikes a good balance between accuracy and speed for research use.

If processing time is a concern, smaller models such as `medium` or `small` are available at the cost of some accuracy. See the [whisply documentation](https://github.com/tsmdt/whisply) for a full list of available models.

> **Note for Windows and Linux users:** `large-v3-turbo` is only available on Apple Silicon (mlx). On CPU or NVIDIA GPU, set `MODEL = "large-v3"` in the script instead.

Speaker annotation is powered by [pyannote](https://github.com/pyannote/pyannote-audio), a state-of-the-art speaker diarization library that also runs fully locally.

## Data Privacy

Research data — especially interview recordings — often contains sensitive, personal, or ethically protected information. This tool is designed with that in mind:

- Audio files never leave your machine
- No API keys or cloud services are used for transcription or speaker annotation
- No usage data, telemetry, or logs are sent anywhere
- HuggingFace is only contacted once to download the pyannote models on first use — after that the tool runs fully offline


## Requirements

- Python 3.12 for [whisply](https://github.com/tsmdt/whisply)
- [uv](https://docs.astral.sh/uv/) — fast Python package manager

## Installation

**1. Install uv**

uv is a fast Python package manager used to install whisply. Install it in terminal with a single command:

macOS:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows:
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**2. Install ffmpeg**

whisply requires [ffmpeg](https://ffmpeg.org) to convert audio files before processing. See [whisply's installation guide](https://github.com/tsmdt/whisply) for more details.

macOS:
```bash
brew install ffmpeg
```

Windows:
```bash
winget install Gyan.FFmpeg
```

**3. Install whisply**

```bash
uv tool install whisply
```

## Usage

**1. Configure the script**

Open `transcribe.py` and set your options at the top of the file. At minimum, set the language of your audio files:

```python
LANGUAGE = "en"    # en=English, zh=Chinese, ja=Japanese, ko=Korean, ar=Arabic,
                   # fr=French, de=German, es=Spanish, pt=Portuguese, ru=Russian,
                   # hi=Hindi, tr=Turkish, vi=Vietnamese, sr=Serbian, fi=Finnish ....
EXPORT   = "all"   # output format: all | txt | srt | vtt | webvtt | json | html | rttm
DEVICE   = "mlx"   # mlx (Apple Silicon) | cuda (NVIDIA GPU) | cpu
```

**2. Drop audio files** in the same folder as `transcribe.py`

Supported formats: `.mp3`, `.mp4`, `.wav`, `.m4a`, `.ogg`, `.flac`, `.aac`, `.wma`

**3. Run the script**

If you are using an IDE such as **VS Code**, **PyCharm**, or **Positron**, you can run it directly by clicking the **Run** button (▶) in the editor.

Alternatively, you can open a terminal in the folder where `transcribe.py` is located and run:

```bash
uv run transcribe.py
```

The script will process each audio file one by one and show progress in the terminal. When finished, transcriptions are saved in a `transcriptions/` folder — each audio file gets its own subfolder with the output files inside. If you run the script again later with new audio files added, already transcribed files are skipped automatically.

## Speaker Annotation

Speaker annotation (also known as speaker diarization) automatically detects speaker changes in the audio and labels each segment with a speaker ID such as `SPEAKER_00` or `SPEAKER_01`. This is particularly useful for interview data with two or more participants, as it makes it much easier to follow who said what during analysis.

To enable speaker annotation, you need a free HuggingFace account:

1. Create a token at [hf.co/settings/tokens](https://hf.co/settings/tokens)
2. Accept the license for both pyannote models (required for legal use):
   - [hf.co/pyannote/speaker-diarization-3.1](https://hf.co/pyannote/speaker-diarization-3.1)
   - [hf.co/pyannote/segmentation-3.0](https://hf.co/pyannote/segmentation-3.0)
3. Paste your token into `transcribe.py`:
```python
HF_TOKEN = "your_token_here"
```

The pyannote models are downloaded once on first use and then run fully offline. If you know the exact number of speakers in advance, you can set `NUM_SPEAKERS` for more accurate results.

## Language List

Full list of supported languages: [github.com/openai/whisper#available-models-and-languages](https://github.com/openai/whisper#available-models-and-languages)

## Credits

- [whisply](https://github.com/tsmdt/whisply) by [@tsmdt](https://github.com/tsmdt)
- [Whisper](https://github.com/openai/whisper) by OpenAI
- [pyannote.audio](https://github.com/pyannote/pyannote-audio) for speaker annotation
