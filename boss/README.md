# 🤖 Claude-Codex BOSS — orquestador de dos agentes

Implementa el **Patrón B** de la Guía Maestra v3: un agente implementa, otro revisa de
forma independiente, y los tests deciden. El BOSS coordina, limita y deja evidencia.
**Nunca hace merge, push ni despliegue**: el mejor resultado posible es
`AWAITING_APPROVAL`, y ahí decide el responsable humano.

```
contrato.json ──► nueva ──► TRIAGED ──► ejecutar
                                          │
          ┌───────────────────────────────┘
          ▼
   RUNNING: implementador en worktree aislado (rama boss/<id>)
          │  commit del BOSS + control de alcance
          ▼
   VALIDATING: comandos_validacion del contrato (deterministas)
          │
          ▼
   REVIEW: revisor en OTRO worktree, solo lectura, commit fijo → veredicto JSON
          │
          ├── tests OK + "aprobar" ──► AWAITING_APPROVAL (revisás la rama y decidís)
          ├── hallazgos ──► nueva iteración con SOLO esos hallazgos (máx. 3)
          └── fallo repetido / fuera de alcance / sin veredicto ──► BLOCKED
```

## Requisitos

- Python 3.8+ (solo librería estándar) y Git con soporte de worktrees.
- Los agentes que vayas a usar, instalados y autenticados según su documentación oficial:
  `claude` (Claude Code) y/o `codex` (Codex CLI).
- `.boss/` en el `.gitignore` del repositorio (el BOSS se niega a trabajar si no está).

## Uso

```bash
# 1. Escribí el contrato (copiá boss/contrato.ejemplo.json y editálo)
python3 boss/boss.py nueva mi-tarea.json

# 2. Ejecutá el ciclo
python3 boss/boss.py ejecutar T-001

# 3. Consultá el estado y la evidencia
python3 boss/boss.py estado T-001
ls .boss/tareas/T-001/            # contrato congelado, estado, eventos.jsonl, iter-N/

# 4. Si quedó en AWAITING_APPROVAL: revisá la rama y decidí vos
git diff main..boss/T-001

# 5. Al terminar, quitá los worktrees (la rama se conserva)
python3 boss/boss.py limpiar T-001
```

Por cada iteración queda en `.boss/tareas/<id>/iter-N/`: los prompts enviados, el log de
cada agente, la salida de la validación, el `diff.patch` revisado y el `veredicto.json`.

## Contrato

| Campo | Obligatorio | Qué es |
|---|---|---|
| `id` | sí | Letras, números, `.`, `_`, `-` (máx. 64) |
| `objetivo` | sí | Qué hay que lograr |
| `contexto` | no | Información mínima útil |
| `alcance` | sí | Rutas o patrones que se pueden modificar. Un cambio fuera → `BLOCKED` |
| `criterios_aceptacion` | sí | Lista verificable |
| `comandos_validacion` | sí | Comandos que deben salir con código 0. Se ejecutan **sin shell** (sin pipes ni `&&`) |
| `acciones_prohibidas` | no | Se le comunican al implementador |
| `implementador` / `revisor` | sí | Nombres de `agents.json`; tienen que ser distintos |
| `max_iteraciones` | sí | 1 a 3 |
| `timeout_segundos` | no | Por cada agente y comando (por defecto 1800, máx. 7200) |
| `rama_base` | no | Por defecto `HEAD` |

Al registrarlo, el contrato se congela con su hash SHA-256. Si alguien lo edita después,
`ejecutar` se niega a seguir.

## Agentes (`agents.json`)

Cada agente define un comando para `implementar` y otro para `revisar`. Se ejecutan sin
shell, en el worktree de la tarea, con el prompt por stdin. Los valores incluidos:

- **claude**: implementa con `--permission-mode acceptEdits` y revisa con
  `--permission-mode dontAsk --allowedTools Read Grep Glob` (solo lectura).
- **codex**: `codex exec --sandbox workspace-write -` para implementar y
  `--sandbox read-only -` para revisar.

Los flags se verificaron el 2026-10-27 contra `claude --help` 2.1.311, la documentación
oficial de Claude Code y `codex exec --help` de codex-cli 0.164.0. Codex todavía no se
ejecutó con una cuenta autenticada: corré `codex exec --help` en tu máquina y ajustá
`agents.json` si tu versión difiere.

## Instalar Codex CLI

Métodos oficiales del [README de openai/codex](https://github.com/openai/codex), que
coinciden con la Guía Maestra (sección 3 de la actualización 2.0). En Windows, la Guía
recomienda instalarlo dentro de WSL (Ubuntu), en la misma terminal donde usás Claude Code.

```bash
# Opción A — npm (requiere Node.js; sin sudo)
npm install -g @openai/codex

# Opción B — instalador oficial (Linux/macOS/WSL). Leé el script antes de ejecutarlo.
curl -fsSL https://chatgpt.com/codex/install.sh -o codex-install.sh
less codex-install.sh
sh codex-install.sh
```

En Windows nativo (PowerShell) el instalador oficial es `install.ps1`, desde la misma URL.

Después:

```bash
codex --version          # verificar la instalación
codex login              # "Sign in with ChatGPT" (plan Plus/Pro/Business/Edu/Enterprise)
codex login status       # debe decir que hay sesión iniciada
codex exec --help        # comparar los flags con boss/agents.json
```

Para usarlo con una API key en lugar de tu cuenta de ChatGPT:
`printenv OPENAI_API_KEY | codex login --with-api-key`. No pegues la clave en chats,
archivos del repo ni capturas. El acceso con ChatGPT y el acceso por API se facturan por
separado.

Primera prueba del BOSS con Codex, desde la raíz de este repo:

```bash
python3 boss/boss.py nueva boss/contrato.ejemplo.json   # Codex implementa, Claude revisa
python3 boss/boss.py ejecutar T-001
python3 boss/boss.py estado T-001
```

## Garantías y límites

- El implementador no puede ampliar su límite de iteraciones ni su alcance: ambos viven en
  el contrato congelado, fuera de su worktree.
- Si el revisor modifica archivos, la revisión se descarta (`BLOCKED`).
- Un "aprobado" del revisor no alcanza si la validación falla.
- Si un agente no devuelve un veredicto JSON válido, no se inventa la aprobación.
- Los textos del repo y los diffs se le pasan al revisor como **datos**, no como órdenes.
- No cubre todavía: fase de planificación automática, CI, ni ejecución en paralelo de
  varias tareas. Se agregan cuando exista un beneficio medible (Guía, Parte XIX).

## Tests

```bash
python3 boss/tests/test_boss.py    # 19 tests con agentes simulados, sin llamar a ningún modelo
```
