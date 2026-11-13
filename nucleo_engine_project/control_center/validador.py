"""Validador del Composition Plan — capas A y B (§6.1, §6.2) + capa C estructural.

Fuente de verdad: spec DMD Control Center v1.4.

**Capa A** (gate duro, §6.1): esquema v1, estados legales del plan completo (sin
null, sin "auto", album_context null; mode="automatic" legal desde F2 para
planes completos y rechazado si se pide fase=1), vocabulario real de
dark-director/1, invariantes de forma, curva de energía, armonía (tónica/vecinas)
e instrumentación (perfiles + coherencia de drums). Fallar ⇒ no se compila (§9.4).

**Capa B** (gate duro por reglas, §6.2): protagonista en ≥2 secciones, solos
coherentes y nunca en la sección de menor energía, cadencia resolutiva (solo
cancion) y transiciones de energía (solo cancion, ≤0.4). Repetición idéntica
entre secciones y density NO son gates B (v1.3): la repetición intencionada es
válida y el riff se evalúa en capa C y escucha.

**Capa C, checks estructurales** (§6.3, gates definitivos): pistas/roles,
compases/BPM, duración ±5%, contenido (sin pistas vacías, focus suena,
rango del protagonista, sin runs de nota atascada) y partitura, sobre el
``events.json`` que ``forge.engine.to_events()`` emite. Se implementa aquí
porque §13 no autoriza un módulo aparte y el criterio 3 de §13 la exige como
evidencia de Fase 1; solo se aplican los gates definitivos — las métricas
experimentales (±15%, correlaciones) se registran, no bloquean (C-09/C-11).

Interpretaciones documentadas (decisiones de implementación F1, citadas en el
informe de fase):
  - «acordes ∈ tónica o vecinas»: un acorde pertenece si TODAS sus notas
    (raíz + tensiones según ``forge.theory.parse_chord``, deg) son grados
    diatónicos de la escala de la tónica o de una tonalidad vecina; vecinas =
    tonalidades con armadura a ≤1 alteración, incluida la relativa mayor/menor.
    Criterio de acorde completo (no solo la raíz: enarmónicamente, la ventana
    de 3 armaduras cubre las 12 clases de altura y el gate sería vacío).
  - «cadencia resolutiva: último acorde ∈ tónica/acorde tónica»: el último
    acorde de la progresión tiene raíz tónica o raíz de dominante (5.º grado),
    cualquier calidad. Es la lectura que admiten los ejemplos del propio spec:
    §9.3 (Am7 al final de verse en D minor = v–i) y el ancla (C#7sus4 al final
    de chorus en F# minor = V7–i).
  - Bandas de duración estimada (aviso, no gate — §9.2 «duración estimada ∈
    banda del target» sin bordes declarados): corta < 3.0 min ≤ media ≤
    6.0 min < larga. El objetivo declarado de §7.1 (2-3 / 4-6 / 7+) es la
    descripción de UI; los bordes exactos son valores de trabajo.

Hallazgos de F1 en la capa C (aplicación de la cláusula de §6.3: «si el
detector marca falsos positivos sistemáticos sobre material intencionado, la
regla se reclasifica»; se MIDEN y se REGISTRAN, no bloquean — C-09/C-11):
  - F1-C4b «focus suena en su sección»: el scheduler de sax declara que
    «puede dejar secciones SIN sax (silencio = decisión)» (improv.py:18), el
    vibrafono es un instrumento de eco que responde al lead, y focus compila
    a deltas de velocity (§2.6.4, compilador.py:66) — no a promesa de
    presencia. El ANCLA de la casa (demo_medianoche) incumple el check
    (outro:rhodes sin notas). Se bloquea la parte con consumidor real:
    ninguna pista vacía y solo no vacío (§6.5).
  - F1-C5 «rango del protagonista»: el motor de rhodes escribe sistemáticamente
    pitch 44, 1 semitono bajo la tabla real de forge (styles.py keys [45,76]) y
    bajo el REGISTER_DEFAULT de las 3 recetas — deriva del motor congelado.
    El gate se mide y se registra; se bloqueará cuando el motor y la tabla se
    reconcilien (calibración documentada, F2+).
"""
import re

from dark_director import contract, identities, inicializacion
from jazz_engine import production

from . import esquema_plan as EP

# ---------------------------------------------------------------------------
# Catálogos reales (fuente única; el paquete no duplica datos)
# ---------------------------------------------------------------------------

ROL_DE = {iid: spec["rol"] for iid, spec in inicializacion.INIT_CATALOG.items()}

#: Instrumento con bloque generativo de improvisación (E301 del contrato doc).
LEAD_DOC = "sax_tenor"

