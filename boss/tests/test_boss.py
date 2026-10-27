#!/usr/bin/env python3
"""Tests del orquestador Claude-Codex BOSS con agentes simulados.

Cada test crea un repositorio Git temporal; nunca se llama a un modelo real.
Ejecutar: python3 boss/tests/test_boss.py
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import boss  # noqa: E402

FAKE = str(AQUI / "fake_agent.py")
CHECK = "import sys; from pathlib import Path; p = Path('src/feature.txt'); " \
        "sys.exit(0 if p.exists() and p.read_text().strip() == 'ok' else 1)\n"


def sh(cwd, *args):
    subprocess.run(list(args), cwd=cwd, check=True, capture_output=True)


class BossTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        sh(self.repo, "git", "init", "-q", "-b", "main")
        (self.repo / "README.md").write_text("demo\n")
        (self.repo / "check.py").write_text(CHECK)
        (self.repo / ".gitignore").write_text(".boss/\n")
        sh(self.repo, "git", "add", "-A")
        sh(self.repo, "git", "-c", "user.name=t", "-c", "user.email=t@t",
           "commit", "-q", "-m", "init")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def contrato(self, **cambios):
        c = {
            "id": "T-1",
            "objetivo": "Crear src/feature.txt con el texto ok",
            "alcance": ["src/"],
            "criterios_aceptacion": ["src/feature.txt contiene ok"],
            "comandos_validacion": [f"{sys.executable} check.py"],
            "implementador": "impl",
            "revisor": "rev",
            "max_iteraciones": 3,
            "rama_base": "main",
            "timeout_segundos": 60,
        }
        c.update(cambios)
        return c

    def correr(self, impl, rev, **cambios):
        ruta_c = self.tmp / "contrato.json"
        ruta_c.write_text(json.dumps(self.contrato(**cambios)))
        agentes = {
            "impl": {"implementar": {"cmd": [sys.executable, FAKE, impl]},
                     "revisar": {"cmd": [sys.executable, FAKE, "rev-aprueba"]}},
            "rev": {"implementar": {"cmd": [sys.executable, FAKE, "impl-nada"]},
                    "revisar": {"cmd": [sys.executable, FAKE, rev]}},
        }
        ruta_a = self.tmp / "agents.json"
        ruta_a.write_text(json.dumps(agentes))
        tarea = boss.nueva_tarea(self.repo, ruta_c)
        self.assertEqual(tarea.leer_estado()["estado"], "TRIAGED")
        return boss.ejecutar_tarea(self.repo, "T-1", ruta_a)

    # --- contrato ---------------------------------------------------------
    def test_contrato_valido(self):
        self.assertEqual(boss.validar_contrato(self.contrato()), [])

    def test_contrato_rechaza_limites_y_campos(self):
        errores = boss.validar_contrato(self.contrato(
            max_iteraciones=5, revisor="impl", id="../x", extra=1, comandos_validacion=[]))
        texto = " ".join(errores)
        for esperado in ("max_iteraciones", "revisor", "'id'", "extra", "comandos_validacion"):
            self.assertIn(esperado, texto)

    def test_alcance(self):
        self.assertEqual(boss.fuera_de_alcance(["src/a.py", "README.md"], ["src/"]), ["README.md"])
        self.assertEqual(boss.fuera_de_alcance(["docs/x.md"], ["docs/*.md"]), [])

    def test_resolver_ejecutable(self):
        r = boss.resolver_ejecutable(["git", "--version"])
        self.assertTrue(Path(r[0]).is_absolute())
        self.assertEqual(r[1:], ["--version"])
        self.assertEqual(boss.resolver_ejecutable(["no-existe-xyz"]), ["no-existe-xyz"])

    def test_veredicto(self):
        self.assertIsNone(boss.parsear_veredicto("todo bien"))
        v = boss.parsear_veredicto('x\n```json\n{"decision": "cambios", "hallazgos": [1, {"a": 1}]}\n```')
        self.assertEqual(v["decision"], "cambios")
        self.assertEqual(v["hallazgos"], [{"a": 1}])

    # --- flujo completo ---------------------------------------------------
    def test_exito_termina_esperando_aprobacion_humana(self):
        e = self.correr("impl-ok", "rev-inteligente")
        self.assertEqual(e["estado"], "AWAITING_APPROVAL")
        self.assertEqual(e["iteracion"], 1)
        # La rama existe, pero main no cambió: el BOSS no hace merge.
        self.assertFalse((self.repo / "src" / "feature.txt").exists())
        rama = subprocess.run(["git", "-C", str(self.repo), "show", "boss/T-1:src/feature.txt"],
                              capture_output=True, text=True).stdout
        self.assertEqual(rama.strip(), "ok")

    def test_prompt_utf8_con_acentos(self):
        # Regresión: en Windows el prompt salía en cp1252 y Codex lo rechazaba.
        e = self.correr("impl-acentos", "rev-inteligente",
                        objetivo="Señal con acentuación: crear src/feature.txt con ok")
        self.assertEqual(e["estado"], "AWAITING_APPROVAL", e.get("motivo"))

    def test_corrige_con_hallazgos_del_revisor(self):
        e = self.correr("impl-corrige", "rev-inteligente")
        self.assertEqual(e["estado"], "AWAITING_APPROVAL")
        self.assertEqual(e["iteracion"], 2)

    def test_validacion_manda_sobre_el_revisor(self):
        # El revisor aprueba pero los tests fallan: no hay éxito.
        e = self.correr("impl-siempre-mal", "rev-aprueba", max_iteraciones=1)
        self.assertEqual(e["estado"], "FAILED")

    def test_mismo_fallo_repetido_bloquea(self):
        e = self.correr("impl-siempre-mal", "rev-inteligente")
        self.assertEqual(e["estado"], "BLOCKED")
        self.assertIn("mismo fallo", e["motivo"])
        self.assertEqual(e["iteracion"], 2)

    def test_fuera_de_alcance_bloquea(self):
        e = self.correr("impl-fuera", "rev-aprueba")
        self.assertEqual(e["estado"], "BLOCKED")
        self.assertIn("README.md", e["motivo"])

    def test_sin_cambios_bloquea(self):
        e = self.correr("impl-nada", "rev-aprueba")
        self.assertEqual(e["estado"], "BLOCKED")

    def test_implementador_falla_bloquea(self):
        e = self.correr("impl-falla", "rev-aprueba")
        self.assertEqual(e["estado"], "BLOCKED")
        self.assertIn("código 3", e["motivo"])

    def test_revisor_sin_veredicto_no_aprueba(self):
        e = self.correr("impl-ok", "rev-basura")
        self.assertEqual(e["estado"], "BLOCKED")
        self.assertIn("veredicto", e["motivo"])

    def test_revisor_que_escribe_se_descarta(self):
        e = self.correr("impl-ok", "rev-escribe")
        self.assertEqual(e["estado"], "BLOCKED")
        self.assertIn("revisor modificó", e["motivo"])

    def test_contrato_manipulado_se_detecta(self):
        ruta_c = self.tmp / "c.json"
        ruta_c.write_text(json.dumps(self.contrato()))
        tarea = boss.nueva_tarea(self.repo, ruta_c)
        congelado = tarea.dir / "contrato.json"
        congelado.write_text(congelado.read_text().replace('"max_iteraciones": 3',
                                                          '"max_iteraciones": 99'))
        with self.assertRaises(boss.BossError):
            boss.ejecutar_tarea(self.repo, "T-1", self.tmp / "noimporta.json")

    def test_rama_base_inexistente_bloquea(self):
        ruta_c = self.tmp / "c.json"
        ruta_c.write_text(json.dumps(self.contrato(rama_base="no-existe")))
        self.assertEqual(boss.nueva_tarea(self.repo, ruta_c).leer_estado()["estado"], "BLOCKED")

    def test_contrato_con_bom_de_powershell(self):
        # Set-Content -Encoding UTF8 de PowerShell 5 agrega BOM.
        ruta_c = self.tmp / "c.json"
        ruta_c.write_bytes(b"\xef\xbb\xbf" + json.dumps(self.contrato()).encode("utf-8"))
        self.assertEqual(boss.nueva_tarea(self.repo, ruta_c).leer_estado()["estado"], "TRIAGED")

    def test_exige_boss_en_gitignore(self):
        (self.repo / ".gitignore").write_text("")
        ruta_c = self.tmp / "c.json"
        ruta_c.write_text(json.dumps(self.contrato()))
        with self.assertRaises(boss.BossError):
            boss.nueva_tarea(self.repo, ruta_c)

    def test_transicion_invalida(self):
        ruta_c = self.tmp / "c.json"
        ruta_c.write_text(json.dumps(self.contrato()))
        tarea = boss.nueva_tarea(self.repo, ruta_c)
        with self.assertRaises(boss.BossError):
            tarea.transicion("AWAITING_APPROVAL")

    def test_limpiar_quita_worktrees_y_conserva_rama(self):
        self.correr("impl-ok", "rev-inteligente")
        boss.limpiar_tarea(self.repo, "T-1")
        self.assertFalse((self.repo / ".boss" / "worktrees" / "T-1-impl").exists())
        self.assertTrue(subprocess.run(["git", "-C", str(self.repo), "rev-parse", "--verify",
                                        "boss/T-1"], capture_output=True).returncode == 0)

    def test_cli_estado(self):
        ruta_c = self.tmp / "c.json"
        ruta_c.write_text(json.dumps(self.contrato()))
        self.assertEqual(boss.main(["--repo", str(self.repo), "nueva", str(ruta_c)]), 0)
        self.assertEqual(boss.main(["--repo", str(self.repo), "estado", "T-1"]), 0)
        self.assertEqual(boss.main(["--repo", str(self.repo), "estado", "NO"]), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
