"""diff_midi.py — Diff estructural L2 entre dos canciones (F5, spec v1.4 §11.1).

Formaliza el nivel de equivalencia **L2 — equivalencia estructural**:

    mismo nº de pistas/roles/secciones/compases/BPM/duración ± tolerancia;
    las NOTAS pueden diferir (eso es L3/L4, fuera del alcance de esta tool).

Entrada canónica: dos ``events.json`` (formato ``to_events()``, el mismo que
``produce.py --events`` escribe). Además reporta — SIN bloquear (§11.1: son
métricas experimentales hasta su calibración) — el diff numérico por pista:
número de notas, densidad por sección y bandas de velocidad (min/p50/max).

Uso:
    python3 tools/diff_midi.py A/events.json B/events.json [--tol 0.05] [--json]

Salida:
    exit 0  — L2 EQUIVALENTES (estructura idéntica dentro de la tolerancia)
    exit 1  — DIFERENCIA ESTRUCTURAL (se listan los bloques que difieren)
    exit 2  — error de uso / archivo ilegible

Bloques estructurales comparados (gates deterministas, §11.1):
  bpm · total_beats/duración (±tol) · secciones (id, kind, bars, t0, t1)
  pistas (id, role, program, channel) · compases por sección
"""
import argparse
import json
import sys
from pathlib import Path


def cargar(ruta):
    p = Path(ruta)
    if not p.is_file():
        print("ERROR: no existe %s" % p)
        sys.exit(2)
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print("ERROR: %s no es events.json válido: %s" % (p, e))
        sys.exit(2)


def estructura(ev, tol):
    """Bloques estructurales L2 de un events.json (dict comparable)."""
    secs = ev.get("sections") or []
    tracks = ev.get("tracks") or []
    bpm = float(ev.get("bpm") or 0)
    total = float(ev.get("total_beats") or 0)
    return {
        "bpm": bpm,
        "total_beats": total,
        "duracion_s": round(total * 60.0 / bpm, 2) if bpm else 0.0,
        "secciones": [[s.get("id"), s.get("kind"), int(s.get("bars") or 0),
                       round(float(s.get("t0") or 0), 4), round(float(s.get("t1") or 0), 4)]
                      for s in secs],
        "pistas": [[t.get("id"), t.get("role"), t.get("program"), t.get("channel")]
                   for t in tracks],
        "_tol_duracion_s": tol,
    }


def diferencias(estructura_a, estructura_b, tol):
    """Lista de bloques L2 que difieren (determinista, legible)."""
    diffs = []
    if abs(estructura_a["bpm"] - estructura_b["bpm"]) > 1e-9:
        diffs.append("bpm: %s != %s" % (estructura_a["bpm"], estructura_b["bpm"]))
    dur_a, dur_b = estructura_a["duracion_s"], estructura_b["duracion_s"]
    if abs(dur_a - dur_b) > tol:
        diffs.append("duración: %.2fs != %.2fs (tol ±%.2fs)" % (dur_a, dur_b, tol))
    if estructura_a["secciones"] != estructura_b["secciones"]:
        sa, sb = estructura_a["secciones"], estructura_b["secciones"]
        diffs.append("secciones: %d vs %d" % (len(sa), len(sb)))
        for i in range(max(len(sa), len(sb))):
            x = sa[i] if i < len(sa) else None
            y = sb[i] if i < len(sb) else None
            if x != y:
                diffs.append("  sección[%d]: %s != %s" % (i + 1, x, y))
    if estructura_a["pistas"] != estructura_b["pistas"]:
        pa, pb = estructura_a["pistas"], estructura_b["pistas"]
        diffs.append("pistas: %d vs %d" % (len(pa), len(pb)))
        for i in range(max(len(pa), len(pb))):
            x = pa[i] if i < len(pa) else None
            y = pb[i] if i < len(pb) else None
            if x != y:
                diffs.append("  pista[%d]: %s != %s" % (i + 1, x, y))
    return diffs


def metricas_numericas(ev):
    """Métricas por pista (REPORTADAS, no gates — §11.1 experimental)."""
    total = float(ev.get("total_beats") or 0) or 1.0
    por_pista = {}
    for t in (ev.get("tracks") or []):
        notas = t.get("notes") or []
        vels = sorted(n[3] for n in notas if len(n) >= 4)
        dens = {}
        for s in (ev.get("sections") or []):
            dentro = [n for n in notas if s.get("t0", 0) <= n[0] < s.get("t1", 0)]
            dens[s.get("id")] = round(len(dentro) / max(0.01, (s.get("t1", 0) - s.get("t0", 0))), 3)
        por_pista[t.get("id")] = {
            "notas": len(notas),
            "vel": {"min": vels[0] if vels else None,
                    "p50": vels[len(vels) // 2] if vels else None,
                    "max": vels[-1] if vels else None},
            "densidad_notas_beat_por_seccion": dens,
        }
    return por_pista


def _p50_delta(a, b):
    """Resumen legible del diff numérico (máx delta de notas por pista)."""
    peores = []
    for tid, m in a.items():
        mb = b.get(tid)
        if mb is None:
            peores.append("%s: pista ausente en B" % tid)
            continue
        d = abs(m["notas"] - mb["notas"])
        if d:
            peores.append("%s: notas %d vs %d (Δ%d)" % (tid, m["notas"], mb["notas"], d))
    return peores or ["sin diferencias numéricas"]


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="diff_midi",
        description="Diff estructural L2 (spec v1.4 §11.1) entre dos events.json. "
                    "exit 0 = L2 equivalentes; 1 = diferencia estructural; 2 = uso.")
    ap.add_argument("a", help="events.json A")
    ap.add_argument("b", help="events.json B")
    ap.add_argument("--tol", type=float, default=0.05,
                    help="tolerancia de duración en segundos (default 0.05)")
    ap.add_argument("--json", action="store_true", dest="as_json",
                    help="salida JSON además de la legible")
    args = ap.parse_args(argv)

    ev_a, ev_b = cargar(args.a), cargar(args.b)
    ea, eb = estructura(ev_a, args.tol), estructura(ev_b, args.tol)
    diffs = diferencias(ea, eb, args.tol)
    metricas = {"A": metricas_numericas(ev_a), "B": metricas_numericas(ev_b)}

    print("DIFF L2: %s  vs  %s" % (args.a, args.b))
    print("  bpm: %s vs %s | duración: %ss vs %ss (tol ±%ss)"
          % (ea["bpm"], eb["bpm"], ea["duracion_s"], eb["duracion_s"], args.tol))
    print("  secciones: %d vs %d | pistas: %d vs %d"
          % (len(ea["secciones"]), len(eb["secciones"]),
             len(ea["pistas"]), len(eb["pistas"])))
    if diffs:
        print("RESULTADO: DIFERENCIA ESTRUCTURAL (%d bloque(s))" % len(diffs))
        for d in diffs:
            print("  - %s" % d)
    else:
        print("RESULTADO: L2 EQUIVALENTES (estructura idéntica; las notas "
              "pueden diferir — eso es L3/L4)")
    notas_num = _p50_delta(metricas["A"], metricas["B"])
    print("numérico (informativo, no gate): %s" % "; ".join(notas_num[:6]))
    if args.as_json:
        print(json.dumps({"l2_ok": not diffs, "diferencias": diffs,
                          "estructura": {"A": ea, "B": eb},
                          "metricas": metricas}, ensure_ascii=False))
    return 1 if diffs else 0


if __name__ == "__main__":
    sys.exit(main())
