# Capacidad: Integración de LLMs (Summarizer)

## Resumen
Esta capacidad permite procesar transcripciones a través de modelos de lenguaje grandes (local o nube) con plantillas dinámicas.

## Requerimientos
- **Local (Ollama)**:
  - El usuario debe poder ver una lista de los modelos instalados en su sistema.
  - La sincronización de modelos debe ocurrir al abrir la configuración o al pulsar un botón "Refrescar".
  - Si Ollama no está iniciado, debe avisar al usuario.
- **Cloud (Groq)**:
  - Requiere una clave API válida (`groq_api_key`).
  - Si la clave falta al seleccionar el motor, el usuario debe ver un aviso visual.
  - Al ejecutar una acción con este motor, se debe validar la presencia de la clave antes de llamar a la API.

## Puntos de Extensión
- `Summarizer` debe ser la única interfaz de uso.
- Añadir nuevos motores no debe requerir cambios en `gui.py` más allá de la configuración visual del motor.
- La gestión de errores debe estar centralizada en el `Provider` o en el `Summarizer`.

## Casos de Uso
1. **Selección de Modelo Local**: El usuario abre ajustes, ve la lista de sus modelos de Ollama ("llama3", "mistral", etc.) y selecciona uno. Se guarda en el config.
2. **Error de Conexión**: Ollama está apagado. El usuario ve "Servicio Ollama no disponible" en el menú de selección.
3. **Falta de API Key**: El usuario selecciona Groq sin clave. Al intentar generar un resumen, la app le avisa: "Por favor, introduce tu clave API de Groq en Ajustes".

## Criterios de Aceptación
- La lista de modelos de Ollama se actualiza correctamente.
- La aplicación no se congela al buscar modelos (uso de threading).
- Los errores de API se capturan y se muestran como notificaciones (toasts/messageboxes).

## Notas de Implementación
- El modelo por defecto de Ollama será `llama3.2` si no se detectan modelos.
- Las respuestas del LLM deben ser procesadas para eliminar bloques de código o metadatos innecesarios si la plantilla lo indica (opcional).
