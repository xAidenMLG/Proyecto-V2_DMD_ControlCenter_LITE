"""Intérprete Universal — Fase 2 (spec DMD Control Center v1.4, §7, §9.4.1, §12.1).

Transforma una INTENCIÓN (identity + 6 controles opcionales + overrides
Advanced) en un Composition Plan COMPLETO y válido (capas A/B), sin tocar la
autoridad compositiva: el intérprete solo alimenta a ``validador`` →
``plan_compilador`` → ``scripts/produce.py`` (§10.3). Es una función pura:
mismos inputs + misma seed ⇒ mismo plan (§7.2.3); la fecha vive solo en
``evidence.created_at`` (§9.5) y se inyecta por ``ahora``.

Los 7 pasos (C-02, §7):
    1 parse/normalizar          4 forma + secciones + curva de energía
    2 identidad + protagonista  5 solos
    3 armonía                   6 orquestación + densidad + drums
    7 emitir plan y validar (re-resolución ≤2 si capa B falla, §12.1)

Estados de campo (§9.1): null ⇒ el intérprete resuelve y registra en
``evidence.resolved``; concreto ⇒ se respeta tal cual; concreto con
``locked: true`` (secciones, el único ``locked`` del esquema v1) ⇒ intocable
incluso durante la re-resolución. La re-resolución solo ajusta campos no
locked; si tras 2 intentos sigue fallando ⇒ ``ErrorIntencion`` explicativo.

P-01 (cerrado con registro): tablas fijas declarativas — la variación entre
seeds queda acotada a campos determinados (tonalidad por seed dentro del pool
que pasa la regla de vecinas del validador, título). Reglas citadas en cada
entrada de ``evidence.resolved``.

P-06 (decisión F2): ``original`` excluido del Automatic (§4); el intérprete
solo elige entre los 6 perfiles con motores de jazz_engine.

La tonalidad se elige con el MISMO criterio que la capa A aplica (reutiliza
``validador._vecinas``/``_tonos_acorde`` — cero duplicación, cero drift).

HALLAZGO F2 DOCUMENTADO (inconsistencia spec↔recetas, resuelta): las tablas
``PROGRESIONES`` de las recetas N1 contienen calidades funcionales (IV maj9
dórico, V9 con sensible, iim7b5, bVI13) que NO pasan el criterio de vecinas
de la capa A (§6.1, lectura F1 documentada: todas las notas del acorde ∈
tónica natural o vecinas ≤1 alteración) en NINGUNA tonalidad menor — el
ancla de la casa usa progresiones manuscritas distintas de las de su receta
(y los 13 docs de ``albumes/noches_largas`` declaran solo verse/chorus).
El criterio de capa A NO se debilita (una ampliación de gate exige registro
L4, §11.3). Resolución: el intérprete declara progresiones con los PATRONES
MODALES derivados del propio ancla (offsets y calidades todo-diatónicos,
válidos en las 12 tonalidades menores), que son el lenguaje armónico real de
la casa; las tablas de receta siguen alimentando la producción para los
types no declarados (comportamiento intacto de ``dark_director/compilador``).
Decisión y evidencia: informe de Fase 2, sección 4 (decisiones técnicas).
"""
import hashlib
import json
import re
from datetime import datetime, timezone

from dark_director import contract, identities
from dark_director.compilador import _instanciar_simbolo
from jazz_engine import production

from . import esquema_plan as EP
from .validador import _tonos_acorde, _vecinas, validar

RESOLVED_BY = "interprete@fase2"
SEED_MIN, SEED_MAX = 1, 999_983

#: P-06: ``original`` es el camino sin jazz_engine y queda excluido (§4).
PERFILES_SIN_DRUMS = tuple(p for p in production.nombres() if p != "original"
                           and not (production.resolver(p) or {}).get("engines", {}).get("drums"))
PERFILES_CON_DRUMS = tuple(p for p in production.nombres() if p != "original"
                           and (production.resolver(p) or {}).get("engines", {}).get("drums"))
PERFIL_DEFAULT_SIN_DRUMS = "sax_rhodes"

#: Tonalidades menores con grafía estándar (las 14 del círculo; todas
#: parseables por forge.theory.parse_key). El modo menor es el idioma de la
#: casa (las 3 recetas y el ancla usan modo menor).
POOL_KEYS = ("A minor", "E minor", "B minor", "F# minor", "C# minor", "G# minor",
             "D# minor", "D minor", "G minor", "C minor", "F minor", "Bb minor",
             "Eb minor", "Ab minor")

#: Patrones de progresión por type (pares offset-sobre-la-tónica, calidad),
#: DERIVADOS DEL ANCLA de la casa (ver hallazgo F2 en la cabecera): todo el
#: vocabulario es diatónico de la escala natural menor — pasa el criterio de
#: vecinas de la capa A en las 12 tonalidades menores (verificado
#: programáticamente en la integración). El verse termina en raíz dominante
#: (V114 por construcción en ``cancion``).
PATRONES_PROGRESION = {
    "intro":      ((0, "m9"),),
    "verse":      ((0, "m9"), (8, "maj9"), (5, "m9"), (7, "7sus4")),
    "pre_chorus": ((5, "m9"), (7, "7sus4")),
    "chorus":     ((8, "maj9"), (3, "maj9"), (5, "m9"), (7, "7sus4")),
    "bridge":     ((8, "maj7"), (3, "maj9")),
    "break":      ((0, "m9"), (8, "maj7")),
    "outro":      ((0, "m9"),),
}

#: Instrumento con bloque generativo de improvisación (E301 del contrato doc).
#: Cabecera de interprete.py: R30 — el intérprete no declara solos automáticos
#: del lead (hallazgo P-02); la constante se usa para identificarlo.
LEAD_DOC = "sax_tenor"

#: P-01 — Carácter armónico (control 4) → harmony.language real (§7.1).
#: auto → por accessibility (semántica existente del plan, no inventada).
IDIOMA_POR_CONTROL = {"nocturno": "pop_dream_pop", "jazz": "hybrid",
                      "crudo": "experimental", "sombrio": "experimental"}
IDIOMA_POR_ACCESIBILIDAD = {"commercial": "pop_dream_pop", "balanced": "hybrid",
                            "experimental": "experimental"}
#: Ajuste de tensión por carácter (pedal Nocturno/Sombrío; Crudo tiende a riff).
DELTA_TENSION = {"nocturno": -0.05, "jazz": 0.0, "crudo": 0.08, "sombrio": 0.12}
#: P-01 — Pulso/groove (control 5) propone global.bpm dentro de
#: BPM_RANGO_TIPICO de la receta (§7.1: "propone global.bpm").
FRACCION_BPM = {"lento_arrastrado": 0.0, "swing": 0.4, "recto": 0.6, "latin": 0.8}
#: P-01 — Duración (control 3) → minutos objetivo de la banda (§7.1).
MINUTOS_OBJETIVO = {"corta": 2.5, "media": 5.0, "larga": 8.0}
#: P-01 — Energía (control 1) → punto medio de la curva (§7.1).
ENERGIA_OBJETIVO = {"muy_baja": 0.15, "baja": 0.30, "media": 0.45,
                    "alta": 0.65, "muy_alta": 0.80}
DELTA_ENERGIA_DENSITY = {"muy_baja": -0.06, "baja": -0.03, "media": 0.0,
                         "alta": 0.04, "muy_alta": 0.08}
