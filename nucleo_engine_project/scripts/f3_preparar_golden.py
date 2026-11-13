#!/usr/bin/env python3
"""Fase 3 — prepara las 2 canciones guiadas doradas (gate §16.2 F3).

Ejecuta la ruta REAL de Guided (server Studio en hilo + HTTP → jobs →
runner_cc → intérprete F2 → produce → capa C) para las intenciones G1 y
G2 (= G1 con solo el control pulso cambiado), graba:

    tests/studio/golden_f3/golden_guiadas.json   (fixture de los tests)
    output/plan_f3/golden_guiadas/g1, g2/        (artefactos de evidencia)

Uso: python3 scripts/f3_preparar_golden.py
"""
import json
import shutil
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from studio import server  # noqa: E402
from studio import settings as S  # noqa: E402

IDENT = {"style": "dark_triphop", "accessibility": "balanced",
         "protagonist": "sax_tenor"}
G1_CONTROLES = {"duracion": "corta", "forma": "cancion"}
G2_CONTROLES = {"duracion": "corta", "forma": "cancion", "pulso": "recto"}
OUT = ROOT / "output/plan_f3/golden_guiadas"
FIXTURE = ROOT / "tests/studio/golden_f3/golden_guiadas.json"


def req(method, base, path, body=None):
    r = urllib.request.Request(base + path, method=method)
    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, data) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as e:
        body_txt = e.read().decode("utf-8") or "{}"
        print(f"  HTTP {e.code}: {body_txt[:400]}")
        return e.code, json.loads(body_txt)


def wait_job(base, jid, timeout=180):
    t0 = time.time()
    while time.time() - t0 < timeout:
        _, j = req("GET", base, f"/api/jobs/{jid}")
        if j.get("state") in ("done", "error", "cancelled", "interrupted"):
            return j
        time.sleep(0.3)
    raise SystemExit(f"timeout esperando {jid}")


def main():
    S.ensure_dirs()
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0))
        port = sk.getsockname()[1]
    import uvicorn
    config = uvicorn.Config(server.app, host="127.0.0.1", port=port, log_level="error")
    srv = uvicorn.Server(config)
    threading.Thread(target=srv.run, daemon=True).start()
    base = f"http://127.0.0.1:{port}"
    for _ in range(80):
        try:
            st, _c = req("GET", base, "/api/capabilities")
            if st == 200:
                break
        except (urllib.error.URLError, ConnectionError):
            pass
        time.sleep(0.1)

    st, p = req("POST", base, "/api/projects",
                {"name": "f3_golden_" + uuid.uuid4().hex[:6],
                 "description": "golden guiadas F3"})
    assert st == 200
    pid = p["id"]

    fixture = {}
    for nombre, controles in (("g1", G1_CONTROLES), ("g2", G2_CONTROLES)):
        print(f"--- {nombre}: controls={controles}")
        st, job = req("POST", base, f"/api/projects/{pid}/guided",
                      {"identity": IDENT, "controls": controles, "wav": False})
        assert st == 200, job
        j = wait_job(base, job["jid"])
        assert j["state"] == "done", j.get("result")
        prod = j["result"]["produccion"]
        plan_res = j["result"]["plan"]
        st, g = req("GET", base, f"/api/projects/{pid}/generations/{j['gen_id']}")
        archivos = g["archivos"]
        plan_key = next(k for k in archivos if k.endswith("/plan.json"))
        plan = archivos[plan_key]
        assert plan["seed"] == plan_res["seed"] == prod["seed"]
        entry = {
            "intencion": {"identity": IDENT, "controls": controles},
            "seed": plan["seed"],
            "title": plan["title"],
            "sha256_midi": prod["sha256"],
            "bpm": plan_res["bpm"],
            "key": plan_res["key"],
            "template": plan_res["template"],
            "perfil": plan_res["profile"],
            "bars_total": plan_res["bars_total"],
            "duracion_s": prod["duracion_s"],
            "capa_c_ok": j["result"]["capa_c"]["ok"],
        }
        fixture[nombre] = entry
        # copiar artefactos de evidencia a output/plan_f3
        src = None
        for k in archivos:
            if k.endswith("/plan.json"):
                src = ROOT / "studio_data" / "projects" / pid / "generations" / j["gen_id"] / k.split("/")[0]
        dst = OUT / nombre
        if dst.exists():
            shutil.rmtree(dst)
        dst.mkdir(parents=True)
        for f in ("plan.json", "doc.json", "capa_c.json", "evidencia.json",
                  "events.json", "config_efectiva.json"):
            if (src / f).exists():
                shutil.copy2(src / f, dst / f)
        for f in src.glob("*.mid"):
            shutil.copy2(f, dst / f.name)
        print(f"    seed={entry['seed']} titulo={entry['title']!r} "
              f"sha={entry['sha256_midi'][:16]} dur={entry['duracion_s']}s")

    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, ensure_ascii=False, indent=2) + "\n",
                       encoding="utf-8")
    print(f"fixture → {FIXTURE}")
    print(f"artefactos → {OUT}")
    # el proyecto queda en studio_data como evidencia navegable de Studio


if __name__ == "__main__":
    main()
