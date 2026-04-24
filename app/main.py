import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from time import perf_counter

from PyQt6.QtCore import Qt, QThread, QTimer, QRect, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox,
    QScrollArea, QTextEdit, QFileDialog, QFrame, QSizePolicy, QListWidget, QListWidgetItem,
)

# ── Data ──────────────────────────────────────────────────────────────────────

AUDIO_EXTENSIONS = {".mp3", ".mp4", ".wav", ".m4a", ".ogg", ".flac", ".aac", ".wma"}

LANGUAGES = {
    "Auto-detect": "",
    "English": "en",
    "Chinese": "zh",
    "French": "fr",
    "German": "de",
    "Spanish": "es",
    "Italian": "it",
    "Portuguese": "pt",
    "Russian": "ru",
    "Serbian": "sr",
    "Japanese": "ja",
    "Korean": "ko",
    "Arabic": "ar",
    "Turkish": "tr",
    "Hindi": "hi",
}

EXPORT_FORMATS = ["all", "txt", "srt", "vtt", "webvtt", "json", "html", "rttm"]
DEVICES        = ["auto", "mlx", "cpu", "cuda"]
MODELS         = [
    "large-v3-turbo", "large-v3", "large-v2",
    "large", "medium", "small", "base", "tiny",
]

# ── Colours ───────────────────────────────────────────────────────────────────

BG      = "#1c1c1c"
PANEL   = "#252525"
BORDER  = "#383838"
BLUE    = "#2b6cb0"
BLUE_HV = "#245a9a"
GREEN   = "#2a7d4f"
GREEN_HV= "#1f5e3a"
RED     = "#c0392b"
RED_HV  = "#922b21"
TEXT    = "#e8e8e8"
DIM     = "#888888"
MONO    = "Menlo, Monaco, Courier New"

WELCOME = (
    "<span style='color:#4fc3f7;font-size:14px;font-weight:600;'>"
    "Transcriber is ready.</span><br><br>"
    "<span style='color:#aaa;'>"
    "Built on <b>whisply</b> + OpenAI Whisper large-v3-turbo.<br>"
    "Select your audio files, configure settings, then press <b>Start</b>.<br><br>"
    "Transcriptions are saved in the selected output folder."
    "</span>"
)

# ── Stylesheet ────────────────────────────────────────────────────────────────

def stylesheet():
    return f"""
    * {{
        font-family: Helvetica Neue, Helvetica, Arial;
        font-size: 13px;
        color: {TEXT};
    }}
    QMainWindow, QWidget {{ background: {BG}; }}

    /* Left panel */
    QScrollArea {{
        border: none;
        border-right: 1px solid {BORDER};
        background: {PANEL};
    }}
    QScrollArea > QWidget > QWidget {{ background: {PANEL}; }}

    /* Labels */
    QLabel {{ background: transparent; color: {TEXT}; }}
    QLabel#dim {{ color: {DIM}; font-size: 11px; }}

    /* Dropdowns */
    QComboBox {{
        background: {BLUE};
        color: white;
        border: none;
        border-radius: 5px;
        padding: 5px 28px 5px 10px;
        min-width: 120px;
        font-weight: 500;
    }}
    QComboBox:hover {{ background: {BLUE_HV}; }}
    QComboBox:focus {{ outline: 2px solid #6baed6; outline-offset: 1px; border: 2px solid #6baed6; }}
    QComboBox::drop-down {{ border: none; width: 24px; }}
    QComboBox::down-arrow {{
        width: 0; height: 0;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid white;
        margin-right: 8px;
    }}
    QComboBox QAbstractItemView {{
        background: #2e2e2e;
        color: {TEXT};
        border: 1px solid {BORDER};
        selection-background-color: {BLUE};
        outline: none;
        padding: 2px;
    }}

    /* Text inputs */
    QLineEdit, QSpinBox {{
        background: {BG};
        color: {TEXT};
        border: 1px solid {BORDER};
        border-radius: 5px;
        padding: 5px 8px;
        min-width: 120px;
    }}
    QLineEdit:focus, QSpinBox:focus {{ border-color: {BLUE}; }}
    QSpinBox::up-button, QSpinBox::down-button {{
        background: {BORDER}; border: none; width: 16px;
    }}

    QCheckBox {{ background: transparent; }}

    /* Browse button */
    QPushButton#browse {{
        background: {GREEN};
        color: white;
        border: none;
        border-radius: 5px;
        padding: 5px 10px;
        font-size: 13px;
        font-weight: 500;
        min-width: 68px;
    }}
    QPushButton#browse:hover {{ background: {GREEN_HV}; }}

    /* Start / Stop */
    QPushButton#start {{
        background: {GREEN};
        color: white;
        border: none;
        border-radius: 7px;
        font-size: 15px;
        font-weight: 700;
        padding: 11px;
        letter-spacing: 0.5px;
    }}
    QPushButton#start:hover {{ background: {GREEN_HV}; }}
    QPushButton#start[stop="true"] {{ background: {RED}; }}
    QPushButton#start[stop="true"]:hover {{ background: {RED_HV}; }}

    /* Separator */
    QFrame#sep {{ background: {BORDER}; }}

    /* Log */
    QTextEdit {{
        background: {BG};
        color: {TEXT};
        border: none;
        font-family: {MONO};
        font-size: 12px;
        padding: 16px;
    }}

    /* Scrollbars */
    QScrollBar:vertical {{
        background: transparent; width: 5px; margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {BORDER}; border-radius: 2px; min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{ background: #555; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
    """

