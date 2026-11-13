"""3 canciones doradas Automatic — Fase 2 (spec v1.4, §12.1, §6.6).

Seeds 101/202/303 FIJADAS POR EL TEST (no por el usuario, §12.1); identidades
rotadas según la serie base del protocolo §6.6 (dark_triphop / doom_dark_jazz
/ doom_triphop). El plan dorado es parte del golden (§11.3.4): la intención
del fixture → ``interprete.resolver`` debe reproducir el plan congelado
(normalizando ``evidence.created_at``, el único valor no determinista,
§9.5); el doc compilado reproduce ``sha256_doc``; producir desde el doc SIN
``--seed`` (la seed viaja en ``doc.global.seed``) reproduce ``sha256_midi``
(L1, gate §16.2) y supera los gates bloqueantes de la capa C (§6.3).

Si un golden falla: diagnóstico por nivel (L1 roto = bug de determinismo;
cambio intencional = requiere L4 documentado, §11.3).
"""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from control_center import interprete, plan_compilador, validador  # noqa: E402
from scripts.produce import producir_cancion  # noqa: E402

GOLDEN = Path(__file__).resolve().parent / "golden_f2"
SEEDS = (101, 202, 303)


def _cargar(nombre):
    return json.loads((GOLDEN / nombre).read_text(encoding="utf-8"))


def _plan_sin_fecha(plan):
    p = json.loads(json.dumps(plan))
    if p.get("evidence"):
        p["evidence"]["created_at"] = ""
    return p


class DoradasAutomatic(unittest.TestCase):
    def _caso(self, seed):
        intencion = _cargar(f"intencion_{seed}.json")
        plan_ref = _cargar(f"plan_{seed}.json")
        meta = _cargar(f"meta_{seed}.json")
        return intencion, plan_ref, meta

    def test_reproducir_todas_las_doradas(self):
        for seed in SEEDS:
            with self.subTest(seed=seed):
                intencion, plan_ref, meta = self._caso(seed)
                # intención → plan (idéntico al fixture salvo la fecha)
                plan = interprete.resolver(intencion)
                self.assertEqual(_plan_sin_fecha(plan),
                                 _plan_sin_fecha(plan_ref))
                # plan → doc: L1 del compilador
                doc = plan_compilador.compilar(plan)
                canonico = json.dumps(doc, ensure_ascii=False,
                                      sort_keys=True).encode("utf-8")
                self.assertEqual(hashlib.sha256(canonico).hexdigest(),
                                 meta["sha256_doc"])
                # capas A/B sobre el plan dorado (gate §16.2)
                r = validador.validar(plan)
                self.assertTrue(r["ok"], r["errores"])
                # doc → MIDI sin --seed: seed desde doc.global.seed (§13)
                with tempfile.TemporaryDirectory(
                        prefix=f"cc_f2_golden_{seed}_") as tmp:
                    res = producir_cancion(json.loads(json.dumps(doc)),
                                           production=meta["perfil"],
                                           out_dir=tmp, indice=False,
                                           events=True)
                    self.assertEqual(res["sha256"], meta["sha256_midi"])
                    events = json.loads(
                        (Path(tmp) / "events.json").read_text(encoding="utf-8"))
                # capa C sobre events.json del propio res (§6.3)
                c = validador.verificar_capa_c(plan, events)
                fallidos = [x["id"] for x in c["checks"]
                            if x["bloqueante"] and not x["ok"]]
                self.assertTrue(c["ok"], f"capa C falla: {fallidos}")

    def test_determinismo_del_resolver_sobre_las_doradas(self):
        for seed in SEEDS:
            with self.subTest(seed=seed):
                intencion = _cargar(f"intencion_{seed}.json")
                a = interprete.resolver(intencion)
                b = interprete.resolver(intencion)
                self.assertEqual(_plan_sin_fecha(a), _plan_sin_fecha(b))


if __name__ == "__main__":
    unittest.main()
