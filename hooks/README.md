# Optimus Prime CarosIA — Hook de protección en tiempo real

Esta carpeta contiene la capa de protección que corre en vivo.

## Qué hace

Registra un **hook PreToolUse** en Claude Code. Antes de cada acción que una skill o un MCP intenta hacer, el hook la inspecciona contra la librería `references/iocs.json` (rutas sensibles, dominios maliciosos conocidos, comandos peligrosos, exfiltración de env vars). Las acciones sospechosas se bloquean o marcan en tiempo real — antes de ejecutarse.

## Costo

Cero tokens de IA en operación normal. Es un script de Python local que corre en ~30–80 ms por acción. Una acción bloqueada o marcada agrega un mensaje corto a la conversación (tokens despreciables, solo cuando se dispara).

## Instalar

```bash
# Global para tu usuario (se puede correr desde cualquier carpeta)
bash <carpeta-de-la-skill>/hooks/install_hooks.sh --user

# Solo para un proyecto: correr desde la raíz de ESE proyecto,
# porque el script escribe en $(pwd)/.claude/settings.json
bash <carpeta-de-la-skill>/hooks/install_hooks.sh --project
```

La instalación es idempotente: correrla varias veces deja una sola entrada de Optimus y no duplica ni borra tus otros hooks (lo verifica `tests/test_install.sh`).

## Desinstalar

```bash
bash <carpeta-de-la-skill>/hooks/uninstall_hooks.sh --user
# o, desde la raíz del proyecto
bash <carpeta-de-la-skill>/hooks/uninstall_hooks.sh --project
```

## Allowlist

Los falsos positivos se pueden whitelistear en `.security/optimus-allowlist.json`:

```json
{
  "paths": ["/home/me/project/.env.local"],
  "domains": ["api.mytrustedservice.com"],
  "commands": ["curl -X POST https://api.mytrustedservice.com/webhook"]
}
```

## Archivos

- `optimus_preflight.py` — el hook. Lee la acción por stdin, devuelve la decisión en JSON.
- `install_hooks.sh` — registra el hook en la config de Claude Code.
- `uninstall_hooks.sh` — saca el hook.