# ── Custom checkbox ───────────────────────────────────────────────────────────

class CheckBox(QCheckBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(20, 20)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        box = QRect(2, 2, 16, 16)

        if self.isChecked():
            p.setBrush(QBrush(QColor(BLUE)))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(box, 4, 4)

            # White checkmark
            pen = QPen(QColor("white"), 2,
                       Qt.PenStyle.SolidLine,
                       Qt.PenCapStyle.RoundCap,
                       Qt.PenJoinStyle.RoundJoin)
            p.setPen(pen)
            p.drawLine(5, 10, 8, 13)
            p.drawLine(8, 13, 15, 6)
        else:
            p.setBrush(QBrush(QColor(BG)))
            p.setPen(QPen(QColor(BORDER), 1.5))
            p.drawRoundedRect(box, 4, 4)

        p.end()

# ── Worker thread ─────────────────────────────────────────────────────────────

class Worker(QThread):
    log         = pyqtSignal(str)   # append new line
    log_replace = pyqtSignal(str)   # overwrite last line (tqdm \r updates)
    done        = pyqtSignal()

    def __init__(self, config):
        super().__init__()
        self.config          = config
        self.current_process = None
        self._stop           = False

    def stop(self):
        self._stop = True
        if self.current_process and self.current_process.poll() is None:
            self.current_process.terminate()

    _SUPPRESS = ("resource_tracker", "leaked semaphore", "UserWarning", "warnings.warn")

    def _read_stdout(self):
        """Read stdout char-by-char, emitting \r lines as replacements."""
        buf = ""
        while True:
            ch = self.current_process.stdout.read(1)
            if not ch:
                if buf and not any(s in buf for s in self._SUPPRESS):
                    self.log.emit(buf)
                break
            if ch == "\r":
                if buf and not any(s in buf for s in self._SUPPRESS):
                    self.log_replace.emit(buf)
                buf = ""
            elif ch == "\n":
                if not any(s in buf for s in self._SUPPRESS):
                    self.log.emit(buf)
                buf = ""
            else:
                buf += ch

    def run(self):
        cfg           = self.config
        files         = cfg["files"]
        output_folder = Path(cfg["output_folder"])
        language      = cfg["language"]
        device       = cfg["device"]
        export       = cfg["export"]
        translate    = cfg["translate"]
        hf_token     = cfg["hf_token"]
        num_speakers = cfg["num_speakers"]
        model        = cfg["model"]

        # MLX + translate needs large-v3 (turbo doesn't support translation)
        if not model and translate and device == "mlx":
            model = "large-v3"

        if not files:
            self.log.emit("No files selected.")
            self.done.emit()
            return

        self.log.emit(f"Found {len(files)} file(s) to process...")
        if model:
            self.log.emit(f"Model: {model}")

        failed      = []
        batch_start = perf_counter()

        for i, file in enumerate(files, 1):
            if self._stop:
                break

            self.log.emit(f"\nProcessing {i}/{len(files)}: {file.name}")
            file_start         = perf_counter()
            transcriptions_dir = output_folder

            cmd = [
                "whisply", "run",
                "--files",      str(file),
                "--output_dir", str(transcriptions_dir),
                "--device",     device,
                "--export",     export,
            ]
            if language:
                cmd += ["--language", language]
            if model:
                cmd += ["--model", model]
            if export in {"all", "srt", "vtt", "webvtt"}:
                cmd += ["--subtitle", "--subtitle_length", "5"]
            if translate:
                cmd.append("--translate")
            if hf_token:
                cmd += ["--annotate", "--hf_token", hf_token]
                if num_speakers > 0:
                    cmd += ["--num_speakers", str(num_speakers)]

            returncode = -1
            try:
                output_folder.mkdir(parents=True, exist_ok=True)
                self.current_process = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, encoding="utf-8", errors="replace", bufsize=0, cwd=str(output_folder),
                )
                self._read_stdout()
                returncode = self.current_process.wait()
            finally:
                for tmp in file.parent.glob(f"{file.stem}*_converted.wav"):
                    tmp.unlink(missing_ok=True)
                logs_dir = output_folder / "logs"
                if logs_dir.is_dir():
                    shutil.rmtree(logs_dir, ignore_errors=True)
                self.current_process = None

            elapsed = _fmt(perf_counter() - file_start)
            if self._stop:
                self.log.emit(f"Stopped: {file.name} ({elapsed})")
                break
            elif returncode != 0:
                failed.append(file.name)
                self.log.emit(f"Failed: {file.name} ({elapsed})")
            else:
                self.log.emit(f"Done: {file.name} ({elapsed})")
                if export != "all":
                    out_dir = transcriptions_dir / file.stem
                    if out_dir.is_dir():
                        for f in out_dir.iterdir():
                            if f.suffix.lstrip(".") != export:
                                f.unlink()

        total = _fmt(perf_counter() - batch_start)
        self.log.emit(f"\n{'─' * 40}")
        if self._stop:
            self.log.emit(f"◼  Stopped after {total}.")
        elif failed:
            self.log.emit(f"⚠  Finished with errors — {len(files) - len(failed)}/{len(files)} file(s) in {total}.")
            self.log.emit(f"Failed: {', '.join(failed)}")
        else:
            self.log.emit(f"✓  All done — {len(files)} file(s) transcribed in {total}.")
        self.done.emit()

