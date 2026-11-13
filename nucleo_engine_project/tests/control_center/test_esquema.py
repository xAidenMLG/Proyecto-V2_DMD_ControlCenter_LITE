"""Tests unitarios del contrato v1 del Composition Plan (§9.2, §11.2 Unit).

Cubre: catálogos importados sin deriva de dark_director/contract.py, campos
requeridos/tipos/enums, campos desconocidos (V106), plan_version (V102) y los
límites numéricos de §9.2. Patrón: tests/dmd/test_validador.py (unittest +
sys.path al ROOT del motor).
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from control_center import esquema_plan as EP  # noqa: E402
from dark_director import contract  # noqa: E402


def _plan_base():
    """Plan cancion mínimo válido (3 secciones: intro + verse + outro)."""
    return {
        "plan_version": 1,
        "mode": "guided",
        "seed": 3113,
        "title": "Plan de prueba",
        "identity": {"style": "dark_triphop", "accessibility": "balanced",
                     "protagonist": "sax_tenor"},
        "controls": {"energia": "media", "forma": "cancion", "duracion": "corta",
                     "armonia": "nocturno", "pulso": "swing", "drums": "presente"},
        "album_context": None,
        "form": {"template": "cancion", "sections": [
            {"id": "intro", "type": "intro", "bars": 4, "energy": 0.3,
             "tension": 0.2, "density": 0.25, "focus": ["rhodes", "pad"],
             "drums": "air", "locked": False},
            {"id": "v", "type": "verse", "bars": 8, "energy": 0.55,
             "tension": 0.35, "density": 0.5, "focus": ["sax_tenor"],
             "drums": "groove", "locked": False},
            {"id": "out", "type": "outro", "bars": 4, "energy": 0.3,
             "tension": 0.2, "density": 0.25, "focus": ["sax_tenor"],
             "drums": "air", "locked": False},
        ]},
        "harmony": {"key": "D minor", "language": "pop_dream_pop",
                    "harmonic_rhythm_bars": 2,
                    "progressions": {"verse": ["Dm9", "Gm9", "Am7"]}},
        "orchestration": {"profile": "full"},
        "global": {"bpm": 72},
        "duration": {"target": "corta", "bars_total": 16},
        "notes": "Anotación para humanos (§9.2); nadie decide música con ella.",
        "evidence": {"resolved_by": "manual@fase1", "resolved": [],
                     "inputs_hash": "sha256:" + "0" * 64,
                     "created_at": "2026-11-12T00:00:00Z"},
    }


class CatalogosDesdeContrato(unittest.TestCase):
    """§9.1.4: los catálogos cerrados se importan, no se duplican."""

    def test_catalogos_identicos_a_contract(self):
        self.assertEqual(EP.SECTION_TYPES, contract.SECTION_TYPES)
        self.assertEqual(EP.INSTRUMENT_IDS, contract.INSTRUMENT_IDS)
        self.assertEqual(EP.DRUMS_LADDER, contract.DRUMS_LADDER)
        self.assertEqual(EP.IDENTITIES, contract.IDENTITIES)
        self.assertEqual(EP.ACCESSIBILITIES, contract.ACCESSIBILITIES)
        self.assertEqual(EP.LANGUAGES, contract.LANGUAGES)

    def test_perfiles_son_los_reales_de_production(self):
        from jazz_engine import production
        self.assertEqual(EP.PERFILES_PRODUCCION, production.nombres())
        self.assertEqual(len(EP.PERFILES_PRODUCCION), 7)

    def test_plan_version_es_1(self):
        self.assertEqual(EP.PLAN_VERSION, 1)

    def test_controles_son_exactamente_los_6_de_guia(self):
        self.assertEqual(set(EP.CONTROLES),
                         {"energia", "forma", "duracion", "armonia", "pulso", "drums"})


class EsquemaValido(unittest.TestCase):
    def test_plan_base_pasa_sin_errores(self):
        errores, _ = EP.validar_esquema(_plan_base())
        self.assertEqual(errores, [])

    def test_controles_opcionales_y_sin_controls(self):
        plan = _plan_base()
        del plan["controls"]
        del plan["notes"]
        errores, _ = EP.validar_esquema(plan)
        self.assertEqual(errores, [])

    def test_notes_null_no_es_admitido_como_otro_tipo(self):
        plan = _plan_base()
        plan["notes"] = None
        errores, _ = EP.validar_esquema(plan)
        self.assertEqual(errores, [])  # None = campo no declarado (se omite al compilar)


class Requeridos(unittest.TestCase):
    def _sin(self, clave):
        plan = _plan_base()
        del plan[clave]
        return plan

    def test_raiz_no_objeto(self):
        errores, _ = EP.validar_esquema([1, 2, 3])
        self.assertEqual(errores[0]["codigo"], "V101")

    def test_campos_requeridos_ausentes(self):
        for campo in ("plan_version", "mode", "seed", "title", "identity",
                      "form", "harmony", "orchestration", "global", "duration"):
            with self.subTest(campo=campo):
                errores, _ = EP.validar_esquema(self._sin(campo))
                codigos = [e["codigo"] for e in errores]
                self.assertIn("V103", codigos, campo)

    def test_plan_vacio_falla_con_requeridos(self):
        errores, _ = EP.validar_esquema({})
        self.assertTrue(any(e["codigo"] == "V103" for e in errores))

    def test_requeridos_anidados(self):
        plan = _plan_base()
        del plan["identity"]["protagonist"]
        del plan["harmony"]["progressions"]
        del plan["global"]["bpm"]
        del plan["duration"]["bars_total"]
        errores, _ = EP.validar_esquema(plan)
        self.assertEqual(len([e for e in errores if e["codigo"] == "V103"]), 4)


class Tipos(unittest.TestCase):
    def test_tipos_incorrectos(self):
        casos = [
            ("seed", "3113"),                    # str en vez de int
            ("seed", True),                      # bool no es int aquí
            ("title", 42),
            ("notes", 7),
            ("global", {"bpm": "72"}),
            ("duration", {"target": "corta", "bars_total": "16"}),
            ("ending", {"fade_out": {"enabled": "sí", "bars": 2}}),
        ]
        for clave, valor in casos:
            with self.subTest(campo=clave, valor=valor):
                plan = _plan_base()
                plan[clave] = valor
                errores, _ = EP.validar_esquema(plan)
                self.assertTrue(any(e["codigo"] == "V104" for e in errores), clave)

    def test_tipos_en_seccion(self):
        sustituciones = [
            ({"id": "v"}, {"bars": "8"}),
            ({"id": "v"}, {"bars": True}),
            ({"id": "v"}, {"energy": "0.55"}),
            ({"id": "v"}, {"focus": "sax_tenor"}),
            ({"id": "v"}, {"focus": []}),
            ({"id": "v"}, {"drums": 4}),
            ({"id": "v"}, {"locked": "no"}),
            ({"id": "out"}, {"final": 1}),
        ]
        for selector, cambio in sustituciones:
            with self.subTest(cambio=cambio):
                plan = _plan_base()
                i = next(i for i, s in enumerate(plan["form"]["sections"])
                         if all(s.get(k) == v for k, v in selector.items()))
                plan["form"]["sections"][i].update(cambio)
                errores, _ = EP.validar_esquema(plan)
                self.assertTrue(any(e["codigo"] == "V104" for e in errores), cambio)


class CatalogosYRangos(unittest.TestCase):
    def test_valores_fuera_de_catalogo(self):
        casos = [
            ("mode", "hybrid"),
            ("identity", {"style": "bossa", "accessibility": "balanced",
                          "protagonist": "sax_tenor"}),
            ("identity", {"style": "dark_triphop", "accessibility": "brutal",
                          "protagonist": "sax_tenor"}),
            ("identity", {"style": "dark_triphop", "accessibility": "balanced",
                          "protagonist": "theremin"}),
            ("orchestration", {"profile": "saxofon"}),
            ("global", {"bpm": 300}),
            ("global", {"bpm": 20}),
            ("duration", {"target": "eterna", "bars_total": 16}),
            ("harmony", {"key": "D minor", "language": "bebop",
                         "harmonic_rhythm_bars": 2, "progressions": {"verse": ["Dm9"]}}),
        ]
        for clave, valor in casos:
            with self.subTest(campo=clave, valor=valor):
                plan = _plan_base()
                plan[clave] = valor
                errores, _ = EP.validar_esquema(plan)
                self.assertTrue(any(e["codigo"] == "V105" for e in errores), clave)

    def test_rangos_de_seccion(self):
        sustituciones = [
            ({"id": "v"}, {"bars": 0}),          # §11.2: secciones a 0 compases
            ({"id": "v"}, {"bars": 20}),
            ({"id": "v"}, {"bars": 3}),
            ({"id": "v"}, {"energy": 1.5}),
            ({"id": "v"}, {"energy": -0.1}),
            ({"id": "v"}, {"density": 2.0}),
            ({"id": "v"}, {"drums": "loud"}),
            ({"id": "v"}, {"type": "estribillo"}),
            ({"id": "v"}, {"focus": ["theremin"]}),
        ]
        for selector, cambio in sustituciones:
            with self.subTest(cambio=cambio):
                plan = _plan_base()
                i = next(i for i, s in enumerate(plan["form"]["sections"])
                         if all(s.get(k) == v for k, v in selector.items()))
                plan["form"]["sections"][i].update(cambio)
                errores, _ = EP.validar_esquema(plan)
                self.assertTrue(any(e["codigo"] == "V105" for e in errores), cambio)

    def test_seed_negativa_rechazada(self):
        plan = _plan_base()
        plan["seed"] = -1
        errores, _ = EP.validar_esquema(plan)
        self.assertTrue(any(e["codigo"] == "V105" and "seed" in e["mensaje"]
                            for e in errores))

    def test_progressions_vacio_y_claves_ajenas(self):
        plan = _plan_base()
        plan["harmony"]["progressions"] = {}
        errores, _ = EP.validar_esquema(plan)
        self.assertTrue(any(e["codigo"] == "V104" for e in errores))
        plan["harmony"]["progressions"] = {"estribillo": ["Dm9"]}
        errores, _ = EP.validar_esquema(plan)
        self.assertTrue(any(e["codigo"] == "V105" for e in errores))

    def test_palette_con_perfil_ajeno(self):
        plan = _plan_base()
        plan["identity"]["palette"] = ["full", "orquesta"]
        errores, _ = EP.validar_esquema(plan)
        self.assertTrue(any(e["codigo"] == "V105" for e in errores))

    def test_fade_out_bars_cero(self):
        plan = _plan_base()
        plan["ending"] = {"fade_out": {"enabled": True, "bars": 0}}
        errores, _ = EP.validar_esquema(plan)
        self.assertTrue(any(e["codigo"] == "V105" for e in errores))


class CamposDesconocidos(unittest.TestCase):
    def _y_comprobar(self, mutar):
        plan = _plan_base()
        mutar(plan)
        errores, _ = EP.validar_esquema(plan)
        self.assertTrue(any(e["codigo"] == "V106" for e in errores))

    def test_campo_top_level_desconocido(self):
        self._y_comprobar(lambda p: p.update({"harmony_vocabulary": ["x"]}))

    def test_campo_en_identity_y_seccion_y_harmony(self):
        self._y_comprobar(lambda p: p["identity"].update({"mood": "dark"}))
        self._y_comprobar(lambda p: p["form"]["sections"][0].update({"gain": 0.8}))
        self._y_comprobar(lambda p: p["harmony"].update({"key_plan": "x"}))
        self._y_comprobar(lambda p: p["controls"].update({"bpm": 90}))
        self._y_comprobar(lambda p: p["orchestration"].update({"drums": True}))
        self._y_comprobar(lambda p: p.setdefault(
            "ending", {"fade_out": {"enabled": True, "bars": 2}}).update({"tape_stop": {}}))

    def test_extension_x_rechazada_en_f1(self):
        # §9.1.4: la vía x_* es del doc (meta.director) y "futura"; el plan v1
        # es cerrado y el validador nunca adivina.
        self._y_comprobar(lambda p: p.update({"x_deseo": "más bajo"}))


class VersionYEstados(unittest.TestCase):
    def test_plan_version_desconocida_rechazada(self):
        plan = _plan_base()
        plan["plan_version"] = 2
        errores, _ = EP.validar_esquema(plan)
        self.assertTrue(any(e["codigo"] == "V102" for e in errores))

    def test_mode_fuera_de_catalogo(self):
        plan = _plan_base()
        plan["mode"] = "magic"
        errores, _ = EP.validar_esquema(plan)
        self.assertTrue(any(e["codigo"] == "V105" for e in errores))


if __name__ == "__main__":
    unittest.main()
