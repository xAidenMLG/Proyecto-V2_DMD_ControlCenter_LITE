"""Compilador Plan → doc.json dark-director/1 (spec v1.4, §9.4 paso 3).

Función pura: mismo plan ⇒ mismo doc (dict) ⇒ mismos bytes (§9.1.6). El orden
de claves del doc replica el orden que ``produce.py`` escribe hoy — verificado
byte a byte contra ``output/produccion/demo_medianoche/doc.json`` y contra los
13 docs reales de ``albumes/noches_largas/docs/``:

    schema · meta{title, notes} · direction{identity, accessibility} ·
    global{bpm, seed} · harmony{key, language, harmonic_rhythm_bars,
    progressions} · structure[] · [development] · [ending]

Mapeo (§9.4): title→meta.title; notes→meta.notes; identity.style/
accessibility→direction.*; seed+bpm→global.seed/global.bpm; harmony→harmony
(campo a campo); form.sections[]→structure[] (con energy/tension/density/
focus/drums, campos reales del doc — §9.2 — y `final` solo cuando true; el
estado `locked` es del plan y NO viaja al doc); ending→ending; solos[] con
instrumento lead (sax_tenor, E301) compilan además a
development.improvisation=[{instrument, section}] — para otros instrumentos
el solo queda expresado por focus[] + comportamiento de motores (§9.2).

No va al doc (§9.2): mode, plan_version, controls (informativos), album_context,
form.template (informativo), identity.protagonist (validador/capa C),
identity.palette (validador), orchestration.profile (→ --production),
duration.target (validador), evidence (humanos/depuración).

Serialización idéntica a produce.py: ``json.dumps(doc, ensure_ascii=False,
indent=2)`` sin salto final. La producción posterior llama al CLI existente
(``python3 scripts/produce.py DOC.json --production PERFIL --events``) — este
paquete NUNCA importa produce.py (§13) y la seed viaja en ``doc.global.seed``.
"""
import json
from pathlib import Path

from dark_director import contract
from dark_director.validador import LEAD as LEAD_DOC  # sax_tenor (E301)


def compilar(plan):
    """Traduce un plan completo (dict) al doc dark-director/1 (dict).

    Pura y determinista: no valida (eso es ``validador.validar``, que el flujo
    §9.4 aplica ANTES de compilar), no toca el disco, no inventa campos: solo
    traduce los que §9.4 mapea, en el orden real del doc.
    """
    identity = plan["identity"]
    harmony = plan["harmony"]

    meta = {"title": plan["title"]}
    if plan.get("notes"):
        meta["notes"] = plan["notes"]

    structure = []
    for sec in plan["form"]["sections"]:
        s = {
            "id": sec["id"],
            "type": sec["type"],
            "bars": sec["bars"],
            "energy": sec["energy"],
            "tension": sec["tension"],
            "density": sec["density"],
            "focus": list(sec["focus"]),
            "drums": sec["drums"],
        }
        if sec.get("final"):
            s["final"] = True          # el doc omite final:false (formato real)
        structure.append(s)            # `locked` no viaja al doc (§9.2)

    doc = {
        "schema": contract.CONTRACT_ID,
        "meta": meta,
        "direction": {
            "identity": identity["style"],
            "accessibility": identity["accessibility"],
        },
        "global": {
            "bpm": plan["global"]["bpm"],
            "seed": plan["seed"],
        },
        "harmony": {
            "key": harmony["key"],
            "language": harmony["language"],
            "harmonic_rhythm_bars": harmony["harmonic_rhythm_bars"],
            "progressions": {t: list(acordes)
                             for t, acordes in harmony["progressions"].items()},
        },
        "structure": structure,
    }

    # solos[] → development.improvisation (solo lead, E301; §9.2)
    improv = [{"instrument": solo["instrument"], "section": solo["section_id"]}
              for solo in (plan.get("solos") or [])
              if solo.get("instrument") == LEAD_DOC]
    if improv:
        doc["development"] = {"improvisation": improv}

    if plan.get("ending"):
        fo = plan["ending"]["fade_out"]
        doc["ending"] = {"fade_out": {"enabled": fo["enabled"], "bars": fo["bars"]}}

    return doc


def doc_a_bytes(doc):
    """Bytes exactos que produce.py escribiría para este doc (formato real)."""
    return json.dumps(doc, ensure_ascii=False, indent=2).encode("utf-8")


def escribir_salida(plan, doc, out_dir):
    """Persiste la salida co-localizada por canción (P-05): plan.json + doc.json.

    El resto de artefactos (<tema>.mid, evidencia.json, events.json,
    config_efectiva.json) los escribe el CLI existente produce.py al producir.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "doc.json").write_bytes(doc_a_bytes(doc))
    (out / "plan.json").write_text(
        json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    return out