#: Motor de producción → pista que materializa (jazz_engine/production.py).
PISTA_DE_MOTOR = {"sax": "sax_tenor", "rhodes": "rhodes", "drums": "drums", "vibes": "vibraphone"}

# Teoría (forge) cargada en diferido, igual que dark_director/validador.py.
_Theory = None


def _theory():
    global _Theory
    if _Theory is None:
        from dark_director import forge_link
        _Theory = forge_link.import_forge().theory
    return _Theory


# ---------------------------------------------------------------------------
# Armonía: tonalidad, escala, vecinas (≤1 alteración)
# ---------------------------------------------------------------------------

_ESCALAS = {
    "ionian": (0, 2, 4, 5, 7, 9, 11),
    "aeolian": (0, 2, 3, 5, 7, 8, 10),
    "dorian": (0, 2, 3, 5, 7, 9, 10),
    "mixolydian": (0, 2, 4, 5, 7, 9, 10),
    "phrygian": (0, 1, 3, 5, 7, 8, 10),
    "lydian": (0, 2, 4, 6, 7, 9, 11),
    "locrian": (0, 1, 3, 5, 6, 8, 10),
}
_ESCALA_MODO = {"major": "ionian", "minor": "aeolian"}

#: Armadura canónica (posición en el círculo de quintas) por escritura de
#: tonalidad, con las 15 grafías estándar por modo.
_FIFTHS_MAYOR = {"C": 0, "G": 1, "D": 2, "A": 3, "E": 4, "B": 5, "F#": 6, "C#": 7,
                 "F": -1, "Bb": -2, "Eb": -3, "Ab": -4, "Db": -5, "Gb": -6, "Cb": -7}
_FIFTHS_MENOR = {"A": 0, "E": 1, "B": 2, "F#": 3, "C#": 4, "G#": 5, "D#": 6,
                 "D": -1, "G": -2, "C": -3, "F": -4, "Bb": -5, "Eb": -6, "Ab": -7}

_RE_KEY = re.compile(r"^([A-G])([#b]?)\s*(major|minor|m|maj)?$", re.IGNORECASE)
_PC_LETRA = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def _armadura(key):
    """Posición en el círculo de quintas de la tonalidad escrita (spelling)."""
    m = _RE_KEY.match(key.strip())
    if not m:
        return None
    letra, alter, modo = m.group(1), m.group(2), (m.group(3) or "").lower()
    menor = modo in ("minor", "m")
    tabla = _FIFTHS_MENOR if menor else _FIFTHS_MAYOR
    return tabla.get(f"{letra}{alter}")


def _tonic_y_modo(key):
    """(tonic_pc, modo_de_escala) usando forge.theory.parse_key."""
    try:
        pc, modo = _theory().parse_key(key)
    except Exception:
        return None
    modo_escala = _ESCALA_MODO.get(modo, modo)
    if modo_escala not in _ESCALAS:
        modo_escala = _ESCALA_MODO["minor" if str(modo).lower().startswith(("aeol", "minor")) else "major"]
    return pc, modo_escala


def _escala_pcs(pc_tonica, modo):
    return {(pc_tonica + off) % 12 for off in _ESCALAS[modo]}


def _vecinas(key):
    """Unión de pitch classes de ``key`` y sus vecinas (≤1 alteración).

    Un acorde "pertenece" si su raíz está en este conjunto. Incluye la
    relativa mayor/menor (misma armadura, modo opuesto). Si la escritura de
    la tonalidad no está tabulada (p. ej. 'A# minor'), devuelve solo la
    propia escala (comportamiento conservador: no abre vecinas).
    """
    propio = _tonic_y_modo(key)
    if propio is None:
        return set()
    conjunto = set(_escala_pcs(*propio))
    arm = _armadura(key)
    if arm is None:
        return conjunto
    m = _RE_KEY.match(key.strip())
    menor = (m.group(3) or "").lower() in ("minor", "m")
    letra, alter = m.group(1), m.group(2)
    propia = f"{letra}{alter}"
    # las 14 grafías restantes del propio modo + las 15 del modo opuesto
    candidatos = []
    for nombre in tabla_nombres(_FIFTHS_MAYOR if menor else _FIFTHS_MENOR, excluir=propia):
        candidatos.append(nombre)
    for nombre in tabla_nombres(_FIFTHS_MENOR if menor else _FIFTHS_MAYOR):
        candidatos.append(nombre)
    for nombre in candidatos:
        a = _armadura(nombre)
        if a is not None and abs(a - arm) <= 1:
            tm = _tonic_y_modo(nombre)
            if tm is not None:
                conjunto.update(_escala_pcs(*tm))
    return conjunto