DELTA_DENSITY = {"nocturno": -0.03, "jazz": 0.0, "crudo": 0.08,
                 "sombrio": -0.04}
#: Presencia de drums (control 6): cap para "contenida"; el resto usa la
#: escalera de la receta; "ausente" ⇒ todo off + perfil sin drums (§7.1).
CAP_CONTENIDA = {"groove": "light", "heavy": "light"}
#: Peso relativo por type al repartir compases (informado por D_RECETA/ENERGY
#: de las recetas: intro/outro ligeros, chorus pleno).
PESO_BARS = {"intro": 0.6, "outro": 0.6, "pre_chorus": 0.5, "verse": 1.0,
             "chorus": 1.2, "bridge": 0.8, "break": 1.0}

#: Esqueletos de forma por plantilla y nº de secciones (§7.1 control 2).
#: ``cancion`` exige 1 intro + 1 outro (V109) y ≥1 verse/chorus con cadencia
#: (V114); ``ciclos``/``libre`` sin exigencias formales (§6.2). El slot
#: ``break``/``bridge`` intermedio es el candidato natural de solo (paso 5).
PLANTILLAS = {
    "cancion": {
        4: ("intro", "verse", "chorus", "outro"),
        5: ("intro", "verse", "pre_chorus", "chorus", "outro"),
        6: ("intro", "verse", "pre_chorus", "chorus", "bridge", "outro"),
        7: ("intro", "verse", "pre_chorus", "chorus", "bridge", "chorus", "outro"),
        8: ("intro", "verse", "pre_chorus", "chorus", "break", "bridge", "chorus", "outro"),
        9: ("intro", "verse", "pre_chorus", "chorus", "break", "bridge", "verse", "chorus", "outro"),
    },
    "ciclos": {
        2: ("verse", "verse"),
        3: ("verse", "bridge", "verse"),
        4: ("verse", "verse", "bridge", "verse"),
        5: ("intro", "verse", "verse", "bridge", "verse"),
        6: ("intro", "verse", "verse", "bridge", "verse", "outro"),
        7: ("intro", "verse", "verse", "bridge", "verse", "verse", "outro"),
        8: ("intro", "verse", "break", "verse", "bridge", "verse", "break", "outro"),
        9: ("intro", "verse", "break", "verse", "bridge", "verse", "break", "verse", "outro"),
    },
    "libre": {
        2: ("verse", "bridge"),
        3: ("intro", "verse", "outro"),
        4: ("intro", "verse", "bridge", "outro"),
        5: ("intro", "verse", "break", "verse", "outro"),
        6: ("intro", "verse", "break", "bridge", "verse", "outro"),
        7: ("intro", "verse", "pre_chorus", "chorus", "break", "verse", "outro"),
        8: ("intro", "verse", "pre_chorus", "chorus", "break", "bridge", "verse", "outro"),
        9: ("intro", "verse", "pre_chorus", "chorus", "break", "bridge", "verse", "chorus", "outro"),
    },
}

#: Banco de títulos por identidad (metadata sin consumidor musical, §9.2):
#: elijo por seed; si el usuario aporta title, no se toca.
TITULOS = {
    "dark_triphop": ("Nocturno de Neón", "Bruma Lenta", "Velo de Humo",
                     "Umbral Azul", "Ciudad Dormida", "Pulso de Medianoche",
                     "Sala de Espera", "Lluvia en el Asfalto",
                     "Pasillo Sin Fin", "Alba Tardía"),
    "doom_triphop": ("Plomo y Vapor", "Fosa Atlántica", "Catedral Rota",
                     "Marea Negra", "Búnker de Sal", "Gravedad Lenta",
                     "Túnel Sin Salida", "Hierro Viejo",
                     "Eco de Cemento", "Último Tren"),
    "doom_dark_jazz": ("Humo de Latón", "Sótano con Aire", "Cartografía Oscura",
                       "Cámara Lenta", "Fiebre Baja", "Piano en la Niebla",
                       "Sala sin Esquinas", "Duelo de Medianoche",
                       "Ceniza Sobre el Mar", "Trabajo de Noche"),
}


class ErrorIntencion(Exception):
    """Error explicativo del intérprete: intención inválida o irresoluble
    tras la re-resolución (§6.2: 'o devuelve error explicativo')."""


# ---------------------------------------------------------------------------
# Paso 1 — parse / normalizar (incluye paso 2: identidad + protagonista)
# ---------------------------------------------------------------------------

_RE_TITULO = re.compile(r"\s+")

#: Mapa pc → grafía del pool (primera ocurrencia; D#/Eb y G#/Ab comparten pc).
#: Calculado con las tablas estáticas del validador (sin importar forge aquí).
from .validador import _PC_LETRA as _PC_LETRA_V, _RE_KEY as _RE_KEY_V


def _pc_estatico(key):
    m = _RE_KEY_V.match(key.strip())
    letra, alter = m.group(1), m.group(2)
    return (_PC_LETRA_V[letra] + (1 if alter == "#" else -1 if alter == "b" else 0)) % 12


_KEY_POR_PC = {}
for _k in POOL_KEYS:
    _KEY_POR_PC.setdefault(_pc_estatico(_k), _k)


