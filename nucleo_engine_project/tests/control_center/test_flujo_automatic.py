"""Integración E2E del comando ``automatic`` — Fase 2 (spec v1.4, §12.1, §11.2).

    python3 -m control_center automatic INTENCION.json --out DIR

Verifica el flujo completo por subprocess (sin importar produce.py desde el
paquete, §13): intención → plan.json con seed persistida → doc.json → MIDI +
evidencia.json + events.json → capa_c.json con los gates bloqueantes OK.
También: --no-producir (solo plan+doc), intención inválida (exit 1, sin
archivos), y regeneración L1 (misma intención ⇒ mismo sha256_midi).
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

INTENCION = {
    "identity": {"style": "dark_triphop", "accessibility": "balanced",
                 "protagonist": "sax_tenor"},
    "controls": {"energia": "media", "forma": "cancion", "duracion": "corta",
                 "armonia": "nocturno", "pulso": "swing", "drums": "presente"},
    "seed": 606,
}


class FlujoAutomaticE2E(unittest.TestCase):
    def _ejecuta(self, *args):
        env = dict(os.environ, PYTHONPATH=str(ROOT))
        return subprocess.run([sys.executable, "-m", "control_center", *args],
                              cwd=str(ROOT), env=env, capture_output=True,
                              text=True, timeout=600)

    def test_intencion_a_cancion_completa(self):
        with tempfile.TemporaryDirectory(prefix="cc_f2_e2e_") as tmp:
            inten = Path(tmp) / "intencion.json"
            inten.write_text(json.dumps(INTENCION, ensure_ascii=False),
                             encoding="utf-8")
            salida = Path(tmp) / "salida"
            r = self._ejecuta("automatic", str(inten), "--out", str(salida))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("CAPA A/B: OK", r.stdout)
            self.assertIn("capa C: OK", r.stdout)
            # artefactos co-localizados (P-05)
            for nombre in ("plan.json", "doc.json", "events.json",
                           "capa_c.json"):
                self.assertTrue((salida / nombre).is_file(), nombre)
            midis = list(salida.glob("*.mid"))
            self.assertEqual(len(midis), 1)
            self.assertTrue((salida / "evidencia.json").is_file())
            plan = json.loads((salida / "plan.json").read_text(
                encoding="utf-8"))
            doc = json.loads((salida / "doc.json").read_text(
                encoding="utf-8"))
            ev = json.loads((salida / "evidencia.json").read_text(
                encoding="utf-8"))
            capa_c = json.loads((salida / "capa_c.json").read_text(
                encoding="utf-8"))
            # seed persistida y trazable: plan → doc.global.seed → evidencia
            self.assertEqual(plan["seed"], INTENCION["seed"])
            self.assertEqual(doc["global"]["seed"], plan["seed"])
            self.assertEqual(ev.get("seed"), plan["seed"])
            self.assertEqual(capa_c["seed"], plan["seed"])
            self.assertTrue(capa_c["ok"])
            # el plan emitido pasa A/B y el doc es E1xx-limpio
            sys.path.insert(0, str(ROOT))
            from control_center import validador, plan_compilador  # noqa: E402
            from dark_director import validador as DV  # noqa: E402
            self.assertTrue(validador.validar(plan)["ok"])
            self.assertEqual(DV.validar(doc)["errores"], [])

    def test_regeneracion_l1_mismo_sha256(self):
        with tempfile.TemporaryDirectory(prefix="cc_f2_l1a_") as ta, \
                tempfile.TemporaryDirectory(prefix="cc_f2_l1b_") as tb:
            for destino in (Path(ta) / "a", Path(tb) / "b"):
                inten = Path(ta) / "i.json"
                inten.write_text(json.dumps(INTENCION), encoding="utf-8")
                r = self._ejecuta("automatic", str(inten), "--out",
                                  str(destino))
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            sha_a = json.loads(
                (Path(ta) / "a" / "evidencia.json").read_text())["sha256_midi"]
            sha_b = json.loads(
                (Path(tb) / "b" / "evidencia.json").read_text())["sha256_midi"]
            self.assertEqual(sha_a, sha_b)

    def test_no_producir_solo_plan_y_doc(self):
        with tempfile.TemporaryDirectory(prefix="cc_f2_noprod_") as tmp:
            inten = Path(tmp) / "intencion.json"
            inten.write_text(json.dumps(INTENCION), encoding="utf-8")
            salida = Path(tmp) / "salida"
            r = self._ejecuta("automatic", str(inten), "--out", str(salida),
                              "--no-producir")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertTrue((salida / "plan.json").is_file())
            self.assertTrue((salida / "doc.json").is_file())
            self.assertFalse((salida / "capa_c.json").exists())
            self.assertFalse(list(salida.glob("*.mid")))
            self.assertIn("scripts/produce.py", r.stdout)

    def test_intencion_invalida_exit_1_sin_archivos(self):
        with tempfile.TemporaryDirectory(prefix="cc_f2_mala_") as tmp:
            inten = Path(tmp) / "mala.json"
            mala = dict(INTENCION)
            mala["identity"] = {"style": "techno", "accessibility": "balanced",
                                "protagonist": "sax_tenor"}
            inten.write_text(json.dumps(mala), encoding="utf-8")
            salida = Path(tmp) / "salida"
            r = self._ejecuta("automatic", str(inten), "--out", str(salida))
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("ERROR", r.stdout)
            self.assertFalse(salida.exists())

    def test_seed_automatica_persistida_cuando_no_se_aporta(self):
        inten = dict(INTENCION)
        inten.pop("seed")
        with tempfile.TemporaryDirectory(prefix="cc_f2_autoseed_") as tmp:
            ruta = Path(tmp) / "intencion.json"
            ruta.write_text(json.dumps(inten), encoding="utf-8")
            salida = Path(tmp) / "salida"
            r = self._ejecuta("automatic", str(ruta), "--out", str(salida))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            plan = json.loads((salida / "plan.json").read_text(
                encoding="utf-8"))
            self.assertIsInstance(plan["seed"], int)
            self.assertTrue(1 <= plan["seed"] <= 999_983)


if __name__ == "__main__":
    unittest.main()
