"""Fase 3 — capa Guided de DMD STUDIO (spec v1.4, §7, §12.1).

Guided es una CAPA DE INTERACCIÓN, no un motor musical (§4): convierte
elecciones humanas sencillas en una intención válida del Intérprete
Universal (F2, ``control_center.interprete``) y delega en él TODA la
resolución. Este módulo:

* ``catalogo()``      — los 6 controles + identidad + protagonista con
  nombres humanos, leídos EN VIVO de los catálogos reales de F1/F2
  (``dark_director.contract``, ``control_center.esquema_plan``). La UI no
  inventa valores: si un catálogo cambia, la UI lo refleja.
* ``intencion_desde()`` — cuerpo del endpoint Guided → intención JSON del
  esquema F2 (identity + controls + title). Solo traduce NOMBRES; no
  resuelve nada musical ni rellena valores: vacío = auto (§7.2.2, la UI
  nunca rellena por el intérprete).
* ``prevalidar()``    — ejecuta el intérprete REAL (misma ruta que el CLI
  ``automatic``) para rechazar intenciones inválidas de forma accionable
  ANTES de ocupar el slot de producción. Determinista y puro: el resultado
  se descarta; el trabajo lanza la ruta completa de nuevo.

Sin parámetros técnicos (C-08): aquí no existe bpm, tonalidad, gain ni
seed — la seed la genera el intérprete (R0) y se persiste en el plan.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dark_director import contract  # noqa: E402
from control_center import esquema_plan as EP  # noqa: E402
from control_center import interprete  # noqa: E402

# --------------------------------------------------------------------------
# Nombres humanos (única tabla de etiquetas de la capa Guided; los IDs son
# EXACTAMENTE los de los catálogos reales — ninguna traducción inventada).
# --------------------------------------------------------------------------

ESTILOS = {
    "dark_triphop": "Dark Trip-Hop — nocturno, texturas urbanas",
    "doom_triphop": "Doom Trip-Hop — denso, abismal",
    "doom_dark_jazz": "Doom Dark Jazz — jazz de sombras",
}

ACCESIBILIDADES = {
    "commercial": "Accesible — melodía clara y directa",
    "balanced": "Equilibrado — entre lo clara y lo arriesgada",
    "experimental": "Experimental — frontera, sin concesiones",
}

PROTAGONISTAS = {
    "sax_tenor": "Saxo tenor — voz principal expresiva",
    "rhodes": "Piano Rhodes — eléctrico, cálido y envolvente",
    "vibraphone": "Vibráfono — cristalino, fantasmal",
}

CONTROLES_GUIA = [
    {
        "id": "energia",
        "pregunta": "¿Cuánta fuerza tiene la pieza?",
        "auto": None,  # sin literal 'auto' en el catálogo: null ⇒ auto (R1)
        "opciones": {
            "muy_baja": "Muy baja — susurro",
            "baja": "Baja — contenida",
            "media": "Media — natural",
            "alta": "Alta — empuje",
            "muy_alta": "Muy alta — clímax constante",
        },
    },
    {
        "id": "forma",
        "pregunta": "¿Cómo se organiza?",
        "auto": "auto",  # literal 'auto' del catálogo F2
        "opciones": {
            "cancion": "Canción — verso y estribillo",
            "ciclos": "Ciclos — vamp jazzístico que gira",
            "libre": "Libre — pieza continua",
        },
    },
    {
        "id": "duracion",
        "pregunta": "¿Cuánto va a durar?",
        "auto": "auto",
        "opciones": {
            "corta": "Corta — ~2-3 min",
            "media": "Media — ~4-6 min",
            "larga": "Larga — ~7+ min",
        },
    },
    {
        "id": "armonia",
        "pregunta": "¿Qué color tienen los acordes?",
        "auto": "auto",
        "opciones": {
            "nocturno": "Nocturno — suave, contenido",
            "jazz": "Jazz — extensiones, sofisticado",
            "crudo": "Crudo — riffs, brusco",
            "sombrio": "Sombrío — tenso, oscuro",
        },
    },
    {
        "id": "pulso",
        "pregunta": "¿Cómo es el vaivén rítmico?",
        "auto": "auto",
        "opciones": {
            "swing": "Swing — balanceado",
            "recto": "Recto — marcado",
            "lento_arrastrado": "Lento arrastrado",
            "latin": "Latin — cadencia latina",
        },
    },
    {
        "id": "drums",
        "pregunta": "¿Cuánto peso tiene la batería?",
        "auto": None,  # null ⇒ auto (R2: según la energía)
        "opciones": {
            "ausente": "Sin batería",
            "contenida": "Contenida — al fondo",
            "presente": "Presente — sostiene el pulso",
            "protagonista": "Protagonista — primer plano",
        },
    },
]


def catalogo() -> dict:
    """Catálogo Guided EN VIVO desde los catálogos reales de F1/F2.

    Los IDs y sus órdenes salen de ``contract`` / ``esquema_plan``; las
    etiquetas son la tabla de arriba. Cualquier valor que la UI muestre
    está aquí y es aceptado por el intérprete (cero opciones muertas).
    """
    estilos = [s for s in contract.IDENTITIES if s in ESTILOS]
    protas = [p for p in EP.INSTRUMENTOS_MELDICOS if p in PROTAGONISTAS]
    controles = []
    for c in CONTROLES_GUIA:
        cat = EP.CONTROLES[c["id"]]
        if c["auto"] is None:
            valores = [v for v in cat if v != "auto"]
        else:
            valores = [v for v in cat if v != "auto"]  # 'auto' va aparte
        controles.append({
            "id": c["id"],
            "pregunta": c["pregunta"],
            "auto": True,               # todo control admite vacío = auto
            "opciones": [{"id": v, "label": c["opciones"][v]}
                         for v in valores if v in c["opciones"]],
        })
    return {
        "estilos": [{"id": s, "label": ESTILOS[s]} for s in estilos],
        "accesibilidades": [{"id": a, "label": ACCESIBILIDADES[a]}
                            for a in contract.ACCESSIBILITIES],
        "protagonistas": [{"id": p, "label": PROTAGONISTAS[p]} for p in protas],
        "controles": controles,
        # trazabilidad de origen (para el informe y el diagnóstico)
        "fuente": {
            "identity": "dark_director.contract (IDENTITIES/ACCESSIBILITIES)",
            "protagonist": "control_center.esquema_plan (INSTRUMENTOS_MELDICOS)",
            "controls": "control_center.esquema_plan (CONTROLES, §7.1)",
        },
    }


def intencion_desde(cuerpo: dict) -> dict:
    """Cuerpo del endpoint → intención del esquema F2 (§7/§9.2).

    Solo TRADUCE nombres y deja vacíos los controles en auto: el intérprete
    es el único que resuelve. Rechaza cuerpos con claves desconocidas o
    controles que no sean de los 6 (sin llegar a ser un segundo validador:
    la autoridad sigue siendo ``interprete.resolver``).
    """
    if not isinstance(cuerpo, dict):
        raise ValueError("el cuerpo debe ser un objeto JSON")
    permitidas = {"identity", "controls", "title", "wav"}
    desconocidas = [k for k in cuerpo if k not in permitidas]
    if desconocidas:
        raise ValueError(f"claves no admitidas en Guided: {desconocidas} "
                         "(Guided expone identidad + 6 controles + título; "
                         "los overrides técnicos son Advanced, fuera de esta capa)")

    ident = cuerpo.get("identity")
    if not isinstance(ident, dict):
        raise ValueError("identity es requerido: {style, accessibility, protagonist}")
    desconocidas = [k for k in ident
                    if k not in ("style", "accessibility", "protagonist")]
    if desconocidas:
        raise ValueError(f"identity: claves no admitidas en Guided: {desconocidas}")

    controles_in = cuerpo.get("controls")
    if controles_in is None:
        controles_in = {}
    if not isinstance(controles_in, dict):
        raise ValueError("controls debe ser un objeto con (máximo) los 6 controles")
    ids_validos = {c["id"] for c in CONTROLES_GUIA}
    desconocidos = [k for k in controles_in if k not in ids_validos]
    if desconocidos:
        raise ValueError(f"controles no admitidos: {desconocidos} "
                         "(Guided expone exactamente los 6 de §7.1)")
    # vacío/auto ⇒ OMITIDO (§7.2.2: la UI nunca rellena por el intérprete)
    controles = {}
    for k, v in controles_in.items():
        if v is None or v == "" or v == "auto":
            continue
        if not isinstance(v, str):
            raise ValueError(f"controls.{k} debe ser texto de su catálogo")
        controles[k] = v

    title = cuerpo.get("title")
    if title is not None and (not isinstance(title, str) or not title.strip()):
        raise ValueError("title debe ser texto no vacío")

    intencion = {"identity": ident, "controls": controles}
    if title:
        intencion["title"] = title.strip()
    return intencion


def prevalidar(intencion: dict) -> dict:
    """Ejecuta el intérprete REAL para rechazar intenciones inválidas antes
    de iniciar el trabajo (errores accionables inmediatos, §8).

    Es la MISMA ruta que el CLI ``automatic`` y que el trabajo de producción:
    resolver aquí es solo una pre-verificación (el resultado se descarta;
    la resolución del trabajo es la que produce el plan persistido).
    """
    try:
        interprete.resolver(intencion)
    except interprete.ErrorIntencion as e:
        return {"ok": False, "error": str(e)}
    except Exception as e:  # noqa: BLE001 — cualquier fallo del intérprete es actionable
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}
    return {"ok": True}
