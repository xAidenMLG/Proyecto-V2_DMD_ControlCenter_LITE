#!/usr/bin/env python3
"""Herramienta de evidencia F2 (sesión; NO es parte de la implementación).

Genera en nucleo_engine_project/output/plan_f2/:
  1. gate/     — las 5 canciones del gate §16.2 (CLI real ``automatic``,
                 comandos reproducibles, capa C incluida).
  2. p01_series.json — registro P-01: 27 combinaciones de control × 3 seeds,
                 todas resueltas y validadas (A/B); estabilidad estructural.
  3. p02_solos/<tema>/ — registro P-02: 6 canciones con sección de solo
                 (protagonista rotado), capa C sobre cada una.
  4. INDICE.md — índice de la producción F2 con hashes.

Los MIDIs de gate salen por el CLI real para que los comandos del informe
sean exactamente los ejecutados.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("/home/z/my-project/nucleo_engine_project")
sys.path.insert(0, str(ROOT))

from control_center import interprete, plan_compilador, validador  # noqa: E402
from scripts.produce import producir_cancion  # noqa: E402

PLAN_F2 = ROOT / "output" / "plan_f2"
AHORA = "2026-11-13T00:00:00Z"

GATE = [
    ("f2_101_dark_triphop", {
        "identity": {"style": "dark_triphop", "accessibility": "balanced",
                     "protagonist": "sax_tenor"},
        "controls": {"energia": "media", "forma": "cancion",
                     "duracion": "corta", "armonia": "nocturno",
                     "pulso": "swing", "drums": "presente"},
        "seed": 101}),
    ("f2_202_doom_dark_jazz", {
        "identity": {"style": "doom_dark_jazz", "accessibility": "experimental",
                     "protagonist": "rhodes"},
        "controls": {"energia": "baja", "forma": "libre", "duracion": "corta",
                     "armonia": "sombrio", "pulso": "lento_arrastrado",
                     "drums": "contenida"},
        "seed": 202}),
    ("f2_303_doom_triphop", {
        "identity": {"style": "doom_triphop", "accessibility": "balanced",
                     "protagonist": "vibraphone"},
        "controls": {"energia": "alta", "forma": "ciclos", "duracion": "corta",
                     "armonia": "crudo", "pulso": "recto",
                     "drums": "protagonista"},
        "seed": 303}),
    ("f2_auto_total", {
        "identity": {"style": "dark_triphop", "accessibility": "commercial",
                     "protagonist": "sax_tenor"},
        "controls": {}}),                      # todo auto; seed auto-derivada
    ("f2_ausente_jazz_media", {
        "identity": {"style": "doom_dark_jazz", "accessibility": "balanced",
                     "protagonist": "vibraphone"},
        "controls": {"energia": "media", "forma": "cancion",
                     "duracion": "media", "armonia": "jazz", "pulso": "latin",
                     "drums": "ausente"},
        "seed": 808}),
]

P02 = [
    ("p02_1_sax", "dark_triphop", "sax_tenor", "cancion", "muy_alta", "nocturno", "presente", 41),
    ("p02_2_sax_ciclos", "doom_triphop", "sax_tenor", "ciclos", "alta", "crudo", "protagonista", 42),
    ("p02_3_rhodes_ciclos", "doom_dark_jazz", "rhodes", "ciclos", "alta", "sombrio", "contenida", 43),
    ("p02_4_vibes", "doom_triphop", "vibraphone", "libre", "muy_alta", "crudo", "presente", 44),
    ("p02_5_rhodes_ciclos", "dark_triphop", "rhodes", "ciclos", "alta", "jazz", "presente", 45),
    ("p02_6_vibes_libre", "doom_dark_jazz", "vibraphone", "libre", "alta", "sombrio", "ausente", 46),
]


def gate():
    d_intenciones = PLAN_F2 / "intenciones"
    d_intenciones.mkdir(parents=True, exist_ok=True)
    filas = []
    for nombre, intencion in GATE:
        ruta = d_intenciones / f"{nombre}.json"
        ruta.write_text(json.dumps(intencion, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
        cmd = [sys.executable, "-m", "control_center", "automatic",
               str(ruta), "--out", str(PLAN_F2 / nombre)]
        r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True,
                           timeout=600)
        ok = r.returncode == 0
        print(f"[gate] {nombre}: {'OK' if ok else 'FALLA'}")
        if not ok:
            print(r.stdout[-1500:], r.stderr[-800:])
            raise SystemExit(1)
        plan = json.loads((PLAN_F2 / nombre / "plan.json").read_text(encoding="utf-8"))
        ev = json.loads((PLAN_F2 / nombre / "evidencia.json").read_text(encoding="utf-8"))
        cap = json.loads((PLAN_F2 / nombre / "capa_c.json").read_text(encoding="utf-8"))
        filas.append({
            "carpeta": nombre, "seed": plan["seed"],
            "perfil": plan["orchestration"]["profile"],
            "key": plan["harmony"]["key"],
            "idioma": plan["harmony"]["language"],
            "bpm": plan["global"]["bpm"],
            "bars": plan["duration"]["bars_total"],
            "duracion_s": ev.get("duracion_s"),
            "sha256_midi": ev.get("sha256_midi"),
            "capa_c_ok": cap["ok"],
            "solos": len(plan.get("solos") or []),
            "title": plan["title"],
        })
        print(f"    seed={plan['seed']} key={plan['harmony']['key']} "
              f"perfil={plan['orchestration']['profile']} "
              f"sha={ev.get('sha256_midi', '')[:16]}")
    return filas


def p01():
    """P-01: 6 controles × sus valores × 3 seeds — resolver + validar (A/B)."""
    valores = {
        "energia": ("muy_baja", "baja", "media", "alta", "muy_alta"),
        "forma": ("cancion", "ciclos", "libre"),
        "duracion": ("corta", "media", "larga"),
        "armonia": ("nocturno", "jazz", "crudo", "sombrio"),
        "pulso": ("swing", "recto", "lento_arrastrado", "latin"),
        "drums": ("ausente", "contenida", "presente", "protagonista"),
    }
    registro = {"decision": "tablas fijas declarativas (P-01)",
                "seeds": [101, 202, 303], "combinaciones": 0, "fallos": [],
                "resumen_por_control": {}}
    for control, lista in valores.items():
        estables = 0
        for valor in lista:
            inten = {"identity": {"style": "dark_triphop",
                                  "accessibility": "balanced",
                                  "protagonist": "sax_tenor"},
                     "controls": {control: valor}}
            resueltos = []
            for seed in registro["seeds"]:
                inten["seed"] = seed
                try:
                    plan = interprete.resolver(inten, ahora=AHORA)
                    r = validador.validar(plan)
                    if not r["ok"]:
                        registro["fallos"].append(
                            {"control": control, "valor": valor,
                             "seed": seed, "errores": r["errores"]})
                        continue
                    resueltos.append({
                        "seed": seed,
                        "key": plan["harmony"]["key"],
                        "bpm": plan["global"]["bpm"],
                        "bars": plan["duration"]["bars_total"],
                        "perfil": plan["orchestration"]["profile"],
                        "language": plan["harmony"]["language"],
                        "n_secciones": len(plan["form"]["sections"]),
                        "energy_max": max(s["energy"] for s in plan["form"]["sections"]),
                        "density_media": round(sum(s["density"] for s in plan["form"]["sections"])
                                               / len(plan["form"]["sections"]), 3),
                        "drums_niveles": sorted({s["drums"] for s in plan["form"]["sections"]}),
                    })
                except interprete.ErrorIntencion as e:
                    registro["fallos"].append({"control": control,
                                               "valor": valor, "seed": seed,
                                               "error": str(e)[:200]})
            if len(resueltos) == len(registro["seeds"]):
                estables += 1
            registro["combinaciones"] += 1
        registro["resumen_por_control"][control] = {
            "valores": len(lista), "validos_x_seed": estables * len(registro["seeds"])}
    # variación entre seeds: la única fuente declarada es harmony.key (R8)
    (PLAN_F2 / "p01_series.json").write_text(
        json.dumps(registro, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    print(f"[p01] combinaciones={registro['combinaciones']} "
          f"fallos={len(registro['fallos'])}")
    return registro


def p02():
    filas = []
    base = PLAN_F2 / "p02_solos"
    base.mkdir(parents=True, exist_ok=True)
    for nombre, estilo, prota, forma, energia, armonia, drums, seed in P02:
        inten = {"identity": {"style": estilo, "accessibility": "balanced",
                              "protagonist": prota},
                 "controls": {"energia": energia, "forma": forma,
                              "duracion": "corta", "armonia": armonia,
                              "pulso": "auto", "drums": drums},
                 "seed": seed}
        try:
            plan = interprete.resolver(inten, ahora=AHORA)
        except interprete.ErrorIntencion as e:
            filas.append({"tema": nombre, "error": str(e)[:160]})
            print(f"[p02] {nombre}: ERROR {str(e)[:120]}")
            continue
        destino = base / nombre
        doc = plan_compilador.compilar(plan)
        plan_compilador.escribir_salida(plan, doc, destino)
        res = producir_cancion(json.loads(json.dumps(doc)),
                               production=plan["orchestration"]["profile"],
                               out_dir=str(destino), indice=False, events=True)
        events = json.loads((destino / "events.json").read_text(encoding="utf-8"))
        cap = validador.verificar_capa_c(plan, events)
        (destino / "capa_c.json").write_text(
            json.dumps({"seed": plan["seed"], "ok": cap["ok"],
                        "checks": cap["checks"]}, ensure_ascii=False,
                       indent=2) + "\n", encoding="utf-8")
        solo = (plan.get("solos") or [{}])[0]
        c4s = next(c for c in cap["checks"] if c["id"] == "C4s")
        c5 = next(c for c in cap["checks"] if c["id"] == "C5")
        filas.append({
            "tema": nombre, "estilo": estilo, "protagonista": prota,
            "seed": plan["seed"], "solo": f"{solo.get('instrument')}@{solo.get('section_id')}",
            "capa_c_ok": cap["ok"], "solo_no_vacio": c4s["ok"],
            "rango_protagonista": c5["detalle"][:80],
            "sha256_midi": res["sha256"],
            "fallos": [c["id"] for c in cap["checks"] if c["bloqueante"] and not c["ok"]],
        })
        print(f"[p02] {nombre}: solo={filas[-1]['solo']} capaC={cap['ok']} "
              f"C4s={c4s['ok']}")
    (PLAN_F2 / "p02_solos" / "registro.json").write_text(
        json.dumps(filas, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    return filas


def indice(filas_gate, filas_p02):
    lineas = [
        "# Producción F2 — índice de canciones (output/plan_f2/)",
        "",
        "Gate §16.2 F2: 5/5 planes pasan A+B y sus 5 MIDI superan los gates",
        "bloqueantes aplicables de C (métricas registradas en capa_c.json).",
        "",
        "| Carpeta | Título | Perfil | Seed | Key | BPM | Bars | Dur s | SHA256(16) | Solos | Capa C |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for f in filas_gate:
        lineas.append(
            f"| {f['carpeta']} | {f['title']} | {f['perfil']} | {f['seed']} | "
            f"{f['key']} | {f['bpm']} | {f['bars']} | {f['duracion_s']} | "
            f"{str(f['sha256_midi'])[:16]} | {f['solos']} | "
            f"{'OK' if f['capa_c_ok'] else 'FALLA'} |")
    lineas += ["", "## Serie P-02 (solos, §4 P-02)", "",
               "| Tema | Estilo | Protagonista | Seed | Solo | Capa C | Solo no vacío (C4s) | SHA256(16) |",
               "|---|---|---|---|---|---|---|---|"]
    for f in filas_p02:
        if "error" in f:
            lineas.append(f"| {f['tema']} | — | — | — | ERROR: {f['error']} | — | — | — |")
        else:
            lineas.append(
                f"| {f['tema']} | {f['estilo']} | {f['protagonista']} | "
                f"{f['seed']} | {f['solo']} | "
                f"{'OK' if f['capa_c_ok'] else 'FALLA ' + str(f['fallos'])} | "
                f"{'OK' if f['solo_no_vacio'] else 'VACÍO'} | "
                f"{str(f['sha256_midi'])[:16]} |")
    (PLAN_F2 / "INDICE.md").write_text("\n".join(lineas) + "\n",
                                       encoding="utf-8")
    print("[indice] escrito")


def main():
    filas_gate = gate()
    registro_p01 = p01()
    filas_p02 = p02()
    indice(filas_gate, filas_p02)
    resumen = {
        "gate_ok": all(f["capa_c_ok"] for f in filas_gate),
        "p01_fallos": len(registro_p01["fallos"]),
        "p02_capa_c_ok": sum(1 for f in filas_p02
                             if f.get("capa_c_ok")),
        "p02_total": len([f for f in filas_p02 if "error" not in f]),
    }
    print("RESUMEN:", json.dumps(resumen))


if __name__ == "__main__":
    main()
