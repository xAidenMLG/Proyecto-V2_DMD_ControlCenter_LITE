"""F5 — Tests de tools/diff_midi.py (diff estructural L2, spec v1.4 §11.1).

Ejecución:  python3 -m pytest tests/test_diff_midi.py -q

Verifica la herramienta formal de la fase contra eventos REALES producidos por
produce.py: L2 compara estructura (pistas/roles/secciones/compases/BPM/duración)
— las notas PUEDEN diferir (L3/L4) — y reporta el diff numérico sin bloquear.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DOC_FULL = ROOT / "output/plan_f5/serie_base/01_full/doc.json"
DOC_LARGA = ROOT / "output/plan_f5/serie_base/05_atmospheric/doc.json"


def _events(doc, out, seed_extra=None):
    cmd = [sys.executable, "scripts/produce.py", str(doc),
           "--production", "full" if "01_full" in str(doc) else "atmospheric",
           "--events", "--out", str(out)]
    if seed_extra is not None:
        cmd += ["--seed", str(seed_extra)]
    subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True,
                   timeout=600, check=True)
    return Path(out) / "events.json"


class TestDiffMidiL2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.ev_a = _events(DOC_FULL, Path(cls.tmp.name) / "a")           # seed del doc
        cls.ev_a2 = _events(DOC_FULL, Path(cls.tmp.name) / "a2", 4242)   # misma estructura, otras notas
        cls.ev_b = _events(DOC_LARGA, Path(cls.tmp.name) / "b")          # otra estructura

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def _run(self, a, b):
        r = subprocess.run(
            [sys.executable, "tools/diff_midi.py", str(a), str(b), "--json"],
            cwd=str(ROOT), capture_output=True, text=True, timeout=120)
        return r, json.loads(r.stdout.splitlines()[-1])

    def test_identicos_l2_ok(self):
        r, out = self._run(self.ev_a, self.ev_a)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertTrue(out["l2_ok"])
        self.assertEqual(out["diferencias"], [])

    def test_misma_estructura_otras_notas_l2_ok(self):
        """L2: seed distinta cambia las notas pero NO la estructura."""
        r, out = self._run(self.ev_a, self.ev_a2)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertTrue(out["l2_ok"])
        num = out["metricas"]["A"]
        num2 = out["metricas"]["B"]
        dif_notas = any(num[t]["notas"] != num2.get(t, {}).get("notas")
                        for t in num)
        self.assertTrue(dif_notas, "las notas deberían diferir entre seeds")

    def test_estructura_distinta_rechazada(self):
        r, out = self._run(self.ev_a, self.ev_b)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertFalse(out["l2_ok"])
        self.assertTrue(out["diferencias"])

    def test_bloques_estructurales_comparados(self):
        r, out = self._run(self.ev_a, self.ev_b)
        textos = " | ".join(out["diferencias"])
        self.assertIn("secciones", textos)
        self.assertIn("duración", textos)

    def test_metricas_informativas_sin_bloquear(self):
        r, out = self._run(self.ev_a, self.ev_a2)
        for pista in out["metricas"]["A"].values():
            self.assertIn("notas", pista)
            self.assertIn("vel", pista)
            self.assertIn("densidad_notas_beat_por_seccion", pista)

    def test_archivo_ausente_exit_2(self):
        r = subprocess.run(
            [sys.executable, "tools/diff_midi.py", "/no/existe.json",
             str(self.ev_a)],
            cwd=str(ROOT), capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 2, r.stdout)


if __name__ == "__main__":
    unittest.main()
