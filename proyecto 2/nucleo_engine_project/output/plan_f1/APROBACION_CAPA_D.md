# Aprobación de Capa D (escucha humana) — Producción Fase 1

Fecha: 2026-11-13
Alcance: los 4 MIDIs de `output/plan_f1/`
Declarante: el usuario, tras escucha directa de los 4 archivos MIDI.

| Tema | Perfil | Seed | SHA256(16) | Capa C | Capa D |
|---|---|---|---|---|---|
| ancla_demo_medianoche | full | 3113 | 32199acc254a2eef | OK | APROBADO |
| cuartos_de_marea_101 | full | 101 | 9d9d293186f65230 | OK | APROBADO |
| calles_de_ceniza_202 | atmospheric | 202 | 86887fcbe8e73722 | OK | APROBADO |
| vapor_y_neon_303 | full | 303 | 9b247022754b8ed3 | aviso no bloqueante `lead_mono_range` | APROBADO (con aviso) |

Nota: el aviso de `vapor_y_neon_303` es un diagnóstico de capa C (§6.5 v1.4), no un gate bloqueante; la aprobación por escucha humana lo cubre.

## Estado de gates de la Fase 1 (§16.2)

| Capa | Alcance | Resultado |
|---|---|---|
| A — estructura | sobre el plan | OK |
| B — invariantes del plan | sobre el plan | OK |
| C — contenido | sobre el MIDI / events.json | OK (1 aviso no bloqueante) |
| D — escucha humana | sobre los 4 MIDIs | APROBADA (este documento) |

**Estado resultante: Fase 1 cerrada — todos los gates cumplidos.**

**Fase 2: BLOQUEADA.** Permanece sin iniciar; requiere autorización explícita del usuario (orden vigente de la implementación F1).
