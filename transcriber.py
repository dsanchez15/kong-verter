"""Audio transcription engines for kon-verter.

Provides a common interface (BaseTranscriber) with two concrete implementations:
- OfflineTranscriber: Uses faster-whisper for local, no-internet transcription.
- OnlineTranscriber: Uses SpeechRecognition + Google Speech API (requires internet).
"""

from abc import ABC, abstractmethod
from pathlib import Path


class BaseTranscriber(ABC):
    """Abstract base class for transcription engines."""

    @abstractmethod
    def transcribe(self, audio_path: Path, language: str | None = None) -> str:
        """Transcribe an audio file to text.

        Args:
            audio_path: Path to the input audio file (.mp3, .wav, etc.).
            language: BCP-47 language code (e.g. "es", "en") or None for auto-detection.

        Returns:
            The full transcribed text as a single string.

        Raises:
            FileNotFoundError: If the audio file does not exist.
            RuntimeError: If the transcription fails for any reason.
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

    def __init__(self, model_size: str = "small") -> None:
        if model_size not in self.MODEL_SIZES:
            raise ValueError(f"Invalid model size '{model_size}'. Choose from: {self.MODEL_SIZES}")
        self.model_size = model_size
        self._model = None  # Lazy-loaded on first transcription

    def _load_model(self) -> None:
        """Lazy-load the WhisperModel to avoid long startup times."""
        if self._model is None:
            from faster_whisper import WhisperModel  # type: ignore[import-untyped]

            # Use CPU with INT8 quantization for broad compatibility
            self._model = WhisperModel(self.model_size, device="cpu", compute_type="int8")

    def transcribe(self, audio_path: Path, language: str | None = None) -> str:
        """Transcribe using faster-whisper.

        Args:
            audio_path: Path to the audio file.
            language: Language code (e.g. "es", "en") or None for auto-detect.

        Returns:
            Full transcribed text.
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        self._load_model()

        # language=None triggers automatic language detection in faster-whisper
        lang_arg = language if language != "auto" else None
        segments, _info = self._model.transcribe(  # type: ignore[union-attr]
            str(audio_path),
            language=lang_arg,
            vad_filter=True,  # Skip silent segments for speed
        )
        return " ".join(segment.text.strip() for segment in segments)


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
        """Transcribe using Google Speech API via SpeechRecognition.

        Converts MP3 to WAV in memory if needed, then sends to Google's API.

        Args:
            audio_path: Path to the audio file (MP3 or WAV).
            language: Language code ("es", "en", "auto"). Overrides the instance default.

        Returns:
            Transcribed text.

        Raises:
            RuntimeError: On network or API errors.
        """
        import speech_recognition as sr  # type: ignore[import-untyped]

        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        lang = self.LANGUAGE_MAP.get(language or "auto", "es-CO") if language else self.language_code
        recognizer = sr.Recognizer()

        # SpeechRecognition reads WAV natively; for MP3 it uses pydub if available
        try:
            with sr.AudioFile(str(audio_path)) as source:
                audio_data = recognizer.record(source)
            return str(recognizer.recognize_google(audio_data, language=lang))
        except sr.UnknownValueError:
            raise RuntimeError("Google Speech API could not understand the audio.")
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
