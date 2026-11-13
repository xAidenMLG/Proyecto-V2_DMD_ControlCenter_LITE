"""Tests Fase 3 — capa Guided de DMD STUDIO (spec v1.4, §12.1, §16.2 F3).

Cubre el gate de F3 contra el servidor REAL montado en un hilo (puerto
libre, patrón de tests/studio/test_studio_api.py):

* catálogo en vivo == catálogos reales de F1/F2 (sin opciones inventadas)
* traducción exacta de cada control al esquema de intención de F2
* precedencia (Guiado > resolución Automatic > default) — §7.2
* rechazo accionable de valores inválidos y de parámetros técnicos (C-08)
* valores automáticos conservados (vacío = auto, §7.2.2)
* seed automática + determinismo de F2 intactos (R0)
* artefactos completos (P-05 co-localizado) + capa C
* errores del backend accionables desde la UI
* 2 canciones guiadas doradas (L2/L3) contra hashes grabados

No modifica contratos, goldens F1/F2 ni código protegido.
"""
import json
import sys
import time
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from dark_director import contract  # noqa: E402
from control_center import esquema_plan as EP  # noqa: E402
from control_center import interprete  # noqa: E402
from studio import server  # noqa: E402
from studio import settings as S  # noqa: E402
from studio import guided as GUIDED  # noqa: E402

BASE = None


def _req(method, path, body=None):
    import urllib.error
    import urllib.request
    r = urllib.request.Request(BASE + path, method=method)
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, data) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8") or "{}")
        except Exception:
            return e.code, {}


@pytest.fixture(scope="module", autouse=True)
def live_server():
    global BASE
    import threading
    import socket
    import uvicorn
    S.ensure_dirs()
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0))
        port = sk.getsockname()[1]
    config = uvicorn.Config(server.app, host="127.0.0.1", port=port, log_level="error")
    srv = uvicorn.Server(config)
    threading.Thread(target=srv.run, daemon=True).start()
    BASE = f"http://127.0.0.1:{port}"
    for _ in range(50):
        try:
            _req("GET", "/api/capabilities")
            break
        except Exception:
            time.sleep(0.1)
    yield


@pytest.fixture()
def project():
    st, p = _req("POST", "/api/projects",
                 {"name": "G_" + uuid.uuid4().hex[:8], "description": "guided"})
    assert st == 200
    yield p
    _req("DELETE", "/api/projects/" + p["id"])


def wait_job(jid, timeout=120):
    t0 = time.time()
    while time.time() - t0 < timeout:
        _, j = _req("GET", f"/api/jobs/{jid}")
        if j.get("state") in ("done", "error", "cancelled", "interrupted"):
            return j
        time.sleep(0.2)
    return {"state": "timeout"}


def guided(project, identity=None, controls=None, title=None, expect=200):
    body = {
        "identity": identity or {"style": "dark_triphop", "accessibility": "balanced",
                                 "protagonist": "sax_tenor"},
        "controls": controls or {},
        "title": title,
        "wav": False,
    }
    st, r = _req("POST", f"/api/projects/{project['id']}/guided", body)
    assert st == expect, r
    return r


def plan_de_generacion(pid, gen_id):
    """Lee plan.json de la carpeta de salida de una generación (vía API)."""
    st, g = _req("GET", f"/api/projects/{pid}/generations/{gen_id}")
    assert st == 200, g
    archivos = g["archivos"]
    plan_key = next(k for k in archivos if k.endswith("/plan.json"))
    return archivos[plan_key], g, archivos


IDENT = {"style": "dark_triphop", "accessibility": "balanced",
         "protagonist": "sax_tenor"}


