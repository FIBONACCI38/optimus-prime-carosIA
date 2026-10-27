#!/usr/bin/env python3
"""Agente simulado para los tests del BOSS. No llama a ningún modelo.

Uso: fake_agent.py <modo>. Lee el prompt por stdin y actúa en el cwd (worktree).
"""
import sys
from pathlib import Path

modo = sys.argv[1]
prompt = sys.stdin.read()
destino = Path("src/feature.txt")


def escribir(texto, ruta=destino):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto)


if modo == "impl-ok":
    escribir("ok\n")
elif modo == "impl-corrige":
    # Primera iteración mal; si recibe hallazgos ("CORRIGE"), lo arregla.
    escribir("ok\n" if "CORRIGE" in prompt else "mal\n")
elif modo == "impl-siempre-mal":
    escribir("mal\n")
elif modo == "impl-nada":
    pass
elif modo == "impl-fuera":
    escribir("ok\n")
    escribir("intruso\n", Path("README.md"))
elif modo == "impl-falla":
    sys.exit(3)
elif modo == "rev-inteligente":
    contenido = destino.read_text() if destino.exists() else ""
    if contenido.strip() == "ok":
        print('Revisado.\n```json\n{"decision": "aprobar", "hallazgos": []}\n```')
    else:
        print('```json\n{"decision": "cambios", "hallazgos": [{"severidad": "alta", '
              '"archivo": "src/feature.txt", "descripcion": "debe contener ok"}]}\n```')
elif modo == "rev-aprueba":
    print('```json\n{"decision": "aprobar", "hallazgos": []}\n```')
elif modo == "rev-basura":
    print("todo funciona, confía en mí")
elif modo == "rev-escribe":
    escribir("manipulado\n")
    print('```json\n{"decision": "aprobar", "hallazgos": []}\n```')
else:
    sys.exit(f"modo desconocido: {modo}")
