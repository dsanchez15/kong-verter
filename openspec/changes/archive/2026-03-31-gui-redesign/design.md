## Context

Kong-verter actualmente usa un `CTkTabview` con 4 tabs horizontales (Transcribir, Resultado, Convertir, Configuración). Toda la lógica de UI vive en `gui.py` dentro de la clase `KonverterApp(ctk.CTk)`. El backend (summarizer, transcriber, config, template_manager, video_converter) expone interfaces estables que la GUI consume directamente.

La GUI actual tiene ~600 líneas. El rediseño reemplaza el layout de tabs por sidebar + paneles, agrega sub-tabs en Transcribir, y reorganiza el flujo de resumen.

```
LAYOUT ACTUAL                         LAYOUT PROPUESTO
════════════                          ════════════════

┌──────────────────────┐              ┌────┬───────────────────┐
│ [Tab1][Tab2][Tab3][4]│              │    │                   │
├──────────────────────┤              │ S  │   Panel de        │
│                      │              │ I  │   contenido       │
│   Contenido del      │              │ D  │   (cambia según   │
│   tab activo         │              │ E  │    sección)       │
│                      │              │ B  │                   │
│                      │              │ A  │                   │
│                      │              │ R  │                   │
└──────────────────────┘              ├────┴───────────────────┤
                                      │  Status bar            │
                                      └────────────────────────┘
```

## Goals / Non-Goals

**Goals:**
- Reemplazar TabView por sidebar + panel de contenido dinámico
- Implementar sub-tabs en Transcribir (Transcripción, Notas, Resultado IA)
- Agregar panel de notas opcionales que enriquecen el prompt del LLM
- Crear sección Resumen standalone para texto libre
- Agregar barra de estado inferior informativa
- Mantener toda la funcionalidad actual sin regresiones

**Non-Goals:**
- Cambiar de framework (se mantiene CustomTkinter)
- Modificar archivos del backend
- Implementar efectos visuales avanzados (sombras, gradientes, animaciones)
- Agregar iconos SVG o assets externos

## Decisions

### 1. Sidebar con CTkFrame + CTkButtons en lugar de CTkTabview

**Decisión**: Usar un `CTkFrame` fijo a la izquierda con `CTkButton`s apilados verticalmente. Cada botón cambia la visibilidad de frames de contenido usando `grid`/`grid_remove`.

**Alternativa considerada**: Usar `CTkSegmentedButton` vertical — no existe en CustomTkinter, habría que simularlo.

**Razón**: Es el patrón más simple y nativo en CTk. Los botones se pueden estilizar con `fg_color` para indicar la sección activa.

```
┌──────────────┐
│  Kong-verter │  ← Header/logo
├──────────────┤
│ 📝 Transcr.  │  ← CTkButton (fg_color activo)
│ ✨ Resumen   │  ← CTkButton
│ 🎬 Convertir │  ← CTkButton
│              │
│              │
│ ⚙️ Config    │  ← CTkButton (abajo)
└──────────────┘
```

### 2. Navegación por visibilidad de frames (grid/grid_remove)

**Decisión**: Crear todos los frames de contenido al inicio y alternar visibilidad con `grid()`/`grid_remove()`. El frame activo se muestra, los demás se ocultan.

**Alternativa considerada**: Destruir y recrear frames al cambiar de sección — más complejo, pierde estado (texto en notas, transcripción en curso).

**Razón**: Preserva el estado de cada sección. Si el usuario transcribe, va a Notas, y vuelve a Transcripción, el texto sigue ahí. Es el mismo patrón que CTkTabview usa internamente.

### 3. Sub-tabs en Transcribir con CTkTabview interno

**Decisión**: Usar un `CTkTabview` dentro del frame de Transcribir para los 3 sub-tabs (Transcripción, Notas, Resultado IA).

**Razón**: CTkTabview funciona bien para sub-navegación dentro de una sección. Es consistente con el patrón actual de sub-tabs en Configuración (General, Summarizer, Plantillas).

### 4. Notas se concatenan al prompt en la GUI, no en el Summarizer

**Decisión**: La GUI construye el prompt completo (`template + transcripción + notas`) y se lo pasa al `Summarizer` como texto ya armado. El Summarizer no sabe que existen notas.

**Alternativa considerada**: Modificar `Summarizer.summarize_stream()` para aceptar un parámetro `notes` — requiere cambiar el backend.

**Razón**: Mantiene el backend intacto. La GUI ya construye el texto que pasa al summarizer, solo se extiende esa lógica.

```python
# En _run_summarization del frame Transcribir:
text = transcripcion
if notas.strip():
    text += "\n\nNotas adicionales del usuario:\n" + notas
# Se pasa 'text' al summarizer como siempre
```

### 5. Sección Resumen como flujo independiente

**Decisión**: La sección Resumen tiene su propio textbox de entrada, selector de plantilla, botón generar, y textbox de resultado. No comparte estado con Transcribir.

**Razón**: Son flujos distintos. Transcribir parte de audio/video. Resumen parte de texto libre. Compartir estado crearía acoplamientos innecesarios.

### 6. Status bar con CTkFrame fijo abajo

**Decisión**: Un `CTkFrame` en `row=2` del grid principal con labels informativos: motor de transcripción, modelo Whisper, estado de Ollama.

**Razón**: Información útil siempre visible sin ocupar espacio en las secciones. Se actualiza al guardar configuración y al detectar/perder conexión con Ollama.

## Risks / Trade-offs

- **Reescritura de gui.py** → Es un cambio grande (~600 líneas). Mitigación: el backend no se toca, solo la capa de presentación. Se puede testear manualmente sección por sección.
- **Ancho de sidebar fijo** → En ventanas muy pequeñas podría comprimir el contenido. Mitigación: definir `minsize` adecuado y ancho de sidebar fijo (~160px).
- **Estado de Ollama en status bar** → Requiere polling o verificación periódica. Mitigación: verificar solo al inicio y cuando el usuario refresca modelos, no polling continuo.
