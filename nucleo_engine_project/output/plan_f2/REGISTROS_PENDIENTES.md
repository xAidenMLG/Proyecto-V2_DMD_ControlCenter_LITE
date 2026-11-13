# Registros de pendientes — Fase 2 (spec v1.4, §4, §12.1, §16.2)

Fecha: 2026-11-13. Evidencia generada por `scripts/f2_evidencia.py` + el CLI
`python3 -m control_center automatic` (comandos en el informe de fase).

## P-01 — Tablas fijas vs heurística del intérprete → CERRADO

**Decisión: tablas fijas declarativas** (R1–R29 de `control_center/interprete.py`).

Criterio de cierre (§4): "si las heurísticas producen resultados inconsistentes
entre seeds para el mismo control → tablas fijas declarativas". El intérprete
es puro: mismos controles + misma seed ⇒ mismo plan (§7.2.3). La variación
entre seeds queda acotada a campos determinados:
- `harmony.key` — elegida por seed dentro del pool que pasa V110 (R8);
- `title` — banco por identidad (R27).

**Evidencia**: `p01_series.json` — 23 combinaciones (6 controles × sus
valores) × 3 seeds (101/202/303) = 69 resoluciones, **0 fallos de capa A/B**;
los bloques resueltos (perfil, bpm, bars, n_secciones, energy_max,
density_media, drums_niveles) son estables entre seeds para el mismo control;
solo `key` varía (campos declarados).

## P-02 — Calidad de los solos (`jazz_engine/improv.py`) → CERRADO

**Hallazgo (serie 1, seeds 41/42)**: los solos del lead sax declarados en el
plan pueden quedar **vacíos** — `C4s` (solo no vacío, bloqueante, §6.5) falla:

| Tema (serie 1) | Solo declarado | C4s |
|---|---|---|
| p02_1_sax (dark_triphop, seed 41) | sax_tenor@break_3 | **False** |
| p02_2_sax_ciclos (doom_triphop, seed 42) | sax_tenor@bridge_3 | **False** |

Mecanismo verificado en código: `jazz_engine/improv.py:18` («el scheduler
puede dejar secciones SIN sax (silencio = decisión)») + `profiles.py`
`prob_overrides` (break 0.5, bridge 0.45) y `max_consecutive`/`max_active_share`:
la probabilidad de frase en un break es `density × 0.5` — un solo del lead
declarado es, en la práctica, una moneda al aire. Los solos de rhodes y
vibraphone (vía `focus[]` + comportamiento de motores, §9.2) sonan de forma
fiable (serie 1: 4/4 OK).

**Resolución F2 (regla R30)**: el intérprete no declara solos automáticos del
lead; el protagonismo del sax queda garantizado por V113 (focus en ≥2
secciones) y su `section_plan` propio (statement/develop). Un solo del sax
sigue siendo posible como acto Advanced (`solos[]`), con este hallazgo
documentado. La serie final (`p02_solos/`, 6 temas) pasa **6/6 capa C**.

**Cierre P-02** (criterio §4: "si ≥4 de 6 fallan capa C o la escucha, limitar
el solo"): con capa C: 2/6 (serie 1) < 4/6 → **no** se activa la limitación
del MVP. La escucha de la serie final (capa D, 6/6 temas) fue **APROBADA por
el usuario el 2026-11-13** (`APROBACION_CAPA_D.md`): los solos de
rhodes/vibraphone aportan (dimensión 7 Solo) y el comportamiento del lead sax
con `solos[]` Advanced queda documentado como acto experto con el hallazgo de
la serie 1 como advertencia. **P-02 cerrado en ambos criterios (capa C y capa D).**

## P-04 — ¿`events.json` basta o hace falta `decisiones.json`? → CERRADO: NO se crea

Durante la integración (hallazgos de armonía y de solos), cada decisión se
explicó desde `plan.json` + `evidence.resolved[]` + `events.json` +
`capa_c.json` sin necesitar un log adicional. Concretamente: el hallazgo P-02
se diagnosticó comparando `plan.json` (sección de solo declarada),
`events.json` (0 notas del instrumento en t0..t1) y `capa_c.json` (C4s False).
**`decisiones.json` no se crea** (criterio §4: solo si no se puede explicar
una decisión desde plan+events).

## P-07 — Transiciones entre secciones (parcial)

El MVP no promete transiciones mejoradas (§15.10). Sin evidencia de escucha
no se añade ninguna regla de Plan. Registro: los planes del intérprete
respetan la única regla validable (V115, saltos ≤0.4 en `cancion`, §6.5);
el criterio de recuperación ("escucha marca ≥2 canciones con transición=0")
queda abierto para el protocolo D del usuario sobre la serie base.

**Resultado de la capa D (2026-11-13, `APROBACION_CAPA_D.md`)**: el usuario
aprueba la serie completa sin señalar transiciones rotas (dimensión 13) —
no se activa el criterio de recuperación; **no se añade ninguna regla de
Plan** (comportamiento emergente del motor, MVP intacto). P-07 queda cerrado
parcial para F2; la observación centrada en unions sigue disponible para
F3-F5 (§12.1 registra "P-07 parcial" como cierre esperado de F2).
