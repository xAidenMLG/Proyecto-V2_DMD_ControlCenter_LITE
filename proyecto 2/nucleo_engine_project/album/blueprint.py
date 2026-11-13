"""Blueprint de álbum — F4 (spec DMD Control Center v1.4, §8, §12.1 Fase 4).

El Blueprint MVP monta el nivel álbum sobre los dos sistemas existentes y
cerrados: genera los documentos de cada pista por la ruta REAL de Fase 2
(``control_center.interprete`` → capas A/B → ``plan_compilador``) y entrega el
álbum al pipeline REAL de FASE 8 (``album.json`` → ``python3 -m album
producir``). No genera notas fuera del contrato, no duplica el intérprete y no
toca ``orquestador.py``/``planificador.py`` (la API existente bastó: NO hizo
falta el hook de integración autorizado — queda registrado en el informe).

Bloque de identidad global (§8.1, una vez por álbum): receta de identidad,
instrumento protagonista, paleta de perfiles permitidos (subconjunto de los 7
de ``jazz_engine.production``), vocabulario armónico base (tónica del álbum +
tonalidades vecinas ≤1 alteración — regla de álbum RA4) y los controles
globales de carácter (armonía) y pulso.

Deltas por pista (§8.1, lo único que se define pista a pista):
  - ``energia``      → posición en el arco [0..1] → control Energía (banda).
  - ``duracion``     → objetivo de duración (corta/media/larga).
  - ``drums``        → presencia de drums (ausente/contenida/presente/protagonista).
  - ``variacion_protagonista`` → ``mismo`` (protagonista global) |
    ``registro_distinto`` (protagonista melódico alterno, rotación
    determinista) | ``rol_acompanante`` (el protagonista acompaña: solo
    declarado de OTRO instrumento melódico en el break/bridge de mayor energía
    que el intérprete materializa — ruta Advanced ``solos[]``, §9.2).

Motivo firma (P-03, decisión F4 — vía (a) del §12.1): la frase se ESCRIBE UNA
VEZ en el blueprint y se propaga por la vía real del contrato
(``development.melody.phrases`` + ``development.motifs``, consumidos hoy por
``dark_director/validador.py`` y ``dark_director/compilador.py`` §2.7.1) a los
docs de las pistas que la referencian. La frase viaja TRANSPUESTA a la
tonalidad de cada pista (contorno reconocible, adaptado a la armadura, con
desplazamiento de octava si el registro del lead lo exige) y queda AUSENTE en
≥1 pista (mitigación de monotonía del §12.1: ``diversidad.py`` manda). No se
usa el mecanismo ``x_*`` (vía (b) descartada: almacenar metadata no es
ejecutar una decisión musical).

Reglas de álbum (§8.4, capa A sobre el conjunto — ``validar_reglas``):
  RA1 ≥1 pista con energía real en banda baja (< 0.35) — pista de contraste.
  RA2 ≤2 pistas consecutivas con el mismo perfil de producción.
  RA3 la distribución de solos no repite instrumento en pistas consecutivas
      cuando la paleta lo permite.
  RA4 todas las pistas comparten receta de identidad y tónicas relacionadas
      (≤1 alteración).
  P-03 el motivo firma aparece en ≥1 pista y falta en ≥1 (anti-monotonía).

Determinismo: mismo blueprint ⇒ mismos plans ⇒ mismos docs byte a byte (el
intérprete es puro y las seeds se derivan con la fórmula documentada del
planificador: ``seed = semilla_album + 101 * índice``).

Uso:
    python3 -m album.blueprint albumes/<nombre>/blueprint.json --out albumes/<nombre>
    python3 -m album producir  albumes/<nombre>/album.json --out output/plan_f4/<nombre>
"""
import hashlib
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from album.esquema import IDENTIDAD_ALBUM, _RE_ID, _RE_NOMBRE

SCHEMA_BLUEPRINT = "dmd-album-blueprint/1"

#: Rotación determinista de instrumento melódico para ``registro_distinto``.
ROTACION_REGISTRO = {"sax_tenor": "vibraphone", "vibraphone": "rhodes",
                     "rhodes": "sax_tenor"}

#: Umbrales documentados (constantes, NO juicios musicales).
ENERGIA_CONTRASTE = 0.35          # RA1: banda baja del arco/real
MAX_CONSECUTIVOS_PERFIL = 2       # RA2: §8.4 regla 2
UMBRAL_MONOTONIA = 0.85           # banda huellas: Jaccard ≥ → monotonía
                                  # (SIMILITUD_SOSPECHOSA de diversidad.py)
