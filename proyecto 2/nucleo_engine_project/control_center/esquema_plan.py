"""Contrato v1 del Composition Plan — esquema de ``plan.json``.

Fuente de verdad: spec DMD Control Center v1.4, §9 (tabla §9.2, ejemplo §9.3).
Este módulo es dato + funciones puras: define campos, tipos, catálogos y
estados; NO decide música (eso es el validador) ni compila (eso es el
plan_compilador).

Principios (§9.1):
  - Superficie expresiva = dark-director/1: los catálogos cerrados se importan
    de ``dark_director/contract.py`` (fuente única; aquí no se duplican).
  - Estados de cada campo: concreto | null (solo admisible con
    ``mode="automatic"``, que no existe hasta Fase 2) | concreto + locked.
  - Anti-campos-muertos (C-04): todo campo declara consumidor real (§9.2);
    campo desconocido = error (el validador nunca adivina, §9.5).

Códigos de error del paquete (familia V, espejo de la semántica E1xx del doc):
  V101 raíz inválida · V102 plan_version · V103 requerido ausente ·
  V104 tipo incorrecto · V105 valor fuera de catálogo/rango ·
  V106 campo desconocido · V107 referencia rota · V108 estado ilegal en F1
  (null / "auto" / mode=automatic / album_context ≠ null).
"""
from dark_director import contract
from jazz_engine import production

# ---------------------------------------------------------------------------
# Constantes del contrato v1 (§9.2)
# ---------------------------------------------------------------------------

PLAN_VERSION = 1

MODOS = ("guided", "automatic")        # 'automatic' se rechaza en F1 (validador, V108)

#: form.template (§9.2: informativo; el compilador NO lo lee; el intérprete F2
#: genera secciones desde la plantilla). Sin 'auto': en F1 el plan es completo.
PLANTILLAS_FORMA = ("cancion", "ciclos", "libre")

#: duration.target (§9.2).
OBJETIVOS_DURACION = ("corta", "media", "larga")

#: identity.protagonist — instrumentos melódicos con evidencia real de pistas
#: (§9.2). El lead del contrato doc es sax_tenor (E301); el protagonista puede
#: ser otro melódico y se materializa vía focus[] (§9.2).
INSTRUMENTOS_MELDICOS = ("sax_tenor", "rhodes", "vibraphone")

#: Los 6 controles Guided (§7.1), en snake_case como el ejemplo §9.3. Son
#: enums de INTENCIÓN de UI: no son vocabulario doc y nunca se compilan (§9.2).
#: F1: si un control se declara, su valor es concreto (el literal "auto" se
#: rechaza; omitir el control = delegar, §7.2).
CONTROLES = {
    "energia": ("muy_baja", "baja", "media", "alta", "muy_alta"),
    "forma": ("auto", "cancion", "ciclos", "libre"),
    "duracion": ("auto", "corta", "media", "larga"),
    "armonia": ("auto", "nocturno", "jazz", "crudo", "sombrio"),
    "pulso": ("auto", "swing", "recto", "lento_arrastrado", "latin"),
    "drums": ("ausente", "contenida", "presente", "protagonista"),
}

# Catálogos cerrados de dark-director/1 (importados, no duplicados — §9.1.4).
SECTION_TYPES = contract.SECTION_TYPES
INSTRUMENT_IDS = contract.INSTRUMENT_IDS
DRUMS_LADDER = contract.DRUMS_LADDER
IDENTITIES = contract.IDENTITIES
ACCESSIBILITIES = contract.ACCESSIBILITIES
LANGUAGES = contract.LANGUAGES

#: Perfiles de producción válidos (§6.1: jazz_engine/production.py::nombres()).
PERFILES_PRODUCCION = production.nombres()

# ---------------------------------------------------------------------------
# Campos cerrados por nivel (campo desconocido ⇒ V106 — nada ad hoc, §9.1.4)
# ---------------------------------------------------------------------------

