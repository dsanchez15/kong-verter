# Especificación: Retroalimentación en Tiempo Real (Streaming)

## Resumen
Esta capacidad permite visualizar el progreso y el contenido intermedio durante las operaciones pesadas (transcripción y resumen con IA).

## Requerimientos Funcionales
1. **Streaming de Transcripción (Offline)**:
   - Los segmentos de texto deben aparecer en la UI tan pronto como Whisper los genere.
   - Debe calcularse el progreso actual dividiendo el `end_time` del segmento por la duración total.
2. **Barra de Progreso**:
   - Debe ser visible permanentemente durante el proceso.
   - El porcentaje debe actualizarse suavemente.
3. **Tiempo Estimado (ETA)**:
   - Se debe mostrar un label: "ETA: XX:XX".
   - El cálculo debe basarse en la velocidad de procesamiento real de los primeros segmentos.
4. **Streaming de Resumen (IA)**:
   - El motor de resumen debe utilizar el endpoint de `stream=True` de Ollama/Groq.
   - El texto del resumen debe "escribirse solo" en la pestaña de resultados en tiempo real.

## Criterios de Aceptación
- La transcripción en vivo evita que la UI parezca congelada.
- El tiempo estimado (ETA) comienza a aparecer después de los primeros 5-10 segundos de procesamiento.
- El resumen fluye suavemente en la pestaña ✨ Resultado.
- Si el proceso falla a la mitad, se conserva el texto parcial generado.

## Notas Técnicas
- El streaming de LLM requiere un callback en `Summarizer` para no bloquear el hilo de la UI.
- `faster-whisper` segments son dinámicos, por lo que el ETA puede fluctuar si el audio tiene mucho silencio.
