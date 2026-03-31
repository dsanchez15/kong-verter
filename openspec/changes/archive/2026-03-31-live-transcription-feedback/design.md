# Diseño Técnico: Streaming de Transcripción y Progreso

## Arquitectura de Streaming

### 1. Transcriber Generator (`transcriber.py`)
Modificaremos la interfaz de `BaseTranscriber` para soportar streaming. El método `transcribe` podrá devolver un iterador que rinda tuplas `(tipo, contenido)`, donde `tipo` es "progress" (porcentaje o timestamp) o "segment" (texto parcial).

En `OfflineTranscriber`:
- El bucle `for segment in segments:` rendirá cada segmento inmediatamente.
- Utilizaremos `_info.duration` (que el modelo ya proporciona) para calcular `segment.end / duration * 100`.

En `OnlineTranscriber`:
- Al ser un proceso único de API, el progreso será binario (0% - 100%), pero se mantendrá la estructura de generador para uniformidad.

### 2. Componentes de UI (`gui.py`)
- **Pestaña Transcribir**: Se añadirá un objeto `ctk.CTkProgressBar` y un label de tiempo estimado `self._trans_progress_label`.
- **Integración con Hilo**: 
  ```python
  for item_type, content in transcriber.transcribe_stream(...):
      if item_type == "segment":
          self.after(0, self._update_live_text, content)
      elif item_type == "progress":
          self.after(0, self._update_progress_bar, content)
  ```

### 3. Estimación de Tiempo
Si transcurrieron `T1` segundos para transcribir `D1` segundos de audio, y el audio total dura `DT`, el tiempo restante estimado es `(DT - D1) * (T1 / D1)`. Se actualizará en cada segmento.

### 4. Resumen con IA
Para acelerar el resumen:
- El usuario mencionó que el resumen también es lento. 
- Implementaremos una pequeña optimización en `summarizer.py`: añadir un aviso de "⏳ Procesando..." en lugar de esperar a que regrese todo el texto. (Nota: Esto es puramente UX).

## Consideraciones No-Funcionales
- La barra de progreso será asíncrona.
- Se usará el decorador `@property` para mantener la interfaz limpia.
