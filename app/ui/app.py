"""GUI for kong-verter using CustomTkinter.

Sidebar navigation layout with four sections:
  - Transcribir:     Video/Audio → Text transcription with Notes & AI Summary sub-tabs.
  - ✨ Resumen:      Standalone text → AI Summary.
  - 🎬 Convertir:   Video → MP3 conversion.
  - ⚙️ Configuración: Engine, model, language, LLM settings, and Template Editor.
"""

import logging
import shutil
import tempfile
import threading
import time
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from app.audio.transcriber import get_transcriber
from app.audio.video_converter import convert_video_to_audio
from app.core.config import load_config, save_config
from app.llm import templates as template_manager
from app.llm.summarizer import Summarizer

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(Path.home() / ".konverter" / "kong-verter.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("kong-verter")

# ── Constants ─────────────────────────────────────────────────────────────────
VIDEO_EXTS = ("*.mp4", "*.mkv", "*.avi", "*.mov", "*.webm")
AUDIO_EXTS = ("*.mp3", "*.wav", "*.m4a", "*.ogg")

_MODEL_LABELS: dict[str, str] = {
    "tiny":     "Tiny      (~75 MB)   — Rápido, baja precisión",
    "base":     "Base      (~142 MB)  — Rápido, aceptable",
    "small":    "Small     (~461 MB)  — Buen balance ⭐",
    "medium":   "Medium    (~1.5 GB)  — Alta calidad",
    "large-v3": "Large-v3  (~3.1 GB)  — Máxima calidad",
}
_MODEL_KEYS = list(_MODEL_LABELS.keys())
_MODEL_VALUES = list(_MODEL_LABELS.values())

_LANGUAGE_LABELS: dict[str, str] = {"auto": "Automático", "es": "Español", "en": "English"}
_LANGUAGE_KEYS = list(_LANGUAGE_LABELS.keys())
_LANGUAGE_VALUES = list(_LANGUAGE_LABELS.values())

_ENGINE_LABELS: dict[str, str] = {"offline": "🖥️  Offline (faster-whisper)", "online": "🌐  Online (Google Speech)"}
_ENGINE_KEYS = list(_ENGINE_LABELS.keys())
_ENGINE_VALUES = list(_ENGINE_LABELS.values())

_LLM_ENGINE_LABELS: dict[str, str] = {"groq": "☁️  Groq Cloud (Fastest)", "ollama": "🏠  Ollama (Local)"}
_LLM_ENGINE_KEYS = list(_LLM_ENGINE_LABELS.keys())
_LLM_ENGINE_VALUES = list(_LLM_ENGINE_LABELS.values())

# Toast colors
_TOAST_SUCCESS = "#2d6a4f"
_TOAST_ERROR = "#8b1a1a"
_TOAST_INFO = "#1a3a5c"

# Sidebar colors
_SIDEBAR_BG = "#1a1a2e"
_SIDEBAR_BTN_ACTIVE = "#16213e"
_SIDEBAR_BTN_HOVER = "#0f3460"
_SIDEBAR_WIDTH = 160


class KonverterApp(ctk.CTk):  # type: ignore[misc]
    """Main application window with sidebar navigation layout."""

    def __init__(self) -> None:
        super().__init__()

        self.title("kong-verter")
        self.geometry("900x700")
        self.minsize(750, 600)

        self._config = load_config()
        template_manager.init_templates()

        # Main grid: sidebar (col 0) + content (col 1), status bar (row 2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ── Toast notification ───────────────────────────────────────────────
        self._toast = ctk.CTkLabel(
            self, text="", height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=8, fg_color=_TOAST_SUCCESS,
        )
        self._toast_job: str | None = None

        # ── Sidebar ──────────────────────────────────────────────────────────
        self._build_sidebar()

        # ── Content sections ─────────────────────────────────────────────────
        self._sections: dict[str, ctk.CTkFrame] = {}
        self._active_section: str = ""

        self._build_transcribe_section()
        self._build_summary_section()
        self._build_convert_section()
        self._build_settings_section()

        # ── Status bar ───────────────────────────────────────────────────────
        self._ollama_connected: bool = False
        self._build_status_bar()

        # ── Initial state ────────────────────────────────────────────────────
        self._switch_section("transcribir")
        self._refresh_ollama_models()
        self._update_key_visibility()


    # ══════════════════════════════════════════════════════════════════════════
    # Sidebar & Navigation
    # ══════════════════════════════════════════════════════════════════════════

    def _build_sidebar(self) -> None:
        """Build the sidebar with navigation buttons."""
        sidebar = ctk.CTkFrame(self, width=_SIDEBAR_WIDTH, fg_color=_SIDEBAR_BG, corner_radius=0)
        sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            sidebar, text="Kong-verter",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="white",
        ).grid(row=0, column=0, padx=10, pady=(20, 5), sticky="ew")
        ctk.CTkLabel(
            sidebar, text="Video · Audio · IA",
            font=ctk.CTkFont(size=10), text_color="gray",
        ).grid(row=1, column=0, padx=10, pady=(0, 20), sticky="ew")

        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        nav_items = [
            ("transcribir", "📝  Transcribir"),
            ("resumen", "✨  Resumen"),
            ("convertir", "🎬  Convertir"),
        ]
        for i, (key, label) in enumerate(nav_items):
            btn = ctk.CTkButton(
                sidebar, text=label, anchor="w",
                font=ctk.CTkFont(size=13),
                fg_color="transparent", hover_color=_SIDEBAR_BTN_HOVER,
                height=40, corner_radius=8,
                command=lambda k=key: self._switch_section(k),
            )
            btn.grid(row=i + 2, column=0, padx=8, pady=2, sticky="ew")
            self._nav_buttons[key] = btn

        sidebar.grid_rowconfigure(len(nav_items) + 2, weight=1)

        btn_settings = ctk.CTkButton(
            sidebar, text="⚙️  Configuración", anchor="w",
            font=ctk.CTkFont(size=13),
            fg_color="transparent", hover_color=_SIDEBAR_BTN_HOVER,
            height=40, corner_radius=8,
            command=lambda: self._switch_section("configuracion"),
        )
        btn_settings.grid(row=len(nav_items) + 3, column=0, padx=8, pady=(2, 15), sticky="sew")
        self._nav_buttons["configuracion"] = btn_settings

    def _switch_section(self, name: str) -> None:
        """Switch the visible content section and update sidebar highlight."""
        if name == self._active_section:
            return
        if self._active_section and self._active_section in self._sections:
            self._sections[self._active_section].grid_remove()
        if name in self._sections:
            self._sections[name].grid(row=0, column=1, rowspan=2, sticky="nsew", padx=0, pady=0)
        for key, btn in self._nav_buttons.items():
            if key == name:
                btn.configure(fg_color=_SIDEBAR_BTN_ACTIVE)
            else:
                btn.configure(fg_color="transparent")
        self._active_section = name

    # ══════════════════════════════════════════════════════════════════════════
    # Shared UX Utility
    # ══════════════════════════════════════════════════════════════════════════

    def _show_toast(self, message: str, kind: str = "success", duration: int = 4000) -> None:
        """Show a temporary toast notification."""
        color = {"success": _TOAST_SUCCESS, "error": _TOAST_ERROR, "info": _TOAST_INFO}.get(kind, _TOAST_SUCCESS)
        self._toast.configure(text=f"  {message}  ", fg_color=color)
        self._toast.place(relx=0.5, y=10, anchor="n", relwidth=0.6)
        if self._toast_job:
            self.after_cancel(self._toast_job)
        self._toast_job = self.after(duration, lambda: self._toast.place_forget())

    # ══════════════════════════════════════════════════════════════════════════
    # Section 1 — Transcribir (3 sub-tabs)
    # ══════════════════════════════════════════════════════════════════════════

    def _build_transcribe_section(self) -> None:
        """Build the Transcribe section with 3 sub-tabs."""
        frame = ctk.CTkFrame(self, fg_color="transparent")
        self._sections["transcribir"] = frame
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        sub_tabs = ctk.CTkTabview(frame)
        sub_tabs.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        sub_tabs.add("📄  Transcripción")
        sub_tabs.add("📝  Notas")
        sub_tabs.add("✨  Resultado IA")

        self._build_transcription_tab(sub_tabs)
        self._build_notes_tab(sub_tabs)
        self._build_trans_result_tab(sub_tabs)

    def _build_transcription_tab(self, sub_tabs: ctk.CTkTabview) -> None:
        """Build the Transcription sub-tab with multi-file batch support."""
        tab = sub_tabs.tab("📄  Transcripción")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Internal state: list of files queued for transcription
        self._trans_files: list[Path] = []
        self._trans_running: bool = False

        # ── Top bar: file selector + counter ────────────────────────────────
        top_bar = ctk.CTkFrame(tab, fg_color="transparent")
        top_bar.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        top_bar.grid_columnconfigure(1, weight=1)

        self._btn_add_files = ctk.CTkButton(
            top_bar, text="📁  Agregar Videos",
            font=ctk.CTkFont(size=13), width=160, height=36,
            command=self._browse_media_multiple,
        )
        self._btn_add_files.grid(row=0, column=0, padx=(0, 10))

        self._trans_queue_label = ctk.CTkLabel(
            top_bar, text="Sin archivos en cola.",
            font=ctk.CTkFont(size=12), text_color="gray", anchor="w",
        )
        self._trans_queue_label.grid(row=0, column=1, sticky="ew")

        self._btn_clear_queue = ctk.CTkButton(
            top_bar, text="🗑 Limpiar",
            font=ctk.CTkFont(size=12), width=90, height=36,
            fg_color="gray30", hover_color="gray40",
            command=self._clear_trans_queue,
        )
        self._btn_clear_queue.grid(row=0, column=2, padx=(10, 0))
        self._btn_clear_queue.configure(state="disabled")

        # ── Video progress list (scrollable) ────────────────────────────────
        self._trans_list_frame = ctk.CTkScrollableFrame(tab, label_text="Cola de transcripción")
        self._trans_list_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self._trans_list_frame.grid_columnconfigure(0, weight=1)

        # Placeholder shown when queue is empty
        self._trans_list_placeholder = ctk.CTkLabel(
            self._trans_list_frame,
            text="Agrega videos con el botón de arriba.\nSe procesarán en orden.",
            font=ctk.CTkFont(size=12), text_color="gray",
        )
        self._trans_list_placeholder.grid(row=0, column=0, pady=40)

        # Row widgets per file: {path_str: {"row_frame", "status_label", "progress_bar", "pct_label"}}
        self._trans_row_widgets: dict[str, dict] = {}

        # ── Transcribe button ────────────────────────────────────────────────
        self._btn_transcribe = ctk.CTkButton(
            tab, text="🎙️  Transcribir Todo",
            font=ctk.CTkFont(size=14, weight="bold"), height=40,
            command=self._start_batch_transcription,
        )
        self._btn_transcribe.grid(row=2, column=0, padx=10, pady=(5, 10), sticky="ew")


    def _build_notes_tab(self, sub_tabs: ctk.CTkTabview) -> None:
        """Build the Notes sub-tab."""
        tab = sub_tabs.tab("📝  Notas")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            tab, text="Notas opcionales para enriquecer el resumen:",
            font=ctk.CTkFont(size=12, weight="bold"), anchor="w",
        ).grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")

        self._notes_textbox = ctk.CTkTextbox(tab, font=ctk.CTkFont(size=13), wrap="word")
        self._notes_textbox.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

    def _build_trans_result_tab(self, sub_tabs: ctk.CTkTabview) -> None:
        """Build the AI Result sub-tab within Transcribe section."""
        tab = sub_tabs.tab("✨  Resultado IA")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)

        ctrls = ctk.CTkFrame(tab, fg_color="transparent")
        ctrls.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        ctrls.grid_columnconfigure(0, weight=1)

        self._trans_template_var = ctk.StringVar(value="General")
        self._trans_templates_menu = ctk.CTkOptionMenu(ctrls, variable=self._trans_template_var)
        self._trans_templates_menu.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self._refresh_trans_templates_list()

        self._trans_translate_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(ctrls, text="Traducir a Español", variable=self._trans_translate_var).grid(
            row=0, column=1, padx=5
        )

        self._btn_trans_summarize = ctk.CTkButton(
            tab, text="✨  Generar Resumen",
            font=ctk.CTkFont(size=14, weight="bold"), height=40,
            fg_color="#6366F1", hover_color="#4F46E5",
            command=self._start_trans_summarization,
        )
        self._btn_trans_summarize.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        self._trans_result_textbox = ctk.CTkTextbox(tab, font=ctk.CTkFont(size=13), wrap="word")
        self._trans_result_textbox.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        self._trans_result_textbox.insert("0.0", "El resumen aparecerá aquí…")
        self._trans_result_textbox.configure(state="disabled")

        btn_row = ctk.CTkFrame(tab, fg_color="transparent")
        btn_row.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="ew")
        btn_row.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(
            btn_row, text="📋 Copiar", height=36, fg_color="gray30", hover_color="gray40",
            command=self._copy_trans_result,
        ).grid(row=0, column=0, padx=(0, 3), sticky="ew")
        ctk.CTkButton(
            btn_row, text="💾 Guardar .md", height=36,
            command=self._save_trans_result,
        ).grid(row=0, column=1, padx=(3, 0), sticky="ew")

    # ── Queue management ─────────────────────────────────────────────────────

    def _refresh_trans_templates_list(self) -> None:
        """Refresh the template list for the transcription result tab."""
        templates = template_manager.get_all_templates()
        names = [t["name"] for t in templates]
        if not names:
            names = ["General"]
        self._trans_templates_menu.configure(values=names)

    def _browse_media_multiple(self) -> None:
        """Open multi-file dialog for media files and add them to the queue."""
        all_media = " ".join(VIDEO_EXTS + AUDIO_EXTS)
        paths = filedialog.askopenfilenames(
            filetypes=[("Multimedia", all_media), ("Todos", "*.*")]
        )
        if not paths:
            return
        for raw in paths:
            p = Path(raw)
            if str(p) not in self._trans_row_widgets:
                self._trans_files.append(p)
                self._add_queue_row(p)
        self._refresh_queue_label()

    def _add_queue_row(self, file_path: Path) -> None:
        """Add a progress row for a single file in the scrollable list."""
        key = str(file_path)
        row_index = len(self._trans_row_widgets)

        # Hide placeholder once we have rows
        if row_index == 0:
            self._trans_list_placeholder.grid_remove()

        row_frame = ctk.CTkFrame(self._trans_list_frame, corner_radius=6)
        row_frame.grid(row=row_index, column=0, padx=5, pady=4, sticky="ew")
        row_frame.grid_columnconfigure(1, weight=1)

        # File icon + name
        ctk.CTkLabel(
            row_frame, text="⏳", width=28, font=ctk.CTkFont(size=16),
            anchor="center",
        ).grid(row=0, column=0, padx=(10, 5), pady=(8, 2))

        ctk.CTkLabel(
            row_frame, text=file_path.name,
            font=ctk.CTkFont(size=12, weight="bold"), anchor="w",
        ).grid(row=0, column=1, padx=0, pady=(8, 2), sticky="ew")

        status_label = ctk.CTkLabel(
            row_frame, text="En cola…",
            font=ctk.CTkFont(size=11), text_color="gray", anchor="w",
        )
        status_label.grid(row=1, column=1, padx=0, pady=(0, 4), sticky="ew")

        progress_bar = ctk.CTkProgressBar(
            row_frame, height=6, fg_color="#E2E8F0", progress_color="#3B82F6"
        )
        progress_bar.set(0)
        progress_bar.grid(row=2, column=1, padx=0, pady=(0, 4), sticky="ew")

        pct_label = ctk.CTkLabel(
            row_frame, text="0%",
            font=ctk.CTkFont(size=11), text_color="gray", width=40, anchor="e",
        )
        pct_label.grid(row=2, column=2, padx=(5, 10), pady=(0, 4))

        self._trans_row_widgets[key] = {
            "row_frame": row_frame,
            "status_label": status_label,
            "progress_bar": progress_bar,
            "pct_label": pct_label,
        }

    def _clear_trans_queue(self) -> None:
        """Remove all files from the queue (only when not running)."""
        if self._trans_running:
            self._show_toast("⚠️  No se puede limpiar mientras se transcribe.", kind="info")
            return
        for widgets in self._trans_row_widgets.values():
            widgets["row_frame"].destroy()
        self._trans_row_widgets.clear()
        self._trans_files.clear()
        self._trans_list_placeholder.grid(row=0, column=0, pady=40)
        self._refresh_queue_label()

    def _refresh_queue_label(self) -> None:
        """Update the queue counter label and button states."""
        count = len(self._trans_files)
        if count == 0:
            self._trans_queue_label.configure(text="Sin archivos en cola.")
            self._btn_clear_queue.configure(state="disabled")
            self._btn_transcribe.configure(state="disabled")
        else:
            self._trans_queue_label.configure(text=f"{count} archivo{'s' if count != 1 else ''} en cola.")
            self._btn_clear_queue.configure(state="normal")
            self._btn_transcribe.configure(state="normal")

    # ── Batch transcription logic ────────────────────────────────────────────

    def _start_batch_transcription(self) -> None:
        """Start batch transcription of all queued files in a background thread."""
        if not self._trans_files:
            self._show_toast("⚠️  Agrega al menos un archivo.", kind="info")
            return
        if self._trans_running:
            return
        self._trans_running = True
        self._btn_transcribe.configure(state="disabled", text="⏳  Transcribiendo…")
        self._btn_add_files.configure(state="disabled")
        self._btn_clear_queue.configure(state="disabled")
        threading.Thread(target=self._run_batch_transcription, daemon=True).start()

    def _run_batch_transcription(self) -> None:
        """Process each file in the queue sequentially (background thread)."""
        transcriber = get_transcriber(
            self._config.get("engine", "offline"),
            self._config.get("model", "small"),
            self._config.get("language", "auto"),
        )
        move_processed = self._config.get("move_processed", True)
        output_folder_str = self._config.get("output_folder", "")

        for file_path in list(self._trans_files):
            key = str(file_path)
            tmp_path: Path | None = None

            # Skip files that no longer exist (already moved/processed in a previous run)
            if not file_path.exists():
                self._trans_files.remove(file_path)
                self.after(0, self._set_row_error, key, "Archivo no encontrado (ya procesado)")
                continue

            try:
                # ── Update UI: extracting audio ──────────────────────────────
                self.after(0, self._set_row_status, key, "⏳ Extrayendo audio…", "#F59E0B")

                audio_path = file_path
                if file_path.suffix.lower() in [".mp4", ".mkv", ".avi", ".mov", ".webm"]:
                    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
                        tmp_path = Path(tmp_file.name)
                    convert_video_to_audio(str(file_path), str(tmp_path))
                    audio_path = tmp_path

                # ── Update UI: transcribing ──────────────────────────────────
                self.after(0, self._set_row_status, key, "🎙️ Transcribiendo…", "#3B82F6")

                segments: list[str] = []
                start_time = time.time()

                for msg_type, content in transcriber.transcribe_stream(
                    audio_path, self._config.get("language", "auto")
                ):
                    if msg_type == "segment":
                        segments.append(content)
                    elif msg_type == "progress":
                        elapsed = time.time() - start_time
                        self.after(0, self._update_row_progress, key, content, elapsed)

                full_text = " ".join(segments)

                # ── Save .txt ────────────────────────────────────────────────
                output_dir = Path(output_folder_str) if output_folder_str else file_path.parent
                output_dir.mkdir(parents=True, exist_ok=True)
                txt_path = output_dir / (file_path.stem + "_transcripcion.txt")
                txt_path.write_text(full_text, encoding="utf-8")

                # ── Move video to 'procesados/' ──────────────────────────────
                if move_processed and file_path.suffix.lower() in [".mp4", ".mkv", ".avi", ".mov", ".webm"]:
                    dest_dir = file_path.parent / "procesados"
                    dest_dir.mkdir(exist_ok=True)
                    dest_path = dest_dir / file_path.name
                    if dest_path.exists():
                        stem = file_path.stem
                        suffix = file_path.suffix
                        counter = 1
                        while dest_path.exists():
                            dest_path = dest_dir / f"{stem}_{counter}{suffix}"
                            counter += 1
                    shutil.move(str(file_path), str(dest_path))

                # Remove from queue so re-pressing Transcribir won't retry it
                self._trans_files.remove(file_path)
                self.after(0, self._set_row_done, key, str(txt_path.name), str(txt_path.parent))

            except Exception as exc:
                log.exception("Batch transcription failed for %s", file_path)
                self.after(0, self._set_row_error, key, str(exc))
            finally:
                if tmp_path:
                    tmp_path.unlink(missing_ok=True)

        self.after(0, self._on_batch_done)

    def _set_row_status(self, key: str, text: str, color: str) -> None:
        """Update the status label of a queue row."""
        widgets = self._trans_row_widgets.get(key)
        if widgets:
            widgets["status_label"].configure(text=text, text_color=color)

    def _update_row_progress(self, key: str, progress: float, elapsed: float) -> None:
        """Update progress bar and percentage label of a queue row."""
        widgets = self._trans_row_widgets.get(key)
        if not widgets:
            return
        widgets["progress_bar"].configure(progress_color="#3B82F6")
        widgets["progress_bar"].set(progress)
        pct = int(progress * 100)
        if progress > 0.05 and elapsed > 0:
            total_est = elapsed / progress
            remaining = total_est - elapsed
            mins, secs = divmod(int(remaining), 60)
            widgets["pct_label"].configure(text=f"{pct}%")
            widgets["status_label"].configure(
                text=f"🎙️ Transcribiendo… {mins:02d}:{secs:02d} restantes", text_color="#3B82F6"
            )
        else:
            widgets["pct_label"].configure(text=f"{pct}%")

    def _set_row_done(self, key: str, txt_filename: str, txt_folder: str) -> None:
        """Mark a queue row as completed and add an open-folder button."""
        import subprocess
        import sys as _sys
        widgets = self._trans_row_widgets.get(key)
        if not widgets:
            return
        widgets["progress_bar"].set(1.0)
        widgets["progress_bar"].configure(progress_color="#10B981")
        widgets["pct_label"].configure(text="100%")
        widgets["status_label"].configure(
            text=f"✅ Completado — {txt_filename}", text_color="#10B981"
        )
        row_frame = widgets["row_frame"]

        def _open_folder(folder: str = txt_folder) -> None:
            if _sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            elif _sys.platform == "win32":
                subprocess.Popen(["explorer", folder])
            else:
                subprocess.Popen(["xdg-open", folder])

        open_btn = ctk.CTkButton(
            row_frame, text="📂", width=36, height=24,
            font=ctk.CTkFont(size=12),
            fg_color="gray30", hover_color="gray40",
            command=_open_folder,
        )
        open_btn.grid(row=0, column=3, padx=(0, 10), pady=(8, 2))

    def _set_row_error(self, key: str, error_msg: str) -> None:
        """Mark a queue row as failed."""
        widgets = self._trans_row_widgets.get(key)
        if widgets:
            widgets["progress_bar"].configure(progress_color="#EF4444")
            widgets["status_label"].configure(
                text=f"❌ Error: {error_msg[:60]}", text_color="#EF4444"
            )

    def _on_batch_done(self) -> None:
        """Re-enable controls after all batch items are processed."""
        self._trans_running = False
        self._btn_transcribe.configure(state="normal", text="🎙️  Transcribir Todo")
        self._btn_add_files.configure(state="normal")
        self._btn_clear_queue.configure(state="normal")
        self._show_toast("✅ Lote de transcripción completado.")


    # ── Transcription AI summarization ───────────────────────────────────────

    def _start_trans_summarization(self) -> None:
        """Start AI summarization — requires transcription text in the result textbox."""
        text = self._trans_result_textbox.get("0.0", "end").strip()
        # Also check if there's any completed transcription to summarize
        if not text or text == "El resumen aparecerá aquí…":
            self._show_toast("⚠️  Primero transcribe un audio/video.", kind="info")
            return

        llm_engine = self._config.get("llm_engine", "groq")
        if llm_engine == "groq" and not self._config.get("groq_api_key"):
            self._show_toast("⚠️ Configura la API Key de Groq en Ajustes.", kind="error")
            return

        notes = self._notes_textbox.get("0.0", "end").strip()
        if notes:
            text += "\n\nNotas adicionales del usuario:\n" + notes

        self._btn_trans_summarize.configure(state="disabled")

        template_name = self._trans_template_var.get()
        templates = template_manager.get_all_templates()
        selected = next((t for t in templates if t["name"] == template_name), templates[0] if templates else None)
        if not selected:
            self._show_toast("⚠️ No hay plantillas disponibles.", kind="error")
            self._btn_trans_summarize.configure(state="normal")
            return

        threading.Thread(
            target=self._run_trans_summarization, args=(text, selected["body"]), daemon=True
        ).start()

    def _run_trans_summarization(self, text: str, template_body: str) -> None:
        """Run transcription summarization in background thread."""
        try:
            log.info("Starting trans summarization | engine=%s", self._config.get("llm_engine"))
            self.after(0, self._prepare_trans_result_ui)
            summarizer = Summarizer(self._config)
            for chunk in summarizer.summarize_stream(text, template_body, self._trans_translate_var.get()):
                self.after(0, self._append_trans_result_chunk, chunk)
            self.after(0, self._on_trans_summary_success)
        except Exception as e:
            log.exception("Trans summarization failed")
            self.after(0, self._on_generic_error, str(e), self._btn_trans_summarize, ctk.StringVar())

    def _prepare_trans_result_ui(self) -> None:
        """Prepare the transcription result textbox."""
        self._trans_result_textbox.configure(state="normal")
        self._trans_result_textbox.delete("0.0", "end")
        self._trans_result_textbox.configure(state="disabled")

    def _append_trans_result_chunk(self, chunk: str) -> None:
        """Append a chunk to the transcription result textbox."""
        self._trans_result_textbox.configure(state="normal")
        self._trans_result_textbox.insert("end", chunk)
        self._trans_result_textbox.see("end")
        self._trans_result_textbox.configure(state="disabled")

    def _on_trans_summary_success(self) -> None:
        """Handle successful transcription summarization."""
        self._btn_trans_summarize.configure(state="normal")
        self._show_toast("✨ Resumen generado con éxito.")

    def _copy_trans_result(self) -> None:
        """Copy transcription result to clipboard."""
        self.clipboard_clear()
        self.clipboard_append(self._trans_result_textbox.get("0.0", "end").strip())
        self._show_toast("📋 Copiado al portapapeles.")

    def _save_trans_result(self) -> None:
        """Save transcription result as markdown file."""
        text = self._trans_result_textbox.get("0.0", "end").strip()
        if not text:
            return
        path = filedialog.asksaveasfilename(defaultextension=".md", filetypes=[("Markdown", "*.md")])
        if path:
            Path(path).write_text(text, encoding="utf-8")
            self._show_toast(f"💾 Guardado: {Path(path).name}")

    # ══════════════════════════════════════════════════════════════════════════
    # Section 2 — Resumen (standalone)
    # ══════════════════════════════════════════════════════════════════════════

    def _build_summary_section(self) -> None:
        """Build the standalone Summary section."""
        frame = ctk.CTkFrame(self, fg_color="transparent")
        self._sections["resumen"] = frame
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_rowconfigure(4, weight=1)

        ctk.CTkLabel(
            frame, text="✨ Resumen Rápido — Pega o escribe cualquier texto",
            font=ctk.CTkFont(size=14, weight="bold"), anchor="w",
        ).grid(row=0, column=0, padx=15, pady=(15, 5), sticky="ew")

        self._summary_input_textbox = ctk.CTkTextbox(frame, font=ctk.CTkFont(size=13), wrap="word")
        self._summary_input_textbox.grid(row=1, column=0, padx=15, pady=5, sticky="nsew")

        ctrls = ctk.CTkFrame(frame, fg_color="transparent")
        ctrls.grid(row=2, column=0, padx=15, pady=5, sticky="ew")
        ctrls.grid_columnconfigure(0, weight=1)

        self._summary_template_var = ctk.StringVar(value="General")
        self._summary_templates_menu = ctk.CTkOptionMenu(ctrls, variable=self._summary_template_var)
        self._summary_templates_menu.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self._refresh_summary_templates_list()

        self._summary_translate_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(ctrls, text="Traducir a Español", variable=self._summary_translate_var).grid(
            row=0, column=1, padx=5
        )

        self._btn_summary_generate = ctk.CTkButton(
            ctrls, text="✨  Generar Resumen",
            font=ctk.CTkFont(size=13, weight="bold"), height=36,
            fg_color="#6366F1", hover_color="#4F46E5",
            command=self._start_standalone_summary,
        )
        self._btn_summary_generate.grid(row=0, column=2, padx=(5, 0))

        ctk.CTkLabel(
            frame, text="Resultado:", font=ctk.CTkFont(size=12, weight="bold"), anchor="w",
        ).grid(row=3, column=0, padx=15, pady=(10, 0), sticky="ew")

        self._summary_result_textbox = ctk.CTkTextbox(frame, font=ctk.CTkFont(size=13), wrap="word")
        self._summary_result_textbox.grid(row=4, column=0, padx=15, pady=5, sticky="nsew")
        self._summary_result_textbox.insert("0.0", "El resumen aparecerá aquí…")
        self._summary_result_textbox.configure(state="disabled")

        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.grid(row=5, column=0, padx=15, pady=(0, 15), sticky="ew")
        btn_row.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(
            btn_row, text="📋 Copiar", height=36, fg_color="gray30", hover_color="gray40",
            command=self._copy_summary_result,
        ).grid(row=0, column=0, padx=(0, 3), sticky="ew")
        ctk.CTkButton(
            btn_row, text="💾 Guardar .md", height=36,
            command=self._save_summary_result,
        ).grid(row=0, column=1, padx=(3, 0), sticky="ew")

    def _refresh_summary_templates_list(self) -> None:
        """Refresh the template list for the standalone summary section."""
        templates = template_manager.get_all_templates()
        names = [t["name"] for t in templates]
        if not names:
            names = ["General"]
        self._summary_templates_menu.configure(values=names)

    def _start_standalone_summary(self) -> None:
        """Start standalone summarization from free text input."""
        text = self._summary_input_textbox.get("0.0", "end").strip()
        if not text:
            self._show_toast("⚠️  Escribe o pega un texto primero.", kind="info")
            return

        llm_engine = self._config.get("llm_engine", "groq")
        if llm_engine == "groq" and not self._config.get("groq_api_key"):
            self._show_toast("⚠️ Configura la API Key de Groq en Ajustes.", kind="error")
            return

        self._btn_summary_generate.configure(state="disabled")

        template_name = self._summary_template_var.get()
        templates = template_manager.get_all_templates()
        selected = next((t for t in templates if t["name"] == template_name), templates[0] if templates else None)
        if not selected:
            self._show_toast("⚠️ No hay plantillas disponibles.", kind="error")
            self._btn_summary_generate.configure(state="normal")
            return

        threading.Thread(
            target=self._run_standalone_summary, args=(text, selected["body"]), daemon=True
        ).start()

    def _run_standalone_summary(self, text: str, template_body: str) -> None:
        """Run standalone summarization in background thread."""
        try:
            log.info("Starting standalone summary | engine=%s", self._config.get("llm_engine"))
            self.after(0, self._prepare_summary_result_ui)
            summarizer = Summarizer(self._config)
            for chunk in summarizer.summarize_stream(text, template_body, self._summary_translate_var.get()):
                self.after(0, self._append_summary_result_chunk, chunk)
            self.after(0, self._on_standalone_summary_success)
        except Exception as e:
            log.exception("Standalone summary failed")
            self.after(0, self._on_summary_error, str(e))

    def _prepare_summary_result_ui(self) -> None:
        """Prepare the standalone summary result textbox."""
        self._summary_result_textbox.configure(state="normal")
        self._summary_result_textbox.delete("0.0", "end")
        self._summary_result_textbox.configure(state="disabled")

    def _append_summary_result_chunk(self, chunk: str) -> None:
        """Append a chunk to the standalone summary result textbox."""
        self._summary_result_textbox.configure(state="normal")
        self._summary_result_textbox.insert("end", chunk)
        self._summary_result_textbox.see("end")
        self._summary_result_textbox.configure(state="disabled")

    def _on_standalone_summary_success(self) -> None:
        """Handle successful standalone summarization."""
        self._btn_summary_generate.configure(state="normal")
        self._show_toast("✨ Resumen generado con éxito.")

    def _on_summary_error(self, msg: str) -> None:
        """Handle standalone summary error."""
        self._btn_summary_generate.configure(state="normal")
        messagebox.showerror("Error", msg)

    def _copy_summary_result(self) -> None:
        """Copy standalone summary result to clipboard."""
        self.clipboard_clear()
        self.clipboard_append(self._summary_result_textbox.get("0.0", "end").strip())
        self._show_toast("📋 Copiado al portapapeles.")

    def _save_summary_result(self) -> None:
        """Save standalone summary result as markdown file."""
        text = self._summary_result_textbox.get("0.0", "end").strip()
        if not text:
            return
        path = filedialog.asksaveasfilename(defaultextension=".md", filetypes=[("Markdown", "*.md")])
        if path:
            Path(path).write_text(text, encoding="utf-8")
            self._show_toast(f"💾 Guardado: {Path(path).name}")

    # ══════════════════════════════════════════════════════════════════════════
    # Section 3 — Convertir
    # ══════════════════════════════════════════════════════════════════════════

    def _build_convert_section(self) -> None:
        """Build the Convert section (video to MP3)."""
        frame = ctk.CTkFrame(self, fg_color="transparent")
        self._sections["convertir"] = frame
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame, text="🎬 Convertir Video a MP3",
            font=ctk.CTkFont(size=14, weight="bold"), anchor="w",
        ).grid(row=0, column=0, padx=15, pady=(15, 10), sticky="ew")

        self._conv_video_var = ctk.StringVar()
        self._conv_output_var = ctk.StringVar()
        self._conv_status_var = ctk.StringVar(value="Selecciona un video.")

        self._add_file_row(frame, row=1, label="Video:", var=self._conv_video_var, browse_fn=self._browse_conv_video)
        self._add_file_row(
            frame, row=2, label="Salida (opcional):", var=self._conv_output_var,
            browse_fn=self._browse_conv_output, save=True,
        )

        ctk.CTkLabel(frame, textvariable=self._conv_status_var, text_color="gray", anchor="w").grid(
            row=3, column=0, padx=15, pady=10, sticky="ew"
        )

        self._btn_conv = ctk.CTkButton(
            frame, text="🎵  Convertir a MP3",
            font=ctk.CTkFont(size=15, weight="bold"), height=45,
            command=self._start_conversion,
        )
        self._btn_conv.grid(row=4, column=0, padx=15, pady=15, sticky="ew")

    def _browse_conv_video(self) -> None:
        """Open file dialog for video files."""
        path = filedialog.askopenfilename(filetypes=[("Video", " ".join(VIDEO_EXTS))])
        if path:
            self._conv_video_var.set(path)

    def _browse_conv_output(self) -> None:
        """Open save dialog for MP3 output."""
        path = filedialog.asksaveasfilename(defaultextension=".mp3", filetypes=[("MP3", "*.mp3")])
        if path:
            self._conv_output_var.set(path)

    def _start_conversion(self) -> None:
        """Start video to MP3 conversion."""
        v = self._conv_video_var.get()
        if not v:
            return
        self._btn_conv.configure(state="disabled")
        threading.Thread(target=self._run_conversion, args=(v, self._conv_output_var.get()), daemon=True).start()

    def _on_conversion_success(self, res: str) -> None:
        """Handle successful video conversion."""
        self._btn_conv.configure(state="normal")
        self._conv_status_var.set(f"✅ Guardado: {res}")
        self._show_toast("✅ Conversión exitosa")

    def _run_conversion(self, v: str, o: str) -> None:
        """Run video conversion in background thread."""
        try:
            res = convert_video_to_audio(v, o or None)
            self.after(0, self._on_conversion_success, str(res))
        except Exception as e:
            self.after(0, self._on_generic_error, str(e), self._btn_conv, self._conv_status_var)


    # ══════════════════════════════════════════════════════════════════════════
    # Section 4 — Configuración
    # ══════════════════════════════════════════════════════════════════════════

    def _build_settings_section(self) -> None:
        """Build the Settings section with sub-tabs."""
        frame = ctk.CTkFrame(self, fg_color="transparent")
        self._sections["configuracion"] = frame
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        sub_tabs = ctk.CTkTabview(frame, height=450)
        sub_tabs.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        sub_tabs.add("General")
        sub_tabs.add("Summarizer (IA)")
        sub_tabs.add("Plantillas")

        # --- General ---
        g = sub_tabs.tab("General")
        g.grid_columnconfigure(1, weight=1)

        self._engine_sel = self._add_setting_menu(
            g, 0, "Motor Transcripción:", _ENGINE_VALUES, _ENGINE_LABELS.get(self._config["engine"], "offline")
        )
        self._model_sel = self._add_setting_menu(
            g, 1, "Modelo Whisper:", _MODEL_VALUES, _MODEL_LABELS.get(self._config["model"], "small")
        )
        self._lang_sel = self._add_setting_menu(
            g, 2, "Idioma Entrada:", _LANGUAGE_VALUES, _LANGUAGE_LABELS.get(self._config["language"], "auto")
        )

        # ── Batch options ────────────────────────────────────────────────────
        batch_frame = ctk.CTkFrame(g, fg_color="transparent")
        batch_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=(15, 5), sticky="ew")
        batch_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            batch_frame, text="Opciones de lote:",
            font=ctk.CTkFont(size=12, weight="bold"), anchor="w",
        ).grid(row=0, column=0, columnspan=2, padx=0, pady=(0, 8), sticky="ew")

        self._move_processed_var = ctk.BooleanVar(value=self._config.get("move_processed", True))
        ctk.CTkCheckBox(
            batch_frame,
            text="Mover videos procesados a carpeta 'procesados/'",
            variable=self._move_processed_var,
        ).grid(row=1, column=0, columnspan=2, padx=0, pady=4, sticky="w")

        ctk.CTkLabel(batch_frame, text="Carpeta de salida .txt:", anchor="w").grid(
            row=2, column=0, padx=(0, 10), pady=5, sticky="w"
        )
        self._output_folder_entry = ctk.CTkEntry(
            batch_frame, placeholder_text="Vacío = misma carpeta del video"
        )
        self._output_folder_entry.insert(0, self._config.get("output_folder", ""))
        self._output_folder_entry.grid(row=2, column=1, pady=5, sticky="ew")

        ctk.CTkButton(
            g, text="💾 Guardar Configuración General",
            command=self._save_trans_settings,
        ).grid(row=4, column=0, columnspan=2, padx=10, pady=20, sticky="ew")

        # --- Summarizer ---
        s = sub_tabs.tab("Summarizer (IA)")
        s.grid_columnconfigure(1, weight=1)
        self._llm_sel = self._add_setting_menu(
            s, 0, "Motor LLM:", _LLM_ENGINE_VALUES,
            _LLM_ENGINE_LABELS.get(self._config["llm_engine"], "groq"),
        )

        ctk.CTkLabel(s, text="Groq API Key (Cloud):", anchor="w").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self._groq_key_entry = ctk.CTkEntry(s, show="*", placeholder_text="gsk_...")
        self._groq_key_entry.insert(0, self._config.get("groq_api_key", ""))
        self._groq_key_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        self._groq_key_entry.bind("<KeyRelease>", lambda e: self._update_key_visibility())

        self._groq_status_lbl = ctk.CTkLabel(s, text="", text_color="#EF4444", font=ctk.CTkFont(size=11))
        self._groq_status_lbl.grid(row=1, column=2, padx=10, pady=5, sticky="w")

        ctk.CTkLabel(s, text="Modelo Ollama (Local):", anchor="w").grid(row=2, column=0, padx=10, pady=5, sticky="w")

        ollama_frame = ctk.CTkFrame(s, fg_color="transparent")
        ollama_frame.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        ollama_frame.grid_columnconfigure(0, weight=1)

        self._ollama_mod_sel = ctk.CTkOptionMenu(ollama_frame, values=[self._config.get("ollama_model", "llama3.2")])
        self._ollama_mod_sel.set(self._config.get("ollama_model", "llama3.2"))
        self._ollama_mod_sel.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        self._btn_refresh_ollama = ctk.CTkButton(ollama_frame, text="🔄", width=30, command=self._refresh_ollama_models)
        self._btn_refresh_ollama.grid(row=0, column=1)

        ctk.CTkButton(s, text="💾 Guardar Ajustes LLM", command=self._save_llm_settings).grid(
            row=3, column=0, columnspan=2, padx=10, pady=20, sticky="ew"
        )

        # --- Templates Editor ---
        t = sub_tabs.tab("Plantillas")
        t.grid_columnconfigure(0, weight=1)
        t.grid_rowconfigure(3, weight=1)

        self._tpl_list_var = ctk.StringVar(value="Nuevo...")
        self._tpl_selector = ctk.CTkOptionMenu(t, variable=self._tpl_list_var, command=self._on_template_select)
        self._tpl_selector.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

        self._tpl_name_entry = ctk.CTkEntry(t, placeholder_text="Nombre de la plantilla")
        self._tpl_name_entry.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        self._tpl_body_text = ctk.CTkTextbox(t, height=200)
        self._tpl_body_text.grid(row=3, column=0, padx=10, pady=5, sticky="nsew")

        row_btn = ctk.CTkFrame(t, fg_color="transparent")
        row_btn.grid(row=4, column=0, padx=10, pady=10, sticky="ew")
        row_btn.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(row_btn, text="💾 Guardar", fg_color="#10B981", command=self._save_template_item).grid(
            row=0, column=0, padx=(0, 5), sticky="ew"
        )
        ctk.CTkButton(row_btn, text="🗑️ Eliminar", fg_color="#EF4444", command=self._delete_template_item).grid(
            row=0, column=1, padx=(5, 0), sticky="ew"
        )
        self._refresh_template_editor()

    # ── Settings logic ───────────────────────────────────────────────────────

    def _refresh_template_editor(self) -> None:
        """Refresh the template editor dropdown."""
        templates = template_manager.get_all_templates()
        names = ["Nuevo..."] + [t["name"] for t in templates]
        self._tpl_selector.configure(values=names)
        self._refresh_trans_templates_list()
        self._refresh_summary_templates_list()

    def _on_template_select(self, name: str) -> None:
        """Handle template selection in the editor."""
        if name == "Nuevo...":
            self._tpl_name_entry.delete(0, "end")
            self._tpl_body_text.delete("0.0", "end")
        else:
            templates = template_manager.get_all_templates()
            tmpl = next((x for x in templates if x["name"] == name), None)
            if tmpl:
                self._tpl_name_entry.delete(0, "end")
                self._tpl_name_entry.insert(0, tmpl["name"])
                self._tpl_body_text.delete("0.0", "end")
                self._tpl_body_text.insert("0.0", tmpl["body"])

    def _save_template_item(self) -> None:
        """Save a template from the editor."""
        name = self._tpl_name_entry.get().strip()
        body = self._tpl_body_text.get("0.0", "end").strip()
        if not name or not body:
            return
        tid = name.lower().replace(" ", "_")
        template_manager.save_template(tid, name, body)
        self._show_toast("✅ Plantilla guardada.")
        self._refresh_template_editor()

    def _delete_template_item(self) -> None:
        """Delete a template from the editor."""
        name = self._tpl_name_entry.get().strip()
        if not name:
            return
        tid = name.lower().replace(" ", "_")
        template_manager.delete_template(tid)
        self._show_toast("🗑️ Plantilla eliminada.")
        self._refresh_template_editor()

    def _add_setting_menu(self, parent: ctk.CTkFrame, row: int, label: str, values: list[str], default: str) -> ctk.CTkOptionMenu:
        """Add a labeled option menu to a settings tab."""
        ctk.CTkLabel(parent, text=label, anchor="w").grid(row=row, column=0, padx=10, pady=5, sticky="w")
        m = ctk.CTkOptionMenu(parent, values=values)
        m.set(default)
        m.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        return m

    def _save_trans_settings(self) -> None:
        """Save transcription and batch settings."""
        self._config.update({
            "engine": _ENGINE_KEYS[_ENGINE_VALUES.index(self._engine_sel.get())],
            "model": _MODEL_KEYS[_MODEL_VALUES.index(self._model_sel.get())],
            "language": _LANGUAGE_KEYS[_LANGUAGE_VALUES.index(self._lang_sel.get())],
            "move_processed": self._move_processed_var.get(),
            "output_folder": self._output_folder_entry.get().strip(),
        })
        save_config(self._config)
        self._show_toast("✅ Ajustes guardados.")
        self._update_status_bar()

    def _save_llm_settings(self) -> None:
        """Save LLM settings."""
        self._config.update({
            "llm_engine": _LLM_ENGINE_KEYS[_LLM_ENGINE_VALUES.index(self._llm_sel.get())],
            "groq_api_key": self._groq_key_entry.get().strip(),
            "ollama_model": self._ollama_mod_sel.get(),
        })
        save_config(self._config)
        self._show_toast("✅ Ajustes de IA guardados.")
        self._update_key_visibility()
        self._update_status_bar()

    def _update_key_visibility(self) -> None:
        """Update the visual status of the Groq API key field."""
        if not self._groq_key_entry.get().strip():
            self._groq_status_lbl.configure(text="⚠️ Requerido para Cloud")
        else:
            self._groq_status_lbl.configure(text="")

    def _refresh_ollama_models(self) -> None:
        """Trigger a background thread to update the list of available Ollama models."""
        self._btn_refresh_ollama.configure(state="disabled")
        threading.Thread(target=self._run_ollama_discovery, daemon=True).start()

    def _run_ollama_discovery(self) -> None:
        """Fetch models from Ollama API."""
        try:
            import ollama
            response = ollama.list()
            if hasattr(response, "models"):
                models = [m.model for m in response.models]
            elif isinstance(response, dict) and "models" in response:
                models = [m["name"] for m in response["models"]]
            else:
                models = []
            if not models:
                models = ["llama3.2"]
            self.after(0, self._on_ollama_discovery_success, models)
        except (ImportError, Exception):
            self.after(0, self._on_ollama_discovery_error)

    def _on_ollama_discovery_success(self, models: list[str]) -> None:
        """Handle successful Ollama model discovery."""
        current = self._ollama_mod_sel.get()
        self._ollama_mod_sel.configure(values=models)
        if current in models:
            self._ollama_mod_sel.set(current)
        else:
            self._ollama_mod_sel.set(models[0])
        self._btn_refresh_ollama.configure(state="normal")
        self._ollama_connected = True
        self._update_status_bar()

    def _on_ollama_discovery_error(self) -> None:
        """Handle Ollama discovery failure."""
        self._btn_refresh_ollama.configure(state="normal")
        self._ollama_connected = False
        self._update_status_bar()

    # ══════════════════════════════════════════════════════════════════════════
    # Status Bar
    # ══════════════════════════════════════════════════════════════════════════

    def _build_status_bar(self) -> None:
        """Build the status bar at the bottom of the window."""
        bar = ctk.CTkFrame(self, height=30, corner_radius=0, fg_color="#1a1a2e")
        bar.grid(row=2, column=0, columnspan=2, sticky="ew")
        bar.grid_columnconfigure(3, weight=1)

        self._status_engine_lbl = ctk.CTkLabel(
            bar, text="", font=ctk.CTkFont(size=11), text_color="gray",
        )
        self._status_engine_lbl.grid(row=0, column=0, padx=(15, 20), pady=4)

        self._status_model_lbl = ctk.CTkLabel(
            bar, text="", font=ctk.CTkFont(size=11), text_color="gray",
        )
        self._status_model_lbl.grid(row=0, column=1, padx=(0, 20), pady=4)

        self._status_ollama_lbl = ctk.CTkLabel(
            bar, text="", font=ctk.CTkFont(size=11), text_color="gray",
        )
        self._status_ollama_lbl.grid(row=0, column=2, padx=(0, 15), pady=4)

        self._update_status_bar()

    def _update_status_bar(self) -> None:
        """Update status bar labels with current config values."""
        engine_key = self._config.get("engine", "offline")
        engine_label = "Offline" if engine_key == "offline" else "Online"
        self._status_engine_lbl.configure(text=f"Motor: {engine_label}")
        model_key = self._config.get("model", "small")
        self._status_model_lbl.configure(text=f"Modelo: {model_key}")
        if self._ollama_connected:
            self._status_ollama_lbl.configure(text="Ollama: ✅ conectado", text_color="#4ade80")
        else:
            self._status_ollama_lbl.configure(text="Ollama: ❌ no disponible", text_color="#f87171")

    # ══════════════════════════════════════════════════════════════════════════
    # Shared helpers
    # ══════════════════════════════════════════════════════════════════════════

    def _on_generic_error(self, msg: str, btn: ctk.CTkButton, status_var: ctk.StringVar) -> None:
        """Handle a generic error from a background thread."""
        btn.configure(state="normal")
        status_var.set("❌ Error en el proceso.")
        messagebox.showerror("Error", msg)

    def _add_file_row(self, parent: ctk.CTkFrame, row: int, label: str, var: ctk.StringVar, browse_fn: object, save: bool = False) -> None:
        """Add a file selection row with label, entry, and browse button."""
        file_frame = ctk.CTkFrame(parent)
        file_frame.grid(row=row, column=0, padx=10, pady=6, sticky="ew")
        file_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(file_frame, text=label, width=140, anchor="w").grid(row=0, column=0, padx=10, pady=8)
        ctk.CTkEntry(file_frame, textvariable=var, state="readonly").grid(row=0, column=1, padx=6, pady=8, sticky="ew")
        ctk.CTkButton(file_frame, text="📁 Examinar", width=110, command=browse_fn).grid(row=0, column=2, padx=10, pady=8)

