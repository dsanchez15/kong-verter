# Propuesta: Transcripción en Vivo y Tiempo Estimado

## Resumen
Mejorar la experiencia de usuario durante los procesos largos de transcripción. Actualmente, el usuario debe esperar a que todo el proceso termine sin recibir retroalimentación visual del progreso o del texto que se está generando.

## Motivación
El usuario percibe que el proceso es lento y que no tiene información sobre cuánto falta. Al mostrar el texto en tiempo real ("streaming") y un indicador de progreso, la espera se siente menos pesada y el usuario puede confirmar que la transcripción va por buen camino.

## Objetivos
1. **Streaming de Texto**: Actualizar la caja de texto en la pestaña de transcripción palabra por palabra o segmento por segmento.
2. **Indicador de Progreso**: Añadir una barra de progreso o porcentaje basado en el tiempo procesado vs la duración total del audio.
3. **Optimización de Resumen**: Explorar formas de acelerar el resumen (opcional, pero se mencionará en el diseño).
4. **Estimación de Tiempo**: Mostrar el tiempo aproximado restante.

## Impacto
- **Archivos Afectados**:
  - `transcriber.py`: Modificar para devolver segmentos mediante un generador o aceptar un callback.
  - `gui.py`: Actualizar para recibir actualizaciones parciales y manejar una barra de progreso.
  - `video_converter.py`: (Opcional) Obtener metadatos de duración para el cálculo de progreso.

## Riesgos y Mitigaciones
- **Sobrecarga de UI**: Actualizar la UI demasiado rápido puede hacer que la app se trabe. Mitigación: limitar los refrescos a cada segmento o cada 500ms.
- **Incompatibilidad de Motores**: El motor online (Google) no soporta fácilmente streaming parcial por su naturaleza de API cloud. Mitigación: Enfocarse primero en el motor Offline (Whisper).
