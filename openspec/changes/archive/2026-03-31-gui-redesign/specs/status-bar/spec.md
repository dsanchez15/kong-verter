## ADDED Requirements

### Requirement: Barra de estado inferior
La aplicación SHALL mostrar una barra de estado fija en la parte inferior de la ventana que muestre información del estado actual del sistema.

#### Scenario: Información visible al iniciar
- **WHEN** la aplicación se inicia
- **THEN** la barra de estado muestra el motor de transcripción activo, el modelo Whisper seleccionado y el estado de conexión de Ollama

#### Scenario: Actualización al cambiar configuración
- **WHEN** el usuario guarda cambios en la configuración (motor, modelo, o ajustes LLM)
- **THEN** la barra de estado se actualiza para reflejar los nuevos valores

### Requirement: Indicador de estado de Ollama
La barra de estado SHALL mostrar si Ollama está conectado o no disponible.

#### Scenario: Ollama disponible
- **WHEN** la detección de modelos de Ollama es exitosa
- **THEN** la barra de estado muestra un indicador de "Ollama: ✅ conectado"

#### Scenario: Ollama no disponible
- **WHEN** la detección de modelos de Ollama falla
- **THEN** la barra de estado muestra un indicador de "Ollama: ❌ no disponible"
