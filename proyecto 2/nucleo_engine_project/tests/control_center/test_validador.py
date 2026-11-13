"""Matriz del validador de planes — capas A y B (§6.1/§6.2; §11.2 ≥12 casos).

Casos de la matriz de validación de §11.2 cubiertos aquí: secciones a 0
compases, bars_total ≠ Σ bars, controls.drums="ausente" con drums≠off y con
perfil drums:True, acorde fuera de tónica y vecinas, perfil desconocido, seed
negativa, locked válido y conservado (F1: se valida y se descarta del doc; su
bloqueo frente al intérprete se prueba por primera vez en F2, §12.1),
mode="automatic" en F1, valor literal "auto", album_context ≠ null en F1,
forma cancion sin intro/outro, solo mal materializado, solo en la sección de
menor energía, protagonista en <2 secciones, transición >0.4 (cancion),
cadencia ausente (cancion), energía alta sin pico, ids duplicados y —
regla v1.3 — repetición idéntica de secciones que NO es gate en ciclos.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from control_center import esquema_plan as EP  # noqa: E402
from control_center import plan_compilador, validador  # noqa: E402


def _seccion(id_, tipo, bars, e, t, d, focus, drums, **extra):
    sec = {"id": id_, "type": tipo, "bars": bars, "energy": e, "tension": t,
           "density": d, "focus": focus, "drums": drums}
    sec.update(extra)
    return sec


def _plan_cancion():
    """Plan cancion completo y válido (5 secciones, 32 bars, seed 101-like)."""
    return {
        "plan_version": 1,
        "mode": "guided",
        "seed": 101,
        "title": "Cuartos de Marea",
        "identity": {"style": "dark_triphop", "accessibility": "balanced",
                     "protagonist": "sax_tenor", "palette": ["full"]},
        "controls": {"energia": "alta", "forma": "cancion", "duracion": "corta",
                     "armonia": "nocturno", "pulso": "lento_arrastrado",
                     "drums": "presente"},
        "album_context": None,
        "form": {"template": "cancion", "sections": [
            _seccion("intro", "intro", 4, 0.30, 0.20, 0.25, ["rhodes", "pad"], "air"),
            _seccion("verso_a", "verse", 8, 0.50, 0.35, 0.50, ["sax_tenor"], "groove"),
            _seccion("coro_a", "chorus", 8, 0.75, 0.45, 0.65, ["sax_tenor", "bass"], "heavy"),
            _seccion("verso_b", "verse", 8, 0.55, 0.30, 0.40, ["sax_tenor"], "groove"),
            _seccion("outro", "outro", 4, 0.30, 0.20, 0.25, ["rhodes"], "air"),
        ]},
        "ending": {"fade_out": {"enabled": True, "bars": 2}},
        "harmony": {"key": "D minor", "language": "pop_dream_pop",
                    "harmonic_rhythm_bars": 2,
                    "progressions": {
                        "verse": ["Dm9", "Gm9", "Bbmaj9", "Am7"],
                        "chorus": ["Bbmaj9", "Fmaj9", "Gm9", "Dm9"]}},
        "orchestration": {"profile": "full"},
        "global": {"bpm": 72},
        "duration": {"target": "corta", "bars_total": 32},
        "notes": "plan cancion de referencia para la matriz",
        "evidence": {"resolved_by": "manual@fase1", "resolved": [],
                     "inputs_hash": "sha256:" + "1" * 64,
                     "created_at": "2026-11-12T00:00:00Z"},
    }


def _plan_ciclos():
    """Plan ciclos completo y válido (7 secciones × 8, protagonista rhodes)."""
    return {
        "plan_version": 1,
        "mode": "guided",
        "seed": 202,
        "title": "Calles de Ceniza",
        "identity": {"style": "doom_dark_jazz", "accessibility": "balanced",
                     "protagonist": "rhodes", "palette": ["full", "atmospheric"]},
        "controls": {"energia": "media", "forma": "ciclos", "duracion": "media",
                     "armonia": "jazz", "pulso": "swing", "drums": "contenida"},
        "album_context": None,
        "form": {"template": "ciclos", "sections": [
            _seccion("vuelta_a1", "verse", 8, 0.45, 0.40, 0.45, ["rhodes"], "light"),
            _seccion("vuelta_a2", "verse", 8, 0.45, 0.40, 0.45, ["rhodes"], "light"),
            _seccion("vuelta_b1", "bridge", 8, 0.60, 0.55, 0.55, ["rhodes", "vibraphone"], "groove"),
            _seccion("vuelta_a3", "verse", 8, 0.45, 0.40, 0.45, ["rhodes"], "light"),
            _seccion("solo_rhodes", "break", 8, 0.60, 0.50, 0.60, ["rhodes"], "groove"),
            _seccion("cierre_o", "outro", 8, 0.30, 0.25, 0.30, ["rhodes"], "air"),
        ]},
        "ending": {"fade_out": {"enabled": True, "bars": 4}},
        "harmony": {"key": "F minor", "language": "hybrid",
                    "harmonic_rhythm_bars": 2,
                    "progressions": {"verse": ["Fm9", "Bbm7", "Ebmaj7", "Abmaj9"]}},
        "solos": [{"section_id": "solo_rhodes", "instrument": "rhodes"}],
        "orchestration": {"profile": "atmospheric"},
        "global": {"bpm": 64},
        "duration": {"target": "media", "bars_total": 48},
        "notes": "vamp A-A-B-A con solo de rhodes; repetición idéntica intencional",
    }


class CapasAyBPlanesValidos(unittest.TestCase):
    def test_plan_cancion_valido_pasa(self):
        r = validador.validar(_plan_cancion())
        self.assertTrue(r["ok"], r["errores"])

    def test_plan_ciclos_valido_pasa_con_repeticion_identica(self):
        # Regla v1.3: la repetición idéntica entre secciones del mismo type es
        # válida (vamp); la capa B NO exige diferenciación de density.
        r = validador.validar(_plan_ciclos())
        self.assertTrue(r["ok"], r["errores"])

    def test_plan_minimo_sin_controls_ni_ending_ni_notes(self):
        plan = _plan_cancion()
        for k in ("controls", "ending", "notes", "identity.palette"):
            # palette está dentro de identity: se elimina aparte
            pass
        del plan["controls"], plan["ending"], plan["notes"]
        del plan["identity"]["palette"]
        r = validador.validar(plan)
        self.assertTrue(r["ok"], r["errores"])

    def test_fase_desconocida_rechazada(self):
        # F2 implementa fase=2 (§12.1); el validador sigue sin adivinar (§9.5):
        # una fase desconocida se rechaza con error explícito.
        r = validador.validar(_plan_cancion(), fase=2)
        self.assertTrue(r["ok"], r["errores"])
        with self.assertRaises(ValueError):
            validador.validar(_plan_cancion(), fase=3)


class CapaAForma(unittest.TestCase):
    def test_bars_total_distinto_de_suma(self):
        plan = _plan_cancion()
        plan["duration"]["bars_total"] = 30
        r = validador.validar(plan)
        self.assertTrue(any(e["codigo"] == "V109" and "bars_total" in e["mensaje"]
                            for e in r["errores"]))

    def test_seccion_a_cero_compases(self):
        plan = _plan_cancion()
        plan["form"]["sections"][0]["bars"] = 0
        r = validador.validar(plan)
        self.assertTrue(any(e["codigo"] == "V105" for e in r["errores"]))

    def test_ids_duplicados(self):
        plan = _plan_cancion()
        plan["form"]["sections"][1]["id"] = "intro"
        r = validador.validar(plan)
        self.assertTrue(any(e["codigo"] == "V109" and "duplicados" in e["mensaje"]
                            for e in r["errores"]))

    def test_cancion_sin_intro_o_sin_outro(self):
        for quitar in ("intro", "outro"):
            with self.subTest(seccion=quitar):
                plan = _plan_cancion()
                plan["form"]["sections"] = [s for s in plan["form"]["sections"]
                                            if s["id"] != quitar]
                plan["duration"]["bars_total"] = sum(
                    s["bars"] for s in plan["form"]["sections"])
                r = validador.validar(plan)
                self.assertTrue(any(e["codigo"] == "V109" for e in r["errores"]))

    def test_mas_de_9_secciones(self):
        plan = _plan_cancion()
        secciones = [dict(plan["form"]["sections"][0], id=f"s{i}") for i in range(10)]
        plan["form"]["sections"] = secciones
        plan["duration"]["bars_total"] = sum(s["bars"] for s in secciones)
        r = validador.validar(plan)
        self.assertTrue(any(e["codigo"] == "V109" for e in r["errores"]))


class CapaAEstadosF1(unittest.TestCase):
    def test_mode_automatic_rechazado_en_f1(self):
        # gate de estados de fase=1, conservado (se solicita explícitamente);
        # en la fase actual (2) un plan completo mode="automatic" es legal.
        plan = _plan_cancion()
        plan["mode"] = "automatic"
        r = validador.validar(plan, fase=1)
        self.assertTrue(any(e["codigo"] == "V108" and "automatic" in e["mensaje"]
                            for e in r["errores"]))
        r2 = validador.validar(plan)
        self.assertTrue(all(e["codigo"] != "V108" or "automatic" not in e["mensaje"]
                            for e in r2["errores"]), r2["errores"])

    def test_valor_literal_auto_rechazado(self):
        plan = _plan_cancion()
        plan["duration"]["target"] = "auto"
        r = validador.validar(plan)
        self.assertTrue(any(e["codigo"] in ("V105", "V108") for e in r["errores"]))
        plan2 = _plan_cancion()
        plan2["controls"]["pulso"] = "auto"
        r2 = validador.validar(plan2)
        self.assertTrue(any(e["codigo"] in ("V105", "V108") for e in r2["errores"]))

    def test_album_context_no_null_rechazado(self):
        plan = _plan_cancion()
        plan["album_context"] = {"arco": "ascendente"}
        r = validador.validar(plan)
        self.assertTrue(any(e["codigo"] == "V108" and "album_context" in e["mensaje"]
                            for e in r["errores"]))

    def test_campo_null_rechazado(self):
        # §6.1 estricto: en F1 ningún campo queda en null (plan completo);
        # la única excepción es album_context, que DEBE ser null.
        plan = _plan_cancion()
        plan["notes"] = None
        r = validador.validar(plan)
        self.assertFalse(r["ok"])
        self.assertTrue(any(e["codigo"] == "V108" for e in r["errores"]))
        plan2 = _plan_cancion()
        plan2["title"] = None
        r2 = validador.validar(plan2)
        self.assertTrue(any(e["codigo"] == "V108" for e in r2["errores"]))

    def test_seed_negativa_rechazada(self):
        plan = _plan_cancion()
        plan["seed"] = -7
        r = validador.validar(plan)
        self.assertTrue(any("seed" in e["mensaje"] for e in r["errores"]))

    def test_perfil_desconocido(self):
        plan = _plan_cancion()
        plan["orchestration"]["profile"] = "sinfonico"
        r = validador.validar(plan)
        self.assertTrue(any(e["codigo"] == "V105" for e in r["errores"]))


class CapaACoherencia(unittest.TestCase):
    def test_drums_ausente_con_seccion_que_no_esta_off(self):
        plan = _plan_cancion()
        plan["controls"]["drums"] = "ausente"
        r = validador.validar(plan)
        self.assertTrue(any(e["codigo"] == "V111" and "drums" in e["mensaje"]
                            for e in r["errores"]))

    def test_drums_ausente_con_perfil_de_drums_true(self):
        plan = _plan_cancion()
        plan["controls"]["drums"] = "ausente"
        for s in plan["form"]["sections"]:
            s["drums"] = "off"
        r = validador.validar(plan)
        self.assertTrue(any(e["codigo"] == "V111" and "perfil" in e["mensaje"]
                            for e in r["errores"]))

    def test_drums_ausente_coherente_pasa(self):
        plan = _plan_cancion()
        plan["controls"]["drums"] = "ausente"
        for s in plan["form"]["sections"]:
            s["drums"] = "off"
        plan["orchestration"]["profile"] = "sax_rhodes"
        plan["identity"]["palette"] = ["sax_rhodes"]
        r = validador.validar(plan)
        self.assertTrue(r["ok"], r["errores"])

    def test_drums_protagonista_sin_seccion_pesada(self):
        plan = _plan_cancion()
        plan["controls"]["drums"] = "protagonista"
        for s in plan["form"]["sections"]:
            s["drums"] = "air"
        r = validador.validar(plan)
        self.assertTrue(any(e["codigo"] == "V111" for e in r["errores"]))

    def test_energia_alta_sin_pico(self):
        plan = _plan_cancion()
        plan["form"]["sections"][2]["energy"] = 0.55   # se pierde el pico 0.75
        r = validador.validar(plan)
        self.assertTrue(any(e["codigo"] == "V112" for e in r["errores"]))

    def test_acorde_fuera_de_tonica_y_vecinas(self):
        plan = _plan_cancion()
        plan["harmony"]["progressions"]["verse"].append("Bmaj7")
        r = validador.validar(plan)
        self.assertTrue(any(e["codigo"] == "V110" and "Bmaj7" in e["mensaje"]
                            for e in r["errores"]))

    def test_acorde_no_parseable(self):
        plan = _plan_cancion()
        plan["harmony"]["progressions"]["verse"] = ["Dm9", "Do#solb7"]
        r = validador.validar(plan)
        self.assertTrue(any(e["codigo"] == "V110" for e in r["errores"]))

    def test_key_no_parseable(self):
        plan = _plan_cancion()
        plan["harmony"]["key"] = "Re menor"
        r = validador.validar(plan)
        self.assertTrue(any(e["codigo"] == "V110" for e in r["errores"]))

    def test_ending_mayor_que_ultima_seccion(self):
        plan = _plan_cancion()
        plan["ending"]["fade_out"]["bars"] = 9   # última sección tiene 4
        r = validador.validar(plan)
        self.assertTrue(any(e["codigo"] == "V116" for e in r["errores"]))

    def test_palette_sin_el_perfil(self):
        plan = _plan_cancion()
        plan["identity"]["palette"] = ["atmospheric"]   # profile es full
        r = validador.validar(plan)
        self.assertTrue(any(e["codigo"] == "V111" and "palette" in e["mensaje"]
                            for e in r["errores"]))


class CapaB(unittest.TestCase):
    def test_protagonista_en_menos_de_dos_secciones(self):
        plan = _plan_cancion()
        for s in plan["form"]["sections"]:
            if "sax_tenor" in (s.get("focus") or []):
                s["focus"] = [f for f in s["focus"] if f != "sax_tenor"] or ["rhodes"]
        r = validador.validar(plan)
        self.assertTrue(any(e["codigo"] == "V113" and "protagonista" in e["mensaje"]
                            for e in r["errores"]))

    def test_solo_en_seccion_que_no_es_break_ni_bridge(self):
        plan = _plan_cancion()
        plan["solos"] = [{"section_id": "verso_a", "instrument": "sax_tenor"}]
        r = validador.validar(plan)
        self.assertTrue(any(e["codigo"] == "V113" and "break" in e["mensaje"]
                            for e in r["errores"]))

    def test_solo_con_focus_distinto(self):
        plan = _plan_cancion()
        plan["form"]["sections"][2]["type"] = "break"
        plan["solos"] = [{"section_id": "coro_a", "instrument": "sax_tenor"}]
        plan["form"]["sections"][2]["focus"] = ["bass", "sax_tenor"]
        r = validador.validar(plan)
        self.assertTrue(any(e["codigo"] == "V113" and "focus" in e["mensaje"]
                            for e in r["errores"]))

    def test_solo_en_la_seccion_de_menor_energia(self):
        plan = _plan_cancion()
        # sección de solo con la energía mínima del plan (0.30)
        plan["form"]["sections"].append(
            _seccion("solo_bajo", "break", 8, 0.30, 0.40, 0.50, ["sax_tenor"], "groove"))
        plan["duration"]["bars_total"] = 40
        plan["solos"] = [{"section_id": "solo_bajo", "instrument": "sax_tenor"}]
        r = validador.validar(plan)
        self.assertTrue(any(e["codigo"] == "V113" and "menor energía" in e["mensaje"]
                            for e in r["errores"]))

    def test_solo_referencia_inexistente(self):
        plan = _plan_cancion()
        plan["solos"] = [{"section_id": "fantasma", "instrument": "sax_tenor"}]
        r = validador.validar(plan)
        self.assertTrue(any(e["codigo"] == "V107" for e in r["errores"]))

    def test_cadencia_ausente_en_cancion(self):
        plan = _plan_cancion()
        plan["harmony"]["progressions"] = {
            "verse": ["Gm9", "Bbmaj9", "Fmaj9"],   # ninguna termina tónica/dominante
            "chorus": ["Cm9", "Ebmaj7"],
        }
        r = validador.validar(plan)
        self.assertTrue(any(e["codigo"] == "V114" for e in r["errores"]))

    def test_cadencia_sin_progresiones_de_chorus_ni_verse(self):
        plan = _plan_cancion()
        plan["harmony"]["progressions"] = {"bridge": ["Gm9", "Am7"]}
        r = validador.validar(plan)
        self.assertTrue(any(e["codigo"] == "V114" for e in r["errores"]))

    def test_transicion_mayor_que_04_en_cancion(self):
        plan = _plan_cancion()
        plan["form"]["sections"][4]["energy"] = 0.15   # 0.55 → 0.15 = 0.40 no; usar 0.10
        plan["form"]["sections"][4]["energy"] = 0.10   # 0.55 → 0.10 = 0.45 > 0.4
        r = validador.validar(plan)
        self.assertTrue(any(e["codigo"] == "V115" for e in r["errores"]))

    def test_transiciones_exentas_en_ciclos(self):
        plan = _plan_ciclos()
        # salto grande entre vecinas: en ciclos NO es gate (§6.5 exentos)
        plan["form"]["sections"][1]["energy"] = 0.10
        r = validador.validar(plan)
        self.assertFalse(any(e["codigo"] == "V115" for e in r["errores"]))


class LockedConservado(unittest.TestCase):
    def test_locked_valido_y_el_doc_lo_descarta(self):
        # F1: locked se valida como estado y se CONSERVA tal cual en el plan;
        # el compilador no lo lleva al doc. El bloqueo real frente al intérprete
        # se prueba por primera vez en Fase 2 (§9.1, §12.1).
        plan = _plan_cancion()
        plan["form"]["sections"][2]["locked"] = True
        r = validador.validar(plan)
        self.assertTrue(r["ok"], r["errores"])
        doc = plan_compilador.compilar(plan)
        self.assertNotIn("locked", doc["structure"][2])
        self.assertTrue(plan["form"]["sections"][2]["locked"])


class AvisosNoBloqueantes(unittest.TestCase):
    def test_duracion_estimada_fuera_de_banda_es_aviso(self):
        plan = _plan_cancion()
        plan["duration"]["target"] = "larga"   # 32 bars a 72 = 1.8 min (corta)
        r = validador.validar(plan)
        self.assertTrue(r["ok"], r["errores"])
        self.assertTrue(any("banda" in a["mensaje"] for a in r["avisos"]))

    def test_focus_fuera_del_set_base_es_aviso_w406(self):
        plan = _plan_cancion()
        plan["form"]["sections"][1]["focus"] = ["sax_tenor", "strings"]
        r = validador.validar(plan)
        self.assertTrue(r["ok"], r["errores"])
        self.assertTrue(any("set base" in a["mensaje"] for a in r["avisos"]))


class CapaCSintetica(unittest.TestCase):
    """Gates estructurales de §6.3 sobre events.json sintético (to_events)."""

    def _plan_pequeno(self, con_solo=False):
        plan = _plan_cancion()
        secciones = [
            _seccion("intro", "intro", 4, 0.3, 0.2, 0.25, ["rhodes", "pad"], "air"),
            _seccion("verso", "verse", 8, 0.6, 0.35, 0.5, ["sax_tenor"], "groove"),
            _seccion("outro", "outro", 4, 0.3, 0.2, 0.25, ["rhodes"], "air"),
        ]
        if con_solo:
            secciones.insert(2, _seccion("solo_a", "break", 8, 0.7, 0.5, 0.6,
                                         ["sax_tenor"], "groove"))
        plan["form"]["sections"] = secciones
        plan["duration"]["bars_total"] = sum(s["bars"] for s in secciones)
        plan["global"]["bpm"] = 120
        plan["solos"] = ([{"section_id": "solo_a", "instrument": "sax_tenor"}]
                         if con_solo else [])
        return plan

    def _events(self, plan, *, sax_en_solo=True, pista_vacia=None, run=False):
        bb = 4.0
        t = 0.0
        secciones = []
        for s in plan["form"]["sections"]:
            secciones.append({"id": s["id"], "name": s["id"], "kind": s["type"],
                              "t0": t, "t1": t + s["bars"] * bb, "bars": s["bars"]})
            t += s["bars"] * bb
        total = t

        def notas_de(inst):
            out = []
            for s, ev in zip(plan["form"]["sections"], secciones):
                if inst == "sax_tenor" and s["id"] == "solo_a" and not sax_en_solo:
                    continue
                if inst == "sax_tenor" and s["type"] not in ("verse", "break"):
                    continue
                if inst in ("rhodes", "pad") and s["type"] not in ("intro", "outro"):
                    continue
                if inst in ("vibraphone",) and s["type"] != "intro":
                    continue
                if inst == "drums" and s["drums"] == "off":
                    continue
                n = 4 if s["type"] != "outro" else 2
                if inst == "drums":
                    n = 16
                base = {"sax_tenor": 70, "rhodes": 60, "vibraphone": 72,
                        "bass": 38, "drums": 38, "pad": 55}.get(inst, 60)
                for i in range(n):
                    out.append([ev["t0"] + i * 0.5, 0.45, base + (i % 3), 80])
            return out

        tracks = []
        for iid, rol in (("sax_tenor", "lead"), ("rhodes", "keys"),
                         ("vibraphone", "mallet"), ("bass", "bass"),
                         ("drums", "drums"), ("pad", "pad")):
            notas = notas_de(iid)
            if run and iid == "sax_tenor":
                notas = notas[:6] + [[48.0 + i * 0.5, 0.4, 70, 77] for i in range(10)]
            if pista_vacia == iid:
                notas = []
            tracks.append({"id": iid, "role": rol, "notes": notas})
        return {"bpm": float(plan["global"]["bpm"]), "ticks_per_beat": 480,
                "bar_beats": bb, "total_beats": total, "tracks": tracks,
                "sections": secciones}

    def test_bloqueantes_verdes_en_eventos_correctos(self):
        plan = self._plan_pequeno()
        r = validador.verificar_capa_c(plan, self._events(plan))
        bloqueantes = [c for c in r["checks"] if c["bloqueante"]]
        self.assertTrue(r["ok"], [(c["id"], c["detalle"]) for c in bloqueantes if not c["ok"]])
        self.assertTrue(all(c["ok"] for c in bloqueantes))

    def test_c4b_y_c5_son_diagnosticos_no_bloqueantes(self):
        plan = self._plan_pequeno()
        r = validador.verificar_capa_c(plan, self._events(plan))
        ids = {c["id"]: c for c in r["checks"]}
        self.assertFalse(ids["C4b"]["bloqueante"])
        self.assertFalse(ids["C5"]["bloqueante"])

    def test_pista_vacia_rompe_c4_bloqueante(self):
        plan = self._plan_pequeno()
        r = validador.verificar_capa_c(plan, self._events(plan, pista_vacia="bass"))
        ids = {c["id"]: c for c in r["checks"]}
        self.assertFalse(r["ok"])
        self.assertFalse(ids["C4"]["ok"])
        self.assertIn("bass", ids["C4"]["detalle"])

    def test_solo_vacio_rompe_c4s_bloqueante(self):
        plan = self._plan_pequeno(con_solo=True)
        r = validador.verificar_capa_c(plan, self._events(plan, sax_en_solo=False))
        ids = {c["id"]: c for c in r["checks"]}
        self.assertFalse(r["ok"])
        self.assertFalse(ids["C4s"]["ok"])

    def test_run_de_notas_atascadas_rompe_c6(self):
        plan = self._plan_pequeno()
        r = validador.verificar_capa_c(plan, self._events(plan, run=True))
        ids = {c["id"]: c for c in r["checks"]}
        self.assertFalse(r["ok"])
        self.assertFalse(ids["C6"]["ok"])
        self.assertIn("sax_tenor", ids["C6"]["detalle"])

    def test_bpm_y_bars_distintos_del_plan_rompen_c2(self):
        plan = self._plan_pequeno()
        events = self._events(plan)
        events["bpm"] = 90.0
        events["sections"][1]["bars"] = 6
        r = validador.verificar_capa_c(plan, events)
        ids = {c["id"]: c for c in r["checks"]}
        self.assertFalse(ids["C2"]["ok"])

    def test_duracion_fuera_de_5pct_rompe_c3(self):
        plan = self._plan_pequeno()
        events = self._events(plan)
        events["total_beats"] = events["total_beats"] * 1.2   # +20%
        r = validador.verificar_capa_c(plan, events)
        ids = {c["id"]: c for c in r["checks"]}
        self.assertFalse(ids["C3"]["ok"])

    def test_partitura_incoherente_rompe_c7(self):
        plan = self._plan_pequeno()
        events = self._events(plan)
        events["sections"][1]["t0"] = events["sections"][1]["t0"] + 2.0
        r = validador.verificar_capa_c(plan, events)
        ids = {c["id"]: c for c in r["checks"]}
        self.assertFalse(ids["C7"]["ok"])


if __name__ == "__main__":
    unittest.main()
