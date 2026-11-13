"""DMD Control Center — capa fina de autoridad sobre el DOCUMENTO (Fases 1-2).

Flujo (spec DMD Control Center v1.4, §9.4 / §12.1):
    intención (identity + controles)  →  interprete.resolver (F2, 7 pasos)
        →  plan.json COMPLETO (seed persistida, evidence.resolved)
        →  validador.validar (capas A/B)
        →  plan_compilador.compilar  →  doc.json dark-director/1
        →  python3 scripts/produce.py DOC.json --production PERFIL --events

CLI:
    python3 -m control_center automatic INTENCION.json [--out DIR] [--no-producir]
    python3 -m control_center validar  PLAN.json
    python3 -m control_center compilar PLAN.json [--out DIR]

Límites (§12.1): F2 solo añade el intérprete + el comando automatic; studio y
web intactos; produce.py NUNCA lee plan.json (§10.3). La seed tiene fuente
única en ejecución normal: doc.global.seed (sin --seed).
"""
from . import esquema_plan, validador, plan_compilador, interprete  # noqa: F401

FASE = 2
PLAN_VERSION = esquema_plan.PLAN_VERSION
