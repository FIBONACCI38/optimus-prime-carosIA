# Modelo operativo: Claude Code + Codex

## Objetivo
Permitir trabajo asistido por agentes con cambios revisables, pruebas reproducibles y permisos proporcionales al riesgo. La autonomía nunca sustituye la autorización ni la validación determinista.

## Responsabilidades
- **Claude Code:** exploración contextual del repositorio, planificación, cambios delimitados y soporte a revisión.
- **OpenAI Codex:** implementación/reparación o revisión independiente de tareas acotadas.
- **Validadores deterministas:** pruebas, lint, análisis estático y comprobaciones de configuración.
- **Persona responsable:** aprobación de cambios de alto impacto, seguridad, publicación y efectos externos.
- **MCP:** interfaz de herramientas/contexto; no es un modelo de autorización por sí mismo.

Los nombres anteriores describen roles operativos; no presuponen que una herramienta o plan tenga todas las funciones habilitadas.

## Flujo recomendado (Duet)
1. Registrar objetivo, alcance, criterio de aceptación, riesgo y límites.
2. Un agente propone el plan y los archivos esperados.
3. Revisar el plan antes de implementar si el cambio afecta seguridad o datos.
4. Un único agente escribe en la rama de trabajo.
5. El segundo agente revisa el diff y la evidencia sin asumir que el resumen del primero es correcto.
6. Ejecutar pruebas y escaneos deterministas.
7. Si falla, permitir como máximo 3 ciclos de reparación; cada ciclo debe responder a evidencia nueva.
8. Pedir aprobación humana antes de merge, despliegue o acción externa de alto impacto.
9. Registrar el resultado y los riesgos residuales.

## Contrato de tarea
Cada tarea debería definir:
- Identificador de tarea y responsable;
- objetivo y criterio de aceptación;
- rama y commit base;
- rutas autorizadas y prohibidas;
- comandos de prueba permitidos;
- presupuesto de tiempo/uso;
- riesgos y aprobaciones necesarias;
- artefactos y evidencia de terminación;
- condición de cancelación y criterio de escalamiento.

## Loop autónomo acotado
Modelo de estados recomendado:

RECEIVED -> TRIAGED -> PLANNED -> EXECUTING -> VALIDATING -> REVIEWING -> COMPLETED

Estados alternativos: WAITING_FOR_HUMAN, RETRY_WAIT, FAILED, CANCELLED.

Límites obligatorios:
- número máximo de iteraciones, herramientas y duración;
- timeout por operación y cancelación;
- reintentos solo para fallos transitorios, con backoff;
- idempotencia para efectos secundarios;
- registro de cada transición;
- escalamiento si falta evidencia o se necesita más permiso.

No se debe permitir que el agente cambie sus propios permisos, las reglas de aprobación, el presupuesto o los controles del workflow en la misma ejecución.

## Trabajo en paralelo
Por defecto, un escritor por árbol de trabajo. Si dos tareas son independientes, usar ramas/worktrees separados e integrar mediante revisión. No compartir carpetas mutables ni bases de datos entre agentes paralelos sin aislamiento.

## Criterios de aceptación
- El cambio responde al objetivo declarado.
- Las pruebas pertinentes se ejecutaron y se registraron sus resultados.
- El revisor examinó el diff real.
- Se documentaron limitaciones y riesgos no resueltos.
- Ningún resultado se declara exitoso sin confirmación observable.