CAMPOS_PLAN = ("plan_version", "mode", "seed", "title", "identity", "controls",
               "album_context", "form", "ending", "harmony", "solos",
               "orchestration", "global", "duration", "notes", "evidence")
CAMPOS_IDENTITY = ("style", "accessibility", "protagonist", "palette")
CAMPOS_CONTROLS = tuple(CONTROLES)
CAMPOS_FORM = ("template", "sections")
CAMPOS_SECCION = ("id", "type", "bars", "energy", "tension", "density",
                  "focus", "drums", "final", "locked")
CAMPOS_HARMONY = ("key", "language", "harmonic_rhythm_bars", "progressions")
CAMPOS_ENDING = ("fade_out",)                     # tape_stop no existe en el plan v1 (§9.2)
CAMPOS_FADE_OUT = ("enabled", "bars")
CAMPOS_SOLO = ("section_id", "instrument")
CAMPOS_ORCHESTRATION = ("profile",)
CAMPOS_GLOBAL = ("bpm",)
CAMPOS_DURATION = ("target", "bars_total")
CAMPOS_EVIDENCE = ("resolved_by", "resolved", "inputs_hash", "created_at")

REQUERIDOS_PLAN = ("plan_version", "mode", "seed", "title", "identity", "form",
                   "harmony", "orchestration", "global", "duration")
REQUERIDOS_IDENTITY = ("style", "accessibility", "protagonist")
REQUERIDOS_HARMONY = ("key", "language", "harmonic_rhythm_bars", "progressions")
REQUERIDOS_GLOBAL = ("bpm",)
REQUERIDOS_DURATION = ("target", "bars_total")
REQUERIDOS_SECCION = ("id", "type", "bars", "energy", "tension", "density",
                      "focus", "drums")

#: Límites numéricos (§6.1: 2–9 secciones, 4–16 compases por sección; §9.2:
#: bpm 40–200; E112 del doc: ending.bars ≥ 1).
LIMITES = {
    "bpm": (40, 200),
    "bars": (4, 16),
    "secciones": (2, 9),
    "fade_out_bars_min": 1,
}


# ---------------------------------------------------------------------------
# Validación de esquema (tipos, requeridos, catálogos, campos desconocidos)
# ---------------------------------------------------------------------------

def _es_num(v):
    """Número (int/float, excluye bool) — para energy/tension/density."""
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _es_int(v):
    """Entero (excluye bool)."""
    return isinstance(v, int) and not isinstance(v, bool)


def _desconocidos(obj, permitidos):
    return [k for k in obj if k not in permitidos]


