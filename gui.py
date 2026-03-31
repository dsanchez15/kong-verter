"""GUI for kong-verter using CustomTkinter.

Four-tab layout:
  - Transcribir:   Video/Audio → Text transcription & Summary options.
  - ✨ Resultado:  LLM Summary/Extraction result.
  - 🎬 Convertir:     Video → MP3 conversion.
  - ⚙️ Configuración: Engine, model, language, LLM settings, and Template Editor.
"""

import tempfile
import threading
import time
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

import template_manager
from config import load_config, save_config
from summarizer import Summarizer
from transcriber import get_transcriber
from video_converter import convert_video_to_audio

# ── Constants ─────────────────────────────────────────────────────────────────
VIDEO_EXTS = ("*.mp4", "*.mkv", "*.avi", "*.mov", "*.webm")
AUDIO_EXTS = ("*.mp3", "*.wav", "*.m4a", "*.ogg")

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

_LLM_ENGINE_LABELS = {"groq": "☁️  Groq Cloud (Fastest)", "ollama": "🏠  Ollama (Local)"}
_LLM_ENGINE_KEYS = list(_LLM_ENGINE_LABELS.keys())
_LLM_ENGINE_VALUES = list(_LLM_ENGINE_LABELS.values())

# Toast colors
_TOAST_SUCCESS = "#2d6a4f"
_TOAST_ERROR = "#8b1a1a"
_TOAST_INFO = "#1a3a5c"


class KonverterApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        self.title("kong-verter")
        self.geometry("800x650")
        self.minsize(700, 550)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._config = load_config()
        template_manager.init_templates()

        # ── Toast notification ───────────────────────────────────────────────
        self._toast = ctk.CTkLabel(
            self, text="", height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=8, fg_color=_TOAST_SUCCESS,
        )
        self._toast_job: str | None = None

        # ── Header ────────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=20, pady=(16, 0), sticky="ew")
        ctk.CTkLabel(header, text="Kong-verter", font=ctk.CTkFont(size=30, weight="bold")).pack(side="left")
        ctk.CTkLabel(
            header, text="Video · Audio · Texto · IA",
            font=ctk.CTkFont(size=13), text_color="gray",
        ).pack(side="left", padx=12, pady=4)

        # ── Tabs ──────────────────────────────────────────────────────────────
        self._tabs = ctk.CTkTabview(self)
        self._tabs.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")

        self._tabs.add("📝  Transcribir")
        self._tabs.add("✨  Resultado")
        self._tabs.add("🎬  Convertir")
        self._tabs.add("⚙️  Configuración")

        self._build_transcribe_tab()
        self._build_result_tab()
        self._build_convert_tab()
        self._build_settings_tab()

    # ══════════════════════════════════════════════════════════════════════════
    # Shared UX Utility
    # ══════════════════════════════════════════════════════════════════════════

    def _show_toast(self, message: str, kind: str = "success", duration: int = 4000) -> None:
        color = {"success": _TOAST_SUCCESS, "error": _TOAST_ERROR, "info": _TOAST_INFO}.get(kind, _TOAST_SUCCESS)
        self._toast.configure(text=f"  {message}  ", fg_color=color)
        self._toast.place(relx=0.5, y=10, anchor="n", relwidth=0.8)
        if self._toast_job: self.after_cancel(self._toast_job)
        self._toast_job = self.after(duration, lambda: self._toast.place_forget()) # type: ignore[assignment]

    # ══════════════════════════════════════════════════════════════════════════
    # Tab 1 — Transcribir
    # ══════════════════════════════════════════════════════════════════════════

    def _build_transcribe_tab(self) -> None:
        tab = self._tabs.tab("📝  Transcribir")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)

        self._trans_file_var = ctk.StringVar()
        self._trans_status_var = ctk.StringVar(value="Selecciona un archivo para comenzar.")
        self._trans_file_var.trace_add("write", self._on_trans_file_changed)

        # File Input
        self._add_file_row(tab, row=0, label="Video o Audio:", var=self._trans_file_var, browse_fn=self._browse_media)

        # Status
        ctk.CTkLabel(tab, textvariable=self._trans_status_var, text_color="gray", anchor="w").grid(row=1, column=0, padx=10, pady=(4, 0), sticky="ew")

        # Text Area
        self._trans_textbox = ctk.CTkTextbox(tab, font=ctk.CTkFont(size=13), wrap="word")
        self._trans_textbox.grid(row=2, column=0, padx=10, pady=8, sticky="nsew")
        self._trans_textbox.insert("0.0", "La transcripción aparecerá aquí…")
        self._trans_textbox.configure(state="disabled")

        # Summary Options Frame
        summary_ctrls = ctk.CTkFrame(tab, fg_color="transparent")
        summary_ctrls.grid(row=3, column=0, padx=10, pady=(0, 5), sticky="ew")
        summary_ctrls.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(summary_ctrls, text="✨ IA: Plantilla para Resumen / Extracción", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(5,0))

        self._template_var = ctk.StringVar(value="General")
        self._templates_menu = ctk.CTkOptionMenu(summary_ctrls, variable=self._template_var)
        self._templates_menu.grid(row=1, column=0, sticky="ew", padx=(0,5), pady=5)
        self._refresh_templates_list()

        self._translate_var = ctk.BooleanVar(value=False)
        self._chk_translate = ctk.CTkCheckBox(summary_ctrls, text="Traducir a Español", variable=self._translate_var)
        self._chk_translate.grid(row=1, column=1, padx=5, pady=5)

        # Action Buttons
        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.grid(row=4, column=0, padx=10, pady=(0, 10), sticky="ew")
        btn_frame.grid_columnconfigure((0, 1), weight=1)

        self._btn_transcribe = ctk.CTkButton(btn_frame, text="🎙️  Transcribir", font=ctk.CTkFont(size=14, weight="bold"), height=40, command=self._start_transcription)
        self._btn_transcribe.grid(row=0, column=0, padx=(0, 3), sticky="ew")

        self._btn_summarize = ctk.CTkButton(btn_frame, text="✨  Generar Resumen / Extraer", font=ctk.CTkFont(size=14, weight="bold"), height=40, fg_color="#6366F1", hover_color="#4F46E5", command=self._start_summarization)
        self._btn_summarize.grid(row=0, column=1, padx=(3, 0), sticky="ew")

        # Progress elements
        self._progress_frame = ctk.CTkFrame(tab, fg_color="transparent")
        self._progress_frame.grid(row=5, column=0, padx=10, pady=(0, 10), sticky="ew")
        self._progress_frame.grid_columnconfigure(0, weight=1)

        self._trans_progress = ctk.CTkProgressBar(self._progress_frame, height=8, fg_color="#E2E8F0", progress_color="#3B82F6")
        self._trans_progress.set(0)
        self._trans_progress.grid(row=0, column=0, sticky="ew")

        self._trans_eta_var = ctk.StringVar(value="")
        self._trans_eta_label = ctk.CTkLabel(self._progress_frame, textvariable=self._trans_eta_var, font=ctk.CTkFont(size=11), text_color="gray")
        self._trans_eta_label.grid(row=1, column=0, sticky="ew")
        self._progress_frame.grid_remove() # Hide initially

    def _refresh_templates_list(self) -> None:
        templates = template_manager.get_all_templates()
        names = [t["name"] for t in templates]
        if not names: names = ["General"]
        self._templates_menu.configure(values=names)

    def _on_trans_file_changed(self, *args: object) -> None:
        self._trans_textbox.configure(state="normal")
        self._trans_textbox.delete("0.0", "end")
        self._trans_textbox.insert("0.0", "La transcripción aparecerá aquí…")
        self._trans_textbox.configure(state="disabled")

    def _browse_media(self) -> None:
        all_media = " ".join(VIDEO_EXTS + AUDIO_EXTS)
        path = filedialog.askopenfilename(filetypes=[("Multimedia", all_media), ("Todos", "*.*")])
        if path: self._trans_file_var.set(path)

    def _start_transcription(self) -> None:
        file_path = self._trans_file_var.get().strip()
        if not file_path:
            self._show_toast("⚠️  Selecciona un archivo.", kind="info")
            return
        self._btn_transcribe.configure(state="disabled")
        self._btn_summarize.configure(state="disabled")
        self._trans_status_var.set("⏳ Inicializando transcripción…")
        threading.Thread(target=self._run_transcription, args=(file_path,), daemon=True).start()

    def _prepare_trans_ui(self) -> None:
        self._trans_textbox.configure(state="normal")
        self._trans_textbox.delete("0.0", "end")
        self._trans_textbox.insert("0.0", "")
        self._trans_progress.set(0)
        self._trans_eta_var.set("Calculando tiempo...")
        self._progress_frame.grid()

    def _append_trans_text(self, text: str) -> None:
        self._trans_textbox.configure(state="normal")
        self._trans_textbox.insert("end", text + " ")
        self._trans_textbox.see("end")
        self._trans_textbox.configure(state="disabled")

    def _update_trans_progress(self, progress: float, start_time: float) -> None:
        self._trans_progress.set(progress)
        elapsed = time.time() - start_time
        if progress > 0.05: # Wait for some progress to estimate
            total_est = elapsed / progress
            remaining = total_est - elapsed
            mins, secs = divmod(int(remaining), 60)
            self._trans_eta_var.set(f"Progreso: {int(progress*100)}% | Est. restante: {mins:02d}:{secs:02d}")

    def _run_transcription(self, file_path: str) -> None:
        tmp_path: Path | None = None
        try:
            audio_path = Path(file_path)
            if audio_path.suffix.lower() in [".mp4", ".mkv", ".avi", ".mov", ".webm"]:
                self.after(0, self._trans_status_var.set, "⏳ Extrayendo audio...")
                tmp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
                tmp_path = Path(tmp_file.name)
                tmp_file.close()
                convert_video_to_audio(file_path, str(tmp_path))
                audio_path = tmp_path

            self.after(0, self._trans_status_var.set, "🎙️ Transcribiendo en vivo...")
            self.after(0, self._prepare_trans_ui)

            transcriber = get_transcriber(
                self._config.get("engine", "offline"),
                self._config.get("model", "small"),
                self._config.get("language", "auto")
            )
            
            start_time = time.time()
            for msg_type, content in transcriber.transcribe_stream(audio_path, self._config.get("language", "auto")):
                if msg_type == "segment":
                    self.after(0, self._append_trans_text, content)
                elif msg_type == "progress":
                    self.after(0, self._update_trans_progress, content, start_time)

            self.after(0, self._on_trans_success)
        except Exception as e:
            self.after(0, self._on_generic_error, str(e), self._btn_transcribe, self._trans_status_var)
            self.after(0, self._btn_summarize.configure, {"state": "normal"})
        finally:
            if tmp_path:
                tmp_path.unlink(missing_ok=True)

    def _on_trans_success(self) -> None:
        self._btn_transcribe.configure(state="normal")
        self._btn_summarize.configure(state="normal")
        self._trans_status_var.set("✅ Transcripción completa.")
        self._trans_progress.set(1.0)
        self._trans_eta_var.set("Finalizado.")
        self._show_toast("✅ Transcripción completada.")

    def _start_summarization(self) -> None:
        text = self._trans_textbox.get("0.0", "end").strip()
        if not text or text == "La transcripción aparecerá aquí…":
            self._show_toast("⚠️  Primero transcribe un audio/video.", kind="info")
            return

        # Pre-validation
        llm_engine = self._config.get("llm_engine", "groq")
        if llm_engine == "groq" and not self._config.get("groq_api_key"):
            self._show_toast("⚠️ Configura la API Key de Groq en Ajustes.", kind="error")
            return

        self._btn_summarize.configure(state="disabled")
        self._trans_status_var.set("⏳ Generando resumen con IA…")

        template_name = self._template_var.get()
        templates = template_manager.get_all_templates()
        selected = next((t for t in templates if t["name"] == template_name), templates[0])

        threading.Thread(target=self._run_summarization, args=(text, selected["body"]), daemon=True).start()

    def _prepare_summary_ui(self) -> None:
        self._tabs.set("✨  Resultado")
        self._result_textbox.configure(state="normal")
        self._result_textbox.delete("0.0", "end")
        self._result_textbox.insert("0.0", "")
        self._result_textbox.configure(state="disabled")

    def _append_summary_chunk(self, chunk: str) -> None:
        self._result_textbox.configure(state="normal")
        self._result_textbox.insert("end", chunk)
        self._result_textbox.see("end")
        self._result_textbox.configure(state="disabled")

    def _run_summarization(self, text: str, template_body: str) -> None:
        try:
            self.after(0, self._prepare_summary_ui)
            summarizer = Summarizer(self._config)
            
            for chunk in summarizer.summarize_stream(text, template_body, self._translate_var.get()):
                self.after(0, self._append_summary_chunk, chunk)

            self.after(0, self._on_summary_success)
        except Exception as e:
            self.after(0, self._on_generic_error, str(e), self._btn_summarize, self._trans_status_var)

    def _on_summary_success(self) -> None:
        self._btn_summarize.configure(state="normal")
        self._trans_status_var.set("✅ Procesamiento con IA completo.")
        self._show_toast("✨ ¡Resultado generado con éxito!")

    def _on_generic_error(self, msg: str, btn: ctk.CTkButton, status_var: ctk.StringVar) -> None:
        btn.configure(state="normal")
        status_var.set("❌ Error en el proceso.")
        messagebox.showerror("Error", msg)

    # ══════════════════════════════════════════════════════════════════════════
    # Tab 2 — Resultado
    # ══════════════════════════════════════════════════════════════════════════

    def _build_result_tab(self) -> None:
        tab = self._tabs.tab("✨  Resultado")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(tab, text="Resumen / Extracción de Datos (Markdown)", font=ctk.CTkFont(size=14, weight="bold"), anchor="w").grid(row=0, column=0, padx=15, pady=(15, 5), sticky="ew")

        self._result_textbox = ctk.CTkTextbox(tab, font=ctk.CTkFont(size=13), wrap="word")
        self._result_textbox.grid(row=1, column=0, padx=15, pady=5, sticky="nsew")
        self._result_textbox.insert("0.0", "Aquí aparecerá el resumen generado...")
        self._result_textbox.configure(state="disabled")

        row3 = ctk.CTkFrame(tab, fg_color="transparent")
        row3.grid(row=2, column=0, padx=15, pady=15, sticky="ew")
        row3.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(row3, text="📋 Copiar al Portapapeles", height=40, fg_color="gray30", hover_color="gray40", command=self._copy_result).grid(row=0, column=0, padx=(0, 5), sticky="ew")
        ctk.CTkButton(row3, text="💾 Guardar como .md", height=40, font=ctk.CTkFont(size=14, weight="bold"), command=self._save_result_md).grid(row=0, column=1, padx=(5, 0), sticky="ew")

    def _copy_result(self) -> None:
        self.clipboard_clear()
        self.clipboard_append(self._result_textbox.get("0.0", "end").strip())
        self._show_toast("📋 Copiado al portapapeles.")

    def _save_result_md(self) -> None:
        text = self._result_textbox.get("0.0", "end").strip()
        if not text: return
        path = filedialog.asksaveasfilename(defaultextension=".md", filetypes=[("Markdown", "*.md")])
        if path:
            Path(path).write_text(text, encoding="utf-8")
            self._show_toast(f"💾 Guardado: {Path(path).name}")

    # ══════════════════════════════════════════════════════════════════════════
    # Tab 3 — Convertir
    # ══════════════════════════════════════════════════════════════════════════

    def _build_convert_tab(self) -> None:
        tab = self._tabs.tab("🎬  Convertir")
        tab.grid_columnconfigure(0, weight=1)

        self._conv_video_var = ctk.StringVar()
        self._conv_output_var = ctk.StringVar()
        self._conv_status_var = ctk.StringVar(value="Selecciona un video.")

        self._add_file_row(tab, row=0, label="Video:", var=self._conv_video_var, browse_fn=self._browse_conv_video)
        self._add_file_row(tab, row=1, label="Salida (opcional):", var=self._conv_output_var, browse_fn=self._browse_conv_output, save=True)

        ctk.CTkLabel(tab, textvariable=self._conv_status_var, text_color="gray", anchor="w").grid(row=2, column=0, padx=15, pady=10, sticky="ew")

        self._btn_conv = ctk.CTkButton(tab, text="🎵  Convertir a MP3", font=ctk.CTkFont(size=15, weight="bold"), height=45, command=self._start_conversion)
        self._btn_conv.grid(row=3, column=0, padx=15, pady=15, sticky="ew")

    def _browse_conv_video(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Video", " ".join(VIDEO_EXTS))])
        if path: self._conv_video_var.set(path)

    def _browse_conv_output(self) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".mp3", filetypes=[("MP3", "*.mp3")])
        if path: self._conv_output_var.set(path)

    def _start_conversion(self) -> None:
        v = self._conv_video_var.get()
        if not v: return
        self._btn_conv.configure(state="disabled")
        threading.Thread(target=self._run_conversion, args=(v, self._conv_output_var.get()), daemon=True).start()

    def _run_conversion(self, v: str, o: str) -> None:
        try:
            res = convert_video_to_audio(v, o or None)
            self.after(0, lambda: [self._btn_conv.configure(state="normal"), self._conv_status_var.set(f"✅ Guardado: {res}"), self._show_toast("✅ Conversión exitosa")])
        except Exception as e:
            self.after(0, self._on_generic_error, str(e), self._btn_conv, self._conv_status_var)

    # ══════════════════════════════════════════════════════════════════════════
    # Tab 4 — Configuración
    # ══════════════════════════════════════════════════════════════════════════

    def _build_settings_tab(self) -> None:
        tab = self._tabs.tab("⚙️  Configuración")
        tab.grid_columnconfigure(0, weight=1)
        sub_tabs = ctk.CTkTabview(tab, height=450)
        sub_tabs.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        sub_tabs.add("General")
        sub_tabs.add("Summarizer (IA)")
        sub_tabs.add("Plantillas")

        # --- General ---
        g = sub_tabs.tab("General")
        g.grid_columnconfigure(1, weight=1)
        self._engine_sel = self._add_setting_menu(g, 0, "Motor Transcripción:", _ENGINE_VALUES, _ENGINE_LABELS.get(self._config["engine"], "offline"))
        self._model_sel = self._add_setting_menu(g, 1, "Modelo Whisper:", _MODEL_VALUES, _MODEL_LABELS.get(self._config["model"], "small"))
        self._lang_sel = self._add_setting_menu(g, 2, "Idioma Entrada:", _LANGUAGE_VALUES, _LANGUAGE_LABELS.get(self._config["language"], "auto"))
        ctk.CTkButton(g, text="💾 Guardar Transcripción", command=self._save_trans_settings).grid(row=3, column=0, columnspan=2, padx=10, pady=20, sticky="ew")

        # --- Summarizer ---
        s = sub_tabs.tab("Summarizer (IA)")
        s.grid_columnconfigure(1, weight=1)
        self._llm_sel = self._add_setting_menu(s, 0, "Motor LLM:", _LLM_ENGINE_VALUES, _LLM_ENGINE_LABELS.get(self._config["llm_engine"], "groq"))

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

        ctk.CTkButton(s, text="💾 Guardar Ajustes LLM", command=self._save_llm_settings).grid(row=3, column=0, columnspan=2, padx=10, pady=20, sticky="ew")

        # Initial model load and key validation
        self._refresh_ollama_models()
        self._update_key_visibility()

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
        ctk.CTkButton(row_btn, text="💾 Guardar", fg_color="#10B981", command=self._save_template_item).grid(row=0, column=0, padx=(0,5), sticky="ew")
        ctk.CTkButton(row_btn, text="🗑️ Eliminar", fg_color="#EF4444", command=self._delete_template_item).grid(row=0, column=1, padx=(5,0), sticky="ew")
        self._refresh_template_editor()

    def _refresh_template_editor(self) -> None:
        templates = template_manager.get_all_templates()
        names = ["Nuevo..."] + [t["name"] for t in templates]
        self._tpl_selector.configure(values=names)
        self._refresh_templates_list()

    def _on_template_select(self, name: str) -> None:
        if name == "Nuevo...":
            self._tpl_name_entry.delete(0, "end")
            self._tpl_body_text.delete("0.0", "end")
        else:
            templates = template_manager.get_all_templates()
            t = next((x for x in templates if x["name"] == name), None)
            if t:
                self._tpl_name_entry.delete(0, "end")
                self._tpl_name_entry.insert(0, t["name"])
                self._tpl_body_text.delete("0.0", "end")
                self._tpl_body_text.insert("0.0", t["body"])

    def _save_template_item(self) -> None:
        name = self._tpl_name_entry.get().strip()
        body = self._tpl_body_text.get("0.0", "end").strip()
        if not name or not body: return
        tid = name.lower().replace(" ", "_")
        template_manager.save_template(tid, name, body)
        self._show_toast("✅ Plantilla guardada.")
        self._refresh_template_editor()

    def _delete_template_item(self) -> None:
        name = self._tpl_name_entry.get().strip()
        if not name: return
        tid = name.lower().replace(" ", "_")
        template_manager.delete_template(tid)
        self._show_toast("🗑️ Plantilla eliminada.")
        self._refresh_template_editor()

    def _add_setting_menu(self, parent, row, label, values, default) -> ctk.CTkOptionMenu:
        ctk.CTkLabel(parent, text=label, anchor="w").grid(row=row, column=0, padx=10, pady=5, sticky="w")
        m = ctk.CTkOptionMenu(parent, values=values)
        m.set(default)
        m.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        return m

    def _save_trans_settings(self) -> None:
        self._config.update({
            "engine": _ENGINE_KEYS[_ENGINE_VALUES.index(self._engine_sel.get())],
            "model": _MODEL_KEYS[_MODEL_VALUES.index(self._model_sel.get())],
            "language": _LANGUAGE_KEYS[_LANGUAGE_VALUES.index(self._lang_sel.get())],
        })
        save_config(self._config)
        self._show_toast("✅ Ajustes de transcripción guardados.")

    def _save_llm_settings(self) -> None:
        self._config.update({
            "llm_engine": _LLM_ENGINE_KEYS[_LLM_ENGINE_VALUES.index(self._llm_sel.get())],
            "groq_api_key": self._groq_key_entry.get().strip(),
            "ollama_model": self._ollama_mod_sel.get(),
        })
        save_config(self._config)
        self._show_toast("✅ Ajustes de IA guardados.")
        self._update_key_visibility()

    def _update_key_visibility(self):
        """Updates the visual status of the Groq API key field."""
        if not self._groq_key_entry.get().strip():
            self._groq_status_lbl.configure(text="⚠️ Requerido para Cloud")
        else:
            self._groq_status_lbl.configure(text="")

    def _refresh_ollama_models(self) -> None:
        """Triggers a background thread to update the list of available Ollama models."""
        self._btn_refresh_ollama.configure(state="disabled")
        threading.Thread(target=self._run_ollama_discovery, daemon=True).start()

    def _run_ollama_discovery(self) -> None:
        """Fetches models from Ollama API."""
        try:
            import ollama
            response = ollama.list()
            # Handle different versions of the ollama library
            if hasattr(response, 'models'):
                models = [m.model for m in response.models]
            elif isinstance(response, dict) and 'models' in response:
                models = [m['name'] for m in response['models']]
            else:
                models = []

            if not models:
                models = ["llama3.2"] # Fallback

            self.after(0, self._on_ollama_discovery_success, models)
        except (ImportError, Exception):
            self.after(0, self._on_ollama_discovery_error)

    def _on_ollama_discovery_success(self, models: list[str]) -> None:
        current = self._ollama_mod_sel.get()
        self._ollama_mod_sel.configure(values=models)
        if current in models:
            self._ollama_mod_sel.set(current)
        else:
            self._ollama_mod_sel.set(models[0])
        self._btn_refresh_ollama.configure(state="normal")

    def _on_ollama_discovery_error(self) -> None:
        self._btn_refresh_ollama.configure(state="normal")
        # Don't show error popup here as it might be annoying on startup,
        # just keep whatever is there.

    # ══════════════════════════════════════════════════════════════════════════
    # Shared helpers
    # ══════════════════════════════════════════════════════════════════════════

    def _add_file_row(self, parent, row, label, var, browse_fn, save=False) -> None:
        frame = ctk.CTkFrame(parent)
        frame.grid(row=row, column=0, padx=10, pady=6, sticky="ew")
        frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(frame, text=label, width=140, anchor="w").grid(row=0, column=0, padx=10, pady=8)
        ctk.CTkEntry(frame, textvariable=var, state="readonly").grid(row=0, column=1, padx=6, pady=8, sticky="ew")
        ctk.CTkButton(frame, text="📁 Examinar", width=110, command=browse_fn).grid(row=0, column=2, padx=10, pady=8)


if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = KonverterApp()
    app.mainloop()