REGISTRO_LEAD = (62, 81)          # REGISTER_DEFAULT[sax_tenor] (receta de la casa)

_CLAVES_RAIZ = {"schema", "album", "semilla_album", "tonica", "identidad",
                "arco", "motivo_firma"}
_CLAVES_IDENTIDAD = {"style", "accessibility", "protagonista",
                     "paleta_perfiles", "armonia", "pulso"}
_CLAVES_DELTA = {"id", "titulo", "rol", "energia", "duracion", "drums",
                 "variacion_protagonista", "solo"}
_CLAVES_MOTIVO = {"nombre", "frase", "compases"}
_VARIACIONES = ("mismo", "registro_distinto", "rol_acompanante")
_NOTA_KNOWN = {"bar", "beat", "pitch", "dur", "vel"}

_SEED_MAX = 999_983   # límite del intérprete (§9.2); la mínima deriva en ≥101


class ErrorBlueprint(ValueError):
    """El blueprint no es válido o su derivación falla. ``.errores``: mensajes."""

    def __init__(self, errores):
        super().__init__(" | ".join(str(e) for e in errores))
        self.errores = list(errores)


def _err(errores, msg):
    errores.append(msg)


# --------------------------------------------------------------- armaduras --

def _armadura_de(key):
    """Posición en el círculo de quintas (reutiliza el criterio de capa A)."""
    from control_center.validador import _armadura
    return _armadura(key)


def _pc_de(key):
    """Clase de altura de la tónica vía forge (mismo parser que el validador)."""
    from control_center.validador import _tonic_y_modo
    par = _tonic_y_modo(key)
    return None if par is None else par[0] % 12


def _pool_tonalidades(tonica):
    """Vocabulario armónico base (§8.1): tónica + vecinas ≤1 alteración (menores).

    Devuelve (pool, errores). El pool empieza SIEMPRE por la tónica y sigue
    con las vecinas (≤1 alteración en el círculo de quintas) en orden
    alfabético — el conjunto que RA4 exige pairwise.
    """
    from control_center.validador import _RE_KEY, _FIFTHS_MENOR
    errores = []
    base = _armadura_de(tonica)
    if base is None or not _RE_KEY.match(tonica.strip()):
        _err(errores, "B201: 'tonica' no parseable como tonalidad: %r" % (tonica,))
        return None, errores
    if not tonica.strip().lower().endswith(("minor", "m")):
        _err(errores, "B202: la tónica del álbum debe ser MODO MENOR (el idioma "
             "de la casa): %r" % (tonica,))
        return None, errores
    # círculo de quintas REUTILIZADO de la capa A (cero duplicación, cero drift)
    vecinas = sorted("%s minor" % letra for letra, q in _FIFTHS_MENOR.items()
                     if abs(q - base) == 1)
    return [tonica.strip()] + vecinas, errores


def _transponer_frase(frase, semitonos):
    return [dict(n, pitch=n["pitch"] + semitonos) for n in frase]


def _desplazamiento_frase(frase, pc_origen, pc_destino):
    """Semitonos de transposición frase(origen)→frase(destino) que mantiene la
    frase DENTRO del registro del lead: candidato base pc_d−pc_o, con salto de
    octava ±12 si el registro lo exige. None si ninguna variante cabe."""
    d = (pc_destino - pc_origen) % 12
    for candidato in (d if d <= 6 else d - 12, d if d <= 6 else d - 12 + 12,
                      d if d <= 6 else d - 12 - 12):
        lo = min(n["pitch"] for n in frase) + candidato
        hi = max(n["pitch"] for n in frase) + candidato
        if REGISTRO_LEAD[0] <= lo and hi <= REGISTRO_LEAD[1]:
            return candidato
    return None


# ---------------------------------------------------------------- validación --