def validar_esquema(plan):
    """Valida el esquema v1 de un plan (dict ya cargado).

    Devuelve (errores, avisos): listas de dicts {"codigo", "mensaje"}.
    Cubre: requeridos, tipos, catálogos, rangos y campos desconocidos (§9.2).
    NO evalúa coherencia entre campos (capa A del validador) ni musicalidad
    (capa B).
    """
    errores = []
    avisos = []

    def err(cod, msg):
        errores.append({"codigo": cod, "mensaje": msg})

    if not isinstance(plan, dict):
        err("V101", "el plan debe ser un objeto JSON (raíz no-objeto)")
        return errores, avisos

    for k in _desconocidos(plan, CAMPOS_PLAN):
        err("V106", f"campo desconocido en el plan: {k!r} (el contrato v1 es "
                    f"cerrado; extensiones x_* no están admitidas en F1, §9.1.4)")

    # --- requeridos de primer nivel -------------------------------------
    for campo in REQUERIDOS_PLAN:
        if campo not in plan:
            err("V103", f"campo requerido ausente: {campo}")

    # --- plan_version (§9.5: rechazar versiones desconocidas, nunca adivinar)
    if "plan_version" in plan:
        if not _es_int(plan["plan_version"]):
            err("V104", "plan_version debe ser int")
        elif plan["plan_version"] != PLAN_VERSION:
            err("V102", f"plan_version desconocida: {plan['plan_version']!r} "
                        f"(este validador solo conoce v{PLAN_VERSION})")

    # --- mode (§9.2) ------------------------------------------------------
    if "mode" in plan:
        if not isinstance(plan["mode"], str):
            err("V104", "mode debe ser texto")
        elif plan["mode"] not in MODOS:
            err("V105", f"mode fuera de catálogo: {plan['mode']!r} (válidos: {', '.join(MODOS)})")

    # --- seed (§9.2: int; §11.2: seed negativa es caso inválido) ----------
    if "seed" in plan:
        if not _es_int(plan["seed"]):
            err("V104", "seed debe ser int")
        elif plan["seed"] < 0:
            err("V105", f"seed negativa no admitida: {plan['seed']}")

    # --- title ------------------------------------------------------------
    if "title" in plan and (not isinstance(plan["title"], str)
                            or not plan["title"].strip()):
        err("V104", "title debe ser texto no vacío")

    # --- identity (§9.2) ----------------------------------------------------
    if "identity" in plan:
        ident = plan["identity"]
        if not isinstance(ident, dict):
            err("V104", "identity debe ser objeto")
        else:
            for k in _desconocidos(ident, CAMPOS_IDENTITY):
                err("V106", f"campo desconocido en identity: {k!r}")
            for campo in REQUERIDOS_IDENTITY:
                if campo not in ident:
                    err("V103", f"campo requerido ausente en identity: {campo}")
            if "style" in ident:
                if not isinstance(ident["style"], str):
                    err("V104", "identity.style debe ser texto")
                elif ident["style"] not in IDENTITIES:
                    err("V105", f"identity.style fuera de catálogo: {ident['style']!r} "
                                f"(IDENTITIES de dark-director/1)")
            if "accessibility" in ident:
                if not isinstance(ident["accessibility"], str):
                    err("V104", "identity.accessibility debe ser texto")
                elif ident["accessibility"] not in ACCESSIBILITIES:
                    err("V105", f"identity.accessibility fuera de catálogo: {ident['accessibility']!r}")
            if "protagonist" in ident:
                if not isinstance(ident["protagonist"], str):
                    err("V104", "identity.protagonist debe ser texto")
                elif ident["protagonist"] not in INSTRUMENTOS_MELDICOS:
                    err("V105", f"identity.protagonist debe ser un instrumento melódico "
                                f"{INSTRUMENTOS_MELDICOS}: {ident['protagonist']!r}")
            if "palette" in ident:
                pal = ident["palette"]
                if not isinstance(pal, list) or not all(isinstance(p, str) for p in pal):
                    err("V104", "identity.palette debe ser lista de texto")
                else:
                    for p in pal:
                        if p not in PERFILES_PRODUCCION:
                            err("V105", f"identity.palette incluye un perfil desconocido: {p!r} "
                                        f"(válidos: {', '.join(PERFILES_PRODUCCION)})")

    # --- controls (§9.2: opcionales, informativos en F1) --------------------
    if "controls" in plan and plan["controls"] is not None:
        cont = plan["controls"]
        if not isinstance(cont, dict):
            err("V104", "controls debe ser objeto")
        else:
            for k in _desconocidos(cont, CAMPOS_CONTROLS):
                err("V106", f"control desconocido: {k!r} (solo hay 6, §7.1)")
            for k, v in cont.items():
                if k in CONTROLES:
                    if not isinstance(v, str):
                        err("V104", f"controls.{k} debe ser texto")
                    elif v not in CONTROLES[k]:
                        err("V105", f"controls.{k} fuera de catálogo: {v!r} "
                                    f"(válidos: {', '.join(CONTROLES[k])})")

    # --- form (§9.2) ---------------------------------------------------------
    if "form" in plan:
        form = plan["form"]
        if not isinstance(form, dict):
            err("V104", "form debe ser objeto")
        else:
            for k in _desconocidos(form, CAMPOS_FORM):
                err("V106", f"campo desconocido en form: {k!r}")
            if "template" in form:
                if not isinstance(form["template"], str):
                    err("V104", "form.template debe ser texto")
                elif form["template"] not in PLANTILLAS_FORMA:
                    err("V105", f"form.template fuera de catálogo: {form['template']!r} "
                                f"(válidos: {', '.join(PLANTILLAS_FORMA)})")
            if "sections" in form:
                secs = form["sections"]
                if not isinstance(secs, list) or not secs:
                    err("V104", "form.sections debe ser lista no vacía")
                else:
                    for i, sec in enumerate(secs):
                        errores.extend(_validar_seccion(sec, i))

    # --- ending (§9.2: {fade_out: {enabled, bars}}) ---------------------------
    if "ending" in plan and plan["ending"] is not None:
        ending = plan["ending"]
        if not isinstance(ending, dict):
            err("V104", "ending debe ser objeto")
        else:
            for k in _desconocidos(ending, CAMPOS_ENDING):
                err("V106", f"campo desconocido en ending: {k!r} (el plan v1 "
                            f"solo expresa fade_out)")
            fo = ending.get("fade_out")
            if fo is not None:
                if not isinstance(fo, dict):
                    err("V104", "ending.fade_out debe ser objeto")
                else:
                    for k in _desconocidos(fo, CAMPOS_FADE_OUT):
                        err("V106", f"campo desconocido en ending.fade_out: {k!r}")
                    if "enabled" in fo and not isinstance(fo["enabled"], bool):
                        err("V104", "ending.fade_out.enabled debe ser bool")
                    if "bars" in fo:
                        if not _es_int(fo["bars"]):
                            err("V104", "ending.fade_out.bars debe ser int")
                        elif fo["bars"] < LIMITES["fade_out_bars_min"]:
                            err("V105", f"ending.fade_out.bars debe ser ≥ "
                                        f"{LIMITES['fade_out_bars_min']} (E112 del contrato doc)")

    # --- harmony (§9.2) ---------------------------------------------------------
    if "harmony" in plan:
        har = plan["harmony"]
        if not isinstance(har, dict):
            err("V104", "harmony debe ser objeto")
        else:
            for k in _desconocidos(har, CAMPOS_HARMONY):
                err("V106", f"campo desconocido en harmony: {k!r}")
            for campo in REQUERIDOS_HARMONY:
                if campo not in har:
                    err("V103", f"campo requerido ausente en harmony: {campo}")
            if "key" in har and not isinstance(har["key"], str):
                err("V104", "harmony.key debe ser texto ('F# minor', 'D minor', …)")
            if "language" in har:
                if not isinstance(har["language"], str):
                    err("V104", "harmony.language debe ser texto")
                elif har["language"] not in LANGUAGES:
                    err("V105", f"harmony.language fuera de catálogo: {har['language']!r} "
                                f"(LANGUAGES de dark-director/1)")
            if "harmonic_rhythm_bars" in har:
                hrb = har["harmonic_rhythm_bars"]
                if not _es_int(hrb):
                    err("V104", f"harmony.harmonic_rhythm_bars debe ser int: {hrb!r}")
                elif hrb < 1:
                    err("V105", f"harmony.harmonic_rhythm_bars debe ser ≥ 1: {hrb!r}")
            if "progressions" in har:
                prog = har["progressions"]
                if not isinstance(prog, dict) or not prog:
                    err("V104", "harmony.progressions debe ser objeto no vacío "
                                "(<type>: [acordes])")
                else:
                    for t, acordes in prog.items():
                        if t not in SECTION_TYPES:
                            err("V105", f"harmony.progressions clave fuera de "
                                        f"SECTION_TYPES: {t!r}")
                        if not isinstance(acordes, list) or not acordes \
                                or not all(isinstance(a, str) and a.strip() for a in acordes):
                            err("V104", f"harmony.progressions[{t!r}] debe ser lista "
                                        f"no vacía de símbolos de acorde")

    # --- solos (§9.2: {section_id, instrument}) ---------------------------------
    if "solos" in plan and plan["solos"] is not None:
        solos = plan["solos"]
        if not isinstance(solos, list):
            err("V104", "solos debe ser lista")
        else:
            for i, solo in enumerate(solos):
                if not isinstance(solo, dict):
                    err("V104", f"solos[{i}] debe ser objeto")
                    continue
                for k in _desconocidos(solo, CAMPOS_SOLO):
                    err("V106", f"campo desconocido en solos[{i}]: {k!r}")
                for campo in CAMPOS_SOLO:
                    if campo not in solo:
                        err("V103", f"campo requerido ausente en solos[{i}]: {campo}")
                if "instrument" in solo and (not isinstance(solo["instrument"], str)
                                             or solo["instrument"] not in INSTRUMENT_IDS):
                    err("V105", f"solos[{i}].instrument fuera del catálogo de 8 "
                                f"instrumentos: {solo['instrument']!r}")

    # --- orchestration (§9.2) ------------------------------------------------------
    if "orchestration" in plan:
        orq = plan["orchestration"]
        if not isinstance(orq, dict):
            err("V104", "orchestration debe ser objeto")
        else:
            for k in _desconocidos(orq, CAMPOS_ORCHESTRATION):
                err("V106", f"campo desconocido en orchestration: {k!r}")
            if "profile" not in orq:
                err("V103", "campo requerido ausente en orchestration: profile")
            elif not isinstance(orq["profile"], str):
                err("V104", "orchestration.profile debe ser texto")
            elif orq["profile"] not in PERFILES_PRODUCCION:
                err("V105", f"orchestration.profile desconocido: {orq['profile']!r} "
                            f"(perfiles reales: {', '.join(PERFILES_PRODUCCION)})")

    # --- global (§9.2: bpm int 40–200) ----------------------------------------------
    if "global" in plan:
        glob = plan["global"]
        if not isinstance(glob, dict):
            err("V104", "global debe ser objeto")
        else:
            for k in _desconocidos(glob, CAMPOS_GLOBAL):
                err("V106", f"campo desconocido en global: {k!r}")
            if "bpm" not in glob:
                err("V103", "campo requerido ausente en global: bpm")
            elif not _es_int(glob["bpm"]):
                err("V104", f"global.bpm debe ser int: {glob['bpm']!r}")
            elif not (LIMITES["bpm"][0] <= glob["bpm"] <= LIMITES["bpm"][1]):
                err("V105", f"global.bpm fuera de rango {LIMITES['bpm']}: {glob['bpm']}")

    # --- duration (§9.2) ---------------------------------------------------------------
    if "duration" in plan:
        dur = plan["duration"]
        if not isinstance(dur, dict):
            err("V104", "duration debe ser objeto")
        else:
            for k in _desconocidos(dur, CAMPOS_DURATION):
                err("V106", f"campo desconocido en duration: {k!r}")
            for campo in REQUERIDOS_DURATION:
                if campo not in dur:
                    err("V103", f"campo requerido ausente en duration: {campo}")
            if "target" in dur:
                if not isinstance(dur["target"], str):
                    err("V104", "duration.target debe ser texto")
                elif dur["target"] not in OBJETIVOS_DURACION:
                    err("V105", f"duration.target fuera de catálogo: {dur['target']!r} "
                                f"(válidos: {', '.join(OBJETIVOS_DURACION)})")
            if "bars_total" in dur:
                if not _es_int(dur["bars_total"]):
                    err("V104", f"duration.bars_total debe ser int: {dur['bars_total']!r}")
                elif dur["bars_total"] <= 0:
                    err("V105", f"duration.bars_total debe ser > 0: {dur['bars_total']!r}")

    # --- notes / evidence ------------------------------------------------------------------
    if "notes" in plan and plan["notes"] is not None and not isinstance(plan["notes"], str):
        err("V104", "notes debe ser texto (anotación descriptiva para humanos, §9.2)")
    if "evidence" in plan and plan["evidence"] is not None:
        ev = plan["evidence"]
        if not isinstance(ev, dict):
            err("V104", "evidence debe ser objeto")
        else:
            for k in _desconocidos(ev, CAMPOS_EVIDENCE):
                err("V106", f"campo desconocido en evidence: {k!r}")
            for k, tipo in (("resolved_by", str), ("inputs_hash", str), ("created_at", str)):
                if k in ev and not isinstance(ev[k], tipo):
                    err("V104", f"evidence.{k} debe ser texto")
            if "resolved" in ev and not isinstance(ev["resolved"], list):
                err("V104", "evidence.resolved debe ser lista")

    return errores, avisos