# ------------------------------------------------------------------ catálogo
def test_catalogo_guided_refleja_los_catalogos_reales():
    st, cat = _req("GET", "/api/guided/catalog")
    assert st == 200
    assert [e["id"] for e in cat["estilos"]] == list(contract.IDENTITIES)
    assert [e["id"] for e in cat["accesibilidades"]] == list(contract.ACCESSIBILITIES)
    assert [e["id"] for e in cat["protagonistas"]] == list(EP.INSTRUMENTOS_MELDICOS)
    # exactamente los 6 controles de §7.1, con los valores EXACTOS del catálogo F2
    assert [c["id"] for c in cat["controles"]] == list(EP.CAMPOS_CONTROLS)
    for c in cat["controles"]:
        valores_ui = [o["id"] for o in c["opciones"]]
        valores_reales = [v for v in EP.CONTROLES[c["id"]] if v != "auto"]
        assert valores_ui == valores_reales, c["id"]
        assert c["auto"] is True  # vacío = auto (§7.2.2)
    # C-08: sin parámetros técnicos en el catálogo Guided
    texto = json.dumps(cat)
    for prohibido in ("seed", "bpm", "gain", "velocity", "tonalidad"):
        assert prohibido not in texto.lower() or prohibido in ("seed", "bpm"), \
            f"el catálogo Guided no debe exponer {prohibido}"
    assert "seed" not in texto and "bpm" not in texto


def test_vista_guided_registrada_en_el_shell():
    html = (ROOT / "studio/static/index.html").read_text(encoding="utf-8")
    assert 'data-view="guided"' in html and "#/guided" in html
    app_js = (ROOT / "studio/static/js/app.js").read_text(encoding="utf-8")
    assert "guided: guidedView" in app_js and "views/control_center.js" in app_js
    assert "'guided'" in app_js  # REQUIRES_PROJECT
    api_js = (ROOT / "studio/static/js/api.js").read_text(encoding="utf-8")
    assert "guidedCatalog" in api_js and "guidedGenerate" in api_js
    vista = (ROOT / "studio/static/js/views/control_center.js").read_text(encoding="utf-8")
    assert "API.guidedGenerate" in vista and "API.guidedCatalog" in vista


# ------------------------------------------------- traducción de controles
@pytest.mark.parametrize("control,valor", [
    ("energia", "alta"),
    ("forma", "ciclos"),
    ("duracion", "larga"),
    ("armonia", "sombrio"),
    ("pulso", "recto"),
    ("drums", "protagonista"),
])
def test_cada_control_se_traduce_al_esquema_de_intencion(project, control, valor):
    r = guided(project, controls={control: valor})
    j = wait_job(r["jid"])
    assert j["state"] == "done", j.get("result")
    plan, g, _ = plan_de_generacion(project["id"], j["gen_id"])
    assert plan["controls"][control] == valor, "el control llegó EXACTO al intérprete"
    # la intención viaja íntegra en el job_spec (trazabilidad de lo recibido)
    intencion = g["archivos"]["job_spec.json"]["intencion"]
    assert intencion["controls"] == {control: valor}
    assert intencion["identity"] == IDENT


def test_control_invalido_rechazado_de_forma_accionable(project):
    r = guided(project, controls={"energia": "fuertisima"}, expect=422)
    assert "energia" in r["error"] and "fuertisima" in r["error"]
    r = guided(project, controls={"armonia": "jazzoso"}, expect=422)
    assert "armonia" in r["error"] and "jazzoso" in r["error"]


def test_parametros_tecnicos_rechazados_guided_no_es_advanced(project):
    """C-08/§7.2.5: seed, bpm, tonalidad… no entran por Guided."""
    for cuerpo in ({"seed": 42}, {"bpm": 120}, {"harmony": {"key": "D minor"}}):
        st, r = _req("POST", f"/api/projects/{project['id']}/guided",
                     {"identity": IDENT, "controls": {}, **cuerpo})
        assert st in (400, 422), cuerpo
        assert r.get("error") or r.get("detail"), cuerpo
    st, r = _req("POST", f"/api/projects/{project['id']}/guided",
                 {"identity": IDENT, "controls": {"seed": 3}})
    assert st == 400 and "controles no admitidos" in (r.get("error") or r.get("detail"))


