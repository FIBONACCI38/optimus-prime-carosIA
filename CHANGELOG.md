# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/). Versionado [semver](https://semver.org/).

---

## Optimus Prime CarosIA — Rebrand

### [Sin publicar]

#### Corregido

- **Instalador duplicaba hooks ajenos.** `install_hooks.sh` usaba `select(.hooks[]?.command != $cmd)`,
  que emite una entrada por cada hook que no coincide: una entrada del usuario con dos hooks se
  duplicaba en cada instalación (crecimiento exponencial). Ahora quita solo los hooks de Optimus
  y conserva el resto exactamente una vez.
- **README: guía de instalación.** URL de `git clone` apuntaba a otra cuenta; `--project` se
  documentaba "desde la carpeta de la skill", pero el script escribe en `$(pwd)/.claude/settings.json`;
  se afirmaba que el desinstalador restaura el backup, y no lo hace.

#### Agregado

- `tests/test_install.sh` — 5 tests de regresión del instalador/desinstalador.
- `CLAUDE.md` y `AGENTS.md` — instrucciones de proyecto para Claude Code y Codex.
- `entrada-boss/` — carpeta de entrada de recursos para el flujo Claude-Codex BOSS.
- `.gitignore` — evita versionar secretos, estado local y backups.

### [2.0.0-carosia] — 2026-06-05

Versión rebrandeada y adaptada al español de **MCP Sentinel**, por Francisco Carosia
(*francisco.carosIA*). El motor, la lógica de detección y los tests son íntegramente
de Rafael Tunón Sánchez ([@soy-rafa](https://github.com/soy-rafa)); esta versión solo
cambia identidad, idioma de la documentación y empaquetado, bajo licencia MIT.

#### Cambiado

- **Marca.** "MCP Sentinel" → "Optimus Prime CarosIA" en toda la documentación y los mensajes.
- **README.md** reescrito en español, con créditos prominentes al autor original.
- **Hook renombrado.** `hooks/sentinel_preflight.py` → `hooks/optimus_preflight.py`.
- **Archivos de estado renombrados:**
  - allowlist: `sentinel-allowlist.json` → `optimus-allowlist.json`
  - base de amenazas: `mcp-sentinel-threats.json` → `optimus-threats.json`
  - backup del instalador: `*.sentinel.bak` → `*.optimus.bak`
- **Carpeta de la skill:** `mcp-sentinel/` → `optimus-prime-carosia/`.
- **LICENSE** conserva el copyright original de Rafael Tunón Sánchez y suma la línea
  de modificaciones de Francisco Carosia.

#### Sin cambios

- Toda la lógica de detección, los 20 tests de regresión, la librería de IOCs y el
  comportamiento del hook son idénticos al original.

---

## Historial del proyecto original (MCP Sentinel, por @soy-rafa)

> Estas entradas documentan las releases originales de **MCP Sentinel** antes del rebrand.
> En este repo, los archivos mencionados como `sentinel_preflight.py` /
> `mcp-sentinel-threats.json` corresponden hoy a `optimus_preflight.py` /
> `optimus-threats.json`.

### [2.0.0] — 2026-04-17

Esta release convierte a Sentinel de un analizador estático en un guardia de tiempo real.
El escáner v1 queda intacto — v2 le suma encima un hook de protección en vivo.

#### Agregado

- **Hook PreToolUse (`hooks/sentinel_preflight.py`).** Un script de Python que Claude Code
  corre antes de cada acción. La inspecciona contra una librería local de IOCs y la allowlist
  del usuario, devuelve una decisión permitir/bloquear por stdout. Cero tokens de IA en
  operación normal.
- **Librería de IOCs (`references/iocs.json`).** ~60 patrones en cinco categorías: rutas
  sensibles, env vars sensibles, destinos de red sospechosos, comandos peligrosos y frases
  de prompt injection. Incluye dominios maliciosos hardcodeados de incidentes confirmados —
  el `giftshop.club` del backdoor de Postmark viene por default.
- **Scripts de instalación/desinstalación (`hooks/install_hooks.sh`, `hooks/uninstall_hooks.sh`).**
  Idempotentes, validan JSON, hacen backup con timestamp de `settings.json` y preservan
  cualquier otro hook PreToolUse que el usuario ya tenga. Soportan `--user` y `--project`.
- **Soporte de allowlist de usuario.** `.security/sentinel-allowlist.json` (proyecto) o
  `~/.claude/sentinel-allowlist.json` (global). Los IOCs maliciosos confirmados no se
  pueden sobreescribir.
- **Suite de tests de regresión (`tests/test_hook.py`).** 20 casos que cubren permisos
  benignos, cuatro categorías de ataque y casos borde de fail-open. Todos pasan en release.

#### Cambiado

- **SKILL.md.** Nueva sección de protección en tiempo real.
- **README.md.** Reescrito alrededor del bloqueo en vivo y el incidente de Postmark.
- **Modelo de fallo.** Cualquier fallo de v2 cae en `allow` — el hook nunca rompe Claude Code.

### [1.0.0] — 2026-04-12

Release pública inicial.

#### Agregado

- SKILL.md con escaneo de inteligencia de amenazas, verificación de integridad de fuente,
  análisis de coherencia, detección de diffs en updates y monitoreo programado.
- `references/threat-sources.md` — lista de referencia de bases de datos de vulnerabilidades.
- `references/threat-db-template.json` — esquema de la base de amenazas local.
- Licencia MIT.
