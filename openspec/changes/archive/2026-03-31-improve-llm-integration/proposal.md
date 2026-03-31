# Propuesta: Mejora de Integración LLM y Escalabilidad

## Resumen
Mejorar la experiencia de usuario y la robustez de la aplicación al integrar modelos LLM (Ollama y Cloud). Actualmente, la selección de modelos de Ollama es manual, y la gestión de errores ante la falta de claves API de servicios en la nube (como Groq) es insuficiente.

## Motivación
El usuario tiene varios modelos de Ollama instalados localmente, pero la aplicación no los detecta automáticamente, lo que obliga a escribirlos manualmente. Además, si se selecciona un motor en la nube sin una clave API configurada, la aplicación genera un error genérico ("ValueError") en lugar de guiar al usuario.

## Objetivos
1. **Detección Automática**: Listar dinámicamente los modelos de Ollama disponibles en el sistema local.
2. **Validación de Conectividad**: Añadir una función de "Prueba de Conexión" para validar tanto Ollama como servicios en la nube.
3. **Gestión de Errores Amigable**: Mostrar mensajes claros en la interfaz de usuario cuando falten configuraciones críticas.
4. **Arquitectura Extensible**: Refactorizar el motor de LLM (`summarizer.py`) para que sea más fácil añadir nuevos proveedores (OpenAI, Gemini, etc.) en el futuro.

## Impacto
- **Archivos Afectados**:
  - `summarizer.py`: Refactorización de la lógica de llamadas a LLM.
  - `gui.py`: Actualización de la pestaña de configuración y lógica de validación.
  - `config.py`: Pequeñas adiciones para soportar estados de validación o cachés de modelos.
- **Nuevas Dependencias**: Ninguna (se seguirán usando `ollama` y `groq`).

## Riesgos y Mitigaciones
- **Ollama no iniciado**: El listado de modelos fallará si el servicio no corre. Se mitigará detectando el error y sugiriendo iniciar Ollama.
- **Latencia**: El listado de modelos puede tardar un poco. Se realizará de forma asíncrona o al abrir la configuración.