def test_identidad_invalida_rechazada_accionable(project):
    r = guided(project, identity={"style": "no_existe", "accessibility": "balanced",
                                  "protagonist": "sax_tenor"}, expect=422)
    assert "identity.style" in r["error"] or "IDENTITIES" in r["error"]
    r = guided(project, identity={"style": "dark_triphop", "accessibility": "balanced",
                                  "protagonist": "ukelele"}, expect=422)
    assert "protagonist" in r["error"]
    st, r = _req("POST", f"/api/projects/{project['id']}/guided",
                 {"controls": {}})
    assert st in (400, 422) and (r.get("error") or r.get("detail"))


# ---------------------------------------------------- automáticos y precedencia
def test_valores_automaticos_se_conservan_y_se_resuelven(project):
    """Vacío = auto (§7.2.2): la intención solo lleva identity; el plan sale
    CONCRETO en los 6 controles, con la resolución registrada."""
    r = guided(project)
    j = wait_job(r["jid"])
    assert j["state"] == "done", j.get("result")
    plan, _, _ = plan_de_generacion(project["id"], j["gen_id"])
    # los 6 quedan concretos (V108: el plan no contiene literales 'auto')
    assert set(plan["controls"]) == set(EP.CAMPOS_CONTROLS)
    assert all(v not in (None, "auto") for v in plan["controls"].values())
    assert plan["controls"] == {"energia": "media", "forma": "cancion",
                                "duracion": "media", "armonia": "jazz",
                                "pulso": "swing", "drums": "presente"}
    # cada auto queda registrado con su regla (trazabilidad)
    campos = {(x["campo"], x["regla"]) for x in plan["evidence"]["resolved"]}
    for campo, regla in (("controls.energia", "R1"), ("controls.drums", "R2"),
                         ("controls.forma", "R15"), ("controls.duracion", "R12"),
                         ("controls.armonia", "R6"), ("controls.pulso", "R29"),
                         ("seed", "R0")):
        assert (campo, regla) in campos, (campo, regla)
    # seed automática persistida y reproducible (R0, §9.2)
    assert isinstance(plan["seed"], int) and 1 <= plan["seed"] <= 999983


def test_precedencia_guiado_gana_a_automatic_y_default(project):
    """§7.2.1 (sin álbum en F3): valor Guiado > resolución Automatic > default.
    El control concreto llega EXACTO al plan y el intérprete NO lo re-resuelve.
    Se usa lento_arrastrado porque su tabla (FRACCION_BPM → lo del rango)
    difiere del default automático (BPM_DEFAULT de la receta)."""
    r = guided(project, controls={"pulso": "lento_arrastrado", "drums": "ausente"})
    j = wait_job(r["jid"])
    assert j["state"] == "done", j.get("result")
    plan, _, _ = plan_de_generacion(project["id"], j["gen_id"])
    assert plan["controls"]["pulso"] == "lento_arrastrado" != "swing"  # no el default R29
    assert plan["controls"]["drums"] == "ausente"
    # drums ausente ⇒ perfil SIN drums (interacción real, no cosmética)
    assert plan["orchestration"]["profile"] in ("sax", "sax_rhodes", "sax_vibes")
    # el bpm responde al pulso guiado (tabla FRACCION_BPM del intérprete)
    ref = interprete.resolver({"identity": IDENT, "controls": {"pulso": "lento_arrastrado"},
                               "seed": plan["seed"]})
    assert plan["global"]["bpm"] == ref["global"]["bpm"]
    sin_guiado = interprete.resolver({"identity": IDENT, "seed": plan["seed"]})
    assert sin_guiado["global"]["bpm"] != plan["global"]["bpm"], \
        "el pulso guiado debe mover el bpm respecto del default automático"


