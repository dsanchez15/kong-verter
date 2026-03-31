"""GUI for kon-verter using CustomTkinter.

Three-tab layout:
  - Convertir:     Video → MP3 conversion.
  - Transcribir:   Audio (.mp3) → Text transcription.
  - Configuración: Engine, model, and language settings with persistence.
"""

import threading
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from config import load_config, save_config
from transcriber import OfflineTranscriber, get_transcriber
from video_converter import convert_video_to_audio

# ── Model size labels for the UI ──────────────────────────────────────────────
_MODEL_LABELS = {
    "tiny":     "Tiny      (~75 MB)   — Rápido, baja precisión",
    "base":     "Base      (~142 MB)  — Rápido, aceptable",
    "small":    "Small     (~461 MB)  — Buen balance ⭐",
    "medium":   "Medium    (~1.5 GB)  — Alta calidad",
    "large-v3": "Large-v3  (~3.1 GB)  — Máxima calidad",
}
_MODEL_KEYS = list(_MODEL_LABELS.keys())
_MODEL_VALUES = list(_MODEL_LABELS.values())

_LANGUAGE_LABELS = {"auto": "Automático", "es": "Español", "en": "English"}
_LANGUAGE_KEYS = list(_LANGUAGE_LABELS.keys())
_LANGUAGE_VALUES = list(_LANGUAGE_LABELS.values())

_ENGINE_LABELS = {"offline": "🖥️  Offline (faster-whisper)", "online": "🌐  Online (Google Speech)"}
_ENGINE_KEYS = list(_ENGINE_LABELS.keys())
_ENGINE_VALUES = list(_ENGINE_LABELS.values())


class KonverterApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        self.title("kon-verter")
        self.geometry("680x520")
        self.minsize(640, 480)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Load persisted settings
        self._config = load_config()

        # ── Header ────────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=20, pady=(20, 0), sticky="ew")
        ctk.CTkLabel(header, text="Kon-verter", font=ctk.CTkFont(size=30, weight="bold")).pack(side="left")
        ctk.CTkLabel(
            header,
            text="Video · Audio · Texto",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        ).pack(side="left", padx=12, pady=4)

        # ── Tabs ──────────────────────────────────────────────────────────────
        self._tabs = ctk.CTkTabview(self)
        self._tabs.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")

        self._tabs.add("🎬  Convertir")
        self._tabs.add("📝  Transcribir")
        self._tabs.add("⚙️  Configuración")

        self._build_convert_tab()
        self._build_transcribe_tab()
        self._build_settings_tab()

    # ══════════════════════════════════════════════════════════════════════════
    # Tab 1 — Convertir
    # ══════════════════════════════════════════════════════════════════════════

    def _build_convert_tab(self) -> None:
        tab = self._tabs.tab("🎬  Convertir")
        tab.grid_columnconfigure(0, weight=1)

        self._conv_video_var = ctk.StringVar()
        self._conv_output_var = ctk.StringVar()
        self._conv_status_var = ctk.StringVar(value="Selecciona un video para comenzar.")

        # Input
        self._add_file_row(tab, row=0, label="Video:", var=self._conv_video_var, browse_fn=self._browse_video)
        # Output (optional)
        self._add_file_row(tab, row=1, label="Salida (opcional):", var=self._conv_output_var, browse_fn=self._browse_conv_output, save=True)

        # Status
        ctk.CTkLabel(tab, textvariable=self._conv_status_var, text_color="gray", anchor="w").grid(
            row=2, column=0, padx=10, pady=(10, 0), sticky="ew"
        )

        # Button
        self._btn_convert = ctk.CTkButton(
            tab,
            text="Convertir a MP3",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=44,
            command=self._start_conversion,
        )
        self._btn_convert.grid(row=3, column=0, padx=10, pady=12, sticky="ew")

    def _browse_video(self) -> None:
        path = filedialog.askopenfilename(
            title="Seleccionar Video",
            filetypes=[("Archivos de Video", "*.mp4 *.mkv *.avi *.mov *.webm"), ("Todos", "*.*")],
        )
        if path:
            self._conv_video_var.set(path)

    def _browse_conv_output(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Guardar MP3 como…",
            defaultextension=".mp3",
            filetypes=[("Audio MP3", "*.mp3")],
        )
        if path:
            self._conv_output_var.set(path)

    def _start_conversion(self) -> None:
        video = self._conv_video_var.get().strip()
        if not video:
            messagebox.showwarning("Sin Video", "Por favor, selecciona un video primero.")
            return
        self._btn_convert.configure(state="disabled")
        self._conv_status_var.set("⏳ Convirtiendo… Por favor, espera.")
        threading.Thread(
            target=self._run_conversion,
            args=(video, self._conv_output_var.get().strip()),
            daemon=True,
        ).start()

    def _run_conversion(self, video: str, output: str) -> None:
        try:
            result = convert_video_to_audio(video, output or None)
            self.after(0, self._on_conv_success, result)
        except Exception as exc:
            self.after(0, self._on_conv_error, str(exc))

    def _on_conv_success(self, path: Path) -> None:
        self._conv_status_var.set(f"✅ Audio guardado en: {path}")
        self._btn_convert.configure(state="normal")
        messagebox.showinfo("¡Éxito!", f"Audio guardado en:\n{path}")

    def _on_conv_error(self, msg: str) -> None:
        self._conv_status_var.set("❌ Error en la conversión.")
        self._btn_convert.configure(state="normal")
        messagebox.showerror("Error", msg)

    # ══════════════════════════════════════════════════════════════════════════
    # Tab 2 — Transcribir
    # ══════════════════════════════════════════════════════════════════════════

    def _build_transcribe_tab(self) -> None:
        tab = self._tabs.tab("📝  Transcribir")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)

        self._trans_audio_var = ctk.StringVar()
        self._trans_status_var = ctk.StringVar(value="Selecciona un archivo de audio.")

        # Input
        self._add_file_row(tab, row=0, label="Audio (.mp3):", var=self._trans_audio_var, browse_fn=self._browse_audio)

        # Status bar
        ctk.CTkLabel(tab, textvariable=self._trans_status_var, text_color="gray", anchor="w").grid(
            row=1, column=0, padx=10, pady=(4, 0), sticky="ew"
        )

        # Text result area
        self._textbox = ctk.CTkTextbox(tab, font=ctk.CTkFont(size=13), wrap="word")
        self._textbox.grid(row=2, column=0, padx=10, pady=8, sticky="nsew")
        self._textbox.insert("0.0", "El texto transcrito aparecerá aquí…")
        self._textbox.configure(state="disabled")

        # Buttons row
        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="ew")
        btn_frame.grid_columnconfigure((0, 1), weight=1)

        self._btn_transcribe = ctk.CTkButton(
            btn_frame, text="Transcribir", font=ctk.CTkFont(size=14, weight="bold"),
            height=40, command=self._start_transcription,
        )
        self._btn_transcribe.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        self._btn_save_txt = ctk.CTkButton(
            btn_frame, text="Guardar .txt", height=40,
            fg_color="gray30", hover_color="gray40",
            command=self._save_txt,
        )
        self._btn_save_txt.grid(row=0, column=1, padx=(6, 0), sticky="ew")

    def _browse_audio(self) -> None:
        path = filedialog.askopenfilename(
            title="Seleccionar Audio",
            filetypes=[("Archivos de Audio", "*.mp3 *.wav *.m4a *.ogg"), ("Todos", "*.*")],
        )
        if path:
            self._trans_audio_var.set(path)

    def _start_transcription(self) -> None:
        audio = self._trans_audio_var.get().strip()
        if not audio:
            messagebox.showwarning("Sin Audio", "Por favor, selecciona un archivo de audio.")
            return

        engine = self._config.get("engine", "offline")
        model = self._config.get("model", "small")
        language = self._config.get("language", "auto")

        # Warn about model download for offline engine
        if engine == "offline":
            size_mb = OfflineTranscriber.MODEL_SIZES_MB.get(model, 0)
            self._trans_status_var.set(
                f"⏳ Cargando modelo '{model}' (~{size_mb} MB, se descarga solo la primera vez)…"
            )
        else:
            self._trans_status_var.set("⏳ Transcribiendo con Google Speech API…")

        self._btn_transcribe.configure(state="disabled")
        threading.Thread(
            target=self._run_transcription,
            args=(audio, engine, model, language),
            daemon=True,
        ).start()

    def _run_transcription(self, audio: str, engine: str, model: str, language: str) -> None:
        try:
            transcriber = get_transcriber(engine, model, language)
            text = transcriber.transcribe(Path(audio), language)
            self.after(0, self._on_trans_success, text)
        except Exception as exc:
            self.after(0, self._on_trans_error, str(exc))

    def _on_trans_success(self, text: str) -> None:
        self._textbox.configure(state="normal")
        self._textbox.delete("0.0", "end")
        self._textbox.insert("0.0", text)
        self._textbox.configure(state="disabled")
        self._trans_status_var.set("✅ Transcripción completada.")
        self._btn_transcribe.configure(state="normal")

    def _on_trans_error(self, msg: str) -> None:
        self._trans_status_var.set("❌ Error en la transcripción.")
        self._btn_transcribe.configure(state="normal")
        messagebox.showerror("Error de Transcripción", msg)

    def _save_txt(self) -> None:
        text = self._textbox.get("0.0", "end").strip()
        if not text or text == "El texto transcrito aparecerá aquí…":
            messagebox.showwarning("Sin Texto", "No hay texto transcrito para guardar.")
            return
        path = filedialog.asksaveasfilename(
            title="Guardar transcripción",
            defaultextension=".txt",
            filetypes=[("Archivo de Texto", "*.txt")],
        )
        if path:
            Path(path).write_text(text, encoding="utf-8")
            messagebox.showinfo("Guardado", f"Texto guardado en:\n{path}")

    # ══════════════════════════════════════════════════════════════════════════
    # Tab 3 — Configuración
    # ══════════════════════════════════════════════════════════════════════════

    def _build_settings_tab(self) -> None:
        tab = self._tabs.tab("⚙️  Configuración")
        tab.grid_columnconfigure(1, weight=1)

        engine_val = _ENGINE_LABELS.get(self._config.get("engine", "offline"), _ENGINE_VALUES[0])
        model_val = _MODEL_LABELS.get(self._config.get("model", "small"), _MODEL_VALUES[2])
        lang_val = _LANGUAGE_LABELS.get(self._config.get("language", "auto"), _LANGUAGE_VALUES[0])

        # ── Engine ────────────────────────────────────────────────────────────
        ctk.CTkLabel(tab, text="Motor de Transcripción:", anchor="w").grid(row=0, column=0, padx=10, pady=(16, 6), sticky="w")
        self._engine_menu = ctk.CTkOptionMenu(
            tab, values=_ENGINE_VALUES, command=self._on_engine_change
        )
        self._engine_menu.set(engine_val)
        self._engine_menu.grid(row=0, column=1, padx=10, pady=(16, 6), sticky="ew")

        # ── Model (offline only) ──────────────────────────────────────────────
        self._lbl_model = ctk.CTkLabel(tab, text="Modelo Whisper:", anchor="w")
        self._lbl_model.grid(row=1, column=0, padx=10, pady=6, sticky="w")
        self._model_menu = ctk.CTkOptionMenu(tab, values=_MODEL_VALUES)
        self._model_menu.set(model_val)
        self._model_menu.grid(row=1, column=1, padx=10, pady=6, sticky="ew")

        # ── Model size info ────────────────────────────────────────────────────
        self._lbl_model_hint = ctk.CTkLabel(
            tab,
            text="ℹ️  El modelo se descarga automáticamente la primera vez.",
            text_color="gray",
            font=ctk.CTkFont(size=11),
            anchor="w",
        )
        self._lbl_model_hint.grid(row=2, column=0, columnspan=2, padx=10, pady=(0, 6), sticky="w")

        # ── Online warning ─────────────────────────────────────────────────────
        self._lbl_online_warning = ctk.CTkLabel(
            tab,
            text="⚠️  Requiere conexión a internet. Límite ~60s por archivo.",
            text_color="#E8A838",
            font=ctk.CTkFont(size=11),
            anchor="w",
        )
        # Not gridded yet; shown/hidden based on engine

        # ── Language ──────────────────────────────────────────────────────────
        ctk.CTkLabel(tab, text="Idioma:", anchor="w").grid(row=3, column=0, padx=10, pady=6, sticky="w")
        self._lang_menu = ctk.CTkOptionMenu(tab, values=_LANGUAGE_VALUES)
        self._lang_menu.set(lang_val)
        self._lang_menu.grid(row=3, column=1, padx=10, pady=6, sticky="ew")

        ctk.CTkLabel(
            tab,
            text="\"Automático\" detecta el idioma del audio (solo motor offline).",
            text_color="gray",
            font=ctk.CTkFont(size=11),
            anchor="w",
        ).grid(row=4, column=0, columnspan=2, padx=10, pady=(0, 16), sticky="w")

        # ── Save button ───────────────────────────────────────────────────────
        ctk.CTkButton(
            tab, text="💾  Guardar Configuración", height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._save_settings,
        ).grid(row=5, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        self._lbl_saved = ctk.CTkLabel(tab, text="", text_color="#5CB85C")
        self._lbl_saved.grid(row=6, column=0, columnspan=2, pady=(0, 10))

        # Apply initial engine visibility
        self._on_engine_change(engine_val)

    def _on_engine_change(self, value: str) -> None:
        is_offline = value == _ENGINE_VALUES[0]
        state = "normal" if is_offline else "disabled"
        self._model_menu.configure(state=state)

        if is_offline:
            self._lbl_model_hint.grid()
            self._lbl_online_warning.grid_remove()
        else:
            self._lbl_model_hint.grid_remove()
            self._lbl_online_warning.grid(row=2, column=0, columnspan=2, padx=10, pady=(0, 6), sticky="w")

    def _save_settings(self) -> None:
        engine_val = self._engine_menu.get()
        model_val = self._model_menu.get()
        lang_val = self._lang_menu.get()

        engine_key = _ENGINE_KEYS[_ENGINE_VALUES.index(engine_val)]
        model_key = _MODEL_KEYS[_MODEL_VALUES.index(model_val)]
        lang_key = _LANGUAGE_KEYS[_LANGUAGE_VALUES.index(lang_val)]

        self._config = {"engine": engine_key, "model": model_key, "language": lang_key}
        save_config(self._config)
        self._lbl_saved.configure(text="✅ Configuración guardada.")
        self.after(3000, lambda: self._lbl_saved.configure(text=""))

    # ══════════════════════════════════════════════════════════════════════════
    # Shared helpers
    # ══════════════════════════════════════════════════════════════════════════

    def _add_file_row(
        self,
        parent: ctk.CTkFrame,
        row: int,
        label: str,
        var: ctk.StringVar,
        browse_fn: object,
        save: bool = False,
    ) -> None:
        """Add a label + read-only entry + browse button row."""
        frame = ctk.CTkFrame(parent)
        frame.grid(row=row, column=0, padx=10, pady=6, sticky="ew")
        frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(frame, text=label, width=140, anchor="w").grid(row=0, column=0, padx=10, pady=8)
        entry = ctk.CTkEntry(frame, textvariable=var)
        entry.configure(state="readonly")
        entry.grid(row=0, column=1, padx=6, pady=8, sticky="ew")
        ctk.CTkButton(frame, text="📁 Examinar", width=110, command=browse_fn).grid(  # type: ignore[arg-type]
            row=0, column=2, padx=10, pady=8
        )


if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = KonverterApp()
    app.mainloop()
