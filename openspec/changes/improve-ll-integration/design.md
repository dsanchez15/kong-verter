# Diseño Técnico: Mejora de Integración LLM

## Descripción General
Esta mejora implementa una arquitectura de "Providers" para los LLM, separa la lógica de validación de la lógica de ejecución y mejora la interfaz de usuario para permitir la auto-detección de modelos de Ollama.

## Arquitectura de Software

### 1. Refactorización de `Summarizer` (`summarizer.py`)
Se pasará de una clase con métodos internos rígidos a una estructura de proveedores.

```python
class LLMProvider(Protocol):
    def generate(self, prompt: str) -> str: ...

class GroqProvider: ...
class OllamaProvider: ...

class Summarizer:
    def __init__(self, config: dict):
        self.providers = {
            "groq": GroqProvider(config),
            "ollama": OllamaProvider(config)
        }
    
    def summarize(self, text, template, translate):
        # Lógica de construcción del prompt
        # Selección del provider
```

### 2. Detección de Modelos de Ollama
En `gui.py`, se añadirá:
- `_update_ollama_models()`: Llama a `ollama.list()` de forma asíncrona (usando un hilo para no congelar la UI) y actualiza los valores del `OptionMenu`.

### 3. Cambios en la Interfaz de Usuario (`gui.py`)
- **Pestaña Configuración**:
  - Reemplazar `_ollama_mod_entry` (Entry) por `_ollama_mod_sel` (CTkOptionMenu).
  - Añadir botón 🔄 al lado del menú para forzar la actualización.
  - Validación visual: Si falta la key de Groq y está seleccionado, resaltar el campo en rojo o mostrar un icono de alerta.

### 4. Flujo de Control
1. El usuario abre la pestaña de configuración.
2. La app intenta cargar los modelos de Ollama en segundo plano.
3. Si el usuario intenta ejecutar el "Summarizer":
   - Se valida que el motor seleccionado tenga sus requisitos (Key en Groq, Servicio corriendo en Ollama).
   - Si falla, se muestra un `messagebox` descriptivo en lugar de crashear el hilo de ejecución.

## Almacenamiento y Configuración
Se mantiene el uso de `config.py` con el esquema actual. Se podría añadir un campo `last_ollama_models` (opcional) para caché, pero se prefiere carga dinámica para asegurar que el modelo seleccionado realmente exista.

## Consideraciones de Escalabilidad
- La estructura de Providers permite añadir `OpenAI`, `Anthropic`, o `Gemini` simplemente creando una clase nueva que cumpla el protocolo `LLMProvider`.
- Se separa la validación del "motor" de su ejecución.
