# 🦍 Kong-verter

**Kong-verter** es una herramienta de escritorio potente y sencilla diseñada para la gestión de archivos multimedia. Permite convertir videos a audio (MP3) y transcribir esos audios a texto utilizando inteligencia artificial avanzada, todo desde una interfaz gráfica moderna.

---

## ✨ Características Principalest
- **🚀 Conversión de Video a Audio:** Extrae pistas de audio de archivos `.mp4`, `.mkv`, `.avi`, y más, guardándolas como `.mp3`.
- **🎙️ Transcripción Inteligente:** Convierte voz a texto con dos motores:
  - **Offline (Whisper):** Utiliza `faster-whisper` para transcripción local privada y gratuita (soporta múltiples idiomas y detección automática).
  - **Online (Google):** Utiliza la API de Google Speech para transcripciones rápidas (requiere internet).
- **⚙️ Configuración Persistente:** Personaliza el motor, el tamaño del modelo de IA y el idioma preferido. Tus ajustes se guardan automáticamente.
- **🎨 Interfaz Moderna:** Construida con `CustomTkinter` para una experiencia visual premium y soporte nativo de Dark Mode.

---

## 🛠️ Requisitos
- **Python:** 3.10 o superior.
- **FFmpeg:** Necesario para el procesamiento de audio/video. Asegúrate de tenerlo instalado y en tu PATH.

---

## 🚀 Instalación y Uso

### 1. Clonar el repositorio
```bash
git clone git@github.com:dsanchez15/kong-verter.git
cd kong-verter
```

### 2. Crear y activar entorno virtual
```bash
python -m venv .venv
# En Windows:
.\.venv\Scripts\activate
# En Linux/macOS:
source .venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -e .
```

### 4. Ejecutar la aplicación
```bash
python gui.py
```

---

## 🏗️ Arquitectura del Proyecto

- **`gui.py`**: Punto de entrada principal e interfaz de usuario (3 pestañas: Convertir, Transcribir, Configuración).
- **`video_converter.py`**: Lógica central para la extracción de audio mediante `moviepy`.
- **`transcriber.py`**: Abstracción de motores de transcripción (patrón Estrategia).
- **`config.py`**: Gestiona la persistencia de preferencias del usuario en `~/.konverter/config.json`.
- **`.agents/`**: Memoria persistente e instrucciones para el desarrollo asistido por IA.

---

## ⚙️ Configuración de Transcripción
En la pestaña de **Configuración** puedes elegir:
- **Motor Offline:** Recomendado para privacidad. Descarga modelos de Hugging Face automáticamente.
  - *Small/Medium* son ideales para español e inglés.
- **Motor Online:** Rápido y ligero, ideal para audios cortos si tienes buena conexión.

---

## 📄 Licencia
Este proyecto está bajo la licencia MIT. ¡Siéntete libre de contribuir!
