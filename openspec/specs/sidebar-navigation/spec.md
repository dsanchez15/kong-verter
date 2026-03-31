## Requirements

### Requirement: Navegación por sidebar vertical
La aplicación SHALL mostrar un sidebar fijo en el lado izquierdo con botones de navegación vertical para las secciones: Transcribir, Resumen, Convertir y Configuración. El sidebar SHALL permanecer visible en todo momento.

#### Scenario: Cambio de sección
- **WHEN** el usuario hace clic en un botón del sidebar
- **THEN** el panel de contenido muestra la sección correspondiente y el botón activo se resalta visualmente

#### Scenario: Preservación de estado al navegar
- **WHEN** el usuario cambia de sección y luego regresa a la sección anterior
- **THEN** el contenido de la sección anterior se mantiene intacto (texto, selecciones, progreso)

#### Scenario: Sección inicial
- **WHEN** la aplicación se inicia
- **THEN** la sección Transcribir se muestra como sección activa por defecto

### Requirement: Indicador visual de sección activa
El sidebar SHALL indicar visualmente cuál sección está activa mediante un color de fondo diferenciado en el botón correspondiente.

#### Scenario: Resaltado del botón activo
- **WHEN** el usuario selecciona una sección
- **THEN** el botón de esa sección muestra un color de fondo activo y los demás botones muestran el color por defecto
