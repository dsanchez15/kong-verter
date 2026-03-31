## ADDED Requirements

### Requirement: Panel de notas en sección Transcribir
La sección Transcribir SHALL contener 3 sub-tabs: Transcripción, Notas y Resultado IA. El sub-tab Notas SHALL proporcionar un área de texto editable donde el usuario puede escribir notas opcionales.

#### Scenario: Escritura de notas
- **WHEN** el usuario navega al sub-tab Notas dentro de Transcribir
- **THEN** se muestra un área de texto editable donde puede escribir libremente

#### Scenario: Notas vacías no afectan el resumen
- **WHEN** el usuario genera un resumen sin haber escrito notas
- **THEN** el prompt enviado al LLM contiene solo la plantilla y la transcripción, sin texto adicional de notas

### Requirement: Integración de notas en el prompt del LLM
Cuando el usuario genera un resumen desde la sección Transcribir, el sistema SHALL concatenar las notas (si existen) al prompt enviado al LLM junto con la transcripción y la plantilla seleccionada.

#### Scenario: Resumen con notas
- **WHEN** el usuario ha escrito notas y hace clic en "Generar Resumen" en el sub-tab Resultado IA
- **THEN** el prompt enviado al LLM incluye la plantilla, la transcripción y las notas del usuario

#### Scenario: Resumen sin notas
- **WHEN** el área de notas está vacía y el usuario hace clic en "Generar Resumen"
- **THEN** el prompt enviado al LLM incluye solo la plantilla y la transcripción

### Requirement: Controles de generación en sub-tab Resultado IA
El sub-tab Resultado IA dentro de Transcribir SHALL contener: selector de plantilla, checkbox de traducción, botón "Generar Resumen", área de texto con resultado en streaming, y botones de copiar y guardar.

#### Scenario: Generación de resumen desde Resultado IA
- **WHEN** el usuario hace clic en "Generar Resumen" en el sub-tab Resultado IA
- **THEN** el sistema genera el resumen usando la transcripción actual, las notas (si hay), la plantilla seleccionada y la opción de traducción

#### Scenario: Validación de transcripción previa
- **WHEN** el usuario intenta generar un resumen sin haber transcrito primero
- **THEN** el sistema muestra un mensaje indicando que primero debe transcribir un archivo