def test_precedencia_a_seed_fija_solo_cambian_decisiones_esperadas():
    """Golden a nivel plan (§12.1 F3): misma seed, cambia UN control ⇒ el diff
    queda confinado a las decisiones que ese control gobierna."""
    base = {"identity": IDENT, "controls": {"pulso": "swing"}, "seed": 777}
    p1 = interprete.resolver(base)
    p2 = interprete.resolver({**base, "controls": {"pulso": "recto"}})
    assert p1["seed"] == p2["seed"] == 777

    def deep_diff(x, y, ruta=""):
        out = []
        if isinstance(x, dict) and isinstance(y, dict):
            for k in sorted(set(x) | set(y)):
                out += deep_diff(x.get(k), y.get(k), ruta + "." + k)
        elif isinstance(x, list) and isinstance(y, list):
            if len(x) != len(y):
                out.append(ruta + " [len]")
            else:
                for i, (xi, yi) in enumerate(zip(x, y)):
                    out += deep_diff(xi, yi, f"{ruta}[{i}]")
        elif x != y:
            out.append(ruta)
        return out

    d1 = {k: v for k, v in p1.items() if k not in ("evidence", "notes", "album_context")}
    d2 = {k: v for k, v in p2.items() if k not in ("evidence", "notes", "album_context")}
    cambios = set(deep_diff(d1, d2))
    esperado = {".controls.pulso", ".global.bpm", ".duration.bars_total"} | \
               {f".form.sections[{i}].bars" for i in range(1, 9)}
    assert cambios <= esperado, cambios - esperado
    assert ".controls.pulso" in cambios and ".global.bpm" in cambios


# ------------------------------------------------- artefactos y determinismo
def test_ruta_completa_genera_artefactos_y_capa_c(project):
    r = guided(project, controls={"duracion": "corta"}, title="Prueba Guided")
    j = wait_job(r["jid"])
    assert j["state"] == "done", j.get("result")
    plan, g, archivos = plan_de_generacion(project["id"], j["gen_id"])
    nombres = {k.split("/", 1)[1] for k in archivos if "/" in k}
    assert {"plan.json", "doc.json", "capa_c.json", "events.json",
            "evidencia.json", "config_efectiva.json"} <= nombres, nombres
    assert any(n.endswith(".mid") for n in nombres)
    # P-05: plan.json co-localizado con doc.json (misma carpeta)
    carpetas = {k.split("/", 1)[0] for k in archivos if "/" in k}
    assert len(carpetas) == 1, "plan y doc deben estar co-localizados"
    # seed única fuente: plan.seed → doc.global.seed → evidencia
    doc_key = next(k for k in archivos if k.endswith("/doc.json"))
    doc = archivos[doc_key]
    assert doc["global"]["seed"] == plan["seed"]
    ev_key = next(k for k in archivos if k.endswith("/evidencia.json"))
    assert archivos[ev_key]["seed"] == plan["seed"]
    # capa C aplicada y OK
    cc_key = next(k for k in archivos if k.endswith("/capa_c.json"))
    assert archivos[cc_key]["ok"] is True
    assert j["result"]["capa_c"]["ok"] is True
    # el resumen del plan para la UI es fiel
    assert j["result"]["plan"]["seed"] == plan["seed"]
    assert j["result"]["plan"]["title"] == plan["title"]


def test_determinismo_de_f2_intacto_misma_intencion_mismo_midi(project):
    """Misma intención ⇒ misma seed (R0) ⇒ mismo MIDI byte a byte, a través
    de la ruta Guided completa (dos trabajos independientes)."""
    controles = {"duracion": "corta", "forma": "cancion", "energia": "baja"}
    shas, seeds = [], []
    for i in range(2):
        r = guided(project, controls=controles, title="Determinismo Guided")
        j = wait_job(r["jid"])
        assert j["state"] == "done", j.get("result")
        plan, _, archivos = plan_de_generacion(project["id"], j["gen_id"])
        shas.append(j["result"]["produccion"]["sha256"])
        seeds.append(plan["seed"])
    assert seeds[0] == seeds[1], "R0 debe derivar la misma seed"
    assert shas[0] == shas[1], "misma intención debe dar el mismo MIDI"


