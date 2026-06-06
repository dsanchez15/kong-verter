"""Audio transcription engines for kon-verter.

Provides a common interface (BaseTranscriber) with two concrete implementations:
- OfflineTranscriber: Uses faster-whisper for local, no-internet transcription.
- OnlineTranscriber: Uses SpeechRecognition + Google Speech API (requires internet).
"""

import os
import sys
from abc import ABC, abstractmethod
from collections.abc import Iterator
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Windows: register NVIDIA CUDA DLL directories so ctranslate2 can find them.
# pip installs cublas/cudnn under site-packages/nvidia/*/bin/ but does NOT add
# those paths to the Windows DLL search path automatically. ctranslate2 tries to
# load cublas64_12.dll at *import time*, so this must run before any
# faster_whisper / ctranslate2 import.
# ---------------------------------------------------------------------------
if sys.platform == "win32":
    _nvidia_found: bool = False

    # Helper: try to register a single nvidia bin directory
    def _register_nvidia_bin(base: Path) -> None:
        for lib in ("cublas", "cudnn", "cuda_runtime", "cuda_nvrtc"):
            bin_dir = base / lib / "bin"
            if bin_dir.exists():
                os.add_dll_directory(str(bin_dir))
                os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ.get("PATH", "")

    # Strategy 1: sys.prefix (works when venv is active or python.exe is called directly)
    _nvidia_base = Path(sys.prefix) / "Lib" / "site-packages" / "nvidia"
    if _nvidia_base.exists():
        _register_nvidia_bin(_nvidia_base)
        _nvidia_found = True

    # Strategy 2: search sys.path entries for a site-packages that contains nvidia/
    if not _nvidia_found:
        for sp in sys.path:
            candidate = Path(sp) / "nvidia"
            if candidate.exists():
                _register_nvidia_bin(candidate)
                _nvidia_found = True
                break
            # Also try parent (some entries point inside a package, not site-packages root)
            candidate = Path(sp).parent / "nvidia"
            if candidate.exists():
                _register_nvidia_bin(candidate)
                _nvidia_found = True
                break

    # Strategy 3: look for a .venv / venv next to this script
    if not _nvidia_found:
        for venv_name in (".venv", "venv", "env"):
            candidate = Path(__file__).parent / venv_name / "Lib" / "site-packages" / "nvidia"
            if candidate.exists():
                _register_nvidia_bin(candidate)
                _nvidia_found = True
                break


class BaseTranscriber(ABC):
    """Abstract base class for transcription engines."""

    @abstractmethod
    def transcribe(self, audio_path: Path, language: str | None = None) -> str:
        """Transcribe an audio file to text."""
        ...

    @abstractmethod
    def transcribe_stream(self, audio_path: Path, language: str | None = None) -> Iterator[tuple[str, Any]]:
        """Transcribe an audio file and yield progress and segments.

        Yields:
            Tuples of (type, content) where type is "segment" (str) or "progress" (float 0-1).
        """
        ...


