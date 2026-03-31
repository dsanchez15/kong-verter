# Tareas: Transcripción en Vivo y Progreso (Streaming)

## 🛠️ Refactorización del Core (Streaming)
- [x] 1. **Streaming en Transcriber**: Modificar `transcriber.py` para añadir `transcribe_stream`. El generador debe devolver tuplas `("segment", text)` y `("progress", float)`.
- [x] 2. **Streaming en Summarizer**: Actualizar `summarizer.py` y los `Providers` (Groq/Ollama) para soportar generación por fragmentos (`stream=True`).

## 🖥️ Mejoras en la Interfaz de Usuario (GUI)
- [x] 3. **Componentes de Progreso**: Añadir `CTkProgressBar` y un label de **"Tiempo Estimado"** en la pestaña `📝 Transcribir`.
- [x] 4. **Hilos de Consumo (Transcripción)**: Modificar `_run_transcription` para leer el flujo del generador y actualizar la UI en tiempo real vía `self.after(0, ...)`.
- [x] 5. **Hilos de Consumo (Resumen)**: Modificar `_run_summarization` para que rellene el cuadro de resultado frase por frase, haciendo que el proceso se sienta instantáneo.
- [x] 6. **Cálculo de ETA**: Implementar la lógica matemática para estimar el tiempo restante basado en el procesamiento actual.

## ⚠️ Robustez y Gestión de Errores
- [x] 7. **Detección de Duración**: Asegurar que siempre obtenemos la duración del audio para que el progreso no sea "infinito".
- [x] 8. **Limpieza de UI**: Reiniciar la barra de progreso y el ETA al empezar nuevas tareas.

## 🧪 Pruebas y Verificación
- [x] 9. **Test de Streaming**: Verificar que el texto aparece conforme se genera.
- [x] 10. **Precisión del Progreso**: Comprobar que el 100% coincide con el final del archivo.
- [x] 11. **Test de LLM Streaming**: Ver si Groq y Ollama devuelven resultados parciales correctamente.