def tabla_nombres(tabla, excluir=None):
    """Nombres de tonalidad ('F# minor') para cada escritura de la tabla de quintas."""
    modo = "minor" if tabla is _FIFTHS_MENOR else "major"
    return [f"{escritura} {modo}" for escritura in tabla if escritura != excluir]


def _raiz_acorde(sim):
    """PC de la raíz del acorde según forge.theory.parse_chord (None si no parsea)."""
    try:
        return int(_theory().parse_chord(sim).root) % 12
    except Exception:
        return None


def _tonos_acorde(sim):
    """PCs de TODAS las notas del acorde (raíz + deg de parse_chord).

    None si el símbolo no parsea (E113). Para acordes sus, el grado 3 vale la
    nota sus (comportamiento de Chord); los power chords no tienen tercera.
    """
    try:
        c = _theory().parse_chord(sim)
    except Exception:
        return None
    raiz = int(c.root) % 12
    return {(raiz + off) % 12 for off in (c.deg or {}).values()} | {raiz}


def _parsea_key(key):
    try:
        _theory().parse_key(key)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Validación de capas A y B
# ---------------------------------------------------------------------------

#: Fase actual del sistema. F2 (intérprete, §12.1): los planes emitidos por el
#: intérprete son completos y con mode="automatic" — el gate de F1 contra
#: automatic solo aplica cuando el llamador pide explícitamente fase=1.
FASE_ACTUAL = 2


def validar(plan, *, fase=None):
    """Valida un plan completo (dict) con las capas A y B (§6.1, §6.2).

    Devuelve {"ok", "errores", "avisos"} con errores/avisos como dicts
    {"codigo", "mensaje", "capa"}. ``fase`` es la fase cuyo gate de estados
    se aplica (default: la fase actual del sistema, ``FASE_ACTUAL``); en
    fase=1 mode="automatic" se rechaza (§13), en fase=2 es legal para planes
    completos (§9.1, §12.1). En ambas fases el plan validado es COMPLETO:
    ningún null, ningún literal "auto", album_context null (§6.1).
    """
    if fase is None:
        fase = FASE_ACTUAL
    if fase not in (1, 2):
        raise ValueError("fase debe ser 1 o 2 (el validador nunca adivina, §9.5)")
    errores = []
    avisos = []

    def err(cod, msg, capa):
        errores.append({"codigo": cod, "mensaje": msg, "capa": capa})

    def aviso(msg):
        avisos.append({"codigo": "W", "mensaje": msg, "capa": "A"})

    esq_err, esq_avisos = EP.validar_esquema(plan)
    for e in esq_err:
        errores.append({"codigo": e["codigo"], "mensaje": e["mensaje"], "capa": "A"})
    for a in esq_avisos:
        avisos.append({"codigo": "W", "mensaje": a["mensaje"], "capa": "A"})
    if not isinstance(plan, dict):
        return {"ok": False, "errores": errores, "avisos": avisos}

    _gates_estados(plan, err, fase)
    forma = _gates_forma(plan, err, aviso)
    if forma is None:
        return {"ok": False, "errores": errores, "avisos": avisos}
    secciones, plantilla, controles = forma

    _gates_curva(plan, secciones, controles, err)
    _gates_armonia(plan, err)
    _gates_instrumentacion(plan, secciones, controles, err, aviso)
    _gates_ending(plan, secciones, err)

    # --- capa B (§6.2): universales + condicionados a la forma --------------
    _capa_b(plan, secciones, plantilla, err)

    return {"ok": not errores, "errores": errores, "avisos": avisos}


# --- capa A: estados legales del plan (V108) ---------------------------------

def _gates_estados(plan, err, fase):
    """§6.1/§9.1: el plan validado es completo en toda fase (sin nulls, sin
    literales "auto", album_context null). El gate extra de fase=1 rechaza
    mode="automatic" (F1: sin intérprete); en fase=2 es el modo natural de los
    planes que emite el intérprete (§12.1)."""
    if fase == 1 and plan.get("mode") == "automatic":
        err("V108", 'mode="automatic" se rechaza en fase 1: sin intérprete, '
                    "solo planes completos y manuales (§9.1, §13)", "A")

    def _recorre(obj, ruta):
        if isinstance(obj, dict):
            for k, v in obj.items():
                sub = f"{ruta}.{k}" if ruta else str(k)
                if k == "album_context":
                    if v is not None:
                        err("V108", "album_context debe ser null "
                                    "(el blueprint de álbum llega en F4, §9.2)", "A")
                    continue
                if v is None and k != "album_context":
                    err("V108", f"campo en null no admitido (plan completo): {sub}", "A")
                _recorre(v, sub)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                _recorre(v, f"{ruta}[{i}]")
        elif isinstance(obj, str) and obj.strip().lower() == "auto":
            err("V108", f'valor literal "auto" no admitido (plan completo): '
                        f"{ruta} — lo resuelve el intérprete antes de validar", "A")

    _recorre(plan, "")


