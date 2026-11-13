"""Runner Guided/Control Center — proceso hijo aislado (Fase 3, §12.1).

Ejecuta la MISMA ruta del CLI ``control_center automatic`` (F2, §12.1)
dentro del sistema de jobs de Studio, SIN duplicar ninguna lógica
musical: ``interprete.resolver`` → capas A/B (``validador.validar``) →
``plan_compilador.compilar`` → salida co-localizada P-05 →
``scripts/produce.py::producir_cancion`` (la autoridad de producción, el
mismo núcleo que usa ``studio/runner.py``) → capa C
(``validador.verificar_capa_c`` → ``capa_c.json``).

Diferencias con el CLI (declaradas, sin efecto musical):
  * produce se importa EN PROCESO (patrón de studio/runner.py) en vez de
    por subprocess — el CLI conserva su §13 intacto; este módulo es de
    Studio, no del paquete control_center.
  * progreso por líneas "## <paso>" (protocolo de jobs) y resultado
    estructurado en ``_result.json`` para la UI.

Uso:
    python -m studio.runner_cc --spec <ruta_del_spec.json>

Spec (escrito por studio/jobs.py): {intencion, out_dir, wav, soundfont}
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from control_center import interprete, plan_compilador, validador  # noqa: E402
from studio.runner import _load_produce_module  # noqa: E402


def step(msg: str) -> None:
    print(f"## {msg}", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    args = ap.parse_args()

    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    intencion = spec["intencion"]
    out_dir = Path(spec["out_dir"])
    result_path = out_dir.parent / "_result.json"

    def finish(res: dict) -> int:
        result_path.write_text(json.dumps(res, ensure_ascii=False, indent=2),
                               encoding="utf-8")
        print("## RESULT " + ("OK" if res.get("ok") else "ERROR"), flush=True)
        return 0 if res.get("ok") else 1

    try:
        # ---- ruta F2 EXACTA (los mismos pasos y autoridades del CLI) -------
        step("Resolviendo la intención con el Intérprete Universal (F2)")
        plan = interprete.resolver(intencion)
        step(f"Plan resuelto (seed {plan['seed']} persistida, "
             f"{len((plan.get('evidence') or {}).get('resolved') or [])} "
             "decisiones trazadas)")

        step("Validando el plan (capas A/B)")
        resultado = validador.validar(plan)
        for e in resultado["errores"]:
            print(f"  [{e['capa']}] {e['codigo']}: {e['mensaje']}", flush=True)
        for a in resultado["avisos"]:
            print(f"  [aviso] {a['mensaje']}", flush=True)
        if not resultado["ok"]:
            return finish({"ok": False,
                           "error": "el plan emitido no pasa las capas A/B"})
        step(f"Capas A/B: OK ({len(resultado['avisos'])} aviso(s))")

        step("Compilando a doc.json dark-director/1 (salida co-localizada P-05)")
        doc = plan_compilador.compilar(plan)
        plan_compilador.escribir_salida(plan, doc, out_dir)

        # ---- producción: la AUTORIDAD intacta (produce.py), seed via doc ---
        produce = _load_produce_module()
        perfil = plan["orchestration"]["profile"]
        step(f"Produciendo con el pipeline real (perfil={perfil}, "
             "seed desde doc.global.seed)")
        r = produce.producir_cancion(doc, production=perfil, seed=None,
                                     out_dir=str(out_dir), indice=False,
                                     events=True)
        if not r.get("ok"):
            return finish({"ok": False,
                           "error": r.get("error", "producción fallida")})

        # ---- capa C sobre events.json (§6.3, igual que el CLI) -------------
        capa_c = None
        events_path = r.get("events")
        if events_path and Path(events_path).is_file():
            step("Verificando capa C sobre events.json")
            events = json.loads(Path(events_path).read_text(encoding="utf-8"))
            cc = validador.verificar_capa_c(plan, events)
            bloqueantes = [c for c in cc["checks"] if c["bloqueante"]]
            fallidos = [c["id"] for c in bloqueantes if not c["ok"]]
            capa_c = {"ok": cc["ok"], "checks": cc["checks"]}
            (out_dir / "capa_c.json").write_text(
                json.dumps({"seed": plan["seed"], "perfil": perfil,
                            "template": plan["form"]["template"],
                            "bpm": plan["global"]["bpm"],
                            "bars_total": plan["duration"]["bars_total"],
                            "ok": cc["ok"], "checks": cc["checks"]},
                           ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8")
            step(f"Capa C: {'OK' if cc['ok'] else 'FALLA ' + str(fallidos)} "
                 f"({len(bloqueantes)} gates bloqueantes) → capa_c.json")
            if not cc["ok"]:
                return finish({"ok": False,
                               "error": f"capa C falla: {', '.join(fallidos)}",
                               "capa_c": capa_c,
                               "produccion": r})

        # ---- WAV opcional (idéntico a studio/runner.py) ---------------------
        if spec.get("wav"):
            sf = spec.get("soundfont") or None
            try:
                from forge import audio as fa
                step("Renderizando WAV con FluidSynth")
                midi_path = Path(r["midi"])
                wav_bytes = fa.render_wav(midi_path.read_bytes(), soundfont=sf)
                wav_path = out_dir / (out_dir.name + ".wav")
                wav_path.write_bytes(wav_bytes)
                r["wav"] = {"path": str(wav_path),
                            "sha256": hashlib.sha256(wav_bytes).hexdigest(),
                            "bytes": len(wav_bytes)}
            except Exception as e:  # noqa: BLE001 — el MIDI ya existe
                r["wav"] = {"error": f"{type(e).__name__}: {e}"}
                step(f"WAV no disponible: {e}")

        res = {
            "ok": True,
            "produccion": r,
            "plan": {
                "title": plan.get("title"),
                "seed": plan["seed"],
                "bpm": plan["global"]["bpm"],
                "key": plan["harmony"]["key"],
                "language": plan["harmony"]["language"],
                "template": plan["form"]["template"],
                "bars_total": plan["duration"]["bars_total"],
                "target": plan["duration"].get("target"),
                "profile": perfil,
                "controls": plan["controls"],
                "decisiones_resueltas":
                    len((plan.get("evidence") or {}).get("resolved") or []),
                "inputs_hash": plan["evidence"]["inputs_hash"],
            },
        }
        if capa_c is not None:
            res["capa_c"] = {"ok": capa_c["ok"],
                             "fallidos": [c["id"] for c in capa_c["checks"]
                                          if c["bloqueante"] and not c["ok"]],
                             "gates_ok": [c["id"] for c in capa_c["checks"]
                                          if c["bloqueante"] and c["ok"]]}
        step("Generación completada")
        return finish(res)
    except interprete.ErrorIntencion as e:
        return finish({"ok": False, "error": str(e)})
    except Exception as e:  # noqa: BLE001
        tb = traceback.format_exc(limit=12)
        print(tb, file=sys.stderr, flush=True)
        try:
            return finish({"ok": False, "error": f"{type(e).__name__}: {e}",
                           "traceback": tb})
        except Exception:  # noqa: BLE001
            print("## RESULT ERROR", flush=True)
            return 1


if __name__ == "__main__":
    sys.exit(main())
