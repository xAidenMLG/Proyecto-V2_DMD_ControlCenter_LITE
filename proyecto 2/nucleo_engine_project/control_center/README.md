# DMD Control Center — Fases 1-2 (contrato del Composition Plan + Intérprete Universal)

Flujo validar → compilar → producir:

```bash
python3 -m control_center validar  PLAN.json
python3 -m control_center compilar PLAN.json --out output/plan_f1/mi_tema
python3 scripts/produce.py output/plan_f1/mi_tema/doc.json \
    --production full --events --out output/plan_f1/mi_tema
```

Flujo Automatic (F2, §12.1) — intención → canción:

```bash
python3 -m control_center automatic INTENCION.json --out output/plan_f2/mi_tema
python3 -m control_center automatic INTENCION.json --no-producir   # solo plan+doc
```

- `automatic`: intérprete universal (7 pasos, puro, trazable). Lee `identity`
  (+ los 6 controles opcionales, vacío=auto §7.2.2) y overrides Advanced
  (`form`, `harmony`, `global.bpm`, `duration`, `solos`, secciones
  concretas/`locked`, `seed`, `title`); emite un Plan COMPLETO que pasa las
  capas A/B, lo compila a `doc.json` dark-director/1 y produce con el CLI
  existente (subprocess; nunca importa produce.py, §13). Sin `--seed`:
  la seed se genera sola, se persiste en el plan y viaja en
  `doc.global.seed`; fijarla (en la intención) es un acto Advanced (§7.2.5).
- `validar`: capas A/B (§6.1/§6.2) sobre un plan completo; no escribe nada.
  Los planes del intérprete llevan `mode="automatic"` y son legales desde F2
  (fase=1 sigue rechazándolos si se pide explícitamente).
- `compilar`: valida y traduce plan.json → doc.json campo a campo (§9.4);
  deja plan.json co-localizado (P-05).
- Capa C (checks estructurales del MIDI, §6.3): `automatic` la aplica sola
  (→ `capa_c.json`); manualmente:
  `control_center.validador.verificar_capa_c(plan, events)`.
- Los perfiles (`orchestration.profile`) van por `--production`; la capa D es
  escucha humana (protocolo §6.6, `escucha.md` por canción).

## Límites documentados del intérprete (F2)

- Solo resuelve intenciones con `mode` null/`"automatic"`; un plan `guided`
  llega COMPLETO por `validar`/`compilar`.
- `album_context` debe ser null (el blueprint de álbum es F4, §12.1).
- No declara solos automáticos del lead sax (regla R30, hallazgo P-02: el
  scheduler de improv puede silenciarlos); solos de rhodes/vibraphone vía
  focus. Un solo del sax sigue siendo posible en Advanced.
- Progresiones: patrones modales derivados del ancla (hallazgo F2: las tablas
  `PROGRESIONES` de las recetas no pasan el criterio de vecinas V110 en
  ninguna tonalidad; ver informe de Fase 2, decisión 4).
- `original` excluido del Automatic (P-06).
- La re-resolución (capa B falla ⇒ ≤2 intentos, §12.1) no toca secciones
  `locked`; si nada es ajustable, error explicativo.

Solo archivos nuevos de Control Center + evolución mínima declarada de
`validador.py` (gate de fase) y `cli.py` (`automatic`); ningún motor
modificado. Rollback F2: borrar `interprete.py` + revertir `cli.py` (§14).