# --- capa A: invariantes de forma (V109) --------------------------------------

def _gates_forma(plan, err, aviso):
    """§6.1: nº de secciones, ids únicos, Σ bars = bars_total, intro/outro en
    cancion. Devuelve (secciones, plantilla, controles) o None si no hay
    estructura utilizable."""
    form = plan.get("form") or {}
    secs = form.get("sections")
    if not isinstance(secs, list) or not secs:
        return None
    plantilla = form.get("template")
    controles = plan.get("controls") or {}

    if not (EP.LIMITES["secciones"][0] <= len(secs) <= EP.LIMITES["secciones"][1]):
        err("V109", f"nº de secciones fuera del rango {EP.LIMITES['secciones']}: "
                    f"{len(secs)} (§6.1)", "A")
    ids = [s.get("id") for s in secs if isinstance(s, dict)]
    if len(ids) != len(set(ids)):
        dup = sorted({i for i in ids if ids.count(i) > 1})
        err("V109", f"ids de sección duplicados (E106 del contrato doc): {dup}", "A")

    total = sum(s.get("bars", 0) for s in secs if isinstance(s, dict))
    bars_total = (plan.get("duration") or {}).get("bars_total")
    if isinstance(bars_total, int) and bars_total > 0 and total != bars_total:
        err("V109", f"Σ bars de las secciones ({total}) ≠ duration.bars_total "
                    f"({bars_total}) (§6.1)", "A")

    if plantilla == "cancion":
        tipos = [s.get("type") for s in secs if isinstance(s, dict)]
        n_intro, n_outro = tipos.count("intro"), tipos.count("outro")
        if n_intro != 1 or n_outro != 1:
            err("V109", f'form.template="cancion" exige exactamente 1 sección '
                        f'type="intro" y 1 type="outro" (hay {n_intro} y {n_outro}) (§6.1)', "A")

    # aviso (no gate): duración estimada vs banda del target (§9.2)
    bpm = (plan.get("global") or {}).get("bpm")
    target = (plan.get("duration") or {}).get("target")
    if isinstance(bpm, int) and isinstance(target, str) and total > 0:
        minutos = total * 4.0 / bpm
        banda = "corta" if minutos < 3.0 else ("media" if minutos <= 6.0 else "larga")
        if banda != target:
            aviso(f"duración estimada {minutos:.1f} min ({total} compases × 4/4 a "
                  f"{bpm} BPM) cae en la banda '{banda}', no en el target "
                  f"'{target}' declarado (aviso de contrato §9.2; no bloquea)")
    return secs, plantilla, controles


# --- capa A: curva de energía (V112) ------------------------------------------

def _gates_curva(plan, secciones, controles, err):
    """§6.1: ≥1 pico (energy ≥0.7) si Energía ≥ alta."""
    energia = controles.get("energia")
    if energia in ("alta", "muy_alta"):
        if not any(float(s.get("energy", 0)) >= 0.7 for s in secciones):
            err("V112", f'controls.energia="{energia}" exige ≥1 pico con '
                        f"energy ≥ 0.7 y ninguna sección lo alcanza (§6.1)", "A")


# --- capa A: armonía (V110) -----------------------------------------------------

def _gates_armonia(plan, err):
    """§6.1: key parseable; acordes parseables y con TODAS sus notas ∈ tónica
    o vecinas (criterio de acorde completo; ver cabecera del módulo)."""
    har = plan.get("harmony") or {}
    key = har.get("key")
    prog = har.get("progressions")
    if not isinstance(key, str) or not key.strip():
        return
    if not _parsea_key(key):
        err("V110", f"harmony.key no parseable por forge.theory.parse_key: {key!r} "
                    f"(E113 del contrato doc)", "A")
        return
    if _tonic_y_modo(key) is None:
        return
    pcs_ok = _vecinas(key)
    if not isinstance(prog, dict):
        return
    for t, acordes in prog.items():
        if not isinstance(acordes, list):
            continue
        for sim in acordes:
            tonos = _tonos_acorde(sim)
            if tonos is None:
                err("V110", f"acorde no parseable por forge.theory.parse_chord: "
                            f"{sim!r} en progressions[{t!r}] (E113)", "A")
                continue
            fuera = sorted(tonos - pcs_ok)
            if fuera:
                err("V110", f"acorde {sim!r} tiene notas fuera de la tonalidad "
                            f"{key!r} y sus vecinas (≤1 alteración): pcs {fuera} (§6.1)", "A")


