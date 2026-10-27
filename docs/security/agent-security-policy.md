# Política de seguridad para agentes

## Activos
Código y releases; reglas de detección; credenciales; archivos del usuario; configuraciones de Claude Code/Cowork; servidores MCP; integridad de skills y dependencias; logs y evidencia de revisión.

## Amenazas mínimas
- Prompt injection directa o indirecta mediante archivos, issues, páginas, correos o salida de herramientas.
- Exfiltración de secretos a través de logs, solicitudes de red, repositorios o respuestas.
- Abuso de permisos del agente, herramientas MCP o shell.
- Skills, paquetes, plugins o servidores MCP comprometidos.
- Cambios que debiliten silenciosamente detecciones o permitan una ejecución antes bloqueada.
- Falsificación de pruebas, resultados o resúmenes.
- Reintentos duplicados, loops sin límite y consumo excesivo.
- Confusión entre entornos de prueba y producción.
- Cambios de política sin revisión independiente.

## Controles
1. **Mínimo privilegio:** acceso de lectura por defecto; separar permisos de escritura y ejecución.
2. **Aislamiento:** usar sandbox/entorno de prueba sin credenciales de producción.
3. **Validación:** validar entradas y salidas de herramientas; restringir dominios y comandos según el diseño real.
4. **No confianza implícita:** revisar procedencia, permisos, dependencias y cambios de cada skill/MCP.
5. **Fail-safe:** documentar el criterio fail-open/fail-closed. No cambiarlo sin análisis y pruebas.
6. **Secretos:** no incluir tokens en código, archivos de configuración versionados, prompts ni logs.
7. **Trazabilidad:** guardar task ID, commit base, agente/versión si se conoce, herramientas, pruebas, aprobaciones y resultado, minimizando datos sensibles.
8. **Límites de ejecución:** timeouts, cuotas, iteraciones finitas, cancelación y prevención de acciones duplicadas.
9. **Revisión independiente:** pruebas deterministas y revisión del diff antes de integrar.
10. **Recuperación:** procedimiento de rollback, respuesta a incidentes y revocación de credenciales.

## Pruebas seguras
- Usar strings inertes y fixtures controlados para simular comandos sospechosos.
- No ejecutar reverse shells, malware, cargas de exfiltración ni instrucciones destructivas.
- No hacer escaneos contra dominios o sistemas de terceros sin autorización.
- En las pruebas, verificar tanto detección correcta como falsos positivos y falsos negativos.

## Cambios sensibles
Todo cambio en hooks, reglas de bloqueo, allowlists/denylists, parsing de comandos, validaciones de MCP, gestión de secretos o política fail-open/fail-closed debe incluir:
- explicación de la amenaza y del impacto;
- prueba de regresión para el comportamiento permitido y bloqueado;
- revisión independiente del diff;
- actualización de documentación/changelog;
- aprobación humana antes de publicar si modifica el nivel de protección.

## Respuesta a incidente
1. Detener el flujo afectado y deshabilitar la herramienta comprometida.
2. Preservar logs relevantes sin replicar secretos.
3. Revocar/rotar credenciales afectadas.
4. Identificar alcance, cambios y posibles accesos a datos.
5. Corregir y probar en entorno aislado.
6. Publicar únicamente con revisión y comunicar el impacto conocido.