def _normalizar_intencion(intencion):
    """Paso 1-2 (§7): valida identidad y controles, normaliza entradas.

    Devuelve (normalizado, resueltas): ``normalizado`` es un dict con las
    entradas en forma canónica; ``resueltas`` acumula las decisiones ya
    tomadas en la normalización (paso 1), con su regla.
    """
    if not isinstance(intencion, dict):
        raise ErrorIntencion("la intención debe ser un objeto JSON "
                             "(raíz no-objeto)")
    permitidas = {"mode", "seed", "title", "identity", "controls",
                  "album_context", "form", "ending", "harmony", "solos",
                  "orchestration", "global", "duration"}
    desconocidas = [k for k in intencion if k not in permitidas]
    if desconocidas:
        raise ErrorIntencion(
            f"claves desconocidas en la intención: {desconocidas} — una intención "
            "declara identity + controles + overrides Advanced; plan_version, "
            "notes y evidence los emite el propio intérprete")
    resueltas = []
    modo = intencion.get("mode", "automatic")
    if modo not in (None, "automatic"):
        raise ErrorIntencion(
            f'mode={modo!r} no es una intención del intérprete: el comando '
            '"automatic" resuelve intenciones (mode null/"automatic"); un plan '
            'guided llega COMPLETO por "validar"/"compilar" (§9.2: mode gobierna '
            "qué pasos resuelven)")
    if intencion.get("album_context") is not None:
        raise ErrorIntencion("album_context debe ser null en F2 (el bloque de "
                             "identidad de álbum llega en F4, §9.2/§12.1)")

    ident = intencion.get("identity")
    if not isinstance(ident, dict):
        raise ErrorIntencion("identity es requerido: {'style', 'accessibility', "
                             "'protagonist'[, 'palette']} (§9.2)")
    estilo = ident.get("style")
    if estilo not in contract.IDENTITIES:
        raise ErrorIntencion(f"identity.style fuera de IDENTITIES: {estilo!r} "
                             f"(recetas reales: {', '.join(contract.IDENTITIES)})")
    acces = ident.get("accessibility")
    if acces not in contract.ACCESSIBILITIES:
        raise ErrorIntencion(f"identity.accessibility fuera de ACCESSIBILITIES: "
                             f"{acces!r} (válidos: "
                             f"{', '.join(contract.ACCESSIBILITIES)})")
    prota = ident.get("protagonist")
    if prota not in EP.INSTRUMENTOS_MELDICOS:
        raise ErrorIntencion(f"identity.protagonist debe ser un instrumento "
                             f"melódico {EP.INSTRUMENTOS_MELDICOS}: {prota!r}")
    palette = ident.get("palette")
    if palette is not None:
        if (not isinstance(palette, list) or not palette
                or not all(isinstance(p, str) for p in palette)):
            raise ErrorIntencion("identity.palette debe ser lista no vacía de "
                                 "perfiles de producción")
        desconocidos = [p for p in palette if p not in EP.PERFILES_PRODUCCION]
        if desconocidos:
            raise ErrorIntencion(f"identity.palette incluye perfiles "
                                 f"desconocidos: {desconocidos} (válidos: "
                                 f"{', '.join(EP.PERFILES_PRODUCCION)})")
        if "original" in palette:
            raise ErrorIntencion("identity.palette incluye 'original': el "
                                 "camino sin jazz_engine está excluido del "
                                 "Automatic (P-06, §4)")

    controles_in = intencion.get("controls") or {}
    if not isinstance(controles_in, dict):
        raise ErrorIntencion("controls debe ser objeto (los 6 controles, §7.1)")
    desconocidos = [k for k in controles_in if k not in EP.CAMPOS_CONTROLS]
    if desconocidos:
        raise ErrorIntencion(f"controles desconocidos: {desconocidos} (solo hay "
                             f"6, §7.1)")
    # Resolución temprana de los 6 controles (§7.2.2 vacío=auto): todo control
    # null/ausente/"auto" queda CONCRETO por tabla declarativa (P-01) y se
    # registra. El plan emitido no contiene literales "auto" (V108, §6.1).
    controles = {}

    def _delegado(nombre, catalogo):
        v = controles_in.get(nombre)
        if v is not None and v != "auto":
            if v not in catalogo:
                raise ErrorIntencion(f"controls.{nombre} fuera de catálogo: "
                                     f"{v!r} (válidos: {', '.join(catalogo)})")
            return v, False
        return None, True

    energia, energia_auto = _delegado("energia", EP.CONTROLES["energia"])
    if energia_auto:
        energia = "media"
        resueltas.append({"campo": "controls.energia", "regla": "R1",
                          "entrada": "no aportado",
                          "detalle": "default declarativo: 'media' (§7.2.2)"})
    controles["energia"] = energia

    drums, drums_auto = _delegado("drums", EP.CONTROLES["drums"])
    if drums_auto:
        drums = {"muy_baja": "contenida", "baja": "contenida"}.get(
            controles["energia"], "presente")
        resueltas.append({"campo": "controls.drums", "regla": "R2",
                          "entrada": f"energia={controles['energia']}",
                          "detalle": f"default declarativo: '{drums}' (§7.1: "
                                     "interacción energía-drums)"})
    controles["drums"] = drums

    forma, forma_auto = _delegado("forma", EP.CONTROLES["forma"])
    if forma_auto:
        forma = "cancion"
        resueltas.append({"campo": "controls.forma", "regla": "R15",
                          "entrada": "forma=auto",
                          "detalle": "default declarativo: 'cancion' (§7.1 "
                                     "control 2)"})
    controles["forma"] = forma

    duracion, duracion_auto = _delegado("duracion", EP.CONTROLES["duracion"])
    if duracion_auto:
        duracion = "media"
        resueltas.append({"campo": "controls.duracion", "regla": "R12",
                          "entrada": "duracion=auto",
                          "detalle": "default declarativo: 'media' (§7.2.2)"})
    controles["duracion"] = duracion

    armonia, armonia_auto = _delegado("armonia", EP.CONTROLES["armonia"])
    if armonia_auto:
        armonia = {"commercial": "nocturno", "balanced": "jazz",
                   "experimental": "sombrio"}[acces]
        resueltas.append({"campo": "controls.armonia", "regla": "R6",
                          "entrada": f"armonia=auto, accessibility={acces}",
                          "detalle": f"tabla declarativa por accesibilidad → "
                                     f"'{armonia}' (§7.2.2)"})
    controles["armonia"] = armonia

    pulso, pulso_auto = _delegado("pulso", EP.CONTROLES["pulso"])
    if pulso_auto:
        pulso = "swing"
        resueltas.append({"campo": "controls.pulso", "regla": "R29",
                          "entrada": "pulso=auto",
                          "detalle": "pulso de la casa: 'swing'; el tempo lo fija "
                                     "BPM_DEFAULT de la receta (R11)"})
    controles["pulso"] = pulso
    if pulso_auto:
        controles["_pulso_auto"] = True

    seed_in = intencion.get("seed")
    if seed_in is not None and (not isinstance(seed_in, int)
                                or isinstance(seed_in, bool)):
        raise ErrorIntencion(f"seed debe ser int (Advanced, §7.2.5): {seed_in!r}")
    if isinstance(seed_in, int) and seed_in < 0:
        raise ErrorIntencion(f"seed negativa no admitida: {seed_in} (§11.2)")

    title_in = intencion.get("title")
    if title_in is not None and (not isinstance(title_in, str)
                                 or not title_in.strip()):
        raise ErrorIntencion(f"title debe ser texto no vacío: {title_in!r}")

    for bloque in ("form", "harmony", "ending", "global", "duration", "solos"):
        v = intencion.get(bloque)
        if v is None:
            continue
        if bloque == "solos":
            if not isinstance(v, list) or not all(isinstance(s, dict) for s in v):
                raise ErrorIntencion("solos debe ser lista de objetos "
                                     "{section_id, instrument} (§9.2)")
            continue
        if not isinstance(v, dict):
            raise ErrorIntencion(f"{bloque} debe ser objeto (§9.2): {v!r}")

    secciones_in = None
    form_in = intencion.get("form")
    if isinstance(form_in, dict):
        secciones_in = form_in.get("sections")
        if secciones_in is not None:
            if not isinstance(secciones_in, list) or not secciones_in:
                raise ErrorIntencion("form.sections debe ser lista no vacía "
                                     "(§9.2)")
            for i, sec in enumerate(secciones_in):
                faltan = [c for c in EP.REQUERIDOS_SECCION if c not in sec]
                if faltan:
                    raise ErrorIntencion(f"form.sections[{i}] incompleta; faltan "
                                         f"{faltan} (§9.1: secciones concretas o "
                                         "null, sin estados intermedios)")
            resueltas.append({"campo": "form.sections", "regla": "R3",
                              "entrada": f"{len(secciones_in)} secciones concretas",
                              "detalle": "secciones aportadas se respetan tal "
                                         "cual (paso 4 no las regenera)"})
    elif form_in is not None:
        raise ErrorIntencion(f"form debe ser objeto: {form_in!r}")

    armonia_in = intencion.get("harmony")
    if isinstance(armonia_in, dict):
        resueltas.append({"campo": "harmony", "regla": "R4",
                          "entrada": "bloque concreto aportado",
                          "detalle": "los subcampos concretos se respetan; "
                                     "solo los ausentes se resuelven (paso 3)"})

    return {
        "identity": {"style": estilo, "accessibility": acces, "protagonist": prota,
                     "palette": palette},
        "controls": controles,
        "controls_in": dict(controles_in),
        "seed_in": seed_in,
        "title_in": title_in,
        "sections_in": secciones_in,
        "form_in": form_in,
        "harmony_in": armonia_in,
        "ending_in": intencion.get("ending"),
        "global_in": intencion.get("global"),
        "duration_in": intencion.get("duration"),
        "solos_in": intencion.get("solos"),
        "receta": getattr(identities, estilo),
    }, resueltas


