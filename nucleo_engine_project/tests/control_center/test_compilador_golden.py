"""Ancla dorada L1 del compilador Plan→doc + determinismo (§13, §11.2 Golden).

El plan del ancla declara explícitamente todos los bloques del doc de
``demo_medianoche`` (meta, direction, global, harmony, structure con
tension/density/focus/drums, ending) y compila a un ``doc.json`` BYTE-IDÉNTICO
al existente (sha256 canónico ``b2399cc5…93b90f``); producir desde él con el
CLI intacto, sin ``--seed`` (la seed 3113 proviene de ``doc.global.seed``),
reproduce ``sha256_midi 32199acc…b29a9ff``.

HALLAZGO DOCUMENTADO (F1): el plan del ancla NO es un fixture del validador de
capas A/B — la regla de transiciones de §6.5 (solo cancion: sin saltos de
energía >0.4 entre vecinas) rechaza el salto INTENCIONAL 0.8→0.15 de
chorus_2→outro del doc ancla (con fade_out declarado). El criterio 2 de §13
exige fidelidad de compilación para el ancla, no capas A/B; el ancla valida el
COMPILADOR. La matriz del validador vive en test_validador.py. Si algún día el
ancla debe pasar A/B, eso es una decisión L4 documentada del spec, no un cambio
de código.

Los artefactos de producción de la fase viven en ``output/plan_f1/`` (no bajo
``output/produccion/`` para no tocar el INDICE.md preexistente).
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from control_center import plan_compilador, validador  # noqa: E402
from dark_director import validador as DV  # noqa: E402
from tests.control_center.test_validador import _plan_cancion  # noqa: E402

DOC_ANCLA = ROOT / "output" / "produccion" / "demo_medianoche" / "doc.json"
SHA_DOC_CANONICO = "b2399cc582823f0079871145e6312ae4c8b7ecf03eea4f81785c5882cc93b90f"
SHA_MIDI_ANCLA = "32199acc254a2eeff93a12d15df3b38ec2c541a45a10a4719d493c696b29a9ff"

PLAN_ANCLA = {
    "plan_version": 1,
    "mode": "guided",
    "seed": 3113,
    "title": "Medianoche en Puerto Nuevo",
    "identity": {"style": "dark_triphop", "accessibility": "balanced",
                 "protagonist": "sax_tenor", "palette": ["full"]},
    "controls": {"energia": "media", "forma": "cancion", "duracion": "media",
                 "armonia": "nocturno", "pulso": "lento_arrastrado",
                 "drums": "presente"},
    "album_context": None,
    "form": {"template": "cancion", "sections": [
        {"id": "intro", "type": "intro", "bars": 4, "energy": 0.2,
         "tension": 0.2, "density": 0.2, "focus": ["rhodes", "pad"],
         "drums": "air", "locked": False},
        {"id": "verse_1", "type": "verse", "bars": 8, "energy": 0.4,
         "tension": 0.3, "density": 0.4, "focus": ["sax_tenor"],
         "drums": "groove", "locked": False},
        {"id": "verse_2", "type": "verse", "bars": 8, "energy": 0.45,
         "tension": 0.35, "density": 0.45, "focus": ["rhodes"],
         "drums": "groove", "locked": False},
        {"id": "pre_1", "type": "pre_chorus", "bars": 4, "energy": 0.55,
         "tension": 0.5, "density": 0.5, "focus": ["pad", "vibraphone"],
         "drums": "light", "locked": False},
        {"id": "chorus_1", "type": "chorus", "bars": 8, "energy": 0.75,
         "tension": 0.5, "density": 0.6, "focus": ["sax_tenor", "bass"],
         "drums": "heavy", "locked": False},
        {"id": "bridge_1", "type": "bridge", "bars": 8, "energy": 0.5,
         "tension": 0.65, "density": 0.5, "focus": ["rhodes", "vibraphone"],
         "drums": "light", "locked": False},
        {"id": "chorus_2", "type": "chorus", "bars": 12, "energy": 0.8,
         "tension": 0.55, "density": 0.65, "focus": ["sax_tenor", "drums"],
         "drums": "heavy", "final": True, "locked": False},
        {"id": "outro", "type": "outro", "bars": 8, "energy": 0.15,
         "tension": 0.15, "density": 0.2, "focus": ["rhodes"],
         "drums": "air", "locked": False},
    ]},
    "ending": {"fade_out": {"enabled": True, "bars": 4}},
    "harmony": {"key": "F# minor", "language": "pop_dream_pop",
                "harmonic_rhythm_bars": 2,
                "progressions": {
                    "verse": ["F#m9", "Dmaj9", "Amaj9", "E7sus4"],
                    "chorus": ["Dmaj9", "Amaj9", "Bm9", "C#7sus4"]}},
    "solos": [],
    "orchestration": {"profile": "full"},
    "global": {"bpm": 78},
    "duration": {"target": "media", "bars_total": 60},
    "notes": "FASE 6 — generalización: groove lento, F# minor, mucho espacio.",
    "evidence": {"resolved_by": "manual@fase1", "resolved": [],
                 "inputs_hash": "sha256:" + "b" * 64,
                 "created_at": "2026-11-12T00:00:00Z"},
}


def _doc_de_referencia():
    return json.loads(DOC_ANCLA.read_text(encoding="utf-8"))


@unittest.skipUnless(DOC_ANCLA.is_file(), "doc de referencia demo_medianoche no disponible")
class AnclaL1ByteIdentica(unittest.TestCase):
    def test_doc_compilado_byte_identico(self):
        doc = plan_compilador.compilar(PLAN_ANCLA)
        bytes_compilado = plan_compilador.doc_a_bytes(doc)
        bytes_referencia = DOC_ANCLA.read_bytes()
        self.assertEqual(bytes_compilado, bytes_referencia,
                         "el doc compilado no es byte-idéntico al doc.json real")
        # sha256_doc de evidencia.json es el hash canónico (sort_keys, produce.py:138)
        canonico = json.dumps(doc, ensure_ascii=False, sort_keys=True).encode("utf-8")
        self.assertEqual(hashlib.sha256(canonico).hexdigest(), SHA_DOC_CANONICO)

    def test_orden_de_claves_replica_el_formato_real(self):
        doc = plan_compilador.compilar(PLAN_ANCLA)
        self.assertEqual(list(doc.keys()),
                         ["schema", "meta", "direction", "global", "harmony",
                          "structure", "ending"])
        self.assertEqual(list(doc["meta"].keys()), ["title", "notes"])
        self.assertEqual(list(doc["global"].keys()), ["bpm", "seed"])
        self.assertEqual(list(doc["harmony"].keys()),
                         ["key", "language", "harmonic_rhythm_bars", "progressions"])
        self.assertEqual(list(doc["harmony"]["progressions"].keys()), ["verse", "chorus"])
        self.assertEqual(list(doc["structure"][0].keys()),
                         ["id", "type", "bars", "energy", "tension", "density",
                          "focus", "drums"])
        self.assertEqual(list(doc["structure"][6].keys()),
                         ["id", "type", "bars", "energy", "tension", "density",
                          "focus", "drums", "final"])

    def test_determinismo_compilar_dos_veces(self):
        a = plan_compilador.doc_a_bytes(plan_compilador.compilar(PLAN_ANCLA))
        b = plan_compilador.doc_a_bytes(plan_compilador.compilar(PLAN_ANCLA))
        self.assertEqual(a, b)

    def test_locked_y_estado_no_viajan_al_doc(self):
        doc = plan_compilador.compilar(PLAN_ANCLA)
        for s in doc["structure"]:
            self.assertNotIn("locked", s)
        self.assertNotIn("mode", doc)
        self.assertNotIn("plan_version", doc)
        self.assertNotIn("controls", doc)
        self.assertNotIn("orchestration", doc)
        self.assertNotIn("duration", doc)
        self.assertNotIn("evidence", doc)
        self.assertNotIn("album_context", doc)

    def test_doc_compilado_pasa_el_validador_del_contrato_doc(self):
        # el doc compilado debe ser E1xx-limpio para dark-director/1 (produce.py
        # lo compilaría sin errores: compilador.compilar → validador.validar)
        doc = plan_compilador.compilar(PLAN_ANCLA)
        r = DV.validar(doc)
        self.assertEqual(r["errores"], [], r["errores"])

    def test_hallazgo_ancla_no_es_fixture_del_validador(self):
        # Documentado en la cabecera: el salto intencional chorus_2(0.8)→outro(0.15)
        # con fade_out viola la regla B de transiciones (§6.5, >0.4) y NADA más.
        r = validador.validar(PLAN_ANCLA)
        self.assertFalse(r["ok"])
        self.assertEqual([e["codigo"] for e in r["errores"]], ["V115"], r["errores"])
        self.assertIn("chorus_2", r["errores"][0]["mensaje"])
        self.assertIn("outro", r["errores"][0]["mensaje"])


@unittest.skipUnless(DOC_ANCLA.is_file(), "doc de referencia demo_medianoche no disponible")
class AnclaL1MidiReproducido(unittest.TestCase):
    def test_producir_sin_seed_reproduce_sha256_midi(self):
        # flujo §9.4: doc compilado → CLI existente produce.py, SIN --seed
        # (la seed 3113 proviene de doc.global.seed), --verify no escribe nada.
        with tempfile.TemporaryDirectory(prefix="cc_golden_") as tmp:
            doc_path = Path(tmp) / "doc.json"
            doc_path.write_bytes(plan_compilador.doc_a_bytes(
                plan_compilador.compilar(PLAN_ANCLA)))
            cmd = [sys.executable, "scripts/produce.py", str(doc_path),
                   "--production", "full", "--out", tmp, "--verify", SHA_MIDI_ANCLA]
            r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True,
                               timeout=300)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("OK — resultado idéntico", r.stdout)


@unittest.skipUnless(DOC_ANCLA.is_file(), "doc de referencia demo_medianoche no disponible")
class DeterminismoProduccion(unittest.TestCase):
    def test_producir_dos_veces_mismo_sha256(self):
        from scripts.produce import producir_cancion
        doc = plan_compilador.compilar(PLAN_ANCLA)
        with tempfile.TemporaryDirectory(prefix="cc_det_a_") as ta, \
                tempfile.TemporaryDirectory(prefix="cc_det_b_") as tb:
            ra = producir_cancion(json.loads(json.dumps(doc)), production="full",
                                  out_dir=ta, indice=False)
            rb = producir_cancion(json.loads(json.dumps(doc)), production="full",
                                  out_dir=tb, indice=False)
            self.assertEqual(ra["sha256"], SHA_MIDI_ANCLA)
            self.assertEqual(ra["sha256"], rb["sha256"])


class MapeoSolosYMeta(unittest.TestCase):
    def test_solo_lead_compila_a_development_improvisation(self):
        plan = _plan_cancion()
        plan["form"]["sections"][2]["type"] = "break"       # coro_a → break
        plan["form"]["sections"][2]["focus"] = ["sax_tenor"]
        plan["solos"] = [{"section_id": "coro_a", "instrument": "sax_tenor"}]
        doc = plan_compilador.compilar(plan)
        self.assertEqual(doc.get("development"),
                         {"improvisation": [{"instrument": "sax_tenor",
                                             "section": "coro_a"}]})
        self.assertEqual(list(doc.keys())[-2:], ["development", "ending"])
        r = DV.validar(doc)
        self.assertEqual(r["errores"], [], r["errores"])

    def test_solo_no_lead_no_compila_improvisation(self):
        # E301: el bloque generativo es solo del lead; un solo de rhodes se
        # expresa por focus[] + comportamiento de motores (§6.2, §9.2)
        plan = _plan_cancion()
        plan["identity"]["protagonist"] = "sax_tenor"
        plan["form"]["sections"][2]["type"] = "break"
        plan["form"]["sections"][2]["focus"] = ["sax_tenor"]
        plan["form"]["sections"][1]["type"] = "bridge"
        plan["form"]["sections"][1]["focus"] = ["rhodes"]
        plan["solos"] = [{"section_id": "verso_a", "instrument": "rhodes"}]
        r = validador.validar(plan)
        self.assertTrue(r["ok"], r["errores"])
        doc = plan_compilador.compilar(plan)
        self.assertNotIn("development", doc)

    def test_notes_viaja_a_meta_notes_y_ausente_no(self):
        plan = _plan_cancion()
        doc = plan_compilador.compilar(plan)
        self.assertEqual(doc["meta"]["notes"], plan["notes"])
        del plan["notes"]
        doc2 = plan_compilador.compilar(plan)
        self.assertNotIn("notes", doc2["meta"])

    def test_final_false_no_aparece_en_el_doc(self):
        plan = _plan_cancion()
        plan["form"]["sections"][0]["final"] = False
        doc = plan_compilador.compilar(plan)
        self.assertNotIn("final", doc["structure"][0])
        plan["form"]["sections"][0]["final"] = True
        doc2 = plan_compilador.compilar(plan)
        self.assertEqual(doc2["structure"][0].get("final"), True)


class CliControlCenter(unittest.TestCase):
    """Smoke del CLI (§13, §16.1): python3 -m control_center validar|compilar."""

    def _ejecuta(self, *args):
        env = dict(os.environ, PYTHONPATH=str(ROOT))
        return subprocess.run([sys.executable, "-m", "control_center", *args],
                              cwd=str(ROOT), env=env, capture_output=True,
                              text=True, timeout=120)

    def test_validar_plan_vacio_falla_correctamente(self):
        # §16.1: 'validar sobre un plan de ejemplo falla correctamente si el
        # plan está vacío' — sin tocar nada (no escribe archivos).
        with tempfile.TemporaryDirectory(prefix="cc_cli_") as tmp:
            vacio = Path(tmp) / "vacio.json"
            vacio.write_text("{}", encoding="utf-8")
            r = self._ejecuta("validar", str(vacio))
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("V103", r.stdout)

    def test_validar_plan_valido_exit_0(self):
        with tempfile.TemporaryDirectory(prefix="cc_cli_") as tmp:
            plan_path = Path(tmp) / "plan.json"
            plan_path.write_text(json.dumps(_plan_cancion(), ensure_ascii=False),
                                 encoding="utf-8")
            r = self._ejecuta("validar", str(plan_path))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("CAPA A/B: OK", r.stdout)

    def test_compilar_rechaza_plan_invalido_y_no_escribe_doc(self):
        with tempfile.TemporaryDirectory(prefix="cc_cli_") as tmp:
            plan_path = Path(tmp) / "plan.json"
            malo = _plan_cancion()
            malo["duration"]["bars_total"] = 99
            plan_path.write_text(json.dumps(malo), encoding="utf-8")
            r = self._ejecuta("compilar", str(plan_path), "--out", tmp)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertFalse((Path(tmp) / "doc.json").exists())

    def test_compilar_escribe_doc_y_plan_colocalizados(self):
        with tempfile.TemporaryDirectory(prefix="cc_cli_") as tmp:
            plan_path = Path(tmp) / "plan.json"
            plan_path.write_text(json.dumps(_plan_cancion(), ensure_ascii=False),
                                 encoding="utf-8")
            salida = Path(tmp) / "salida"
            r = self._ejecuta("compilar", str(plan_path), "--out", str(salida))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertTrue((salida / "doc.json").is_file())
            self.assertTrue((salida / "plan.json").is_file())
            doc = json.loads((salida / "doc.json").read_text(encoding="utf-8"))
            self.assertEqual(doc["global"]["seed"], 101)
            self.assertEqual(list(doc.keys())[0], "schema")
            r2 = DV.validar(doc)
            self.assertEqual(r2["errores"], [], r2["errores"])


if __name__ == "__main__":
    unittest.main()
