#!/usr/bin/env python3
"""Herramienta de evidencia F2 (sesión; NO es parte de la implementación).

Prepara los fixtures golden de las 3 canciones doradas Automatic del spec
(§12.1: "seeds 101/202/303 fijadas por el test, no por el usuario"; protocolo
de serie base §6.6: identidades rotadas). Para cada una:
  intención → interprete.resolver → plan → plan_compilador.compilar → doc →
  scripts.produce.producir_cancion (sin --seed; seed desde doc.global.seed)
  → sha256_midi.

Escribe en tests/control_center/golden_f2/: intencion_<seed>.json,
plan_<seed>.json (con created_at congelado), meta_<seed>.json (perfil,
sha256_doc, sha256_midi). El test test_golden_automatic.py re-ejecuta todo el
flujo y compara L1.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path("/home/z/my-project/nucleo_engine_project")
sys.path.insert(0, str(ROOT))

from control_center import interprete, plan_compilador  # noqa: E402
from scripts.produce import producir_cancion  # noqa: E402

DEST = ROOT / "tests" / "control_center" / "golden_f2"

INTENCIONES = [
    {
        "nombre": "f2_101_dark_triphop",
        "seed": 101,
        "intencion": {
            "identity": {"style": "dark_triphop", "accessibility": "balanced",
                         "protagonist": "sax_tenor"},
            "controls": {"energia": "media", "forma": "cancion",
                         "duracion": "corta", "armonia": "nocturno",
                         "pulso": "swing", "drums": "presente"},
            "seed": 101,
        },
    },
    {
        "nombre": "f2_202_doom_dark_jazz",
        "seed": 202,
        "intencion": {
            "identity": {"style": "doom_dark_jazz", "accessibility": "experimental",
                         "protagonist": "rhodes"},
            "controls": {"energia": "baja", "forma": "libre",
                         "duracion": "corta", "armonia": "sombrio",
                         "pulso": "lento_arrastrado", "drums": "contenida"},
            "seed": 202,
        },
    },
    {
        "nombre": "f2_303_doom_triphop",
        "seed": 303,
        "intencion": {
            "identity": {"style": "doom_triphop", "accessibility": "balanced",
                         "protagonist": "vibraphone"},
            "controls": {"energia": "alta", "forma": "ciclos",
                         "duracion": "corta", "armonia": "crudo",
                         "pulso": "recto", "drums": "protagonista"},
            "seed": 303,
        },
    },
]

AHORA = "2026-11-13T00:00:00Z"


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    for caso in INTENCIONES:
        plan = interprete.resolver(caso["intencion"], ahora=AHORA)
        doc = plan_compilador.compilar(plan)
        doc_bytes = plan_compilador.doc_a_bytes(doc)
        sha_doc = hashlib.sha256(
            json.dumps(doc, ensure_ascii=False, sort_keys=True)
            .encode("utf-8")).hexdigest()
        perfil = plan["orchestration"]["profile"]
        with __import__("tempfile").TemporaryDirectory() as tmp:
            res = producir_cancion(json.loads(json.dumps(doc)),
                                   production=perfil, out_dir=tmp,
                                   indice=False)
            sha_midi = res["sha256"]
        (DEST / f"intencion_{caso['seed']}.json").write_text(
            json.dumps(caso["intencion"], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
        (DEST / f"plan_{caso['seed']}.json").write_text(
            json.dumps(plan, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
        (DEST / f"meta_{caso['seed']}.json").write_text(
            json.dumps({"nombre": caso["nombre"], "perfil": perfil,
                        "sha256_doc": sha_doc, "sha256_midi": sha_midi,
                        "seed": caso["seed"], "bpm": plan["global"]["bpm"],
                        "bars_total": plan["duration"]["bars_total"],
                        "key": plan["harmony"]["key"]},
                       ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{caso['nombre']}: key={plan['harmony']['key']} "
              f"bpm={plan['global']['bpm']} bars={plan['duration']['bars_total']} "
              f"perfil={perfil}")
        print(f"  sha256_doc  {sha_doc}")
        print(f"  sha256_midi {sha_midi}")


if __name__ == "__main__":
    main()