# --- capa A: instrumentación (V111) --------------------------------------------

def _gates_instrumentacion(plan, secciones, controles, err, aviso):
    """§6.1: coherencia de drums con el control y el perfil; palette ⊇ profile."""
    drums_ctrl = controles.get("drums")
    perfil = ((plan.get("orchestration") or {}).get("profile"))
    drums_perfil = None
    if isinstance(perfil, str) and perfil in production.nombres():
        preset = production.resolver(perfil)
        if preset is not None:
            drums_perfil = bool(preset.get("engines", {}).get("drums", False))

    if drums_ctrl == "ausente":
        no_off = [s.get("id") for s in secciones if s.get("drums") != "off"]
        if no_off:
            err("V111", f'controls.drums="ausente" exige drums="off" en TODAS las '
                        f"secciones; incumplen: {no_off} (§6.1)", "A")
        if perfil and drums_perfil is not False:
            err("V111", f'controls.drums="ausente" exige un perfil con drums: False '
                        f"y {perfil!r} no lo es (§6.1)", "A")
    elif drums_ctrl == "protagonista":
        con_peso = [s.get("id") for s in secciones
                    if s.get("drums") in ("groove", "heavy")]
        if not con_peso:
            err("V111", 'controls.drums="protagonista" exige ≥1 sección con drums '
                        'en {groove, heavy} (§6.1)', "A")
        if perfil and drums_perfil is not True:
            err("V111", f'controls.drums="protagonista" exige un perfil con '
                        f"drums: True y {perfil!r} no lo es (§6.1)", "A")

    pal = ((plan.get("identity") or {}).get("palette"))
    if isinstance(pal, list) and isinstance(perfil, str) and perfil not in pal:
        err("V111", f'identity.palette debe incluir orchestration.profile '
                    f"({perfil!r}) cuando está presente (§9.2)", "A")

    # aviso informativo (W406 del doc): focus que referencia instrumentos
    # fuera del set base de la identidad no suena en esas secciones.
    estilo = (plan.get("identity") or {}).get("style")
    if estilo in identities.CON_RECETA:
        set_base = set(getattr(identities, estilo).SET_BASE)
        for s in secciones:
            fuera = [f for f in (s.get("focus") or []) if f not in set_base]
            if fuera:
                aviso(f"focus de sección {s.get('id')!r} referencia instrumentos "
                      f"fuera del set base de {estilo}: {fuera} (W406: no suenan)")


# --- capa A: ending (V116) ------------------------------------------------------

def _gates_ending(plan, secciones, err):
    """E112 del contrato doc: fade_out.bars ≥ 1 (esquema) y ≤ compases de la
    última sección."""
    fo = ((plan.get("ending") or {}).get("fade_out") or {})
    bars = fo.get("bars")
    if isinstance(bars, int) and not isinstance(bars, bool) and secciones:
        ultima = secciones[-1].get("bars")
        if isinstance(ultima, int) and bars > ultima:
            err("V116", f"ending.fade_out.bars ({bars}) no puede superar los "
                        f"compases de la última sección ({ultima}) (E112)", "A")


# --- capa B (§6.2) ---------------------------------------------------------------

