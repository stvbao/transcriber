import atexit
import signal
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from time import perf_counter

# ═══════════════════════════════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# ── Common ─────────────────────────────────────────────────────────────────────
LANGUAGE        = "sr"      # language: zh | en | ja | ko | fr | de | es | it | pt | ru | sr
                              # full list: github.com/openai/whisper#available-models-and-languages
TRANSLATE       = True     # translate transcription to English

EXPORT          = "all"     # output format: all | txt | srt | vtt | webvtt | json | html | rttm
DEVICE          = "mlx"     # mlx = Apple Silicon (M1–M5) | cuda = NVIDIA GPU | cpu = slowest


# ── Speaker annotation ─────────────────────────────────────────────────────────
# Identifies who is speaking at each point. Requires a HuggingFace token
# (hf.co/settings/tokens) and accepting the license for both pyannote models:
#   hf.co/pyannote/speaker-diarization-3.1  |  hf.co/pyannote/segmentation-3.0

HF_TOKEN        = ""  # leave empty to skip
NUM_SPEAKERS    = 2       # number of speakers (0 = auto-detect)

# ── Advanced ───────────────────────────────────────────────────────────────────
MODEL           = ""      # whisper model, leave empty for default (large-v3-turbo)
                            # options: tiny | base | small | medium | large | large-v2 | large-v3 | large-v3-turbo
                            # run "whisply list" in terminal for full list with device compatibility
SUBTITLE_LENGTH = 5       # words per subtitle segment — applies to srt | vtt | webvtt
POST_CORRECTION = ""      # path to YAML file for post-correction (leave empty to skip)
VERBOSE         = True    # print transcribed chunks to terminal during processing

# ── DO NOT CHANGE ──────────────────────────────────────────────────────────────
AUDIO_EXTENSIONS = {".mp3", ".mp4", ".wav", ".m4a", ".ogg", ".flac", ".aac", ".wma"}


# ═══════════════════════════════════════════════════════════════════════════════
#  SETUP
# ═══════════════════════════════════════════════════════════════════════════════

input_folder          = Path(__file__).parent        # drop audio files in the same folder as this script
transcriptions_folder = input_folder / "transcriptions"
current_process = None


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def format_duration(seconds: float) -> str:
    minutes, remaining_seconds = divmod(seconds, 60)
    hours, remaining_minutes = divmod(int(minutes), 60)
    if hours:
        return f"{hours}h {remaining_minutes}m {remaining_seconds:.1f}s"
    if minutes >= 1:
        return f"{int(minutes)}m {remaining_seconds:.1f}s"
    return f"{seconds:.1f}s"


def already_transcribed(file: Path) -> bool:
    # Skip files that already have a transcription folder
    return (transcriptions_folder / file.stem).is_dir()


def cleanup_converted(file: Path):
    # Delete temporary *_converted.wav files whisply creates during processing
    for leftover in file.parent.glob(f"{file.stem}*_converted.wav"):
        leftover.unlink()


def cleanup_all_converted():
    # Remove any temporary converted wav files left behind by interrupted runs
    for leftover in input_folder.glob("*_converted.wav"):
        leftover.unlink(missing_ok=True)


def handle_shutdown(signum, _frame):
    global current_process
    log(f"Stopping on signal {signum}; cleaning up temporary files...")
    if current_process is not None and current_process.poll() is None:
        current_process.terminate()
        try:
            current_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            current_process.kill()
            current_process.wait()
    cleanup_all_converted()
    sys.exit(130)


def resolve_model() -> str | None:
    # whisply's MLX default model (large-v3-turbo) does not actually emit
    # translated output even when --translate is enabled, so force a
    # translation-capable multilingual model in that case.
    if MODEL:
        return MODEL
    if TRANSLATE and DEVICE == "mlx":
        return "large-v3"
    return None


atexit.register(cleanup_all_converted)
signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════════

# Find audio files in the folder that haven't been transcribed yet
files = [
    f for f in input_folder.iterdir()
    if f.suffix.lower() in AUDIO_EXTENSIONS and not already_transcribed(f)
]

if not files:
    log("No new files to process.")
else:
    log(f"Found {len(files)} file(s) to process...")
    failed = []
    batch_start = perf_counter()
    selected_model = resolve_model()

    if selected_model:
        log(f"Using model: {selected_model}")

    for i, file in enumerate(files, 1):
        log(f"Processing {i}/{len(files)}: {file.name}")
        file_start = perf_counter()

        # Build whisply command from options above
        cmd = [
            "whisply", "run",
            "--files",      str(file),
            "--output_dir", str(transcriptions_folder),
            "--device",     DEVICE,
            "--export",     EXPORT,
            "--language",   LANGUAGE,
        ]
        if selected_model:
            cmd += ["--model", selected_model]
        if EXPORT == "all" or EXPORT in {"srt", "vtt", "webvtt"}:
            cmd += ["--subtitle", "--subtitle_length", str(SUBTITLE_LENGTH)]
        if TRANSLATE:
            cmd.append("--translate")
        if HF_TOKEN:
            cmd += ["--annotate", "--hf_token", HF_TOKEN]
            if NUM_SPEAKERS:
                cmd += ["--num_speakers", str(NUM_SPEAKERS)]
        if POST_CORRECTION:
            cmd += ["--post_correction", POST_CORRECTION]
        if VERBOSE:
            cmd.append("--verbose")

        try:
            current_process = subprocess.Popen(cmd)
            returncode = current_process.wait()
        finally:
            cleanup_converted(file)
            current_process = None

        elapsed = perf_counter() - file_start

        if returncode != 0:
            failed.append(file.name)
            log(f"Failed: {file.name}")
            log(f"Time cost: {format_duration(elapsed)}")
        else:
            log(f"Finished: {file.name}")
            log(f"Time cost: {format_duration(elapsed)}")
            # If a specific format was requested, delete the rest
            if EXPORT != "all":
                out_dir = transcriptions_folder / file.stem
                for f in out_dir.iterdir():
                    if f.suffix.lstrip(".") != EXPORT:
                        f.unlink()

    total_elapsed = perf_counter() - batch_start
    log(f"Done! Processed {len(files) - len(failed)}/{len(files)} file(s).")
    log(f"Total time: {format_duration(total_elapsed)}")
    if failed:
        log(f"Failed files: {', '.join(failed)}")
    else:
        log("All files transcribed successfully.")
