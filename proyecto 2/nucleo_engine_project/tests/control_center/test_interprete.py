"""Tests del Intérprete Universal — Fase 2 (spec v1.4, §12.1, §7, §9.4).

Cubre los tests/golden declarados para Fase 2:
  - determinismo del intérprete (mismo input ⇒ mismo plan, §12.1)
  - seed automática persistida y reproducible; seed explícita cambia el
    resultado de forma controlada (§9.2, §7.2.5)
  - bloqueo real de ``locked``: el intérprete no re-resuelve secciones locked
    (primera prueba de ese comportamiento, §9.1/§12.1)
  - matriz de re-resolución (capa B/A falla ⇒ re-resuelve ≤2, §12.1)
  - matriz de intenciones válidas/inválidas (§11.2)
  - contrato: intención → Plan → doc dark-director/1 limpio (§9.4)
"""
import copy
import json
import unittest

from control_center import interprete, plan_compilador, validador
from control_center import esquema_plan as EP
from control_center.esquema_plan import validar_esquema
from control_center.interprete import ErrorIntencion
from dark_director import validador as DV

AHORA = "2026-11-13T00:00:00Z"


def _intencion(**overrides):
    """Intención base completa (los 6 controles concretos, seed fija).
    Los overrides con nombre de control van a ``controls``; los de identidad
    (style/accessibility/protagonist) a ``identity``; el resto, al nivel raíz."""
    base = {
        "identity": {"style": "dark_triphop", "accessibility": "balanced",
                     "protagonist": "sax_tenor"},
        "controls": {"energia": "media", "forma": "cancion",
                     "duracion": "corta", "armonia": "nocturno",
                     "pulso": "swing", "drums": "presente"},
        "seed": 101,
    }
    for k, v in overrides.items():
        if k in EP.CONTROLES:
            base["controls"][k] = v
        elif k in ("style", "accessibility", "protagonist"):
            base["identity"][k] = v
        else:
            base[k] = v
    return base


def _sin_fecha(plan):
    """Copia del plan con evidence.created_at normalizado (§9.5: la fecha es
    el único valor no determinista y está aislado en evidence)."""
    p = copy.deepcopy(plan)
    if p.get("evidence"):
        p["evidence"]["created_at"] = ""
    return p


class DeterminismoInteprete(unittest.TestCase):
    def test_mismo_input_mismo_plan(self):
        a = interprete.resolver(_intencion(), ahora=AHORA)
        b = interprete.resolver(_intencion(), ahora=AHORA)
        self.assertEqual(_sin_fecha(a), _sin_fecha(b))

    def test_sin_seed_es_reproducible_y_persistida(self):
        inten = _intencion()
        del inten["seed"]
        a = interprete.resolver(inten, ahora=AHORA)
        b = interprete.resolver(inten, ahora=AHORA)
        self.assertIsInstance(a["seed"], int)
        self.assertEqual(a["seed"], b["seed"])
        self.assertTrue(1 <= a["seed"] <= interprete.SEED_MAX)
        # la seed queda registrada en evidence (trazabilidad, R0)
        r0 = next(r for r in a["evidence"]["resolved"]
                  if r["campo"] == "seed")
        self.assertIn(str(a["seed"]), r0["detalle"])

    def test_seed_explicita_cambia_resultado_de_forma_controlada(self):
        a = interprete.resolver(_intencion(seed=101), ahora=AHORA)
        b = interprete.resolver(_intencion(seed=202), ahora=AHORA)
        self.assertEqual(a["seed"], 101)
        self.assertEqual(b["seed"], 202)
        self.assertNotEqual(_sin_fecha(a), _sin_fecha(b))

    def test_fecha_solo_en_evidence(self):
        a = interprete.resolver(_intencion(), ahora=AHORA)
        b = interprete.resolver(_intencion(), ahora="2026-11-13T12:00:00Z")
        self.assertEqual(_sin_fecha(a), _sin_fecha(b))
        self.assertNotEqual(a["evidence"]["created_at"],
                            b["evidence"]["created_at"])

    def test_inputs_hash_formula_93(self):
        plan = interprete.resolver(_intencion(), ahora=AHORA)
        self.assertEqual(plan["evidence"]["inputs_hash"],
                         interprete.inputs_hash(
                             plan["seed"], plan["identity"], plan["controls"]))
        self.assertTrue(plan["evidence"]["inputs_hash"].startswith("sha256:"))