# ── Main window ───────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Transcriber")
        self.setMinimumSize(1000, 700)
        self.resize(1000, 700)
        self.worker          = None
        self._selected_files = []
        self._output_folder  = Path.home() / "Downloads"
        self._transcribe_start = None
        self._build_ui()
        self.log_box.setHtml(WELCOME)

        self._pulse_timer = QTimer(self)
        self._pulse_timer.setInterval(1000)
        self._pulse_timer.timeout.connect(self._pulse_progress)

        # Fires 2s after last output — if still running, transcription is in progress
        self._silence_timer = QTimer(self)
        self._silence_timer.setSingleShot(True)
        self._silence_timer.setInterval(300)
        self._silence_timer.timeout.connect(self._start_pulsing)

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        h = QHBoxLayout(root)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)
        h.addWidget(self._left_panel())
        h.addWidget(self._right_panel(), 1)

    # ── Left panel ────────────────────────────────────────────────────────────

    def _left_panel(self):
        scroll = QScrollArea()
        scroll.setFixedWidth(340)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(28, 32, 28, 28)
        v.setSpacing(0)

        # Title block
        title = QLabel("Transcriber")
        title.setStyleSheet("font-size: 26px; font-weight: 800; color: white; letter-spacing: -0.5px;")
        sub = QLabel("AI transcription · offline · private")
        sub.setStyleSheet(f"font-size: 11px; color: {DIM}; margin-bottom: 20px;")
        v.addWidget(title)
        v.addWidget(sub)

        # Form grid
        grid = QGridLayout()
        grid.setVerticalSpacing(10)
        grid.setHorizontalSpacing(12)
        grid.setColumnStretch(1, 1)
        row = 0

        def lbl(text):
            l = QLabel(text)
            l.setStyleSheet(f"color: {DIM}; font-size: 12px;")
            l.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            return l

        def sep():
            nonlocal row
            line = QFrame()
            line.setObjectName("sep")
            line.setFrameShape(QFrame.Shape.HLine)
            line.setFixedHeight(1)
            grid.addWidget(line, row, 0, 1, 2)
            row += 1

        # Audio file
        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("browse")
        browse_btn.setFixedWidth(68)
        browse_btn.setStyleSheet(f"""
            QPushButton {{
                background: {GREEN}; color: white; border: none;
                border-radius: 5px; padding: 5px 10px;
                font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ background: {GREEN_HV}; }}
        """)
        browse_btn.clicked.connect(self._browse)
        grid.addWidget(lbl("Audio file:"), row, 0)
        grid.addWidget(browse_btn, row, 1, Qt.AlignmentFlag.AlignLeft)
        row += 1

        # File list box spanning both columns
        self.file_list = QListWidget()
        self.file_list.setFixedHeight(72)
        self.file_list.setFrameShape(QFrame.Shape.NoFrame)
        self.file_list.setStyleSheet(f"""
            QListWidget {{
                background: {PANEL};
                border: 1px solid {BORDER};
                border-radius: 5px;
                color: {DIM};
                font-size: 11px;
                padding: 2px;
                outline: none;
            }}
            QListWidget::item {{ padding: 3px 6px; background: {PANEL}; }}
            QListWidget::item:selected {{ background: {BLUE}; color: white; border-radius: 3px; }}
            QListWidget QScrollBar:vertical {{
                background: {PANEL}; width: 5px;
            }}
        """)
        self.file_list.addItem("No files selected")
        grid.addWidget(self.file_list, row, 0, 1, 2)
        row += 1

        # Output folder
        out_btn = QPushButton("Browse")
        out_btn.setObjectName("browse")
        out_btn.setFixedWidth(68)
        out_btn.setStyleSheet(f"""
            QPushButton {{
                background: {GREEN}; color: white; border: none;
                border-radius: 5px; padding: 5px 10px;
                font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ background: {GREEN_HV}; }}
        """)
        out_btn.clicked.connect(self._browse_output)
        grid.addWidget(lbl("Output folder:"), row, 0)
        grid.addWidget(out_btn, row, 1, Qt.AlignmentFlag.AlignLeft)
        row += 1

        self.output_box = QLineEdit(str(Path.home() / "Downloads"))
        self.output_box.setReadOnly(True)
        self.output_box.setStyleSheet(f"""
            QLineEdit {{
                background: {PANEL};
                border: 1px solid {BORDER};
                border-radius: 5px;
                color: {DIM};
                font-size: 11px;
                padding: 3px 6px;
            }}
        """)
        grid.addWidget(self.output_box, row, 0, 1, 2)
        row += 1

        sep()

        # Language
        self.language_combo = QComboBox()
        self.language_combo.addItems(list(LANGUAGES.keys()))
        self.language_combo.setCurrentText("English")
        self.language_combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.language_combo.wheelEvent = lambda e: e.ignore()
        grid.addWidget(lbl("Language:"), row, 0)
        grid.addWidget(self.language_combo, row, 1)
        row += 1

        # Device
        self.device_combo = QComboBox()
        self.device_combo.addItems(DEVICES)
        self.device_combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.device_combo.wheelEvent = lambda e: e.ignore()
        grid.addWidget(lbl("Device:"), row, 0)
        grid.addWidget(self.device_combo, row, 1)
        row += 1

        # Model
        self.model_combo = QComboBox()
        self.model_combo.addItems(MODELS)
        self.model_combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.model_combo.wheelEvent = lambda e: e.ignore()
        grid.addWidget(lbl("Model:"), row, 0)
        grid.addWidget(self.model_combo, row, 1)
        row += 1

        # Export format
        self.export_combo = QComboBox()
        self.export_combo.addItems(EXPORT_FORMATS)
        self.export_combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.export_combo.wheelEvent = lambda e: e.ignore()
        grid.addWidget(lbl("Export:"), row, 0)
        grid.addWidget(self.export_combo, row, 1)
        row += 1

        # Translate
        self.translate_check = CheckBox()
        grid.addWidget(lbl("Translate to English:"), row, 0)
        grid.addWidget(self.translate_check, row, 1, Qt.AlignmentFlag.AlignLeft)
        row += 1

        sep()

        # Speaker annotation header
        sa_lbl = QLabel("Speaker annotation")
        sa_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #aaa; margin-top: 2px;")
        grid.addWidget(sa_lbl, row, 0, 1, 2)
        row += 1

        # HF Token
        self.hf_token_edit = QLineEdit()
        self.hf_token_edit.setPlaceholderText("hf_...")
        self.hf_token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        grid.addWidget(lbl("HF token:"), row, 0)
        grid.addWidget(self.hf_token_edit, row, 1)
        row += 1

        # Num speakers
        self.num_speakers_edit = QLineEdit()
        self.num_speakers_edit.setPlaceholderText("0  (auto-detect)")
        grid.addWidget(lbl("Speakers:"), row, 0)
        grid.addWidget(self.num_speakers_edit, row, 1)
        row += 1

        v.addLayout(grid)
        v.addStretch()

        # Start button
        v.addSpacing(16)
        self.start_btn = QPushButton("Start")
        self.start_btn.setObjectName("start")
        self.start_btn.setMinimumHeight(46)
        self.start_btn.clicked.connect(self._toggle)
        v.addWidget(self.start_btn)

        scroll.setWidget(w)
        return scroll

    # ── Right panel ───────────────────────────────────────────────────────────

    def _right_panel(self):
        wrapper = QWidget()
        wrapper.setStyleSheet(f"background: {BG};")
        v = QVBoxLayout(wrapper)
        v.setContentsMargins(20, 20, 20, 20)

        # "Log" label tab like noScribe
        tab = QLabel("Log")
        tab.setStyleSheet(f"""
            background: {BORDER}; color: {TEXT};
            font-size: 12px; font-weight: 600;
            padding: 4px 14px;
            border-radius: 4px;
        """)
        tab.setFixedHeight(26)
        tab.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        v.addWidget(tab)
        v.addSpacing(6)

        # Log box in a bordered container
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setStyleSheet(f"""
            QTextEdit {{
                background: {PANEL};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 8px;
                font-family: {MONO};
                font-size: 12px;
                padding: 14px;
            }}
        """)
        v.addWidget(self.log_box)
        return wrapper

    # ── Actions ───────────────────────────────────────────────────────────────

    def _browse(self):
        exts = " ".join(f"*{e}" for e in sorted(AUDIO_EXTENSIONS))
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select audio files", "", f"Audio files ({exts})"
        )
        if files:
            self._selected_files = [Path(f) for f in files]
            self.file_list.clear()
            self.file_list.setStyleSheet(self.file_list.styleSheet().replace(f"color: {DIM};", f"color: {TEXT};"))
            for f in files:
                self.file_list.addItem(Path(f).name)

    def _browse_output(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select output folder", str(self._output_folder)
        )
        if folder:
            self._output_folder = Path(folder)
            self.output_box.setText(folder)
            self.output_box.setStyleSheet(self.output_box.styleSheet().replace(
                f"color: {DIM};", f"color: {TEXT};"
            ))

    def _toggle(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self._set_btn_start()
        else:
            self._start()

    def _start(self):
        if not self._selected_files:
            self._log("Please select audio files first.")
            return

        config = {
            "files":          self._selected_files,
            "output_folder":  self._output_folder,
            "language":       LANGUAGES[self.language_combo.currentText()],
            "device":       self.device_combo.currentText(),
            "export":       self.export_combo.currentText(),
            "translate":    self.translate_check.isChecked(),
            "hf_token":     self.hf_token_edit.text().strip(),
            "num_speakers": int(self.num_speakers_edit.text().strip() or 0),
            "model":        "" if self.model_combo.currentText() == "large-v3-turbo"
                            else self.model_combo.currentText(),
        }

        self._model_download_noted = False
        self.log_box.append("")
        self.worker = Worker(config)
        self.worker.log.connect(self._on_worker_log)
        self.worker.log_replace.connect(self._log_replace)
        self.worker.done.connect(self._set_btn_start)
        self.worker.start()

        self.start_btn.setText("Stop")
        self.start_btn.setProperty("stop", True)
        self.start_btn.style().unpolish(self.start_btn)
        self.start_btn.style().polish(self.start_btn)

    def _set_btn_start(self):
        self._pulse_timer.stop()
        self._silence_timer.stop()
        self._transcribe_start = None
        self.start_btn.setText("Start")
        self.start_btn.setProperty("stop", False)
        self.start_btn.style().unpolish(self.start_btn)
        self.start_btn.style().polish(self.start_btn)

    def _on_worker_log(self, msg):
        # Stop pulsing while output is arriving
        self._pulse_timer.stop()
        self._silence_timer.stop()
        self._transcribe_start = None

        # Annotate model download lines
        if "Fetching" in msg and not self._model_download_noted:
            self._log("Downloading Whisper model files (first run only, cached after this)...")
            self._model_download_noted = True

        self._log(msg)

        # Start pulsing immediately after model fetch completes
        if "Fetching" in msg and "100%" in msg and self.worker and self.worker.isRunning():
            self._silence_timer.start()

    def _start_pulsing(self):
        if self.worker and self.worker.isRunning():
            self._transcribe_start = perf_counter()
            self._log("\nTranscribing.")
            self._pulse_timer.start()

    def _pulse_progress(self):
        if self._transcribe_start is None:
            return
        elapsed  = perf_counter() - self._transcribe_start
        m, s     = divmod(int(elapsed), 60)
        frames   = ["[●○○○]", "[○●○○]", "[○○●○]", "[○○○●]", "[○○●○]", "[○●○○]"]
        frame    = frames[int(elapsed) % len(frames)]
        self._log_replace(f"{frame}  Transcribing  ({m:02d}:{s:02d} elapsed)")

    def _log(self, msg):
        ts   = datetime.now().strftime("%H:%M:%S")
        text = f"\n[{ts}] {msg.lstrip()}" if msg.startswith("\n") else f"[{ts}] {msg}"
        self.log_box.append(text)

    def _log_replace(self, msg):
        """Overwrite the last line — used for tqdm \r progress updates."""
        ts     = datetime.now().strftime("%H:%M:%S")
        text   = f"[{ts}] {msg}"
        cursor = self.log_box.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.select(cursor.SelectionType.LineUnderCursor)
        cursor.insertText(text)
        self.log_box.setTextCursor(cursor)
        self.log_box.ensureCursorVisible()

# ── Helpers ───────────────────────────────────────────────────────────────────

def _fmt(seconds: float) -> str:
    m, s = divmod(seconds, 60)
    h, m = divmod(int(m), 60)
    if h:   return f"{h}h {m}m {s:.1f}s"
    if m:   return f"{m}m {s:.1f}s"
    return f"{seconds:.1f}s"

# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(stylesheet())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