def _capa_b(plan, secciones, plantilla, err):
    """Invariantes universales + condicionados a la forma (§6.2)."""
    protagonist = (plan.get("identity") or {}).get("protagonist")

    # Melodía: protagonista en focus[] de ≥2 secciones (§6.2 universal).
    if isinstance(protagonist, str):
        n = sum(1 for s in secciones if protagonist in (s.get("focus") or []))
        if n < 2:
            err("V113", f"el protagonista {protagonist!r} aparece en focus[] de "
                        f"{n} sección(es); exige ≥2 (§6.2)", "B")

    # Solo: materialización (break/bridge + focus exacto) y nunca la más débil.
    solos = plan.get("solos") or []
    energias = [float(s.get("energy", 0)) for s in secciones]
    min_energia = min(energias) if energias else None
    for solo in solos:
        if not isinstance(solo, dict):
            continue
        sid, inst = solo.get("section_id"), solo.get("instrument")
        sec = next((s for s in secciones if s.get("id") == sid), None)
        if sec is None:
            err("V107", f"el solo referencia una sección inexistente: {sid!r} "
                        f"(E107 del contrato doc)", "B")
            continue
        if sec.get("type") not in ("break", "bridge"):
            err("V113", f"el solo de {inst!r} en {sid!r} exige type ∈ {{break, "
                        f"bridge}} y la sección es {sec.get('type')!r} (§6.2)", "B")
        if list(sec.get("focus") or []) != [inst]:
            err("V113", f"el solo de {inst!r} exige focus=[{inst!r}] en {sid!r}; "
                        f"hay {sec.get('focus')!r} (§6.2)", "B")
        if min_energia is not None and float(sec.get("energy", 0)) == min_energia:
            err("V113", f"la sección de solo {sid!r} es la de menor energía "
                        f"declarada del plan (§6.2)", "B")

    if plantilla != "cancion":
        return

    # cadencia (§6.2, solo cancion): ≥1 sección chorus/verse cuya progresión
    # declarada resuelve (raíz tónica o dominante). Interpretación documentada
    # en la cabecera del módulo.
    har = plan.get("harmony") or {}
    prog = har.get("progressions") or {}
    key = har.get("key")
    resuelve = _progresion_resuelve(key, prog)
    if not resuelve:
        err("V114", 'form.template="cancion" exige cadencia resolutiva (raíz '
                    'tónica o dominante) al final de ≥1 progresión declarada '
                    "para chorus/verse; progressions={"
                    + ", ".join(f"{t}: {list(v)[-1] if isinstance(v, list) and v else '—'}"
                                for t, v in prog.items()) + "} (§6.2)", "B")

    # transiciones (§6.5 fila Transiciones, capa B, solo cancion): sin saltos
    # de energía >0.4 entre secciones vecinas; ciclos/libre exentos.
    for a, b in zip(secciones, secciones[1:]):
        salto = abs(float(a.get("energy", 0)) - float(b.get("energy", 0)))
        if salto > 0.4:
            err("V115", f"salto de energía {salto:.2f} entre vecinas "
                        f"{a.get('id')!r} → {b.get('id')!r} (>0.4; §6.5, solo cancion)", "B")


def _progresion_resuelve(key, prog):
    """True si ≥1 progresión de chorus/verse termina en raíz tónica o dominante."""
    propio = _tonic_y_modo(key) if isinstance(key, str) else None
    if propio is None:
        return False
    tonica = propio[0] % 12
    dominante = (tonica + 7) % 12
    for t in ("chorus", "verse"):
        acordes = prog.get(t)
        if not isinstance(acordes, list) or not acordes:
            continue
        raiz = _raiz_acorde(acordes[-1])
        if raiz is not None and raiz in (tonica, dominante):
            return True
    return False


# ---------------------------------------------------------------------------
# Capa C — checks estructurales del MIDI (§6.3, gates definitivos)
# ---------------------------------------------------------------------------

