## Why

La interfaz actual de Kong-verter usa un layout de tabs horizontales (CTkTabview) que agrupa toda la funcionalidad en 4 pestañas planas. Esto presenta dos problemas:

1. **Navegación limitada**: El TabView ocupa espacio vertical y no escala bien visualmente. Una sidebar vertical es más moderna, aprovecha mejor el espacio horizontal y permite expandir la navegación sin sacrificar área de contenido.
2. **Flujo de transcripción rígido**: Actualmente la transcripción y el resumen IA están separados en tabs distintos, lo que obliga al usuario a saltar entre pestañas. No hay forma de agregar notas o contexto adicional que enriquezca el resumen generado por el LLM.

## What Changes

- **Reemplazar TabView principal por layout sidebar + panel de contenido**: Sidebar izquierdo fijo con navegación vertical (iconos + texto) y panel de contenido dinámico a la derecha.
- **Agregar barra de estado inferior**: Muestra motor de transcripción activo, modelo Whisper seleccionado y estado de conexión de Ollama.
- **Rediseñar sección Transcribir con 3 sub-tabs internos**:
  - 📄 Transcripción: Selector de archivo, área de transcripción, botón transcribir, barra de progreso (funcionalidad actual).
  - 📝 Notas: Área de texto editable para notas opcionales que se concatenan al prompt del LLM.
  - ✨ Resultado IA: Selector de plantilla, checkbox traducción, botón generar, área de resultado en streaming, botones copiar/guardar.
- **Rediseñar sección Resumen como herramienta standalone**: Área de texto libre para pegar/escribir texto, selector de plantilla, generación de resumen con IA. No depende de la transcripción.
- **Mantener secciones Convertir y Configuración** sin cambios funcionales, solo adaptadas al nuevo layout.

## No-objetivos

- No se cambia de framework (se mantiene CustomTkinter).
- No se modifican archivos del backend (`summarizer.py`, `transcriber.py`, `config.py`, `template_manager.py`, `video_converter.py`).
- No se buscan efectos visuales avanzados (sombras, gradientes, animaciones).
- No se agrega funcionalidad nueva al backend (no hay nuevos providers, modelos, etc.).

## Capabilities

### New Capabilities
- `sidebar-navigation`: Sistema de navegación por sidebar vertical que reemplaza el TabView principal, con selección de sección y panel de contenido dinámico.
- `transcription-notes`: Panel de notas opcionales dentro de la sección Transcribir que se integran al prompt del LLM para enriquecer el resumen generado.
- `status-bar`: Barra de estado inferior que muestra información del motor activo, modelo y estado de Ollama.

### Modified Capabilities

## Impact

- **Código afectado**: Solo `gui.py` — reescritura completa de la clase `KonverterApp` manteniendo las mismas interfaces con el backend.
- **Dependencias**: Sin cambios. Se sigue usando CustomTkinter y las mismas librerías.
- **Prompt del LLM**: Se modifica la construcción del prompt en la GUI para incluir notas opcionales (`template + transcripción + notas`). El `Summarizer` recibe el prompt ya construido, no se modifica.