# ------------------------------------------------------ golden guiadas F3
GOLDEN = json.loads((ROOT / "tests/studio/golden_f3/golden_guiadas.json")
                    .read_text(encoding="utf-8"))


def test_golden_guiadas_l2_l3(project):
    """2 canciones guiadas doradas (§16.2 F3): la G2 cambia UN control de la
    G1 ⇒ la seed se re-deriva (R0) y solo cambian las decisiones esperadas.
    Hashes y seeds grabados en tests/studio/golden_f3/."""
    resultados = {}
    for nombre in ("g1", "g2"):
        g = GOLDEN[nombre]
        r = guided(project, controls=g["intencion"]["controls"],
                   identity=g["intencion"]["identity"],
                   title=g["intencion"].get("title"))
        j = wait_job(r["jid"])
        assert j["state"] == "done", j.get("result")
        plan, _, _ = plan_de_generacion(project["id"], j["gen_id"])
        sha = j["result"]["produccion"]["sha256"]
        assert plan["seed"] == g["seed"], f"{nombre}: seed derivada cambió"
        assert sha == g["sha256_midi"], \
            f"{nombre}: MIDI distinto al golden grabado (L2)"
        assert j["result"]["capa_c"]["ok"] is True
        assert plan["title"] == g["title"]
        resultados[nombre] = plan
    # G2 solo cambia pulso ⇒ el diff de planes queda en lo esperado
    # (a seed distinta: seed, título del banco y tonalidad del pool también)
    def deep_diff(x, y, ruta=""):
        out = []
        if isinstance(x, dict) and isinstance(y, dict):
            for k in sorted(set(x) | set(y)):
                out += deep_diff(x.get(k), y.get(k), ruta + "." + k)
        elif isinstance(x, list) and isinstance(y, list):
            if len(x) != len(y):
                out.append(ruta + " [len]")
            else:
                for i, (xi, yi) in enumerate(zip(x, y)):
                    out += deep_diff(xi, yi, f"{ruta}[{i}]")
        elif x != y:
            out.append(ruta)
        return out

    def limpiar(p):
        return {k: v for k, v in p.items()
                if k not in ("evidence", "notes", "album_context", "solos")}

    cambios = set(deep_diff(limpiar(resultados["g1"]), limpiar(resultados["g2"])))
    # Consecuencias legítimas de cambiar pulso (el control) y de la re-deriva
    # de seed R0 que arrastra: título del banco (P-01), tonalidad del pool y
    # las progresiones re-instanciadas en la nueva tonalidad. global.bpm y
    # bars_total SON consecuentes posibles de pulso (R11/R14/R13); con
    # duracion=corta la negociación R13 colapsa ambos pulsos al mismo bpm.
    permitidos = {".seed", ".title", ".controls.pulso", ".global.bpm",
                  ".harmony.key", ".duration.bars_total"} | \
                 {f".form.sections[{i}].bars" for i in range(0, 10)} | \
                 {f".harmony.progressions.{t}[{i}]"
                  for t in ("intro", "verse", "pre_chorus", "chorus",
                            "bridge", "break", "outro") for i in range(0, 4)}
    assert cambios <= permitidos, cambios - permitidos
    assert ".controls.pulso" in cambios and ".seed" in cambios
    # el control llegó al intérprete: la regla de bpm cita pulso=recto (R11)
    bpm_res = [x for x in resultados["g2"]["evidence"]["resolved"]
               if x["campo"] == "global.bpm"]
    assert any("recto" in x["entrada"] for x in bpm_res), bpm_res
    # y el MIDI es distinto: el control afecta la producción real, no es cosmético
    assert GOLDEN["g1"]["sha256_midi"] != GOLDEN["g2"]["sha256_midi"]
