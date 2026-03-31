from abc import ABC, abstractmethod
from collections.abc import Iterator
import logging
from typing import Any

log = logging.getLogger("kong-verter.summarizer")


class LLMProvider(ABC):
    """Base class for LLM providers."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate a completion for the given prompt."""
        pass

    @abstractmethod
    def generate_stream(self, prompt: str) -> Iterator[str]:
        """Generate a completion for the given prompt yielding chunks."""
        pass


class GroqProvider(LLMProvider):
    """Provider for Groq Cloud API."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    def generate(self, prompt: str) -> str:
        return "".join(self.generate_stream(prompt))

    def generate_stream(self, prompt: str) -> Iterator[str]:
        from groq import Groq

        if not self.api_key:
            raise ValueError("Groq API Key no configurada. Por favor, ve a Configuración.")

        log.info("Groq request | model=llama-3.3-70b-specdec | prompt_len=%d", len(prompt))
        client = Groq(api_key=self.api_key)
        stream = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.3-70b-specdec",
            stream=True,
        )
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content


class OllamaProvider(LLMProvider):
    """Provider for Ollama local API."""

    def __init__(self, model_name: str):
        self.model_name = model_name

    def generate(self, prompt: str) -> str:
        return "".join(self.generate_stream(prompt))

    def generate_stream(self, prompt: str) -> Iterator[str]:
        import ollama

        log.info("Ollama request | model=%s | prompt_len=%d", self.model_name, len(prompt))
        try:
            stream = ollama.chat(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                stream=True,
            )
            for chunk in stream:
                yield chunk["message"]["content"]
        except Exception as e:
            raise RuntimeError(f"Error llamando a Ollama: {e}. ¿Está Ollama corriendo?") from e


class Summarizer:
    """Summarization engine for kong-verter."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.providers: dict[str, LLMProvider] = {
            "groq": GroqProvider(config.get("groq_api_key", "")),
            "ollama": OllamaProvider(config.get("ollama_model", "llama3.2")),
        }

    def summarize(self, text: str, template_body: str, translate_to_es: bool = False) -> str:
        """Process transcription text with a template and optional translation."""
        return "".join(self.summarize_stream(text, template_body, translate_to_es))

    def summarize_stream(self, text: str, template_body: str, translate_to_es: bool = False) -> Iterator[str]:
        """Process transcription text yielding updates."""
        engine_name = self.config.get("llm_engine", "groq")
        provider = self.providers.get(engine_name)

        if not provider:
            raise ValueError(f"Motor LLM desconocido: {engine_name}")

        prompt = f"{template_body}\n\nTexto:\n{text}"
        if translate_to_es:
            prompt += "\n\nIMPORTANTE: El resultado final DEBE estar en ESPAÑOL, sin importar el idioma del texto original."

        yield from provider.generate_stream(prompt)
