# 🛡️ Optimus Prime CarosIA

### Tu antivirus para Claude Code — bloquea skills y MCP maliciosos en tiempo real

Optimus Prime CarosIA es un agente de seguridad para Claude Code y Cowork. **Frena ataques antes de que se ejecuten:** un hook se mete delante de cada acción que hace Claude y bloquea el robo de credenciales, los dominios maliciosos conocidos (como `giftshop.club`, del backdoor de Postmark), las reverse shells y los `curl | bash`. Además incluye un escáner que revisa tus skills y MCP contra bases de datos de amenazas y detecta updates envenenados.

---



---

> ## ⚠️ La regla de oro: revisá toda skill o MCP antes de instalarla
>
> La razón por la que esto existe es que **las skills y los MCP no son confiables por default**. El 36% de las skills públicas tienen fallas de seguridad ([Snyk ToxicSkills 2025](https://snyk.io/blog/toxicskills-malicious-ai-agent-skills-clawhub/)) y ataques como el backdoor de Postmark ya filtraron los mails de miles de usuarios con una sola línea de código metida en un update.
>
> Antes de instalar **cualquier cosa** — incluso esto — hacé el hábito de:
>
> - **Abrí Claude y pedile que revise los archivos primero.** Una charla rápida: qué hace cada archivo, qué permisos pide, a qué servidores se conecta, y si el comportamiento coincide con lo que dice hacer. Si algo no cierra, frená.
> - **Chequeá la fuente oficial.** Compará los archivos contra el repo canónico. El historial de commits es tu registro de autoría — un zip de un desconocido no lo es.
> - **Leé el diff en cada update.** Que ayer estuviera limpio no garantiza que hoy lo esté. El ataque de Postmark llegó en la v1.0.16, después de quince versiones limpias.
>
> Optimus automatiza la parte de runtime una vez instalado — pero **la instalación es responsabilidad tuya**. Hacé ese hábito innegociable, siempre, para cada skill, cada MCP, cada update.

---

## Por qué

El ecosistema de skills de IA crece rápido — y los ataques también. El estudio [ToxicSkills de Snyk](https://snyk.io/blog/toxicskills-malicious-ai-agent-skills-clawhub/) encontró que **el 36% de las skills tienen fallas de seguridad**, incluidas 76 con payloads maliciosos confirmados. Y en septiembre 2025 el [incidente de Postmark MCP](https://thehackernews.com/2025/09/first-malicious-mcp-server-found.html) se volvió el ataque de cadena de suministro canónico del ecosistema: quince versiones limpias seguidas de un update de una línea que mandaba en copia oculta cada mail saliente a `phan@giftshop.club`.

Un escaneo estático de la v1.0.15 no habría encontrado nada — estaba limpia. Ese es el agujero que tapa la protección en tiempo real.

## Capa 1 — Bloqueo en tiempo real (lo principal)

Un **hook PreToolUse** corre antes de cada acción de Claude. Inspecciona la acción contra una librería local de indicadores de compromiso (IOCs) más tu allowlist, y decide permitir o bloquear:

- **Rutas sensibles** — lecturas de `~/.ssh/`, `~/.aws/`, `~/.env`, `credentials.json`, `/etc/shadow` se bloquean.
- **Dominios maliciosos conocidos** — hardcodeados de incidentes confirmados. `giftshop.club` viene por default y no se puede poner en la allowlist.
- **Servicios de exfiltración** — pastebin.com, transfer.sh, webhook.site, requestbin, ngrok, serveo, URLs con IP cruda.
- **Comandos peligrosos** — `curl … | bash`, `nc -e`, `bash -i >& /dev/tcp/…`, cadenas base64 | curl, agregados a `.bashrc`.
- **Variables de entorno sensibles** — `ANTHROPIC_API_KEY`, `AWS_SECRET_ACCESS_KEY`, `GITHUB_TOKEN`, `DATABASE_URL`, y los patrones genéricos `*_API_KEY` / `*_SECRET` / `*_TOKEN` / `*_PASSWORD`.

**Cero costo de IA.** Es Python local puro (~30–80 ms por acción). Solo las acciones bloqueadas agregan un mensaje corto a la conversación.

**Fail-open.** Si falta el archivo de IOCs, el stdin viene mal, o el hook crashea — todo cae por default en `permitir`. El hook nunca rompe Claude Code.

**Allowlist.** Los falsos positivos legítimos van en `.security/optimus-allowlist.json` (proyecto) o `~/.claude/optimus-allowlist.json` (global). Los dominios maliciosos confirmados no se pueden sobreescribir.

## Capa 2 — Escaneo estático (incluido)

1. **Inteligencia de amenazas** — chequea cada skill y MCP instalado contra 6 bases vivas mantenidas por la comunidad: GitHub Advisory DB, vulnerablemcp.info, mcpscan.ai, Snyk, ClawHub/VirusTotal y Reddit r/ClaudeAI.
2. **Verificación de integridad de la fuente** — antes de instalar una skill, busca el original oficial y lo compara con tu copia. Si alguien agarró una skill confiable, le metió código malicioso y la redistribuyó, Optimus caza la diferencia.
3. **Análisis de coherencia** — analiza si todo lo que hace una skill coincide con lo que dice hacer. ¿Un optimizador de tokens que quiere leer tus claves SSH? ¿Un formateador de markdown que manda tus credenciales afuera? Optimus marca el desajuste.
4. **Detección de diffs en updates** — guarda un snapshot de cada skill. Si un update cambia algo, lo diffea y analiza la coherencia del código nuevo. Así caza los ataques de cadena de suministro.
5. **Monitoreo programado** — re-escanea todo cada mañana. Una skill segura ayer puede tener un CVE nuevo hoy.

---

## Instalación — paso a paso

### Requisitos

- Claude Code CLI **o** la app de escritorio de Claude con modo Cowork
- Python 3.8+ (para el hook de tiempo real)
- `jq` (para el script de instalación — suele venir preinstalado en macOS, `apt install jq` en Linux)
- Git (solo si querés clonar el repo en vez de bajar el zip)

Verificá con:

```bash
python3 --version
jq --version
```

### Método 1 — Bajar el ZIP (el más fácil)

1. Tocá el botón verde **Code** arriba en este repo → **Download ZIP**.
2. Descomprimilo.
3. Copiá la carpeta descomprimida a:
   - `~/.claude/skills/optimus-prime-carosia/` — para usarlo en todos tus proyectos
   - `.claude/skills/optimus-prime-carosia/` — solo para el proyecto actual
4. Seguí con "Activar el hook de tiempo real" más abajo.

### Método 2 — Clonar el repo

```bash
# 1. Clonar
git clone https://github.com/FIBONACCI38/optimus-prime-carosIA.git
cd optimus-prime-carosIA

# 2. Instalar como skill global
mkdir -p ~/.claude/skills/optimus-prime-carosia
cp -R . ~/.claude/skills/optimus-prime-carosia/

# 3. O instalar solo para el proyecto actual
mkdir -p .claude/skills/optimus-prime-carosia
cp -R . .claude/skills/optimus-prime-carosia/
```

### Activar el hook de tiempo real

El hook es lo que te da el bloqueo en vivo. **Sin él, solo tenés el escáner estático.**

**Global (recomendado)** — corre en todos los proyectos. Se puede ejecutar desde cualquier carpeta:

```bash
bash ~/.claude/skills/optimus-prime-carosia/hooks/install_hooks.sh --user
```

**Solo para un proyecto** — el script escribe en `.claude/settings.json` de la carpeta **desde la que lo ejecutás** (`$(pwd)`), así que corrélo desde la raíz de **tu proyecto**, no desde la carpeta de la skill:

```bash
cd /ruta/a/tu-proyecto
bash .claude/skills/optimus-prime-carosia/hooks/install_hooks.sh --project
```

El script:
- Hace backup de tu `~/.claude/settings.json` actual a `*.optimus.bak.<timestamp>`
- Agrega el hook `PreToolUse` apuntando a `optimus_preflight.py`
- Verifica que estén Python y `jq`
- Imprime una confirmación con la ruta instalada

### Verificar la instalación

```bash
# 1. Confirmar que el hook quedó registrado
jq '.hooks.PreToolUse' ~/.claude/settings.json      # instalación --user
jq '.hooks.PreToolUse' .claude/settings.json        # instalación --project (desde la raíz del proyecto)

# 2. Correr los tests
cd ~/.claude/skills/optimus-prime-carosia
python3 tests/test_hook.py      # hook: tenés que ver "20/20 passed"
bash tests/test_install.sh      # instalador: tenés que ver "5/5 passed"
```

Si algo falla, la instalación no quedó limpia.

### Desinstalar

```bash
bash ~/.claude/skills/optimus-prime-carosia/hooks/uninstall_hooks.sh --user
# o, desde la raíz de tu proyecto:
bash .claude/skills/optimus-prime-carosia/hooks/uninstall_hooks.sh --project

rm -rf ~/.claude/skills/optimus-prime-carosia
```

El script de desinstalación **no** restaura el backup: quita solo las entradas del hook de Optimus y deja intactos tus otros hooks. Los backups `settings.json.optimus.bak.<timestamp>` que creó el instalador quedan en la misma carpeta por si querés volver a un estado anterior a mano.

---

## Cómo se usa

Simplemente hablale a Claude:

- *"Escaneá mi proyecto por temas de seguridad"*
- *"¿Es seguro instalar este MCP?"*
- *"Fijate si esta skill fue manipulada"*
- *"Hacé una auditoría de seguridad"*

Optimus se activa solo cuando detecta que estás por instalar algo o cuando mencionás temas de seguridad.

## Cómo funciona

Optimus Prime CarosIA es una skill de Claude — un archivo `.md` con instrucciones que le dicen a Claude cómo actuar de agente de seguridad. El **escáner estático** usa las herramientas nativas de Claude (WebSearch, Read, Write, Bash, Glob, Grep) para escanear archivos, buscar en bases de datos y generar reportes. Sin dependencias externas, sin API keys, sin infraestructura.

El **hook de tiempo real** es un script de Python local (`hooks/optimus_preflight.py`) que Claude Code ejecuta antes de cada acción. Lee la acción por stdin, la compara contra la librería de IOCs (`references/iocs.json`) más tu allowlist, y devuelve una decisión permitir/bloquear por stdout. Sin IA, sin llamadas de red.

Todo el análisis pasa local + búsquedas web públicas (para el escaneo estático). Tu código y tus credenciales nunca salen de tu máquina.

## Benchmarks (del proyecto original)

### Hook de tiempo real (20 casos de regresión en `tests/test_hook.py`)

| Categoría | Casos | Resultado |
|---|---|---|
| Acciones benignas correctamente permitidas | 5 | ✅ 5/5 |
| Ataques de robo de credenciales bloqueados | 4 | ✅ 4/4 |
| Exfiltración de red bloqueada (incl. el IOC `giftshop.club` de Postmark) | 4 | ✅ 4/4 |
| Comandos peligrosos bloqueados (`curl\|bash`, reverse shell, hijack de `.bashrc`) | 4 | ✅ 4/4 |
| Fail-open ante input vacío / malformado | 3 | ✅ 3/3 |
| **Total** | **20** | **✅ 20/20** |

Overhead: ~30–80 ms por acción. Cero tokens de IA en operación normal.

---

## Legal y atribución

Este proyecto está licenciado bajo la [Licencia MIT](./LICENSE).



Si redistribuís esto, en parte o entero, tenés que mantener el aviso de copyright del archivo LICENSE intacto y mencionar al autor original.

### Disclaimer

Este software se provee "tal cual", sin garantía de ningún tipo. Optimus Prime CarosIA ayuda a detectar amenazas potenciales, pero no garantiza la detección de todas las vulnerabilidades o código malicioso. Las decisiones de seguridad son responsabilidad del usuario.

### Marcas

"MCP Sentinel" es el nombre elegido por su autor original. GitHub, Claude, Anthropic, Snyk y otros nombres de productos mencionados son marcas de sus respectivos dueños.

---

Adaptado con cariño por **francisco.carosIA** · Motor original por [@soy-rafa](https://github.com/soy-rafa)
