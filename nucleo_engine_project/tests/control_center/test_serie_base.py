"""F5 — Tests GOLDEN de la serie base MVP (5 canciones sin seed, §5.4).

Ejecución:  python3 -m pytest tests/control_center/test_serie_base.py -q

§5.4 (criterio de completitud del MVP): 5 canciones reales generadas end-to-end
con SOLO identidad + protagonista + 6 controles, SIN aportar seed (el sistema
la genera y la guarda). Verifica por canción: capas A/B sobre el plan en disco,
capa C verde, perfil representativo esperado (expansión del set golden: 1 por
perfil con motores — P-06 excluye `original`), seed auto persistida y
determinismo L1 de regeneración completa sin seed.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from control_center import validador  # noqa: E402

BASE = ROOT / "output/plan_f5/serie_base"
CASOS = {
    "01_full": "full",
    "02_sax": "sax",
    "03_drums": "drums",
    "04_sax_vibes": "sax_vibes",
    "05_atmospheric": "atmospheric",
}


class TestSerieBaseMVP(unittest.TestCase):
    """§5.4: 5 canciones reales sin seed + 1 golden por perfil representativo."""

    def test_intenciones_sin_seed(self):
        for nombre in CASOS:
            inten = json.loads((BASE / "intenciones" / f"{nombre}.json")
                               .read_text("utf-8"))
            self.assertNotIn("seed", inten, nombre)
            self.assertIn("identity", inten)
            self.assertIn("controls", inten)

    def test_cinco_canciones_completas(self):
        for nombre in CASOS:
            carpeta = BASE / nombre
            for artefacto in ("plan.json", "doc.json", "capa_c.json",
                              "evidencia.json"):
                self.assertTrue((carpeta / artefacto).is_file(),
                                (nombre, artefacto))
            mids = list(carpeta.glob("*.mid"))
            self.assertEqual(len(mids), 1, nombre)
            self.assertGreater(mids[0].stat().st_size, 1000, nombre)

    def test_perfil_representativo_por_cancion(self):
        """Expansión del set golden: 1 canción por perfil con motores."""
        for nombre, perfil in CASOS.items():
            plan = json.loads((BASE / nombre / "plan.json").read_text("utf-8"))
            self.assertEqual(plan["orchestration"]["profile"], perfil,
                             (nombre, perfil))

    def test_capas_ab_en_disco_y_capa_c_verde(self):
        for nombre in CASOS:
            carpeta = BASE / nombre
            plan = json.loads((carpeta / "plan.json").read_text("utf-8"))
            resultado = validador.validar(plan)
            self.assertTrue(resultado["ok"], (nombre, resultado["errores"]))
            capa_c = json.loads((carpeta / "capa_c.json").read_text("utf-8"))
            self.assertTrue(capa_c["ok"], nombre)
            self.assertTrue(capa_c["checks"])

    def test_seed_auto_generada_y_persistida(self):
        for nombre in CASOS:
            plan = json.loads((BASE / nombre / "plan.json").read_text("utf-8"))
            self.assertIsInstance(plan["seed"], int)
            self.assertGreaterEqual(plan["seed"], 1)
            evidencia = json.loads(
                (BASE / nombre / "evidencia.json").read_text("utf-8"))
            doc = json.loads((BASE / nombre / "doc.json").read_text("utf-8"))
            self.assertEqual(doc["global"]["seed"], plan["seed"], nombre)
            self.assertEqual(evidencia["seed"], plan["seed"], nombre)

    def test_reproducibilidad_l1_sin_seed(self):
        """§5.4: las 5 canciones regeneran idénticas (L1) sin pasar seed."""
        with tempfile.TemporaryDirectory() as tmp:
            for nombre, perfil in CASOS.items():
                doc = BASE / nombre / "doc.json"
                out = Path(tmp) / nombre
                subprocess.run(
                    [sys.executable, "scripts/produce.py", str(doc),
                     "--production", perfil, "--out", str(out)],
                    cwd=str(ROOT), capture_output=True, text=True,
                    timeout=600, check=True)
                ev2 = json.loads((out / "evidencia.json").read_text("utf-8"))
                ev1 = json.loads((BASE / nombre / "evidencia.json")
                                 .read_text("utf-8"))
                self.assertEqual(ev1["sha256_midi"], ev2["sha256_midi"],
                                 "L1 roto en %s" % nombre)


if __name__ == "__main__":
    unittest.main()
