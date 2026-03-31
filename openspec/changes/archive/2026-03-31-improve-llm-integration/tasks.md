# Tareas: Mejora de Integración LLM

## 🛠️ Refactorización del Núcleo (Engine)
- [x] 1. **Definir Infraestructura de Proveedores**: Crear una estructura modular en `summarizer.py` usando el patrón de proveedores para separar la lógica de Groq y Ollama.
- [x] 2. **Implementar Proveedor Ollama**: Mover la lógica de llamada a Ollama y asegurar que soporte la detección de modelos.
- [x] 3. **Implementar Proveedor Groq**: Mover la lógica de Cloud y añadir una validación explícita de `API_KEY`.

## 🖥️ Interfaz de Usuario (Settings)
- [x] 4. **Detección Dinámica de Modelos**: Crear función asíncrona en `gui.py` para cargar los modelos de Ollama al abrir la configuración.
- [x] 5. **Actualizar Controles de Ollama**: Reemplazar el campo de texto manual por un `CTkOptionMenu`.
- [x] 6. **Botón de Recarga**: Añadir un botón para forzar la sincronización con Ollama sin reiniciar la aplicación.
- [x] 7. **Indicadores de Validación**: Mostrar avisos visuales (colores/iconos) cuando falten configuraciones críticas en la pestaña de IA.

## ⚠️ Robustez y Gestión de Errores
- [x] 8. **Validación Pre-Ejecución**: En el hilo de generación del resumen, comprobar que el motor seleccionado está operativo antes de proceder.
- [x] 9. **Captura de Excepciones Específicas**: Manejar errores de red, claves inválidas y falta de modelos con `messagebox` informativos.

## 🧪 Pruebas y Verificación
- [x] 10. **Test de Ollama**: Verificar que se listan y seleccionan modelos correctamente.
- [x] 11. **Test de Groq**: Validar el flujo de error cuando no hay clave API.
- [x] 12. **Test de Persistencia**: Asegurar que los nuevos campos se guardan y cargan correctamente en `config.json`.