def validar_blueprint(spec):
    """Valida un spec ``dmd-album-blueprint/1`` (dict cargado). Fail-fast
    acumulado: devuelve avisos o lanza ErrorBlueprint con todos los errores."""
    if not isinstance(spec, dict):
        raise ErrorBlueprint(["B101: la raíz del blueprint debe ser un objeto JSON"])
    errores, avisos = [], []

    if spec.get("schema") != SCHEMA_BLUEPRINT:
        _err(errores, "B102: schema ausente o != '%s': %r"
             % (SCHEMA_BLUEPRINT, spec.get("schema")))
    desc = set(spec) - _CLAVES_RAIZ
    if desc:
        _err(errores, "B109: campos desconocidos en la raíz: %s (válidos: %s)"
             % (", ".join(sorted(desc)), ", ".join(sorted(_CLAVES_RAIZ))))

    nombre = spec.get("album")
    if not isinstance(nombre, str) or not _RE_NOMBRE.match(nombre or ""):
        _err(errores, "B103: 'album' debe ser un nombre corto (letras/dígitos/"
             "espacio/_/-): %r" % (nombre,))

    sa = spec.get("semilla_album")
    if not isinstance(sa, int) or isinstance(sa, bool) or sa < 0:
        _err(errores, "B105: 'semilla_album' debe ser entero ≥ 0: %r" % (sa,))
        sa = 0

    arco = spec.get("arco")
    if not isinstance(arco, list) or not arco:
        _err(errores, "B106: 'arco' debe ser una lista con ≥1 delta de pista")
        arco = []

    # identidad global (§8.1)
    gid = spec.get("identidad")
    if not isinstance(gid, dict):
        _err(errores, "B110: falta 'identidad' (bloque de identidad global §8.1)")
        gid = {}
    else:
        desc = set(gid) - _CLAVES_IDENTIDAD
        if desc:
            _err(errores, "B109: campos desconocidos en 'identidad': %s (válidos: %s)"
                 % (", ".join(sorted(desc)), ", ".join(sorted(_CLAVES_IDENTIDAD))))
        if gid.get("style") != IDENTIDAD_ALBUM:
            _err(errores, "B104: identidad.style debe ser la identidad ACTIVA '%s': %r"
                 % (IDENTIDAD_ALBUM, gid.get("style")))
        if gid.get("accessibility") not in ("commercial", "balanced", "experimental"):
            _err(errores, "B111: identidad.accessibility fuera de catálogo: %r"
                 % (gid.get("accessibility"),))
        if gid.get("protagonista") not in ROTACION_REGISTRO:
            _err(errores, "B111: identidad.protagonista debe ser un instrumento "
                 "melódico (sax_tenor/rhodes/vibraphone): %r"
                 % (gid.get("protagonista"),))
        paleta = gid.get("paleta_perfiles")
        from jazz_engine import production
        validos = list(production.nombres())
        if (not isinstance(paleta, list) or not paleta
                or not all(isinstance(p, str) for p in paleta)
                or any(p not in validos for p in paleta)):
            _err(errores, "B112: identidad.paleta_perfiles debe ser una lista no "
                 "vacía de perfiles de producción (subconjunto de los 7, §8.1): %r "
                 "(válidos: %s)" % (paleta, ", ".join(validos)))
        else:
            if "original" in paleta:
                _err(errores, "B113: 'original' excluido del blueprint (P-06: el "
                     "camino sin jazz_engine no participa del Automatic)")
            if len(set(paleta)) != len(paleta):
                _err(errores, "B112: paleta_perfiles con duplicados: %r" % (paleta,))
        if gid.get("armonia") not in ("nocturno", "jazz", "crudo", "sombrio"):
            _err(errores, "B111: identidad.armonia fuera de catálogo: %r (válidos: "
                 "nocturno/jazz/crudo/sombrio)" % (gid.get("armonia"),))
        if gid.get("pulso") not in ("swing", "recto", "lento_arrastrado", "latin"):
            _err(errores, "B111: identidad.pulso fuera de catálogo: %r (válidos: "
                 "swing/recto/lento_arrastrado/latin)" % (gid.get("pulso"),))

    # tónica + pool (vocabulario armónico base)
    tonica = spec.get("tonica")
    pool, err_pool = _pool_tonalidades(tonica if isinstance(tonica, str) else "")
    errores.extend(err_pool)

    # deltas por pista (§8.1)
    ids_vistos = set()
    for i, d in enumerate(arco):
        pref = "arco[%d]" % (i + 1)
        if not isinstance(d, dict):
            _err(errores, "B114: %s debe ser un objeto" % pref)
            continue
        desc = set(d) - _CLAVES_DELTA
        if desc:
            _err(errores, "B109: campos desconocidos en %s: %s (válidos: %s)"
                 % (pref, ", ".join(sorted(desc)), ", ".join(sorted(_CLAVES_DELTA))))
        pid = d.get("id")
        if not isinstance(pid, str) or not _RE_ID.match(pid or ""):
            _err(errores, "B115: %s.id inválido (letras/dígitos/_/-): %r" % (pref, pid))
        elif pid in ids_vistos:
            _err(errores, "B115: id de pista duplicado: %r" % (pid,))
        else:
            ids_vistos.add(pid)
        e = d.get("energia")
        if (not isinstance(e, (int, float)) or isinstance(e, bool)
                or not 0.0 <= float(e) <= 1.0):
            _err(errores, "B116: %s.energia debe ser número 0–1 (posición en el "
                 "arco §8.1): %r" % (pref, e))
        if d.get("duracion") not in ("corta", "media", "larga"):
            _err(errores, "B111: %s.duracion fuera de catálogo: %r (válidos: "
                 "corta/media/larga)" % (pref, d.get("duracion")))
        if d.get("drums") not in ("ausente", "contenida", "presente", "protagonista"):
            _err(errores, "B111: %s.drums fuera de catálogo: %r" % (pref, d.get("drums")))
        if d.get("variacion_protagonista") not in _VARIACIONES:
            _err(errores, "B117: %s.variacion_protagonista debe ser uno de %s: %r"
                 % (pref, "/".join(_VARIACIONES), d.get("variacion_protagonista")))
        solo = d.get("solo")
        if solo is not None:
            if d.get("variacion_protagonista") != "rol_acompanante":
                _err(errores, "B118: %s.solo solo tiene sentido con "
                     "variacion_protagonista='rol_acompanante'" % pref)
            if solo not in ROTACION_REGISTRO:
                _err(errores, "B111: %s.solo debe ser un instrumento melódico: %r"
                     % (pref, solo))
            elif solo == gid.get("protagonista"):
                _err(errores, "B119: %s.solo debe ser OTRO instrumento melódico "
                     "distinto del protagonista global (%r): el rol de acompañante "
                     "requiere que otro instrumento tome el momento destacado"
                     % (pref, gid.get("protagonista")))

    # seeds derivadas dentro del rango del intérprete
    n = len(arco)
    if sa + 101 * n > _SEED_MAX:
        _err(errores, "B105: semilla_album=%d excede el rango del intérprete con "
             "%d pistas (seed máxima derivada %d > %d)" % (sa, n, sa + 101 * n,
                                                           _SEED_MAX))

    # motivo firma (P-03, vía a)
    motivo = spec.get("motivo_firma")
    if motivo is not None:
        if not isinstance(motivo, dict):
            _err(errores, "B120: 'motivo_firma' debe ser objeto o null")
        else:
            desc = set(motivo) - _CLAVES_MOTIVO
            if desc:
                _err(errores, "B109: campos desconocidos en 'motivo_firma': %s "
                     "(válidos: %s)" % (", ".join(sorted(desc)),
                                        ", ".join(sorted(_CLAVES_MOTIVO))))
            frase = motivo.get("frase")
            compases = motivo.get("compases")
            if (not isinstance(compases, int) or isinstance(compases, bool)
                    or not 1 <= compases <= 16):
                _err(errores, "B121: motivo_firma.compases debe ser entero 1–16: %r"
                     % (compases,))
            if not isinstance(frase, list) or not frase:
                _err(errores, "B122: motivo_firma.frase debe ser una lista de notas "
                     "del contrato ({bar, beat, pitch, dur, vel})")
            else:
                for j, nota in enumerate(frase):
                    desc = set(nota) - _NOTA_KNOWN if isinstance(nota, dict) else None
                    if desc:
                        _err(errores, "B109: campos desconocidos en nota %d de la "
                             "frase: %s" % (j + 1, ", ".join(sorted(desc))))
                pitches = [n.get("pitch") for n in frase if isinstance(n, dict)]
                if not all(isinstance(p, int) and not isinstance(p, bool)
                           and 0 <= p <= 127 for p in pitches):
                    _err(errores, "B123: pitch de la frase debe ser MIDI 0–127")
                elif pool:
                    # aviso informativo: ¿cabe la frase en el registro del lead
                    # para TODAS las transposiciones posibles del pool?
                    pc_t = _pc_de(tonica)
                    saltos = [abs(((_pc_de(k) - pc_t) % 12) - (12 if ((_pc_de(k) - pc_t)
                                      % 12) > 6 else 0)) for k in pool]
                    lo = min(pitches) - max(saltos)
                    hi = max(pitches) + max(saltos)
                    if lo < REGISTRO_LEAD[0] or hi > REGISTRO_LEAD[1]:
                        avisos.append(
                            "W-B1: la frase del motivo firma puede quedar fuera "
                            "del registro del lead (%d–%d) al transponerse al "
                            "pool (±%d st); la derivación busca octava y, si no "
                            "cabe, la pista pierde el motivo (W-B2)"
                            % (REGISTRO_LEAD[0], REGISTRO_LEAD[1], max(saltos)))
                bars_usados = {int(n["bar"]) for n in frase if isinstance(n, dict)}
                if compases and bars_usados and max(bars_usados) >= (compases or 0):
                    _err(errores, "B124: la frase usa compases %s fuera de "
                         "motivo_firma.compases=%s" % (sorted(bars_usados), compases))

    if errores:
        raise ErrorBlueprint(errores)
    return avisos