class OfflineTranscriber(BaseTranscriber):
    """Transcribes audio locally using faster-whisper.

    Downloads the selected model from Hugging Face on first use.
    Subsequent uses load from the local cache (~/.cache/huggingface).

    Args:
        model_size: One of "tiny", "base", "small", "medium", or "large-v3".
    """

    MODEL_SIZES = ["tiny", "base", "small", "medium", "large-v3"]
    # Approximate download sizes in MB for user-facing warnings
    MODEL_SIZES_MB = {
        "tiny": 75,
        "base": 142,
        "small": 461,
        "medium": 1500,
        "large-v3": 3100,
    }

    # Session-level cache: avoids re-loading (and re-downloading) the same model
    _model_cache: dict[str, object] = {}

    def __init__(self, model_size: str = "small") -> None:
        if model_size not in self.MODEL_SIZES:
            raise ValueError(f"Invalid model size '{model_size}'. Choose from: {self.MODEL_SIZES}")
        self.model_size = model_size

    def _load_model(self) -> None:
        """Lazy-load the WhisperModel, using a session cache to avoid repeat downloads."""
        if self.model_size not in OfflineTranscriber._model_cache:
            from faster_whisper import WhisperModel  # type: ignore[import-untyped]

            OfflineTranscriber._model_cache[self.model_size] = WhisperModel(
                self.model_size, device="auto", compute_type="auto"
            )

    @property
    def _model(self) -> Any:
        return OfflineTranscriber._model_cache.get(self.model_size)

    def transcribe(self, audio_path: Path, language: str | None = None) -> str:
        """Transcribe using faster-whisper."""
        return " ".join(content for t, content in self.transcribe_stream(audio_path, language) if t == "segment")

    def transcribe_stream(self, audio_path: Path, language: str | None = None) -> Iterator[tuple[str, Any]]:
        """Transcribe using faster-whisper and yield updates."""
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        self._load_model()

        lang_arg = language if language != "auto" else None
        segments, info = self._model.transcribe(
            str(audio_path),
            language=lang_arg,
            beam_size=1,
            vad_filter=True,
        )

        duration = info.duration
        for segment in segments:
            yield "segment", segment.text.strip()
            if duration > 0:
                progress = segment.end / duration
                yield "progress", min(1.0, progress)


class OnlineTranscriber(BaseTranscriber):
    """Transcribes audio using Google Speech Recognition (requires internet).

    Uses the SpeechRecognition library with Google's free API.
    Note: The free API has usage limits and may not work for files longer than ~60s.
    Long audio is split into segments automatically.

    Args:
        language_code: BCP-47 language code, e.g. "es-CO", "en-US". Defaults to "es-CO".
    """

    LANGUAGE_MAP = {
        "es": "es-CO",
        "en": "en-US",
        "auto": "es-CO",  # Google API requires an explicit language
    }

    def __init__(self, language_code: str = "es-CO") -> None:
        self.language_code = language_code

    def transcribe(self, audio_path: Path, language: str | None = None) -> str:
        """Transcribe using Google Speech API via SpeechRecognition."""
        # For simplicity, we just collect all items from the stream
        return " ".join(content for t, content in self.transcribe_stream(audio_path, language) if t == "segment")

    def transcribe_stream(self, audio_path: Path, language: str | None = None) -> Iterator[tuple[str, Any]]:
        """Transcribe using Google Speech API and yield updates."""
        import speech_recognition as sr  # type: ignore[import-untyped]

        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        yield "progress", 0.1
        lang = self.LANGUAGE_MAP.get(language or "auto", "es-CO") if language else self.language_code
        recognizer = sr.Recognizer()

        try:
            with sr.AudioFile(str(audio_path)) as source:
                audio_data = recognizer.record(source)
            yield "progress", 0.5
            text = str(recognizer.recognize_google(audio_data, language=lang))
            yield "segment", text
            yield "progress", 1.0
        except sr.UnknownValueError as exc:
            raise RuntimeError("Google Speech API could not understand the audio.") from exc
        except sr.RequestError as e:
            raise RuntimeError(f"Google Speech API request failed: {e}") from e


def get_transcriber(engine: str, model: str = "small", language: str = "auto") -> BaseTranscriber:
    """Factory function to create the appropriate transcriber.

    Args:
        engine: "offline" or "online".
        model: Model size for the offline engine.
        language: Language code for the online engine.

    Returns:
        An instance of the appropriate BaseTranscriber subclass.

    Raises:
        ValueError: If an unknown engine name is provided.
    """
    if engine == "offline":
        return OfflineTranscriber(model_size=model)
    if engine == "online":
        lang_code = OnlineTranscriber.LANGUAGE_MAP.get(language, "es-CO")
        return OnlineTranscriber(language_code=lang_code)
    raise ValueError(f"Unknown transcription engine: '{engine}'. Use 'offline' or 'online'.")