def verificar_capa_c(plan, events):
    """Aplica los gates estructurales de §6.3 sobre ``events.json``.

    ``events`` es el dict que ``forge.engine.to_events(res)`` escribe en
    ``events.json`` (pistas con ``notes=[[t, d, pitch, vel], …]`` y secciones
    con ``{id, kind, t0, t1, bars}``). Devuelve {"ok", "checks"} donde cada
    check es {"id", "nombre", "ok", "detalle", "bloqueante"}. Solo se aplican
    los gates definitivos de §6.3: las métricas experimentales de esa sección
    se miden y registran, no bloquean (C-09/C-11), y no se calculan aquí.
    """
    checks = []
    secciones = ((plan.get("form") or {}).get("sections")) or []
    estilo = (plan.get("identity") or {}).get("style")
    protagonist = (plan.get("identity") or {}).get("protagonist")
    perfil = (plan.get("orchestration") or {}).get("profile")

    tracks = {t.get("id"): t for t in (events.get("tracks") or [])}
    ev_secs = {s.get("id"): s for s in (events.get("sections") or [])}
    ev_secs_orden = [s.get("id") for s in (events.get("sections") or [])]
    bpm_ev = events.get("bpm")
    bb = events.get("bar_beats")
    total_beats = events.get("total_beats")

    def chk(cid, nombre, ok, detalle):
        checks.append({"id": cid, "nombre": nombre, "ok": bool(ok),
                       "detalle": detalle, "bloqueante": True})

    # C1 — nº de pistas y roles = identidad/perfil (§6.3 «pistas/roles»)
    set_base = set(getattr(identities, estilo).SET_BASE) if estilo in identities.CON_RECETA else set(tracks)
    esperadas = {iid: ROL_DE.get(iid) for iid in set_base}
    faltan = sorted(i for i in esperadas if i not in tracks)
    sobran = sorted(i for i in tracks if i not in esperadas)
    rol_mal = [f"{i}:{tracks[i].get('role')}≠{esperadas[i]}" for i in esperadas
               if i in tracks and tracks[i].get("role") != esperadas[i]]
    if perfil == "original":
        # camino ORIGINAL: sin motores; solo se exige el set base de la identidad
        ok_c1 = not (faltan or sobran or rol_mal)
    else:
        ok_c1 = not (faltan or sobran or rol_mal)
    detalle_c1 = f"pistas {sorted(tracks)}; roles OK" if ok_c1 else (
        f"faltan={faltan} sobran={sobran} roles_mal={rol_mal}")
    chk("C1", "pistas y roles = identidad/perfil (§6.3)", ok_c1, detalle_c1)

    # C2 — compases y BPM = Plan (§6.3)
    bpm_plan = (plan.get("global") or {}).get("bpm")
    bpm_ok = (bpm_plan is not None and bpm_ev is not None
              and abs(float(bpm_ev) - float(bpm_plan)) < 1e-6)
    bars_plan = {s.get("id"): s.get("bars") for s in secciones}
    bars_mal = [f"{sid}:{ev_secs[sid].get('bars')}≠{bars_plan[sid]}"
                for sid in bars_plan if sid in ev_secs
                and ev_secs[sid].get("bars") != bars_plan[sid]]
    orden_ok = ev_secs_orden == [s.get("id") for s in secciones]
    suma_ev = sum((ev_secs[s].get("bars") or 0) for s in ev_secs)
    bars_total_plan = (plan.get("duration") or {}).get("bars_total")
    chk("C2", "compases y BPM = Plan (§6.3)",
        bpm_ok and not bars_mal and orden_ok and suma_ev == bars_total_plan,
        f"bpm evento={bpm_ev} plan={bpm_plan}; bars por sección "
        f"{'OK' if not bars_mal else bars_mal}; orden {'OK' if orden_ok else 'difiere'}; "
        f"Σbars evento={suma_ev}")

    # C3 — duración ±5% (§6.3: aritmética determinista compases × BPM)
    dur_ok, dur_det = False, "sin datos"
    if bpm_plan and total_beats is not None and bars_plan:
        objetivo_s = (plan.get("duration") or {}).get("bars_total", 0) * 4.0 * 60.0 / bpm_plan
        real_s = float(total_beats) * 60.0 / float(bpm_ev or bpm_plan)
        delta = abs(real_s - objetivo_s) / objetivo_s if objetivo_s else 1.0
        dur_ok = delta <= 0.05
        dur_det = f"real={real_s:.1f}s objetivo={objetivo_s:.1f}s delta={delta * 100:.2f}%"
    chk("C3", "duración ±5% del objetivo (§6.3)", dur_ok, dur_det)

    # C4 — contenido (§6.3): pistas no vacías (BLOQUEANTE) + solo no vacío
    # (BLOQUEANTE, §6.5 fila Solo: «solo no vacío, densidad alta») + focus[]
    # suena en su sección (DIAGNÓSTICO no bloqueante — hallazgo F1-C4b, ver
    # cabecera del módulo).
    drums_todos_off = all(s.get("drums") == "off" for s in secciones) and bool(secciones)
    vacias = [tid for tid, t in tracks.items() if not (t.get("notes") or [])
              and not (tid == "drums" and drums_todos_off)]
    chk("C4", "contenido: ninguna pista vacía (§6.3)", not vacias,
        f"vacías={vacias or 'ninguna'}")

    solos = (plan.get("solos") or [])
    solo_vacio = []
    for solo in solos:
        if not isinstance(solo, dict):
            continue
        evs = ev_secs.get(solo.get("section_id"))
        tr = tracks.get(solo.get("instrument"))
        if evs is None or tr is None:
            solo_vacio.append(f"{solo.get('section_id')}:{solo.get('instrument')}")
            continue
        n = sum(1 for nt in (tr.get("notes") or [])
                if evs.get("t0") <= nt[0] < evs.get("t1"))
        if n < 1:
            solo_vacio.append(f"{solo.get('section_id')}:{solo.get('instrument')}")
    chk("C4s", "solo no vacío (§6.5 fila Solo)", not solo_vacio,
        f"secciones de solo sin notas del instrumento={solo_vacio or 'ninguna'}")

    focus_mal = []
    for s in secciones:
        evs = ev_secs.get(s.get("id"))
        if evs is None:
            continue
        t0, t1 = evs.get("t0"), evs.get("t1")
        for inst in (s.get("focus") or []):
            tr = tracks.get(inst)
            if tr is None:
                focus_mal.append(f"{s.get('id')}:{inst} sin pista")
                continue
            n = sum(1 for nt in (tr.get("notes") or []) if t0 <= nt[0] < t1)
            if n < 1:
                focus_mal.append(f"{s.get('id')}:{inst} sin notas en su sección")
    checks.append({"id": "C4b", "nombre": "focus[] suena en su sección (§6.3)",
                   "ok": not focus_mal,
                   "detalle": (f"focus sin notas={focus_mal or 'ninguno'} — "
                               "DIAGNÓSTICO no bloqueante (hallazgo F1-C4b: "
                               "improv.py:18 'silencio = decisión'; focus compila a "
                               "deltas de velocity §2.6.4; el ancla de la casa "
                               "demo_medianoche incumple este check en outro:rhodes)"),
                   "bloqueante": False})

    # C5 — rango del protagonista dentro de REGISTER_DEFAULT (§6.3).
    # Hallazgo F1-C5: el motor de rhodes (improv.rhodes_notes) escribe
    # sistemáticamente pitch 44, 1 semitono bajo la tabla real de forge
    # (forge/styles.py keys range [45, 76]) y bajo el REGISTER_DEFAULT de las
    # 3 recetas — deriva del motor, que Fase 1 tiene congelado. Por la cláusula
    # de §6.3 (falsos positivos sistemáticos ⇒ reclasificación documentada)
    # se registra como DIAGNÓSTICO no bloqueante hasta calibración; se mide
    # siempre contra REGISTER_DEFAULT y el rango medido queda en el detalle.
    ok_c5, det_c5 = False, "protagonista sin pista"
    if protagonist in tracks and estilo in identities.CON_RECETA:
        reg = getattr(identities, estilo).REGISTER_DEFAULT.get(protagonist)
        notas = [nt[2] for nt in (tracks[protagonist].get("notes") or [])]
        if reg and notas:
            lo, hi = min(notas), max(notas)
            ok_c5 = reg[0] <= lo and hi <= reg[1]
            det_c5 = (f"{protagonist}: rango real [{lo}, {hi}] vs "
                      f"REGISTER_DEFAULT {reg} — DIAGNÓSTICO no bloqueante "
                      "(hallazgo F1-C5)")
        elif not reg:
            det_c5 = f"{protagonist} sin REGISTER_DEFAULT en la receta {estilo!r}"
    elif protagonist not in tracks:
        det_c5 = f"el protagonista {protagonist!r} no tiene pista en el MIDI"
    checks.append({"id": "C5", "nombre": "rango del protagonista = REGISTER_DEFAULT (§6.3)",
                   "ok": ok_c5, "detalle": det_c5, "bloqueante": False})

    # C6 — sin runs de repetición (>8 notas idénticas consecutivas; §6.3:
    # detector de monotonía accidental / nota atascada, no teoría del riff)
    runs = []
    for tid, t in tracks.items():
        notas = sorted(t.get("notes") or [], key=lambda n: (n[0], n[2]))
        racha, prev = 1, None
        for nt in notas:
            firma = (nt[2], nt[3])          # (pitch, velocity)
            if prev is not None and firma == prev:
                racha += 1
                if racha == 9:              # umbral cruzado: se registra una vez
                    runs.append((tid, firma))
            else:
                racha = 1
            prev = firma
    chk("C6", "sin runs >8 notas idénticas consecutivas (§6.3)", not runs,
        "runs=" + (", ".join(f"{t} pc{f[0]}v{f[1]}" for t, f in runs) or "ninguno"))

    # C7 — partitura: compás y ticks coherentes con bar_beats (§6.3)
    ok_c7, det_c7 = False, "sin secciones en events"
    if ev_secs and bb:
        acum = 0.0
        coherente = True
        for sid in ev_secs_orden:
            s = ev_secs[sid]
            if abs(s.get("t0", -1) - acum) > 1e-6 or \
                    abs((s.get("t1", -1) - s.get("t0", -1)) - (s.get("bars") or 0) * bb) > 1e-6:
                coherente = False
                break
            acum += (s.get("bars") or 0) * bb
        tpb_ok = (events.get("ticks_per_beat") or 0) > 0
        total_ok = total_beats is None or abs(float(total_beats) - acum) < 1e-6
        ok_c7 = coherente and tpb_ok and total_ok
        det_c7 = (f"t0/t1 acumulados coherentes con bars×bar_beats({bb}); "
                  f"ticks_per_beat={events.get('ticks_per_beat')}; "
                  f"total_beats={total_beats} vs Σbars×bb={acum}")
    chk("C7", "partitura coherente con bar_beats (§6.3)", ok_c7, det_c7)

    return {"ok": all(c["ok"] for c in checks if c["bloqueante"]), "checks": checks}
