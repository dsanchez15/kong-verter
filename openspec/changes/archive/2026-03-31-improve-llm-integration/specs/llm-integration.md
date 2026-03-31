# Especificación: Mejora de Integración LLM

## Requerimientos Funcionales
1. **Detección de Modelos (Ollama)**:
   - La aplicación debe obtener la lista de modelos instalados mediante la API de Ollama.
   - Si la API no responde, debe mostrar un mensaje de error o aviso en la UI.
   - El usuario debe poder seleccionar un modelo de una lista desplegable.
2. **Validación de Credenciales (Groq)**:
   - El motor Groq solo debe estar habilitado si existe una clave API.
   - Si se intenta usar sin clave, se debe bloquear la ejecución con un mensaje claro.
3. **Soporte Multi-Motor**:
   - El sistema debe estar preparado para admitir nuevos proveedores de LLM sin cambios estructurales profundos.

## Casos de Uso
1. **Selección de Modelo Local**: El usuario abre ajustes, ve la lista de sus modelos de Ollama ("llama3", "mistral", etc.) y selecciona uno. Se guarda en el config.
2. **Error de Conexión**: Ollama está apagado. El usuario ve "Servicio Ollama no disponible" en el menú de selección.
3. **Falta de API Key**: El usuario selecciona Groq sin clave. Al intentar generar un resumen, la app le avisa: "Por favor, introduce tu clave API de Groq en Ajustes".

## Criterios de Aceptación
- La lista de modelos de Ollama se actualiza correctamente.
- La aplicación no se congela al buscar modelos (uso de threading).
- Los errores de API se capturan y se muestran como notificaciones (toasts/messageboxes).
