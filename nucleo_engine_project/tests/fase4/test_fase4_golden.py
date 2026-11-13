"""F4 — Test GOLDEN de producción del álbum (gate de avance de la Fase 4).

Ejecución:  python3 -m pytest tests/fase4/test_fase4_golden.py -q

Produce el álbum dorado ``Ecos de Neblina`` (3 pistas) por el pipeline REAL
de FASE 8 (``python3 -m album producir``) y verifica el gate completo del
spec v1.4 §12.1 Fase 4:
  - reglas de álbum §8.4: 4/4 (+ P-03) en el álbum de 3 pistas;
  - diversidad (huellas Jaccard) dentro de banda — sin monotonía;
  - producción íntegra: 3 pistas ok, 0 fails de compliance, informe+manifiesto;
  - determinismo: re-producción --forzar ⇒ mismos sha256 MIDI byte a byte;
  - motivo firma (P-03 vía a) materializado en el MIDI real: frase en la
    fuente, recurrencia transpuesta, ausencia en la pista de contraste.
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from album import blueprint as BP   # noqa: E402
from album import esquema as ES     # noqa: E402

GOLDEN_DIR = ROOT / "albumes" / "ecos_de_neblina"
ALBUM_JSON = GOLDEN_DIR / "album.json"

#: frase firma esperada por pista (pitch en orden): F minor y transposición.
FRASE_F = [65, 68, 72, 70, 67]


class TestGoldenF4(unittest.TestCase):
    """Gate de avance F4 ejecutado de punta a punta sobre disco real."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls._tmp.name) / "produccion"
        r = subprocess.run(
            [sys.executable, "-m", "album", "producir", str(ALBUM_JSON),
             "--out", str(cls.out)],
            cwd=str(ROOT), capture_output=True, text=True, timeout=600)
        cls.salida = r.stdout
        cls.returncode = r.returncode

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def _estado(self):
        return json.loads((self.out / "estado.json").read_text(encoding="utf-8"))

    def test_produccion_exitosa(self):
        self.assertEqual(self.returncode, 0, self.salida[-2000:])
        estado = self._estado()
        self.assertEqual(len(estado["pistas"]), 3)
        for tid, reg in estado["pistas"].items():
            self.assertEqual(reg["estado"], "ok", (tid, reg.get("error")))
            self.assertEqual(reg.get("compliance_fails"), [], tid)
        self.assertIn("ÁLBUM OK", self.salida)

    def test_artifactos_completos_por_pista(self):
        estado = self._estado()
        for tid, reg in estado["pistas"].items():
            carpeta = Path(reg["carpeta"])
            for nombre in ("doc.json", "config_efectiva.json",
                           "evidencia.json"):
                self.assertTrue((carpeta / nombre).is_file(),
                                (tid, nombre))
            mids = list(carpeta.glob("*.mid"))
            self.assertEqual(len(mids), 1, tid)
            self.assertGreater(mids[0].stat().st_size, 1000, tid)

    def test_informe_y_manifiesto(self):
        for nombre in ("informe_album.json", "informe_album.md",
                       "manifiesto.json", "huellas.json", "plan.json"):
            self.assertTrue((self.out / nombre).is_file(), nombre)
        informe = json.loads((self.out / "informe_album.json")
                             .read_text(encoding="utf-8"))
        self.assertEqual(informe.get("album"), "Ecos de Neblina")

    def test_duplicados_y_banda_de_diversidad(self):
        huellas = json.loads((self.out / "huellas.json").read_text("utf-8"))
        estado = self._estado()
        ids_ok = [t for t, reg in estado["pistas"].items()
                  if reg["estado"] == "ok"]
        banda = BP.validar_banda_huellas(huellas, ids_ok)
        self.assertTrue(banda["ok"], banda)
        self.assertLess(banda["peor_par"]["similitud"], BP.UMBRAL_MONOTONIA)
        dups = [d for d in banda["matriz"].values() if d >= 1.0]
        self.assertEqual(dups, [])

    def test_reglas_84_en_el_album_dorado(self):
        resolucion = json.loads(
            (GOLDEN_DIR / "blueprint_resolucion.json").read_text("utf-8"))
        spec = json.loads((GOLDEN_DIR / "blueprint.json").read_text("utf-8"))
        reglas = BP.validar_reglas(spec, resolucion["resolucion"])
        self.assertTrue(reglas["todas_ok"],
                        json.dumps(reglas["reglas"], ensure_ascii=False))

    def test_motivo_firma_en_el_midi_real(self):
        """Evidencia musical del P-03 vía (a): frase + recurrencia + ausencia."""
        docs = {}
        estado = self._estado()
        for tid, reg in estado["pistas"].items():
            docs[tid] = json.loads(
                (Path(reg["carpeta"]) / "doc.json").read_text("utf-8"))
        # pista 1 (F minor): frase en verse_2, recurrencia en chorus_4
        dev1 = docs["umbral_de_neblina"].get("development") or {}
        self.assertEqual([n["pitch"] for n in
                          dev1["melody"]["phrases"]["verse_2"]], FRASE_F)
        self.assertEqual(dev1["motifs"]["firma_neblina"]["sections"], ["chorus_4"])
        # pista 2 (Bb minor, +5 st): frase transpuesta y recurrencia en chorus_8
        dev2 = docs["camara_de_espejos"].get("development") or {}
        self.assertEqual([n["pitch"] for n in
                          dev2["melody"]["phrases"]["verse_2"]],
                         [p + 5 for p in FRASE_F])
        self.assertEqual(dev2["motifs"]["firma_neblina"]["sections"], ["chorus_8"])
        # pista 3: sin motivo (anti-monotonía §12.1)
        self.assertEqual(docs["marea_baja_de_neon"].get("development"), None)

    def test_eventos_reales_del_lead(self):
        """El MIDI de la pista 1 contiene la frase exacta en verse_2."""
        doc = self.out / "01_umbral_de_neblina" / "doc.json"
        with tempfile.TemporaryDirectory() as t:
            subprocess.run(
                [sys.executable, "scripts/produce.py", str(doc),
                 "--production", "atmospheric", "--events", "--out", t],
                cwd=str(ROOT), capture_output=True, text=True, timeout=600,
                check=True)
            ev = json.loads((Path(t) / "events.json").read_text("utf-8"))
        sax = next(t for t in ev["tracks"] if t["id"] == "sax_tenor")
        secs = {s["id"]: s for s in ev["sections"]}
        t0 = secs["verse_2"]["t0"]
        pitches = [n[2] for n in sax["notes"]
                   if t0 <= n[0] < t0 + 16][:5]
        self.assertEqual(pitches, FRASE_F)
        c0 = secs["chorus_4"]["t0"]
        pitches_c = [n[2] for n in sax["notes"]
                     if c0 <= n[0] < c0 + 16][:5]
        self.assertEqual(pitches_c, FRASE_F, "recurrencia en chorus_4")

    def test_determinismo_de_produccion(self):
        estado_1 = {t: reg.get("sha256_midi")
                    for t, reg in self._estado()["pistas"].items()}
        r = subprocess.run(
            [sys.executable, "-m", "album", "producir", str(ALBUM_JSON),
             "--out", str(self.out), "--forzar"],
            cwd=str(ROOT), capture_output=True, text=True, timeout=600)
        self.assertEqual(r.returncode, 0, r.stdout[-2000:])
        estado_2 = {t: reg.get("sha256_midi")
                    for t, reg in self._estado()["pistas"].items()}
        self.assertEqual(estado_1, estado_2,
                         "re-producción --forzar no fue byte-idéntica")


if __name__ == "__main__":
    unittest.main()
