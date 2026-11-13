"""CLI del Control Center — Fase 2 (spec v1.4, §12.1, §13).

    python3 -m control_center automatic INTENCION.json [--out DIR] [--no-producir]
    python3 -m control_center validar  PLAN.json
    python3 -m control_center compilar PLAN.json [--out DIR]

automatic  F2: intérprete universal por CLI (§12.1). Lee una INTENCIÓN
           (identity + controles opcionales + overrides Advanced, §7/§9.4),
           resuelve el Plan completo (seed auto-generada y persistida si no
           se aporta, §9.2), lo valida (capas A/B) y compila a doc.json
           dark-director/1; por defecto produce la canción con el CLI
           existente (subprocess, sin importar produce.py, §13) y aplica la
           capa C sobre events.json → capa_c.json. La producción invoca
           produce.py SIN --seed: la seed viaja en doc.global.seed (§13).
validar    aplica las capas A y B (§6.1/§6.2) e imprime el informe; exit 0 si
           el plan pasa, 1 si no. No escribe nada.
compilar   valida primero (fallar ⇒ no se compila, §9.4 paso 2) y escribe en
           DIR (default: junto al plan) la salida co-localizada de la canción
           (P-05): doc.json + plan.json.

La producción posterior es el CLI existente, invocado a mano o por el flujo:

    python3 scripts/produce.py DIR/doc.json --production PERFIL --events

sin --seed: la seed tiene fuente única en ejecución normal
(doc.global.seed, §13); --events deja events.json para la capa C (§6.3).
Este paquete no importa produce.py (§13); produce.py nunca lee plan.json (§10.3).
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from control_center import interprete, plan_compilador, validador  # noqa: E402


def _cargar_plan(ruta):
    try:
        return json.loads(Path(ruta).read_text(encoding="utf-8")), None
    except json.JSONDecodeError as e:
        return None, f"JSON malformado en {ruta}: {e}"
    except OSError as e:
        return None, f"no se pudo leer {ruta}: {e}"


def _imprimir_informe(resultado):
    for e in resultado["errores"]:
        print(f"  [{e['capa']}] {e['codigo']}: {e['mensaje']}")
    for a in resultado["avisos"]:
        print(f"  [aviso] {a['mensaje']}")
    if resultado["ok"]:
        print(f"CAPA A/B: OK ({len(resultado['avisos'])} aviso(s))")
    else:
        print(f"CAPA A/B: RECHAZADO — {len(resultado['errores'])} error(es)")


def cmd_validar(ruta):
    plan, error = _cargar_plan(ruta)
    if error:
        print(f"ERROR: {error}")
        return 2
    resultado = validador.validar(plan)
    _imprimir_informe(resultado)
    return 0 if resultado["ok"] else 1


def cmd_compilar(ruta, out):
    plan, error = _cargar_plan(ruta)
    if error:
        print(f"ERROR: {error}")
        return 2
    resultado = validador.validar(plan)
    _imprimir_informe(resultado)
    if not resultado["ok"]:
        print("compilación abortada: el plan no pasa las capas A/B (§9.4: "
              "fallar ⇒ no se compila)")
        return 1
    doc = plan_compilador.compilar(plan)
    destino = Path(out) if out else Path(ruta).resolve().parent
    plan_compilador.escribir_salida(plan, doc, destino)
    perfil = (plan.get("orchestration") or {}).get("profile", "full")
    seed = plan.get("seed")
    print(f"compilado: {destino / 'doc.json'} (plan.json co-localizado, P-05)")
    print(f"siguiente paso (seed desde doc.global.seed, sin --seed, §13):")
    print(f"  python3 scripts/produce.py {destino / 'doc.json'} "
          f"--production {perfil} --events --out <carpeta>")
    if seed is not None:
        print(f"  seed del plan: {seed} → doc.global.seed")
    return 0


def _slug(texto):
    """Nombre de carpeta a partir del título (ASCII, minúsculas, '_')."""
    texto = (texto or "tema").encode("ascii", "ignore").decode().lower()
    texto = re.sub(r"[^a-z0-9]+", "_", texto).strip("_")
    return texto or "tema"


def cmd_automatic(ruta, out, producir=True, con_events=True):
    """F2 (§12.1): intención → plan completo (seed persistida) → doc → canción."""
    intencion, error = _cargar_plan(ruta)
    if error:
        print(f"ERROR: {error}")
        return 2
    try:
        plan = interprete.resolver(intencion)
    except interprete.ErrorIntencion as e:
        print(f"ERROR: {e}")
        return 1
    # re-verificación defensiva (el intérprete ya valida en el paso 7)
    resultado = validador.validar(plan)
    _imprimir_informe(resultado)
    if not resultado["ok"]:
        print("automatic abortado: el plan emitido no pasa las capas A/B")
        return 1
    doc = plan_compilador.compilar(plan)
    destino = Path(out) if out else Path(_slug(plan.get("title")))
    plan_compilador.escribir_salida(plan, doc, destino)
    perfil = plan["orchestration"]["profile"]
    print(f"plan resuelto: {destino / 'plan.json'} "
          f"(seed {plan['seed']} persistida, inputs {plan['evidence']['inputs_hash'][:19]}…)")
    print(f"compilado: {destino / 'doc.json'} (dark-director/1)")
    if not producir:
        print("siguiente paso (sin --seed; seed desde doc.global.seed, §13):")
        print(f"  python3 scripts/produce.py {destino / 'doc.json'} "
              f"--production {perfil} --events --out {destino}")
        return 0
    cmd = [sys.executable, "scripts/produce.py", str(destino / "doc.json"),
           "--production", perfil, "--out", str(destino)]
    if con_events:
        cmd.append("--events")
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True,
                       timeout=600)
    if r.returncode != 0:
        print(f"ERROR: produce.py terminó con código {r.returncode}")
        if r.stdout:
            print(r.stdout[-2000:])
        if r.stderr:
            print(r.stderr[-2000:])
        return 1
    print(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "producido")
    if con_events and (destino / "events.json").is_file():
        events = json.loads((destino / "events.json").read_text(encoding="utf-8"))
        capa_c = validador.verificar_capa_c(plan, events)
        informe = {
            "seed": plan["seed"], "perfil": perfil,
            "template": plan["form"]["template"],
            "bpm": plan["global"]["bpm"],
            "bars_total": plan["duration"]["bars_total"],
            "ok": capa_c["ok"], "checks": capa_c["checks"],
        }
        (destino / "capa_c.json").write_text(
            json.dumps(informe, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
        bloqueantes = [c for c in capa_c["checks"] if c["bloqueante"]]
        fallidos = [c["id"] for c in bloqueantes if not c["ok"]]
        print(f"capa C: {'OK' if capa_c['ok'] else 'FALLA ' + str(fallidos)} "
              f"({len(bloqueantes)} gates bloqueantes) → capa_c.json")
        return 0 if capa_c["ok"] else 1
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="control_center",
        description="Control Center F2: automatic (intención → plan → doc → "
                    "canción), validar (capas A/B) y compilar (plan.json → "
                    "doc.json dark-director/1) sin tocar el motor.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_auto = sub.add_parser(
        "automatic", help="F2: intérprete universal — intención → canción")
    p_auto.add_argument("intencion", help="ruta de la intención (JSON)")
    p_auto.add_argument("--out", default=None,
                        help="carpeta de salida (default: slug del título; "
                             "escribe plan.json + doc.json co-localizados, P-05)")
    p_auto.add_argument("--no-producir", action="store_true",
                        help="resuelve y compila sin producir el MIDI")
    p_auto.add_argument("--no-events", action="store_true",
                        help="producir sin events.json (sin capa C)")
    p_val = sub.add_parser("validar", help="capas A/B sobre un plan completo")
    p_val.add_argument("plan", help="ruta del plan.json")
    p_com = sub.add_parser("compilar", help="validar + compilar a doc.json")
    p_com.add_argument("plan", help="ruta del plan.json")
    p_com.add_argument("--out", default=None,
                       help="carpeta de salida (default: junto al plan; escribe "
                            "doc.json y plan.json co-localizados, P-05)")
    args = ap.parse_args(argv)

    if args.cmd == "validar":
        return cmd_validar(args.plan)
    if args.cmd == "compilar":
        return cmd_compilar(args.plan, args.out)
    if args.cmd == "automatic":
        return cmd_automatic(args.intencion, args.out,
                             producir=not args.no_producir,
                             con_events=not args.no_events)
    return 2


if __name__ == "__main__":
    sys.exit(main())