class ContratoPlanDoc(unittest.TestCase):
    def _plan(self):
        return interprete.resolver(_intencion(), ahora=AHORA)

    def test_plan_pasa_capas_ab(self):
        plan = self._plan()
        r = validador.validar(plan)
        self.assertTrue(r["ok"], r["errores"])

    def test_plan_completo_sin_auto_ni_null(self):
        plan = self._plan()
        self.assertEqual(plan["mode"], "automatic")

        def recorre(obj, ruta=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k == "album_context":
                        self.assertIsNone(v)
                        continue
                    self.assertIsNotNone(v, f"null en {ruta}.{k}")
                    recorre(v, f"{ruta}.{k}")
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    recorre(v, f"{ruta}[{i}]")
            elif isinstance(obj, str):
                self.assertNotEqual(obj.strip().lower(), "auto",
                                    f"'auto' en {ruta}")
        recorre(plan)

    def test_esquema_v1_y_error_explicativo_en_rerresolucion(self):
        plan = self._plan()
        errores, _ = validar_esquema(plan)
        self.assertEqual(errores, [])

    def test_doc_compilado_limpio_y_con_seed(self):
        plan = self._plan()
        doc = plan_compilador.compilar(plan)
        self.assertEqual(DV.validar(doc)["errores"], [])
        self.assertEqual(doc["global"]["seed"], plan["seed"])
        self.assertEqual(doc["global"]["bpm"], plan["global"]["bpm"])
        self.assertEqual(doc["direction"]["identity"],
                         plan["identity"]["style"])
        for t, acordes in doc["harmony"]["progressions"].items():
            self.assertIn(t, ("intro", "verse", "pre_chorus", "chorus",
                              "bridge", "break", "outro"))
            self.assertTrue(acordes)

    def test_evidence_resolved_trazable(self):
        # intención sin controles: TODO se delega y cada resolución queda
        # registrada con su regla (§7.2.4, P-04)
        inten = _intencion()
        inten.pop("controls")
        inten.pop("seed")          # sin seed: la auto-generación queda registrada (R0)
        plan = interprete.resolver(inten, ahora=AHORA)
        campos = {r["campo"] for r in plan["evidence"]["resolved"]}
        for esperado in ("controls.energia", "controls.drums",
                         "controls.forma", "controls.duracion",
                         "controls.armonia", "controls.pulso",
                         "harmony.key", "harmony.progressions",
                         "orchestration.profile", "global.bpm",
                         "duration.bars_total", "ending", "title", "seed"):
            self.assertIn(esperado, campos)
        self.assertEqual(plan["evidence"]["resolved_by"],
                         interprete.RESOLVED_BY)


class MapeosDeControles(unittest.TestCase):
    def test_tabla_idioma_por_control(self):
        pares = [("nocturno", "pop_dream_pop"), ("jazz", "hybrid"),
                 ("crudo", "experimental"), ("sombrio", "experimental")]
        for control, idioma in pares:
            plan = interprete.resolver(_intencion(armonia=control), ahora=AHORA)
            self.assertEqual(plan["harmony"]["language"], idioma)

    def test_armonia_auto_por_accesibilidad(self):
        esperado = {"commercial": "nocturno", "balanced": "jazz",
                    "experimental": "sombrio"}
        for acces, control in esperado.items():
            inten = _intencion(accessibility=acces)
            inten["controls"] = {k: v for k, v in inten["controls"].items()
                                 if k != "armonia"}
            plan = interprete.resolver(inten, ahora=AHORA)
            self.assertEqual(plan["controls"]["armonia"], control)

    def test_energia_muy_alta_exige_pico(self):
        plan = interprete.resolver(_intencion(energia="muy_alta"), ahora=AHORA)
        self.assertTrue(max(s["energy"] for s in
                            plan["form"]["sections"]) >= 0.7)

    def test_drums_ausente_coherente(self):
        inten = _intencion(drums="ausente")
        plan = interprete.resolver(inten, ahora=AHORA)
        self.assertTrue(all(s["drums"] == "off"
                            for s in plan["form"]["sections"]))
        self.assertIn(plan["orchestration"]["profile"],
                      interprete.PERFILES_SIN_DRUMS)
        r = validador.validar(plan)
        self.assertTrue(r["ok"], r["errores"])

    def test_drums_protagonista_coherente(self):
        plan = interprete.resolver(_intencion(drums="protagonista"),
                                   ahora=AHORA)
        self.assertTrue(any(s["drums"] in ("groove", "heavy")
                            for s in plan["form"]["sections"]))
        self.assertIn(plan["orchestration"]["profile"],
                      interprete.PERFILES_CON_DRUMS)

    def test_protagonista_en_dos_secciones_y_solo_en_alta(self):
        # R30 (hallazgo P-02): el lead (sax_tenor) no recibe solo automático;
        # protagonismo garantizado por V113 (focus en ≥2 secciones).
        plan = interprete.resolver(_intencion(energia="alta"), ahora=AHORA)
        prota = plan["identity"]["protagonist"]
        self.assertEqual(prota, "sax_tenor")
        self.assertGreaterEqual(
            sum(1 for s in plan["form"]["sections"]
                if prota in s["focus"]), 2)
        self.assertEqual(plan["solos"], [])

    def test_solo_automatico_de_protagonista_no_lead(self):
        for prota in ("rhodes", "vibraphone"):
            with self.subTest(protagonista=prota):
                plan = interprete.resolver(_intencion(energia="alta",
                                                      protagonist=prota),
                                           ahora=AHORA)
                self.assertEqual(len(plan["solos"]), 1)
                solo = plan["solos"][0]
                self.assertEqual(solo["instrument"], prota)
                sec = next(s for s in plan["form"]["sections"]
                           if s["id"] == solo["section_id"])
                self.assertIn(sec["type"], ("break", "bridge"))
                self.assertEqual(sec["focus"], [prota])
                minima = min(s["energy"] for s in plan["form"]["sections"])
                self.assertGreater(sec["energy"], minima)

    def test_cancion_tiene_intro_y_outro_unicos(self):
        plan = interprete.resolver(_intencion(forma="cancion"), ahora=AHORA)
        tipos = [s["type"] for s in plan["form"]["sections"]]
        self.assertEqual(tipos.count("intro"), 1)
        self.assertEqual(tipos.count("outro"), 1)

    def test_suma_bars_igual_bars_total(self):
        for duracion in ("corta", "media", "larga"):
            plan = interprete.resolver(_intencion(duracion=duracion),
                                       ahora=AHORA)
            self.assertEqual(sum(s["bars"] for s in plan["form"]["sections"]),
                             plan["duration"]["bars_total"])

    def test_bpm_dentro_del_rango_tipico_de_la_receta(self):
        plan = interprete.resolver(_intencion(pulso="lento_arrastrado"),
                                   ahora=AHORA)
        lo, hi = (70, 96)
        self.assertGreaterEqual(plan["global"]["bpm"], lo)
        self.assertLessEqual(plan["global"]["bpm"], hi)

    def test_seed_diferente_elige_key_diferente_o_misma_estable(self):
        keys = [interprete.resolver(_intencion(seed=s), ahora=AHORA)
                ["harmony"]["key"] for s in (101, 202, 303, 404)]
        self.assertEqual(len(set(keys)), len(keys) or 1)
        for k in keys:
            self.assertIn(k, interprete.POOL_KEYS)


class BloqueoLocked(unittest.TestCase):
    """El bloqueo real de ``locked`` frente al intérprete (§9.1, §12.1)."""

    def _secciones_con_salto(self, lock_s1=False, lock_s2=False):
        sec = [
            {"id": "s1", "type": "intro", "bars": 4, "energy": 0.85,
             "tension": 0.2, "density": 0.2, "focus": ["rhodes", "pad"],
             "drums": "air"},
            {"id": "s2", "type": "verse", "bars": 8, "energy": 0.15,
             "tension": 0.3, "density": 0.4, "focus": ["sax_tenor"],
             "drums": "groove"},
            {"id": "s3", "type": "chorus", "bars": 8, "energy": 0.6,
             "tension": 0.5, "density": 0.6, "focus": ["sax_tenor", "bass"],
             "drums": "heavy"},
            {"id": "s4", "type": "outro", "bars": 4, "energy": 0.3,
             "tension": 0.2, "density": 0.2, "focus": ["rhodes"],
             "drums": "air"},
        ]
        sec[0]["locked"] = lock_s1
        sec[1]["locked"] = lock_s2
        return sec

    def test_rerresolucion_suaviza_seccion_no_locked(self):
        inten = _intencion()
        inten["form"] = {"sections": self._secciones_con_salto()}
        plan = interprete.resolver(inten, ahora=AHORA)
        secciones = {s["id"]: s for s in plan["form"]["sections"]}
        salto = abs(secciones["s1"]["energy"] - secciones["s2"]["energy"])
        self.assertLessEqual(salto, 0.4)
        r = validador.validar(plan)
        self.assertTrue(r["ok"], r["errores"])

    def test_locked_no_se_toca_y_salto_se_corrige_por_el_otro_lado(self):
        inten = _intencion()
        inten["form"] = {"sections": self._secciones_con_salto(lock_s2=True)}
        plan = interprete.resolver(inten, ahora=AHORA)
        secciones = {s["id"]: s for s in plan["form"]["sections"]}
        self.assertEqual(secciones["s2"]["energy"], 0.15)   # locked intacta
        salto = abs(secciones["s1"]["energy"] - secciones["s2"]["energy"])
        self.assertLessEqual(salto, 0.4)
        r = validador.validar(plan)
        self.assertTrue(r["ok"], r["errores"])

    def test_dos_locked_irreconciliables_devuelven_error_explicativo(self):
        inten = _intencion()
        secciones = self._secciones_con_salto(lock_s1=True, lock_s2=True)
        secciones[0]["energy"] = 0.9
        secciones[1]["energy"] = 0.1
        inten["form"] = {"sections": secciones}
        with self.assertRaises(ErrorIntencion) as ctx:
            interprete.resolver(inten, ahora=AHORA)
        self.assertIn("re-resolución", str(ctx.exception))

    def test_solo_sobre_seccion_locked_error_explicativo(self):
        inten = _intencion()
        secciones = self._secciones_con_salto(lock_s2=True)
        inten["form"] = {"sections": secciones}
        inten["solos"] = [{"section_id": "s2", "instrument": "sax_tenor"}]
        with self.assertRaises(ErrorIntencion) as ctx:
            interprete.resolver(inten, ahora=AHORA)
        self.assertIn("locked", str(ctx.exception))

    def test_secciones_aportadas_se_respetan_y_protagonista_se_garantiza(self):
        inten = _intencion()
        secciones = self._secciones_con_salto()
        for s in secciones:
            s["focus"] = [f for f in s["focus"] if f != "sax_tenor"]
        secciones[2]["focus"] = ["bass"]
        inten["form"] = {"sections": secciones}
        plan = interprete.resolver(inten, ahora=AHORA)
        self.assertGreaterEqual(
            sum(1 for s in plan["form"]["sections"]
                if "sax_tenor" in s["focus"]), 2)
        # bars aportados intactos
        aportados = {s["id"]: s["bars"] for s in secciones}
        for s in plan["form"]["sections"]:
            self.assertEqual(s["bars"], aportados[s["id"]])


class MatrizReResolucion(unittest.TestCase):
    """Capa B/A falla ⇒ re-resuelve ≤2 (§12.1); cada intento queda registrado."""

    def _intencion_con_secciones(self):
        inten = _intencion()
        inten["form"] = {"sections": [
            {"id": "s1", "type": "intro", "bars": 4, "energy": 0.3,
             "tension": 0.2, "density": 0.2, "focus": ["rhodes", "pad"],
             "drums": "air"},
            {"id": "s2", "type": "verse", "bars": 8, "energy": 0.5,
             "tension": 0.3, "density": 0.4, "focus": ["sax_tenor"],
             "drums": "groove"},
            {"id": "s3", "type": "chorus", "bars": 8, "energy": 0.9,
             "tension": 0.5, "density": 0.6, "focus": ["bass"],
             "drums": "heavy"},
            {"id": "s4", "type": "outro", "bars": 4, "energy": 0.2,
             "tension": 0.2, "density": 0.2, "focus": ["rhodes"],
             "drums": "air"},
        ]}
        return inten

    def test_salto_09_a_02_se_corrige(self):
        inten = self._intencion_con_secciones()
        inten["form"]["sections"][2]["energy"] = 0.9
        inten["form"]["sections"][3]["energy"] = 0.2
        plan = interprete.resolver(inten, ahora=AHORA)
        secciones = {s["id"]: s for s in plan["form"]["sections"]}
        self.assertLessEqual(
            abs(secciones["s3"]["energy"] - secciones["s4"]["energy"]), 0.4)
        r = validador.validar(plan)
        self.assertTrue(r["ok"], r["errores"])

    def test_energia_alta_sin_pico_se_corige(self):
        inten = self._intencion_con_secciones()
        inten["controls"]["energia"] = "alta"
        inten["form"]["sections"][2]["energy"] = 0.5   # sin pico ≥0.7
        plan = interprete.resolver(inten, ahora=AHORA)
        self.assertTrue(max(s["energy"] for s in
                            plan["form"]["sections"]) >= 0.7)
        r = validador.validar(plan)
        self.assertTrue(r["ok"], r["errores"])

    def test_protagonista_insuficiente_se_refuerza(self):
        inten = self._intencion_con_secciones()
        for s in inten["form"]["sections"]:
            s["focus"] = [f for f in s["focus"] if f != "sax_tenor"]
        plan = interprete.resolver(inten, ahora=AHORA)
        self.assertGreaterEqual(
            sum(1 for s in plan["form"]["sections"]
                if "sax_tenor" in s["focus"]), 2)


class IntencionesInvalidas(unittest.TestCase):
    def test_identity_requerida(self):
        with self.assertRaises(ErrorIntencion):
            interprete.resolver({}, ahora=AHORA)
        with self.assertRaises(ErrorIntencion):
            interprete.resolver({"identity": {}}, ahora=AHORA)

    def test_estilo_fuera_de_catalogo(self):
        inten = _intencion()
        inten["identity"]["style"] = "techno"
        with self.assertRaises(ErrorIntencion) as ctx:
            interprete.resolver(inten, ahora=AHORA)
        self.assertIn("IDENTITIES", str(ctx.exception))

    def test_protagonista_no_melodico(self):
        inten = _intencion()
        inten["identity"]["protagonist"] = "bass"
        with self.assertRaises(ErrorIntencion):
            interprete.resolver(inten, ahora=AHORA)

    def test_control_fuera_de_catalogo(self):
        inten = _intencion()
        inten["controls"]["energia"] = "brutal"
        with self.assertRaises(ErrorIntencion) as ctx:
            interprete.resolver(inten, ahora=AHORA)
        self.assertIn("energia", str(ctx.exception))

    def test_control_desconocido(self):
        inten = _intencion()
        inten["controls"]["mood"] = "feliz"
        with self.assertRaises(ErrorIntencion) as ctx:
            interprete.resolver(inten, ahora=AHORA)
        self.assertIn("desconocidos", str(ctx.exception))

    def test_claves_desconocidas_en_la_intencion(self):
        inten = _intencion()
        inten["identty"] = {}          # typo del usuario (no es identidad)
        with self.assertRaises(ErrorIntencion) as ctx:
            interprete.resolver(inten, ahora=AHORA)
        self.assertIn("identty", str(ctx.exception))

    def test_album_context_no_null(self):
        inten = _intencion(album_context={"arco": 0.5})
        with self.assertRaises(ErrorIntencion) as ctx:
            interprete.resolver(inten, ahora=AHORA)
        self.assertIn("album_context", str(ctx.exception))

    def test_seed_negativa(self):
        with self.assertRaises(ErrorIntencion):
            interprete.resolver(_intencion(seed=-3), ahora=AHORA)

    def test_mode_guided_rechazado(self):
        with self.assertRaises(ErrorIntencion) as ctx:
            interprete.resolver(_intencion(mode="guided"), ahora=AHORA)
        self.assertIn("guided", str(ctx.exception))

    def test_palette_incoherente_con_drums_error_explicativo(self):
        inten = _intencion(drums="protagonista")
        inten["identity"]["palette"] = ["sax", "sax_rhodes"]
        with self.assertRaises(ErrorIntencion) as ctx:
            interprete.resolver(inten, ahora=AHORA)
        self.assertIn("palette", str(ctx.exception))

    def test_palette_con_original_rechazada(self):
        inten = _intencion()
        inten["identity"]["palette"] = ["original", "full"]
        with self.assertRaises(ErrorIntencion):
            interprete.resolver(inten, ahora=AHORA)

    def test_palette_desconocida(self):
        inten = _intencion()
        inten["identity"]["palette"] = ["sinfonico"]
        with self.assertRaises(ErrorIntencion):
            interprete.resolver(inten, ahora=AHORA)

    def test_key_y_progresiones_aportadas_incompatibles_error_explicativo(self):
        # Advanced aporta tonalidad + progresión con acorde fuera de tónica y
        # vecinas (V110): el intérprete NO reescribe progresiones concretas →
        # error explicativo tras la re-resolución
        inten = _intencion()
        inten["harmony"] = {"key": "A minor",
                            "progressions": {"verse": ["Ebmaj7"]}}
        with self.assertRaises(ErrorIntencion) as ctx:
            interprete.resolver(inten, ahora=AHORA)
        self.assertIn("V110", str(ctx.exception))

    def test_secciones_incompletas_rechazadas(self):
        inten = _intencion()
        inten["form"] = {"sections": [{"id": "x", "type": "verse"}]}
        with self.assertRaises(ErrorIntencion) as ctx:
            interprete.resolver(inten, ahora=AHORA)
        self.assertIn("incompleta", str(ctx.exception))

    def test_forma_cancion_irresoluble_con_muy_pocos_compases(self):
        inten = _intencion()
        inten["controls"]["duracion"] = "corta"
        inten["global"] = {"bpm": 40}          # Advanced: bpm muy lento
        inten["duration"] = {"bars_total": 12}  # < 4 secciones de 4 bars... no: 3×4
        with self.assertRaises(ErrorIntencion) as ctx:
            interprete.resolver(inten, ahora=AHORA)
        self.assertIn("cancion", str(ctx.exception))

    def test_solos_seccion_inexistente(self):
        inten = _intencion()
        inten["solos"] = [{"section_id": "no_existe", "instrument": "sax_tenor"}]
        with self.assertRaises(ErrorIntencion):
            interprete.resolver(inten, ahora=AHORA)


class FlujoEndToEnd(unittest.TestCase):
    def test_intencion_a_doc_y_configuracion_coherente(self):
        inten = _intencion(energia="alta")
        plan = interprete.resolver(inten, ahora=AHORA)
        doc = plan_compilador.compilar(plan)
        self.assertEqual(doc["schema"], "dark-director/1")
        self.assertEqual(len(doc["structure"]), len(plan["form"]["sections"]))
        if plan["solos"] and plan["solos"][0]["instrument"] == "sax_tenor":
            self.assertIn("development", doc)
            self.assertEqual(
                doc["development"]["improvisation"][0]["section"],
                plan["solos"][0]["section_id"])
        self.assertEqual(doc["ending"]["fade_out"]["bars"],
                         plan["ending"]["fade_out"]["bars"])
        self.assertEqual(DV.validar(doc)["errores"], [])


if __name__ == "__main__":
    unittest.main()