def _validar_seccion(sec, i):
    """Esquema de una sección (§9.2 form.sections[]): todo concreto en F1."""
    errores = []

    def err(cod, msg):
        errores.append({"codigo": cod, "mensaje": msg})

    if not isinstance(sec, dict):
        err("V104", f"sections[{i}] debe ser objeto")
        return errores
    pref = f"sections[{i}]"
    for k in _desconocidos(sec, CAMPOS_SECCION):
        err("V106", f"campo desconocido en {pref}: {k!r}")
    for campo in REQUERIDOS_SECCION:
        if campo not in sec:
            err("V103", f"campo requerido ausente en {pref}: {campo}")
    if "id" in sec and (not isinstance(sec["id"], str) or not sec["id"].strip()):
        err("V104", f"{pref}.id debe ser texto no vacío")
    if "type" in sec:
        if not isinstance(sec["type"], str):
            err("V104", f"{pref}.type debe ser texto")
        elif sec["type"] not in SECTION_TYPES:
            err("V105", f"{pref}.type fuera de SECTION_TYPES: {sec['type']!r} "
                        f"(catálogo cerrado de dark-director/1)")
    if "bars" in sec:
        if not _es_int(sec["bars"]):
            err("V104", f"{pref}.bars debe ser int (compases)")
        elif not (LIMITES["bars"][0] <= sec["bars"] <= LIMITES["bars"][1]):
            err("V105", f"{pref}.bars fuera del rango {LIMITES['bars']}: {sec['bars']}")
    for eje in ("energy", "tension", "density"):
        if eje in sec:
            v = sec[eje]
            if not _es_num(v):
                err("V104", f"{pref}.{eje} debe ser número en [0, 1]")
            elif not (0.0 <= float(v) <= 1.0):
                err("V105", f"{pref}.{eje} fuera del dominio [0, 1]: {v}")
    if "focus" in sec:
        foc = sec["focus"]
        if not isinstance(foc, list) or not foc or not all(isinstance(f, str) for f in foc):
            err("V104", f"{pref}.focus debe ser lista no vacía de instrumentos")
        else:
            for f in foc:
                if f not in INSTRUMENT_IDS:
                    err("V105", f"{pref}.focus incluye un instrumento fuera del "
                                f"catálogo de 8: {f!r} (E110 del contrato doc)")
    if "drums" in sec:
        if not isinstance(sec["drums"], str):
            err("V104", f"{pref}.drums debe ser texto")
        elif sec["drums"] not in DRUMS_LADDER:
            err("V105", f"{pref}.drums fuera de DRUMS_LADDER: {sec['drums']!r} "
                        f"(off→air→light→groove→heavy)")
    if "final" in sec and not isinstance(sec["final"], bool):
        err("V104", f"{pref}.final debe ser bool")
    if "locked" in sec and not isinstance(sec["locked"], bool):
        err("V104", f"{pref}.locked debe ser bool")
    return errores