def cargar_blueprint(ruta):
    """Carga y valida un blueprint.json. Devuelve (spec, avisos)."""
    ruta = Path(ruta)
    if not ruta.is_file():
        raise ErrorBlueprint(["B114: no existe el blueprint.json: %s" % ruta])
    try:
        spec = json.loads(ruta.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ErrorBlueprint(["B115: blueprint.json no es JSON UTF-8 válido: %s" % e])
    avisos = validar_blueprint(spec)
    return spec, avisos


# ----------------------------------------------------------------- derivación --

def nivel_energia(pos):
    """Posición del arco [0..1] → control Energía (bandas documentadas)."""
    if pos < 0.2:
        return "muy_baja"
    if pos < 0.4:
        return "baja"
    if pos < 0.6:
        return "media"
    if pos < 0.8:
        return "alta"
    return "muy_alta"


def _keys_por_pista(pool, n):
    """Asignación determinista de tonalidad por pista (regla RA4 por
    construcción): tónica en pistas impares, vecina (≤1 alteración) en pares."""
    tonica = pool[0]
    vecina = pool[1] if len(pool) > 1 else pool[0]
    return [tonica if i % 2 == 0 else vecina for i in range(n)]


def derivar_album(spec, out_dir):
    """Deriva el álbum ejecutable desde el blueprint.

    Para cada delta: construye la intención (identidad global + delta), la
    resuelve por el intérprete REAL de F2, la valida (capas A/B) y compila el
    doc; inyecta el motivo firma por la vía del contrato cuando procede.
    Escribe ``docs/NN_<id>.json`` y devuelve ``(album_spec, resolucion, avisos,
    reglas)``.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    gid = spec["identidad"]
    arco = spec["arco"]
    n = len(arco)
    pool, _ = _pool_tonalidades(spec["tonica"])
    keys = _keys_por_pista(pool, n)
    paleta = list(gid["paleta_perfiles"])
    pc_tonica = _pc_de(pool[0])

    from control_center import interprete, plan_compilador, validador

    motivo = spec.get("motivo_firma")
    pistas_spec, resolucion = [], []
    avisos = []
    for i, d in enumerate(arco):
        idx = i + 1
        seed = int(spec["semilla_album"]) + 101 * idx
        key = keys[i]
        variacion = d["variacion_protagonista"]
        prota = gid["protagonista"]
        solos_in = None
        detalle_var = {"regla": variacion, "variacion": variacion}
        if variacion == "registro_distinto":
            prota = ROTACION_REGISTRO[gid["protagonista"]]
            detalle_var["protagonista_pista"] = prota
            detalle_var["detalle"] = "protagonista melódico alterno (otro registro)"

        intencion = {
            "identity": {"style": gid["style"],
                         "accessibility": gid["accessibility"],
                         "protagonist": prota, "palette": paleta},
            "controls": {"energia": nivel_energia(float(d["energia"])),
                         "forma": "cancion", "duracion": d["duracion"],
                         "armonia": gid["armonia"], "pulso": gid["pulso"],
                         "drums": d["drums"]},
            "seed": seed,
            "title": d.get("titulo") or d["id"],
            "harmony": {"key": key},
        }
        plan = interprete.resolver(intencion)
        resultado = validador.validar(plan)
        if not resultado["ok"]:
            raise ErrorBlueprint(
                ["B130: pista %d (%s): el plan no pasa capas A/B: %s"
                 % (idx, d["id"], "; ".join("%s %s" % (e["codigo"], e["mensaje"])
                                            for e in resultado["errores"]))])
        if variacion == "rol_acompanante":
            # el solo materializa el break/bridge de MAYOR energía del esqueleto
            # resuelto (determinista); ruta Advanced solos[] (§9.2): el
            # intérprete exige sección existente, se declara tras resolver.
            slots = [s for s in plan["form"]["sections"]
                     if s["type"] in ("break", "bridge") and not s.get("locked")]
            if not slots:
                raise ErrorBlueprint(
                    ["B131: pista %d (%s): variacion '%s' exige un break/bridge "
                     "y la forma resuelta no tiene ninguno — ajusta duración"
                     % (idx, d["id"], variacion)])
            elegido = max(slots, key=lambda s: (s["energy"], s["id"]))
            intencion["solos"] = [{"section_id": elegido["id"],
                                   "instrument": d["solo"]}]
            plan = interprete.resolver(intencion)
            resultado = validador.validar(plan)
            if not resultado["ok"]:
                raise ErrorBlueprint(
                    ["B130: pista %d (%s): el plan con solo no pasa capas A/B: %s"
                     % (idx, d["id"], "; ".join("%s %s" % (e["codigo"], e["mensaje"])
                                                for e in resultado["errores"]))])
            detalle_var["solo_materializado"] = {"section_id": elegido["id"],
                                                 "instrument": d["solo"]}
            detalle_var["regla"] = "solos[] Advanced (§9.2)"
            detalle_var["detalle"] = "protagonista acompaña; solo Advanced de " \
                                     "otro melódico (§9.2 solos[])"

        doc = plan_compilador.compilar(plan)
        con_lead = [s["id"] for s in plan["form"]["sections"]
                    if gid["protagonista"] in (s.get("focus") or [])
                    and s["type"] in ("verse", "pre_chorus", "chorus")]
        colocado = None
        if motivo and i < n - 1:
            # P-03 vía (a): frase escrita una vez, propagada transpuesta; la
            # ÚLTIMA pista del álbum queda SIN motivo (anti-monotonía §12.1).
            tr = _desplazamiento_frase(motivo["frase"], pc_tonica, _pc_de(key))
            if tr is not None and con_lead:
                frase = _transponer_frase(motivo["frase"], tr)
                src = con_lead[0]
                dst = con_lead[-1] if len(con_lead) > 1 else None
                dev = {"melody": {"phrases": {src: [dict(x) for x in frase]}}}
                if dst is not None and dst != src:
                    dev["motifs"] = {motivo["nombre"]: {"from_section": src,
                                                        "sections": [dst],
                                                        "transpose_st": 0}}
                nuevo = {}
                for k, v in doc.items():
                    if k == "ending":
                        nuevo["development"] = dev
                    nuevo[k] = v
                if "development" not in nuevo:
                    nuevo["development"] = dev
                doc = nuevo
                colocado = {"seccion_fuente": src, "seccion_destino": dst,
                            "transpose_st": tr, "notas": len(frase)}
            else:
                avisos.append("W-B2: pista %d (%s): el motivo firma no se colocó "
                              "(registro del lead o secciones con lead "
                              "insuficientes)" % (idx, d["id"]))

        ruta_doc = "docs/%02d_%s.json" % (idx, d["id"])
        pistas_spec.append({
            "id": d["id"],
            "doc": ruta_doc,
            "titulo": d.get("titulo") or d["id"],
            "perfil": plan["orchestration"]["profile"],
            "seed": seed,
            "rol": d.get("rol"),
        })
        (out / "docs").mkdir(exist_ok=True)
        (out / ruta_doc).write_bytes(
            json.dumps(doc, ensure_ascii=False, indent=2).encode("utf-8"))

        resolucion.append({
            "indice": idx, "id": d["id"], "seed": seed,
            "seed_formula": "semilla_album + 101 * %d" % idx,
            "tonalidad": key, "pool_tonalidades": list(pool),
            "variacion_protagonista": detalle_var,
            "protagonista_intencion": prota,
            "perfil_resuelto": plan["orchestration"]["profile"],
            "perfil_regla": "R23 (drums + energía dentro de la paleta)",
            "bpm": plan["global"]["bpm"],
            "bars_total": plan["duration"]["bars_total"],
            "secciones": [[s["id"], s["type"], s["bars"]]
                          for s in plan["form"]["sections"]],
            "solos": list(plan.get("solos") or []),
            "energia_objetivo_arco": float(d["energia"]),
            "energia_media_plan": round(sum(float(s["energy"]) for s in
                                            plan["form"]["sections"])
                                        / len(plan["form"]["sections"]), 3),
            "motivo_firma": colocado,
            "inputs_hash": plan["evidence"]["inputs_hash"],
            "sha256_doc": hashlib.sha256(
                json.dumps(doc, ensure_ascii=False, sort_keys=True).encode()
            ).hexdigest(),
            "doc": ruta_doc,
        })

    album_spec = {
        "schema": "dmd-album/1",
        "album": spec["album"],
        "identidad": gid["style"],
        "semilla_album": int(spec["semilla_album"]),
        "objetivo": {"pistas": n},
        "curva_energia": [float(d["energia"]) for d in arco],
        "pistas": pistas_spec,
    }

    reglas = validar_reglas(spec, resolucion)
    return album_spec, resolucion, avisos, reglas


# ------------------------------------------------------------- reglas §8.4 --

def validar_reglas(spec, resolucion):
    """Reglas de álbum (§8.4) — capa A sobre el conjunto derivado.

    ``resolucion``: lista devuelta por ``derivar_album`` (per-track). Devuelve
    dict con RA1–RA4 + P-03 (motivo firma) y ``todas_ok``.
    """
    pistas = list(resolucion)

    # RA1 — contraste: ≥1 pista con energía real < 0.35 y arco declarado < 0.35
    arco_bajo = [r for r in pistas if r["energia_objetivo_arco"] < ENERGIA_CONTRASTE]
    real_bajo = [r for r in pistas if r["energia_media_plan"] < ENERGIA_CONTRASTE]
    ra1 = bool(arco_bajo) and bool(real_bajo)

    # RA2 — ≤2 pistas consecutivas con el mismo perfil
    peor_racha, racha = 1, 1
    for a, b in zip(pistas, pistas[1:]):
        racha = racha + 1 if a["perfil_resuelto"] == b["perfil_resuelto"] else 1
        peor_racha = max(peor_racha, racha)
    ra2 = peor_racha <= MAX_CONSECUTIVOS_PERFIL

    # RA3 — solos consecutivos no repiten instrumento (la casa siempre ofrece
    # 3 instrumentos melódicos: la paleta lo permite salvo catálogo de uno)
    solos = [r["solos"] for r in pistas]
    ra3, detalle_ra3 = True, []
    for i in range(len(solos) - 1):
        a, b = {s["instrument"] for s in solos[i]}, {s["instrument"] for s in solos[i + 1]}
        if a & b:
            ra3 = False
            detalle_ra3.append("pistas %d–%d repiten solo: %s"
                               % (i + 1, i + 2, sorted(a & b)))
    detalle_ra3.append("secuencia de solos: %s" % (" → ".join(
        ",".join(sorted({s["instrument"] for s in s_list})) or "—"
        for s_list in solos)))

    # RA4 — receta compartida + tónicas relacionadas (≤1 alteración)
    gid = spec["identidad"]
    ra4, det_ra4 = True, []
    arm = {r["id"]: _armadura_de(r["tonalidad"]) for r in pistas}
    for r in pistas:
        if arm[r["id"]] is None:
            ra4 = False
            det_ra4.append("%s: tonalidad no parseable %r" % (r["id"], r["tonalidad"]))
    for x, y in zip(pistas, pistas[1:]):
        if arm.get(x["id"]) is not None and arm.get(y["id"]) is not None:
            d = abs(arm[x["id"]] - arm[y["id"]])
            det_ra4.append("%s(%s)↔%s(%s): %d alteración(es)"
                           % (x["id"], x["tonalidad"], y["id"], y["tonalidad"], d))
            if d > 1:
                ra4 = False

    # P-03 — motivo firma: presente en ≥1 pista y ausente en ≥1 (anti-monotonía)
    con_motivo = [r["id"] for r in pistas if r["motivo_firma"]]
    sin_motivo = [r["id"] for r in pistas if not r["motivo_firma"]]
    p03 = bool(con_motivo) and bool(sin_motivo)

    reglas = [
        {"id": "RA1", "nombre": "pista de contraste (energía < %.2f)" % ENERGIA_CONTRASTE,
         "ok": ra1,
         "detalle": "arco<%.2f: %s | energía real<%.2f: %s"
                    % (ENERGIA_CONTRASTE, [r["id"] for r in arco_bajo] or "ninguna",
                       ENERGIA_CONTRASTE,
                       [r["id"] for r in real_bajo] or "ninguna")},
        {"id": "RA2", "nombre": "≤2 pistas consecutivas con el mismo perfil",
         "ok": ra2, "detalle": "racha máxima de perfil igual: %d — secuencia: %s"
                               % (peor_racha, " → ".join(r["perfil_resuelto"]
                                                         for r in pistas))},
        {"id": "RA3", "nombre": "solos no repiten instrumento en consecutivas",
         "ok": ra3, "detalle": "; ".join(detalle_ra3)},
        {"id": "RA4", "nombre": "identidad compartida + tónicas ≤1 alteración",
         "ok": ra4, "detalle": "receta %s en %d/%d pistas; %s"
                               % (gid["style"], len(pistas), len(pistas),
                                  "; ".join(det_ra4))},
        {"id": "P03", "nombre": "motivo firma presente ≥1 y ausente ≥1 pista",
         "ok": p03, "detalle": "con motivo: %s | sin motivo: %s"
                               % (con_motivo or "ninguna", sin_motivo or "ninguna")},
    ]
    return {"reglas": reglas,
            "todas_ok": all(r["ok"] for r in reglas),
            "referencia": "spec DMD Control Center v1.4 §8.4 + §12.1 Fase 4"}


def validar_banda_huellas(huellas, ids_ok):
    """Banda de diversidad POST (gate F4): ninguna pareja de pistas producidas
    alcanza la monotonía (Jaccard ≥ 0.85 = SIMILITUD_SOSPECHOSA de
    diversidad.py). Referencia empírica del álbum previo ``noches_largas``:
    máximo observado 0.399, media 0.202 (78 pares)."""
    from album import diversidad as DV
    matriz, peores = {}, []
    ids = [i for i in ids_ok if huellas.get(i)]
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            s = DV.similitud(huellas[a], huellas[b])
            matriz["%s|%s" % (a, b)] = s
            peores.append((s, a, b))
    peores.sort(reverse=True)
    peor = peores[0] if peores else None
    return {"umbral_monotonia": UMBRAL_MONOTONIA, "matriz": matriz,
            "peor_par": {"pistas": [peor[1], peor[2]], "similitud": peor[0]}
            if peor else None,
            "ok": bool(peor) and peor[0] < UMBRAL_MONOTONIA,
            "referencia_noches_largas": {"max": 0.399, "media": 0.202}}


# ---------------------------------------------------------------------- CLI --

def escribir_salida(spec, album_spec, resolucion, avisos, reglas, out_dir):
    """Escribe album.json + blueprint_resolucion.json (deterministas)."""
    out = Path(out_dir)
    (out / "album.json").write_text(
        json.dumps(album_spec, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    (out / "blueprint_resolucion.json").write_text(
        json.dumps({"blueprint": {"album": spec.get("album"),
                                  "semilla_album": spec.get("semilla_album"),
                                  "tonica": spec.get("tonica"),
                                  "identidad": spec.get("identidad"),
                                  "motivo_firma": bool(spec.get("motivo_firma"))},
                    "resolucion": resolucion, "reglas": reglas, "avisos": avisos},
                   ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    return out / "album.json"


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(
        prog="album.blueprint",
        description="F4 Album Blueprint MVP (§8, §12.1): blueprint.json → "
                    "album.json + docs/ por la ruta real F2 (intérprete → A/B "
                    "→ compilador), reglas §8.4 y motivo firma (P-03 vía a).")
    ap.add_argument("blueprint", help="ruta del blueprint.json")
    ap.add_argument("--out", required=True,
                    help="carpeta de salida (album.json + docs/ + resolucion)")
    args = ap.parse_args(argv)

    spec, avisos_carga = cargar_blueprint(args.blueprint)
    for a in avisos_carga:
        print("aviso: %s" % a)
    album_spec, resolucion, avisos, reglas = derivar_album(spec, args.out)
    ruta = escribir_salida(spec, album_spec, resolucion, avisos, reglas, args.out)
    pool, _ = _pool_tonalidades(spec["tonica"])
    print("BLUEPRINT OK: %s" % ruta)
    print("  pistas: %d · semilla_album: %s · tónica: %s (pool: %s)"
          % (len(album_spec["pistas"]), album_spec["semilla_album"],
             spec["tonica"], ", ".join(pool)))
    for r in resolucion:
        motivo = ("motivo→%s(+%dst)" % (r["motivo_firma"]["seccion_fuente"],
                                        r["motivo_firma"]["transpose_st"])
                  if r["motivo_firma"] else "sin motivo")
        solo = (" solo:%s" % ",".join(s["instrument"] for s in r["solos"])
                if r["solos"] else "")
        print("  %02d %-22s %-8s seed=%-5d %-11s E=%.2f %s%s"
              % (r["indice"], r["id"], r["tonalidad"], r["seed"],
                 r["perfil_resuelto"], r["energia_media_plan"], motivo, solo))
    for a in avisos:
        print("  aviso: %s" % a)
    print("REGLAS §8.4: %s" % ("4/4 + P-03 OK" if reglas["todas_ok"] else "FALLO"))
    for r in reglas["reglas"]:
        print("  %s %-48s %s" % ("PASS" if r["ok"] else "FAIL", r["nombre"],
                                 r["detalle"][:96]))
    print("siguiente paso: python3 -m album producir %s --out output/plan_f4/%s"
          % (ruta, Path(args.out).name))
    return 0 if reglas["todas_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
