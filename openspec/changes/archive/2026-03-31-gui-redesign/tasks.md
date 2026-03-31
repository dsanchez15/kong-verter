## 1. Estructura base del layout

- [x] 1.1 Crear el frame del sidebar (CTkFrame fijo, ~160px de ancho) con los botones de navegación: Transcribir, Resumen, Convertir, Configuración. Incluir header con nombre "Kong-verter" en la parte superior del sidebar.
- [x] 1.2 Implementar el sistema de navegación por frames: crear un frame de contenido por cada sección, implementar método `_switch_section(name)` que alterna visibilidad con `grid()`/`grid_remove()` y actualiza el color del botón activo.
- [x] 1.3 Crear el frame de la barra de estado inferior con labels para: motor de transcripción, modelo Whisper y estado de Ollama. Conectar la actualización al guardar configuración y al resultado del discovery de Ollama.

## 2. Sección Transcribir (3 sub-tabs)

- [x] 2.1 Crear el frame de Transcribir con un CTkTabview interno de 3 tabs: "📄 Transcripción", "📝 Notas", "✨ Resultado IA".
- [x] 2.2 Migrar el contenido actual de transcripción al sub-tab "📄 Transcripción": selector de archivo, área de texto, botón transcribir, barra de progreso con ETA. Reutilizar la lógica existente de `_run_transcription`, `_append_trans_text`, `_update_trans_progress`.
- [x] 2.3 Implementar el sub-tab "📝 Notas": área de texto editable (CTkTextbox) con placeholder "Escribe notas opcionales para enriquecer el resumen...".
- [x] 2.4 Implementar el sub-tab "✨ Resultado IA": selector de plantilla (CTkOptionMenu), checkbox traducción, botón "Generar Resumen", área de texto resultado (CTkTextbox readonly), botones copiar y guardar .md.
- [x] 2.5 Implementar la lógica de generación de resumen que concatena transcripción + notas (si hay) y lo pasa al Summarizer. Conectar el streaming de chunks al textbox de resultado.

## 3. Sección Resumen (standalone)

- [x] 3.1 Crear el frame de Resumen con: área de texto editable para input libre, selector de plantilla, checkbox traducción, botón "Generar Resumen", área de texto resultado con streaming, botones copiar y guardar .md.
- [x] 3.2 Implementar la lógica de generación que toma el texto libre del input, lo combina con la plantilla seleccionada y lo pasa al Summarizer con streaming.

## 4. Secciones Convertir y Configuración

- [x] 4.1 Migrar la sección Convertir al nuevo layout (mover contenido de `_build_convert_tab` a un frame independiente). Mantener funcionalidad idéntica.
- [x] 4.2 Migrar la sección Configuración al nuevo layout (mover contenido de `_build_settings_tab` a un frame independiente). Mantener sub-tabs General, Summarizer (IA) y Plantillas con funcionalidad idéntica.

## 5. Integración y limpieza

- [x] 5.1 Eliminar el CTkTabview principal y todo código relacionado con el layout anterior que ya no se use. Verificar que no queden referencias huérfanas.
- [x] 5.2 Verificar que el código pasa ruff y mypy strict. Corregir errores de tipo y formato.
- [ ] 5.3 Prueba manual completa: transcribir un archivo, escribir notas, generar resumen con notas, generar resumen sin notas, usar resumen standalone, convertir video, cambiar configuración, verificar status bar.