def derivar_seed(intencion_normalizada):
    """Seed auto-generada (§9.2, §7.2.5): derivada determinísticamente de
    identidad + controles (los mismos inputs canónicos de ``inputs_hash``,
    §9.3). El intérprete es puro: misma intención ⇒ misma seed ⇒ mismo plan;
    fijarla manualmente (seed en la intención) cambia el resultado de forma
    controlada."""
    base = json.dumps({"identity": intencion_normalizada["identity"],
                       "controls": intencion_normalizada["controls"]},
                      ensure_ascii=False, sort_keys=True)
    h = int(hashlib.sha256(base.encode("utf-8")).hexdigest()[:8], 16)
    return SEED_MIN + h % (SEED_MAX - SEED_MIN + 1)


def inputs_hash(seed, identidad, controles):
    """Fórmula §9.3: sha256 sobre identidad + controles + seed (misma que el
    tool de evidencia de F1)."""
    base = json.dumps({"identity": identidad, "controls": controles, "seed": seed},
                      ensure_ascii=False, sort_keys=True)
    return "sha256:" + hashlib.sha256(base.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Paso 3 — armonía (language, key, harmonic_rhythm, progresiones instanciadas)
# ---------------------------------------------------------------------------

def _idioma_de(norm, resueltas):
    """P-01: tabla declarativa control → language (el control ya es concreto:
    el paso 1 resolvió 'auto' por accesibilidad, R6)."""
    control = norm["controls"]["armonia"]
    idioma = IDIOMA_POR_CONTROL[control]
    resueltas.append({"campo": "harmony.language", "regla": "R5",
                      "entrada": f"controls.armonia={control}",
                      "detalle": f"tabla declarativa → '{idioma}' (§7.1)"})
    return idioma


def _progresiones_instanciadas(tonal_pc, types):
    """PATRONES_PROGRESION → símbolos en la tonalidad, con la MISMA función
    de instanciación que usa la autoridad (dark_director.compilador)."""
    return {t: [_instanciar_simbolo(tonal_pc, off, cal)
                for off, cal in PATRONES_PROGRESION[t]]
            for t in types}


def _key_pasa(tonal_pc, progresiones):
    """El criterio EXACTO de la capa A (V110): todas las notas de todos los
    acordes ∈ tónica o vecinas ≤1 alteración (reutiliza validador)."""
    pcs_ok = _vecinas(_nombre_key(tonal_pc))
    for acordes in progresiones.values():
        for sim in acordes:
            tonos = _tonos_acorde(sim)
            if tonos is None or (tonos - pcs_ok):
                return False
    return True


def _nombre_key(tonal_pc):
    """Grafía del pool para ese pc ( KeyError imposible: las 12 clases están)."""
    return _KEY_POR_PC[tonal_pc % 12]


def _resolver_armonia(norm, resueltas):
    """Paso 3 (§7): respeta el bloque aportado; resuelve language/key/progresiones."""
    receta = norm["receta"]
    har_in = dict(norm["harmony_in"]) if isinstance(norm["harmony_in"], dict) else {}
    idioma = har_in.get("language") or _idioma_de(norm, resueltas)
    hrb = har_in.get("harmonic_rhythm_bars")
    if hrb is None:
        hrb = receta.HARMONIC_RHYTHM_BARS
        resueltas.append({"campo": "harmony.harmonic_rhythm_bars", "regla": "R7",
                          "entrada": "no aportado",
                          "detalle": f"default de la receta {norm['identity']['style']}"
                                     f" = {hrb} (§3.2: default = receta)"})
    key = har_in.get("key")
    prog_in = har_in.get("progressions")
    if key is None:
        # Pool filtrado con el criterio de la capa A; índice por seed (P-01:
        # variación entre seeds dentro de un conjunto validado). Los patrones
        # del ancla pasan en las 12 clases de altura; el filtro es defensivo
        # (usa el criterio REAL de V110) y documenta el conjunto elegible.
        tipos = sorted(contract.SECTION_TYPES)
        candidatos = []
        for tonal_pc in range(12):
            nombre = _KEY_POR_PC[tonal_pc]
            if _armadura_de(nombre) is None:
                continue
            prog = _progresiones_instanciadas(tonal_pc, tipos)
            if _key_pasa(tonal_pc, prog):
                candidatos.append((tonal_pc, nombre, prog))
        if not candidatos:
            raise ErrorIntencion(f"ninguna tonalidad del pool pasa la regla de "
                                 f"vecinas (V110) con los patrones de progresión "
                                 "— el intérprete no inventa vocabulario (§9.1.4)")
        seed = norm["seed_efectiva"]
        tonal_pc, key, _ = candidatos[seed % len(candidatos)]
        resueltas.append({"campo": "harmony.key", "regla": "R8",
                          "entrada": f"seed={seed}",
                          "detalle": f"{key!r} elegida del pool de "
                                     f"{len(candidatos)} tonalidades que pasan "
                                     "V110 con los patrones de progresión"})
    tonal_pc = _pc_de_key(key)
    if prog_in is None:
        types_necesitados = sorted(contract.SECTION_TYPES)
        progresiones = _progresiones_instanciadas(tonal_pc, types_necesitados)
        resueltas.append({"campo": "harmony.progressions", "regla": "R9",
                          "entrada": f"key={key!r}",
                          "detalle": "instanciadas de PATRONES_PROGRESION "
                                     "(derivados del ancla de la casa; hallazgo "
                                     "F2 sobre las tablas de receta, ver informe) "
                                     "para los 7 types del contrato"})
    else:
        progresiones = {t: list(a) for t, a in prog_in.items()}
    return {"key": key, "language": idioma, "harmonic_rhythm_bars": hrb,
            "progressions": progresiones}


def _pc_de_key(key):
    """PC de la tónica vía forge (mismo parser que el validador)."""
    from .validador import _tonic_y_modo
    propio = _tonic_y_modo(key)
    if propio is None:
        raise ErrorIntencion(f"harmony.key no parseable por forge.theory: "
                             f"{key!r} (E113)")
    return propio[0] % 12


def _armadura_de(key):
    from .validador import _armadura
    return _armadura(key)


# ---------------------------------------------------------------------------
# Paso 4 — forma: plantilla, secciones, curva de energía/tensión/densidad
# ---------------------------------------------------------------------------

def _resolver_bpm(norm, resueltas):
    """global.bpm: pulso propone dentro de BPM_RANGO_TIPICO de la receta
    (P-01); la duración negocia (§7.1) para caer en la banda del target.
    Con pulso auto (R29) el tempo es BPM_DEFAULT de la receta."""
    receta = norm["receta"]
    glob_in = norm["global_in"] or {}
    bpm_in = glob_in.get("bpm")
    if bpm_in is not None:
        if not isinstance(bpm_in, int) or isinstance(bpm_in, bool) \
                or not (EP.LIMITES["bpm"][0] <= bpm_in <= EP.LIMITES["bpm"][1]):
            raise ErrorIntencion(f"global.bpm concreto debe ser int en "
                                 f"{EP.LIMITES['bpm']}: {bpm_in!r}")
        resueltas.append({"campo": "global.bpm", "regla": "R10",
                          "entrada": f"aportado (Advanced) = {bpm_in}",
                          "detalle": "se respeta tal cual; la duración se "
                                     "deriva de él"})
        return bpm_in
    pulso = norm["controls"]["pulso"]
    lo, hi = receta.BPM_RANGO_TIPICO
    if norm["controls"].get("_pulso_auto"):
        bpm = receta.BPM_DEFAULT
        detalle = (f"pulso auto → BPM_DEFAULT de la receta "
                   f"{norm['identity']['style']} = {bpm} (§3.1)")
    else:
        bpm = round(lo + FRACCION_BPM[pulso] * (hi - lo))
        detalle = (f"tabla declarativa FRACCION_BPM[{pulso!r}] sobre "
                   f"BPM_RANGO_TIPICO {receta.BPM_RANGO_TIPICO} → {bpm}")
    resueltas.append({"campo": "global.bpm", "regla": "R11",
                      "entrada": f"controls.pulso={pulso}", "detalle": detalle})
    return bpm


def _negociar_bars_y_bpm(norm, bpm, resueltas):
    """Duración ↔ forma (§7.1 control 2/3): compases objetivo por banda,
    con ajuste de bpm si el cap de 144 compases impide la banda (regla
    explícita registrada). El target ya es concreto (R12 en paso 1)."""
    dur_in = norm["duration_in"] or {}
    target = dur_in.get("target") or norm["controls"]["duracion"]
    if target not in EP.OBJETIVOS_DURACION:
        raise ErrorIntencion(f"duration.target fuera de catálogo: {target!r}")
    minutos = MINUTOS_OBJETIVO[target]
    if dur_in.get("bars_total") is not None:
        bars = dur_in["bars_total"]
        if not isinstance(bars, int) or isinstance(bars, bool) or bars <= 0:
            raise ErrorIntencion(f"duration.bars_total debe ser int > 0: {bars!r}")
        resueltas.append({"campo": "duration.bars_total", "regla": "R10",
                          "entrada": f"aportado (Advanced) = {bars}",
                          "detalle": "se respeta tal cual"})
        return target, bars
    bars = min(round(minutos * bpm / 4.0), EP.LIMITES["secciones"][1] * 16)
    bars = max(bars, 8)
    estimado = bars * 4.0 / bpm
    banda = "corta" if estimado < 3.0 else ("media" if estimado <= 6.0 else "larga")
    if banda != target:
        # negociación explícita (§7.1): bpm que centra la banda con esos bars
        bpm2 = max(EP.LIMITES["bpm"][0], min(EP.LIMITES["bpm"][1],
                                             round(bars * 4.0 / minutos)))
        if bpm2 != bpm:
            resueltas.append({"campo": "global.bpm", "regla": "R13",
                              "entrada": f"bpm={bpm}, target='{target}'",
                              "detalle": f"negociación duración-forma: bpm "
                                         f"{bpm} → {bpm2} para que "
                                         f"{bars} compases caigan en la banda "
                                         f"'{target}' (§7.1 control 3)"})
            bpm = bpm2
    resueltas.append({"campo": "duration.bars_total", "regla": "R14",
                      "entrada": f"target='{target}', bpm={bpm}",
                      "detalle": f"{bars} compases ≈ {bars * 4.0 / bpm:.1f} min "
                                 f"(banda '{target}')"})
    return target, bars


def _repartir_bars(total, tipos, resueltas=None, detalle=""):
    """Reparte ``total`` compases entre los types (PESO_BARS), 4..16 por
    sección (V105), Σ = total (V109). Determinista. Devuelve lista o None."""
    n = len(tipos)
    pesos = [PESO_BARS.get(t, 1.0) for t in tipos]
    s = sum(pesos)
    bars = [max(4, min(16, round(p * total / s))) for p in pesos]
    diff = total - sum(bars)
    guard = 0
    while diff != 0 and guard < 4 * n + 16:
        guard += 1
        progreso = False
        for i in range(n) if diff > 0 else range(n - 1, -1, -1):
            if diff > 0 and bars[i] < 16:
                bars[i] += 1
                diff -= 1
                progreso = True
            elif diff < 0 and bars[i] > 4:
                bars[i] -= 1
                diff += 1
                progreso = True
            if diff == 0:
                break
        if not progreso:
            return None
    if diff != 0 or sum(bars) != total or any(not 4 <= b <= 16 for b in bars):
        return None
    return bars


def _esqueleto(template, n, energia):
    """Esqueleto de la plantilla para n secciones. Con Energía ≥ alta, la
    variante de ``cancion`` n=5 intercambia el pre_chorus por un ``break``
    (slot de solo, R22/R5b — §7.1: el solo necesita type ∈ {break, bridge})."""
    if template == "cancion" and n == 5 and energia in ("alta", "muy_alta"):
        return ("intro", "verse", "break", "chorus", "outro")
    return list(PLANTILLAS[template][n])


def _resolver_forma(norm, resueltas):
    """Paso 4 (§7): plantilla por control; esqueleto por nº de secciones;
    curvas desde ENERGY_BASE/TENSION_BASE/D_RECETA de la receta + deltas del
    control (§7.1); drums por receta ajustados al control; V109/V112/V115 por
    construcción. Respeta secciones aportadas (R3)."""
    receta = norm["receta"]
    controles = norm["controls"]
    form_in = norm["form_in"] or {}
    template_in = form_in.get("template")
    if template_in is None:
        if norm["sections_in"] is not None:
            # secciones aportadas: la forma declarada por el control manda
            template_in = controles["forma"]
            resueltas.append({"campo": "form.template", "regla": "R15",
                              "entrada": f"controls.forma={template_in}, "
                                         "secciones aportadas",
                              "detalle": "etiqueta declarativa del control "
                                         "sobre secciones del usuario"})
        else:
            template_in = controles["forma"]
    if template_in not in EP.PLANTILLAS_FORMA:
        raise ErrorIntencion(f"form.template fuera de catálogo: {template_in!r}")

    secciones_in = norm["sections_in"]
    if secciones_in is not None:
        secciones = [dict(s) for s in secciones_in]
        if controles["drums"] == "ausente":
            no_off = [s["id"] for s in secciones if s["drums"] != "off"]
            if no_off:
                resueltas.append({"campo": "form.sections[].drums", "regla": "R16",
                                  "entrada": f"controls.drums=ausente, secciones "
                                             f"{no_off}",
                                  "detalle": "ajustadas a 'off' para la coherencia "
                                             "V111 (secciones aportadas, no locked)"})
                for s in secciones:
                    if s["drums"] != "off" and not s.get("locked"):
                        s["drums"] = "off"
        return template_in, secciones

    bpm = norm["bpm"]
    _, bars_total = _negociar_bars_y_bpm(norm, bpm, resueltas)
    n_max = min(EP.LIMITES["secciones"][1], bars_total // 4)
    n_min = max(EP.LIMITES["secciones"][0], -(-bars_total // 16))
    minimo = 4 if template_in == "cancion" else 2
    if n_max < minimo:
        raise ErrorIntencion(
            f"forma '{template_in}' exige ≥{minimo} secciones y {bars_total} "
            f"compases a {bpm} BPM solo permiten {n_max} (4..16 por sección); "
            "ajusta duración/pulso (Advanced) o usa una forma más corta (§7.1 "
            "negociación forma-duración)")
    n = max(minimo, min(n_max, round(bars_total / 10)))
    n = max(n, n_min)
    tipos = _esqueleto(template_in, n, controles["energia"])
    bars = _repartir_bars(bars_total, tipos)
    if bars is None:
        raise ErrorIntencion(f"reparto de compases irresoluble: {bars_total} "
                             f"entre {n} secciones {tipos} (4..16 cada una)")
    resueltas.append({"campo": "form.sections", "regla": "R17",
                      "entrada": f"plantilla={template_in}, bars_total={bars_total}",
                      "detalle": f"esqueleto de {n} secciones {list(tipos)} con "
                                 f"reparto {bars} (PESO_BARS; §7.1)"})

    energia_ctrl = controles["energia"]
    media_receta_e = sum(receta.ENERGY_BASE.values()) / len(receta.ENERGY_BASE)
    shift_e = ENERGIA_OBJETIVO[energia_ctrl] - media_receta_e
    delta_t = DELTA_TENSION.get(controles["armonia"], 0.0)
    delta_d = (DELTA_ENERGIA_DENSITY[energia_ctrl]
               + DELTA_DENSITY.get(controles["armonia"], 0.0))

    secciones = []
    for i, (tipo, b) in enumerate(zip(tipos, bars)):
        energy = max(0.05, min(0.95, receta.ENERGY_BASE[tipo] + shift_e))
        tension = max(0.05, min(0.95, receta.TENSION_BASE[tipo] + delta_t))
        density = max(0.05, min(0.95, receta.D_RECETA[tipo] + delta_d))
        nivel = receta.DRUMS_NIVEL[tipo]
        if controles["drums"] == "ausente":
            nivel = "off"
        elif controles["drums"] == "contenida":
            nivel = CAP_CONTENIDA.get(nivel, nivel)
        secciones.append({
            "id": f"{tipo}_{i + 1}", "type": tipo, "bars": b,
            "energy": round(energy, 2), "tension": round(tension, 2),
            "density": round(density, 2),
            "focus": list(receta.FOCUS_DEFAULT.get(tipo) or ["rhodes"]),
            "drums": nivel, "locked": False,
        })

    # pico de energía si Energía ≥ alta (V112 por construcción, §7.1)
    if energia_ctrl in ("alta", "muy_alta"):
        pico = max(secciones, key=lambda s: (s["energy"], s["id"]))
        if pico["energy"] < 0.72:
            pico["energy"] = 0.75
            resueltas.append({"campo": f"sections[{pico['id']}].energy",
                              "regla": "R18",
                              "entrada": f"energia={energia_ctrl}",
                              "detalle": "pico ajustado a 0.75 para el gate V112 "
                                         "(≥1 pico con energy ≥0.7, §6.1)"})
    if controles["drums"] == "protagonista":
        con_peso = [s for s in secciones if s["drums"] in ("groove", "heavy")]
        if not con_peso:
            objetivo = max(secciones, key=lambda s: (s["energy"], s["id"]))
            objetivo["drums"] = "heavy"
            resueltas.append({"campo": f"sections[{objetivo['id']}].drums",
                              "regla": "R19",
                              "entrada": "drums=protagonista",
                              "detalle": "la receta no alcanza {groove, heavy} "
                                         "en ninguna sección; el control "
                                         "prevalece (§7.1 control 6) → heavy"})
    # transiciones (V115, solo cancion): suavizado determinista hacia adelante
    if template_in == "cancion":
        for a, b2 in zip(secciones, secciones[1:]):
            salto = abs(a["energy"] - b2["energy"])
            if salto > 0.38:
                b2["energy"] = round(a["energy"] + (0.38 if b2["energy"] > a["energy"]
                                                    else -0.38), 2)
                resueltas.append({"campo": f"sections[{b2['id']}].energy",
                                  "regla": "R20",
                                  "entrada": f"salto {salto:.2f} "
                                             f"{a['id']}→{b2['id']}",
                                  "detalle": "suavizado a ±0.38 para V115 "
                                             "(≤0.4 entre vecinas, §6.5)"})
    return template_in, secciones


# ---------------------------------------------------------------------------
# Pasos 5 y 6 — solos; orquestación + focus + palette
# ---------------------------------------------------------------------------

def _resolver_solos(norm, template, secciones, resueltas):
    """Paso 5 (§7): solos[] aportados se respetan; si el protagonista pide
    solos (Energía ≥ alta) y las secciones las generó el intérprete, añade
    UN solo del protagonista en el break/bridge de mayor energía (nunca la
    sección de menor energía, V113; materialización V113: type ∈ {break,
    bridge}, focus exacto). Con secciones aportadas NO añade solos: la
    estructura es del usuario (Advanced define solos[] explícito)."""
    solos_in = norm["solos_in"]
    if solos_in is not None:
        for s in solos_in:
            sid, inst = s.get("section_id"), s.get("instrument")
            if not isinstance(sid, str) or not sid.strip() \
                    or not isinstance(inst, str):
                raise ErrorIntencion(f"solos[] requiere section_id e instrument "
                                     f"de texto: {s!r} (§9.2)")
            sec = next((x for x in secciones if x["id"] == sid), None)
            if sec is None:
                raise ErrorIntencion(f"solos referencia una sección inexistente: "
                                     f"{sid!r} (E107)")
            if inst not in contract.INSTRUMENT_IDS:
                raise ErrorIntencion(f"solos instrument fuera de catálogo: "
                                     f"{inst!r} (E110)")
            if sec.get("locked"):
                raise ErrorIntencion(f"el solo en {sid!r} no puede materializarse: "
                                     "la sección está locked (§9.1: el intérprete "
                                     "no re-resuelve secciones locked)")
            # materialización contractual (§9.2 solos): la sección queda
            # type ∈ {break, bridge} con focus=[instrumento]
            sec["type"] = "break" if template != "ciclos" else "bridge"
            sec["focus"] = [inst]
        return [{"section_id": s["section_id"], "instrument": s["instrument"]}
                for s in solos_in]
    if norm["sections_in"] is not None:
        return []
    if norm["controls"]["energia"] not in ("alta", "muy_alta"):
        return []
    prota = norm["identity"]["protagonist"]
    if prota == LEAD_DOC:
        # R30 (hallazgo P-02, registro p02_solos/): el scheduler del motor de
        # improv (improv.py:18 'silencio = decisión') da a break/bridge una
        # probabilidad de frase de density × prob_overrides (≤0.5) con caps de
        # respiración — un solo del lead DECLARADO puede quedarse vacío y la
        # capa C (C4s, bloqueante, §6.5) lo rechazaría. El intérprete no
        # declara solos automáticos del lead: el sax ya tiene su plan de
        # sección (statement/develop) y el protagonismo queda garantizado por
        # V113 (focus en ≥2 secciones). Un solo del sax sigue siendo posible
        # como acto Advanced (solos[]), con el hallazgo documentado.
        resueltas.append({"campo": "solos", "regla": "R30",
                          "entrada": f"protagonista={prota} (lead), energia="
                                     f"{norm['controls']['energia']}",
                          "detalle": "sin solo automático del lead: el scheduler "
                                     "de improv puede silenciarlo (hallazgo P-02, "
                                     "p02_solos/registro.json); el protagonismo "
                                     "queda garantizado por V113"})
        return []
    candidatos = [s for s in secciones
                  if s["type"] in ("break", "bridge") and not s.get("locked")]
    if not candidatos:
        return []
    elegida = max(candidatos, key=lambda s: (s["energy"], s["id"]))
    minima = min(secciones, key=lambda s: (s["energy"], s["id"]))
    if elegida["id"] == minima["id"] or all(
            s["energy"] == minima["energy"] for s in secciones):
        elegida["energy"] = round(min(0.95, minima["energy"] + 0.1), 2)
        resueltas.append({"campo": f"sections[{elegida['id']}].energy",
                          "regla": "R21", "entrada": "solo automático",
                          "detalle": "energía elevada: el solo nunca es la "
                                     "sección de menor energía (V113, §6.2)"})
    elegida["focus"] = [prota]
    resueltas.append({"campo": "solos", "regla": "R22",
                      "entrada": f"energia={norm['controls']['energia']}, "
                                 f"protagonista={prota}",
                      "detalle": f"solo de {prota} en {elegida['id']} "
                                 f"(type={elegida['type']}; vía focus[] + "
                                 "comportamiento de motores, §9.2)"})
    return [{"section_id": elegida["id"], "instrument": prota}]


def _resolver_orquestacion(norm, secciones, resueltas):
    """Paso 6 (§7): perfil por drums control + energía dentro de la palette
    (V111 por construcción); ``original`` excluido (P-06); palette aportada
    se respeta y el perfil debe caber en ella. Protagonista garantizado en
    focus de ≥2 secciones (V113)."""
    controles = norm["controls"]
    palette = norm["identity"]["palette"]
    drums = controles["drums"]
    energia = controles["energia"]

    preferido = {
        "ausente": PERFIL_DEFAULT_SIN_DRUMS,
        "contenida": "atmospheric",
        "presente": "full" if energia in ("alta", "muy_alta", "media") else "atmospheric",
        "protagonista": "full",
    }[drums]
    if palette is None:
        perfil = preferido
    else:
        validos = [p for p in palette
                   if (p in PERFILES_SIN_DRUMS) == (drums == "ausente")]
        if not validos:
            raise ErrorIntencion(
                f"identity.palette={palette} no contiene ningún perfil coherente "
                f"con controls.drums='{drums}' (perfiles con drums: "
                f"{list(PERFILES_CON_DRUMS)}; sin drums: {list(PERFILES_SIN_DRUMS)}); "
                "el gate V111 lo rechazaría — corrige la intención (§7.1 control 6)")
        perfil = preferido if preferido in validos else validos[0]
    resueltas.append({"campo": "orchestration.profile", "regla": "R23",
                      "entrada": f"drums={drums}, energia={energia}, "
                                 f"palette={palette}",
                      "detalle": f"'{perfil}' (V111 coherente; original excluido "
                                 "del Automatic, P-06)"})
    if palette is None:
        resueltas.append({"campo": "identity.palette", "regla": "R24",
                          "entrada": "no aportada",
                          "detalle": f"paleta mínima [{perfil!r}]: el perfil "
                                     "elegido queda incluido (§9.2)"})
        palette = [perfil]

    # protagonista en focus de ≥2 secciones (V113): añade al protagonista a las
    # primeras secciones no-locked que no lo tengan, en orden determinista.
    prota = norm["identity"]["protagonist"]
    faltan = 2 - sum(1 for s in secciones if prota in (s.get("focus") or []))
    if faltan > 0:
        ajustadas = []
        for s in secciones:
            if faltan <= 0:
                break
            if s.get("locked") or prota in s["focus"]:
                continue
            set_base = norm["receta"].SET_BASE
            if prota not in set_base:
                continue
            s["focus"] = [prota] + list(s["focus"])
            ajustadas.append(s["id"])
            faltan -= 1
        if faltan > 0:
            raise ErrorIntencion(
                f"no hay suficientes secciones no-locked para garantizar al "
                f"protagonista {prota!r} en focus de ≥2 secciones (V113); "
                "ajusta las secciones aportadas o cambia el protagonista")
        resueltas.append({"campo": "form.sections[].focus", "regla": "R25",
                          "entrada": f"protagonista={prota}",
                          "detalle": f"añadido a focus de {ajustadas} "
                                     "(≥2 secciones, §6.2)"})
    return perfil, palette


# ---------------------------------------------------------------------------
# Paso 7 — emitir plan y validar, con re-resolución ≤2 (§12.1)
# ---------------------------------------------------------------------------

def _notas_descriptivas(plan):
    """``notes`` (§9.2: anotación descriptiva para humanos; ningún consumidor
    musical): describe la estructura realmente declarada (v1.4)."""
    secciones = plan["form"]["sections"]
    cadena = ", ".join(f"{s['id']} ({s['type']}, {s['bars']})"
                       for s in secciones)
    fo = (plan.get("ending") or {}).get("fade_out") or {}
    fade = ""
    if fo.get("enabled"):
        fade = f", fade-out de {fo['bars']} compases"
    solos = plan.get("solos") or []
    solo_txt = ""
    if solos:
        solo_txt = "; " + ", ".join(f"solo de {s['instrument']} en {s['section_id']}"
                                    for s in solos)
    return (f"Automatic — {plan['identity']['style']} en {plan['harmony']['key']} "
            f"({plan['harmony']['language']}), {plan['duration']['bars_total']} "
            f"compases a {plan['global']['bpm']} BPM: {cadena}{solo_txt}{fade}.")


def _ajusta_según_errores(plan, errores, resueltas, intento):
    """Re-resolución (§12.1): ajustes dirigidos y deterministas sobre campos
    NO locked para satisfacer la capa B/A. Devuelve True si aplicó algún
    ajuste (nuevo intento), False si nada es ajustable (error explicativo)."""
    aplico = False
    secciones = plan["form"]["sections"]

    def ajustable(s):
        return isinstance(s, dict) and not s.get("locked")

    for e in errores:
        cod, msg = e["codigo"], e["mensaje"]
        if cod == "V115" and plan["form"]["template"] == "cancion":
            m = re.search(r"'([\w_]+)' → '([\w_]+)'", msg)
            if m:
                a = next((s for s in secciones if s["id"] == m.group(1)), None)
                b = next((s for s in secciones if s["id"] == m.group(2)), None)
                if ajustable(b):
                    b["energy"] = round(a["energy"] + (0.38 if b["energy"] > a["energy"]
                                                       else -0.38), 2)
                    aplico = True
                    resueltas.append({"campo": f"sections[{b['id']}].energy",
                                      "regla": f"RR{intento}-V115",
                                      "entrada": f"salto {a['id']}→{b['id']}",
                                      "detalle": "suavizado en re-resolución"})
                elif ajustable(a):
                    a["energy"] = round(b["energy"] + (0.38 if a["energy"] > b["energy"]
                                                       else -0.38), 2)
                    aplico = True
                    resueltas.append({"campo": f"sections[{a['id']}].energy",
                                      "regla": f"RR{intento}-V115",
                                      "entrada": f"salto {a['id']}→{b['id']}",
                                      "detalle": "suavizado en re-resolución "
                                                 "(sección anterior)"})
        elif cod == "V112":
            candidatos = [s for s in secciones if ajustable(s)]
            if candidatos:
                pico = max(candidatos, key=lambda s: (s["energy"], s["id"]))
                pico["energy"] = 0.75
                aplico = True
                resueltas.append({"campo": f"sections[{pico['id']}].energy",
                                  "regla": f"RR{intento}-V112",
                                  "entrada": "falta pico ≥0.7",
                                  "detalle": "pico elevado a 0.75 en re-resolución"})
        elif cod == "V113":
            if "menor energía" in msg:
                m = re.search(r"'([\w_]+)'", msg)
                sid = m.group(1) if m else None
                sec = next((s for s in secciones if s["id"] == sid), None)
                if ajustable(sec):
                    minima = min(float(s["energy"]) for s in secciones)
                    sec["energy"] = round(min(0.95, minima + 0.1), 2)
                    aplico = True
                    resueltas.append({"campo": f"sections[{sec['id']}].energy",
                                      "regla": f"RR{intento}-V113",
                                      "entrada": "solo en mínima energía",
                                      "detalle": "energía elevada en re-resolución"})
            elif "exige ≥2" in msg:
                m = re.search(r"'([\w_]+)'", msg)
                prota = m.group(1) if m else plan["identity"]["protagonist"]
                for s in secciones:
                    if ajustable(s) and prota not in (s.get("focus") or []) \
                            and prota in norm_set_base(plan):
                        s["focus"] = [prota] + list(s["focus"])
                        aplico = True
                        resueltas.append({"campo": f"sections[{s['id']}].focus",
                                          "regla": f"RR{intento}-V113",
                                          "entrada": f"protagonista={prota}",
                                          "detalle": "focus reforzado en "
                                                     "re-resolución"})
                        break
            elif "exige type" in msg or "focus=" in msg:
                m = re.search(r"el solo de '([\w_]+)' en '([\w_]+)'", msg)
                if m:
                    inst, sid = m.group(1), m.group(2)
                    sec = next((s for s in secciones if s["id"] == sid), None)
                    if ajustable(sec):
                        sec["type"] = "break"
                        sec["focus"] = [inst]
                        aplico = True
                        resueltas.append({"campo": f"sections[{sid}]",
                                          "regla": f"RR{intento}-V113",
                                          "entrada": f"solo de {inst}",
                                          "detalle": "materialización break+focus "
                                                     "en re-resolución"})
        elif cod == "V111" and "drums=\"ausente\"" in msg.replace("'", '"'):
            for s in secciones:
                if ajustable(s) and s["drums"] != "off":
                    s["drums"] = "off"
                    aplico = True
            if aplico:
                resueltas.append({"campo": "form.sections[].drums",
                                  "regla": f"RR{intento}-V111",
                                  "entrada": "drums=ausente",
                                  "detalle": "secciones a off en re-resolución"})
        elif cod == "V114":
            # cadencia: el intérprete no reescribe progresiones concretas;
            # si las generó él, sustituye el final del verse por el dominante
            resueltas.append({"campo": "harmony.progressions", "regla": f"RR{intento}-V114",
                              "entrada": "cadencia ausente",
                              "detalle": "no ajustable en re-resolución: "
                                         "progresiones concretas se respetan"})
    return aplico


def norm_set_base(plan):
    estilo = (plan.get("identity") or {}).get("style")
    return getattr(identities, estilo).SET_BASE if estilo in identities.CON_RECETA else ()


def resolver(intencion, *, ahora=None):
    """Intención (dict) → Plan COMPLETO (dict) que pasa las capas A/B (§9.4.1).

    Lanza ``ErrorIntencion`` con mensaje explicativo si la intención es
    inválida o si, tras la re-resolución (≤2), el plan sigue sin pasar.
    ``ahora`` (ISO-8601) permite fijar ``evidence.created_at``; por defecto
    es la hora UTC actual — el único valor no determinista, aislado en
    evidence (§9.5).
    """
    norm, resueltas = _normalizar_intencion(intencion)
    seed = norm["seed_in"] if norm["seed_in"] is not None else derivar_seed(norm)
    norm["seed_efectiva"] = seed
    if norm["seed_in"] is None:
        resueltas.append({"campo": "seed", "regla": "R0",
                          "entrada": "no aportada",
                          "detalle": f"seed auto-generada {seed} por sha256 de "
                                     "identidad+controles (§9.2, §7.2.5; "
                                     "intérprete puro, reproducible)"})

    ident = dict(norm["identity"])
    ident["palette"] = ident["palette"]

    # pasos 3-6 (el orden interno atiende dependencias de datos; la
    # responsabilidad de cada paso es la de C-02)
    bpm = _resolver_bpm(norm, resueltas)
    norm["bpm"] = bpm
    template, secciones = _resolver_forma(norm, resueltas)
    harmony = _resolver_armonia(norm, resueltas)
    solos = _resolver_solos(norm, template, secciones, resueltas)
    perfil, palette = _resolver_orquestacion(norm, secciones, resueltas)
    ident["palette"] = palette

    # ending (§9.2): resuelto si no se aportó; E112 por construcción
    ending = norm["ending_in"]
    if ending is None:
        ultima = secciones[-1]
        fo_bars = min(2, ultima["bars"])
        ending = {"fade_out": {"enabled": True, "bars": max(1, fo_bars)}}
        resueltas.append({"campo": "ending", "regla": "R26",
                          "entrada": "no aportado",
                          "detalle": f"fade-out de {ending['fade_out']['bars']} "
                                     f"compases (≤ compases de {ultima['id']}, "
                                     "E112)"})

    # duration: el target ya es concreto (R12 en paso 1)
    dur_in = norm["duration_in"] or {}
    target = dur_in.get("target") or norm["controls"]["duracion"]
    bars_total = dur_in.get("bars_total") or sum(s["bars"] for s in secciones)

    title = norm["title_in"]
    if title is None:
        banco = TITULOS[norm["identity"]["style"]]
        title = banco[seed % len(banco)]
        resueltas.append({"campo": "title", "regla": "R27",
                          "entrada": f"seed={seed}",
                          "detalle": f"título auto-generado {title!r} (metadata "
                                     "sin consumidor musical, §9.2)"})

    plan = {
        "plan_version": EP.PLAN_VERSION,
        "mode": "automatic",
        "seed": seed,
        "title": title,
        "identity": ident,
        "controls": {k: v for k, v in norm["controls"].items()
                     if not k.startswith("_")},   # sin marcas internas (V106)
        "album_context": None,
        "form": {"template": template, "sections": secciones},
        "ending": ending,
        "harmony": harmony,
        "solos": solos,
        "orchestration": {"profile": perfil},
        "global": {"bpm": bpm},
        "duration": {"target": target, "bars_total": bars_total},
    }
    # nota: notes y evidence se añaden DESPUÉS de validar (el plan validado es
    # completo: ningún null — V108; evidence.created_at no participa, §9.5)

    # paso 7: validar; re-resolución ≤2 si no pasa (§12.1)
    r = validar(plan)
    intento = 0
    while not r["ok"] and intento < 2:
        intento += 1
        if not _ajusta_según_errores(plan, r["errores"], resueltas, intento):
            break
        r = validar(plan)
    if not r["ok"]:
        raise ErrorIntencion(
            "el plan no pasa las capas A/B tras la re-resolución "
            f"({intento} intento(s)); errores: "
            + "; ".join(f"{e['codigo']} {e['mensaje']}" for e in r["errores"])
            + " — corrige la intención (Advanced) o relaja los campos locked")

    plan["notes"] = _notas_descriptivas(plan)
    plan["evidence"] = {
        "resolved_by": RESOLVED_BY,
        "resolved": resueltas,
        "inputs_hash": inputs_hash(seed, plan["identity"],
                                   plan["controls"]),
        "created_at": (ahora or datetime.now(timezone.utc)
                       .strftime("%Y-%m-%dT%H:%M:%SZ")),
    }
    return plan

