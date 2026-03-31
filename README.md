# 🦍 Kong-verter

**Kong-verter** es una herramienta de escritorio potente y sencilla diseñada para la gestión de archivos multimedia. Permite convertir videos a audio (MP3), transcribir esos audios a texto con IA avanzada, y generar resúmenes o extracciones de datos utilizando modelos de lenguaje locales o en la nube.

---

## ✨ Características Principales

- **🚀 Conversión de Video a Audio:** Extrae pistas de audio de archivos `.mp4`, `.mkv`, `.avi`, `.mov`, `.webm` y más, guardándolas como `.mp3`.
- **🎙️ Transcripción Inteligente:** Convierte voz a texto con dos motores:
  - **Offline (Whisper):** Usa `faster-whisper` para transcripción local, privada y gratuita. Soporta múltiples idiomas y detección automática.
  - **Online (Google):** Usa la API de Google Speech para transcripciones rápidas (requiere internet).
- **🤖 Resumen y Extracción con IA (LLM):** Procesa transcripciones con plantillas personalizadas usando:
  - **Ollama (Local):** Ejecuta modelos en tu propia máquina. La app detecta automáticamente los modelos instalados.
  - **Groq Cloud:** Acceso a modelos de alta performance vía API (requiere clave API de [console.groq.com](https://console.groq.com)).
- **📝 Editor de Plantillas:** Crea y gestiona plantillas personalizadas para guiar al LLM (resúmenes, extracción de puntos clave, minutos de reunión, etc.).
- **⚙️ Configuración Persistente:** Todos tus ajustes (motor, modelo, idioma, clave API) se guardan automáticamente en `~/.konverter/config.json`.
- **🎨 Interfaz Moderna:** Construida con `CustomTkinter`. Soporte nativo de Dark Mode.

---

## 🛠️ Requisitos del Sistema

| Requisito | Detalle |
|---|---|
| **Python** | 3.10 o superior (`pip >= 21.3` requerido para editable install) |
| **FFmpeg** | Requerido para conversión de video/audio. Debe estar en el PATH. |
| **Ollama** *(opcional)* | Para usar LLMs locales. Descarga desde [ollama.ai](https://ollama.ai) |
| **Clave API de Groq** *(opcional)* | Para usar el motor Cloud. Obtén una en [console.groq.com](https://console.groq.com) |

---

## 🚀 Instalación

### Windows

```bash
# 1. Clonar el repositorio
git clone https://github.com/dsanchez15/kong-verter.git
cd kong-verter

# 2. Crear y activar entorno virtual
python -m venv .venv
.\.venv\Scripts\activate

# 3. Instalar dependencias
pip install --upgrade pip
pip install -e .

# 4. Ejecutar
python gui.py
```

> **FFmpeg en Windows:** Descarga desde [ffmpeg.org](https://ffmpeg.org/download.html) y añádelo al PATH del sistema, o usa `winget install ffmpeg`.

### macOS

```bash
# 1. Instalar dependencias del sistema (requiere Homebrew)
brew install ffmpeg

# 2. Clonar el repositorio
git clone https://github.com/dsanchez15/kong-verter.git
cd kong-verter

# 3. Crear y activar entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# 4. Instalar dependencias de Python
pip install --upgrade pip
pip install -e .

# 5. Ejecutar
python gui.py
```

> **Ollama en macOS:** Descarga el instalador nativo desde [ollama.ai](https://ollama.ai) y luego instala los modelos que quieras: `ollama pull llama3.2`.

### Linux

```bash
# FFmpeg (Ubuntu/Debian)
sudo apt install ffmpeg

# El resto del proceso es igual que en macOS (pasos 2–5)
```

---

## 🏗️ Arquitectura del Proyecto

```
kong-verter/
├── gui.py              # Interfaz de usuario (CustomTkinter, 4 pestañas)
├── transcriber.py      # Motores de transcripción (patrón estrategia: Offline/Online)
├── summarizer.py       # Motor LLM con arquitectura de Providers (Groq / Ollama)
├── video_converter.py  # Conversión de video a MP3 vía moviepy/ffmpeg
├── template_manager.py # CRUD de plantillas personalizadas para el LLM
├── config.py           # Persistencia de configuración en ~/.konverter/config.json
└── pyproject.toml      # Dependencias y configuración de herramientas (ruff, mypy)
```

### Módulos clave

- **`summarizer.py`**: Implementa el patrón "Provider". Cada motor LLM (`GroqProvider`, `OllamaProvider`) es independiente y extensible. Añadir un nuevo proveedor (OpenAI, Gemini, etc.) solo requiere crear una nueva clase.
- **`transcriber.py`**: Patrón estrategia con `BaseTranscriber`. Los motores `OfflineTranscriber` y `OnlineTranscriber` son intercambiables.
- **`config.py`**: Lee y escribe `~/.konverter/config.json`. Incluye merge automático con valores por defecto para compatibilidad con versiones futuras.

---

## ⚙️ Guía de Configuración (pestaña ⚙️)

### Transcripción
| Ajuste | Opciones | Notas |
|---|---|---|
| Motor | Offline / Online | Offline recomendado para privacidad |
| Modelo Whisper | tiny / base / small / medium / large-v3 | `small` es el mejor balance velocidad/calidad |
| Idioma | Auto / Español / English | Auto detecta el idioma automáticamente |

### IA / LLM
| Ajuste | Descripción |
|---|---|
| Motor LLM | **Ollama** (local) o **Groq Cloud** |
| Modelos Ollama | Se detectan automáticamente. Usa 🔄 para refrescar la lista. |
| API Key Groq | Requerida para el motor Cloud. La app avisa si falta. |

---

## 📄 Licencia

Este proyecto está bajo la licencia MIT. ¡Siéntete libre de contribuir!
