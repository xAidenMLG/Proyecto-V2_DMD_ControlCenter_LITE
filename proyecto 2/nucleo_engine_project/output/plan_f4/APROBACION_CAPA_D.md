# Aprobación de Capa D (escucha humana) — Fases 4–5 · «Ecos de Neblina» + serie base MVP

Fecha: 2026-11-13
Alcance: los 8 MIDIs pendientes de veredicto en el cierre del roadmap F1–F5 —
el álbum «Ecos de Neblina» (3 pistas, Fase 4) y la serie base MVP sin seed
(5 piezas, Fase 5). La declaración del usuario es global («los midis»): ninguna
pieza queda excluida.
Declarante: el usuario, tras escucha directa de los archivos MIDI
(«totalmente aceptados los midis», mensaje literal del usuario).
Documentos de referencia: `output/plan_f4/PROTOCOLO_ESCUCHA_F4.md` (escucha
comparada, gate F4) y `docs/PROTOCOLO_ESCUCHA.md` (13 dimensiones §6.5,
procedimiento §6.6, gate F5).

## Piezas evaluadas (8)

| # | Pieza | Origen | Perfil | Seed | Duración | SHA256(16) | Capa C | Capa D |
|---|---|---|---|---|---|---|---|---|
| 1 | 01_umbral_de_neblina | álbum «Ecos de Neblina» (blueprint → ruta real F2 + pipeline FASE 8) | atmospheric | 9000 | 150.0 s | 51bb6a6b8f3a11ec | OK | APROBADO |
| 2 | 02_camara_de_espejos | álbum «Ecos de Neblina» | full | 9101 | 300.0 s | 511227d31a8ac2db | OK | APROBADO |
| 3 | 03_marea_baja_de_neon | álbum «Ecos de Neblina» (sin drums) | sax_rhodes | 9202 | 300.0 s | 4b590b654666fba4 | OK | APROBADO |
| 4 | 01_full | serie base MVP sin seed (§5.4) | full | 421278 | 150.0 s | a12ec71b0bdcd5fd | OK | APROBADO |
| 5 | 02_sax | serie base MVP sin seed | sax | 225802 | 150.7 s | dc5546611ab3b548 | OK | APROBADO |
| 6 | 03_drums | serie base MVP sin seed | drums | 574370 | 150.3 s | 678d623b1fc11598 | OK | APROBADO |
| 7 | 04_sax_vibes | serie base MVP sin seed | sax_vibes | 172484 | 301.7 s | fbaebfba3ddc6a66 | OK | APROBADO |
| 8 | 05_atmospheric | serie base MVP sin seed | atmospheric | 108204 | 401.9 s | fc2fe007f4c4ebbf | OK | APROBADO |

Verificación previa al registro: los 8 SHA256(16) fueron recalculados sobre los
archivos en disco y coinciden con el campo `sha256_midi` de su `evidencia.json`;
Capa C OK 8/8 con `compliance_fails` vacío 8/8.

Veredicto del protocolo: las 8 piezas **APROBADAS** — «totalmente aceptados los
midis», mensaje literal del usuario (equivalente al veredicto APROBADO de ambos
protocolos; sin observaciones ni regresiones declaradas).

## Registro honesto del veredicto (C-09 / C-11)

La Capa D no se disfraza de scoring numérico: el usuario declaró una aprobación
global («totalmente aceptados»), sin puntuación por dimensión y sin keep/regen
por pieza. Este documento registra el veredicto tal cual fue declarado y NO
inventa notas por las 13 dimensiones. La aprobación total declarada satisface el
umbral §6.5 (≥8 de 13 dimensiones con nota ≥1 y ninguna con 0) como veredicto
sintético del oyente — el criterio del MVP §5.4 queda cumplido por declaración
humana, que es la única forma que el spec admite para este gate.

## Estado de gates resultante

| Gate | Resultado |
|---|---|
| F4 — «escucha comparada ≥ banda» (§12.1) | **APROBADO** — Fase 4 cerrada COMPLETAMENTE (ya no solo «técnicamente») |
| F5 — «protocolo de escucha ejecutado con veredicto» (§12) | **APROBADO** — Fase 5 cerrada COMPLETAMENTE |
| MVP §5.4 — criterio «Veredicto de escucha ≥8/13 ≥1, ninguna 0» | **CUMPLIDO** (último criterio pendiente del informe final) |
| P-07 (transiciones) | PARCIAL por diseño del MVP, sin cambio: la dimensión 13 quedó dentro de la escucha aprobada |

**Estado resultante: roadmap F1–F5 COMPLETADO.** Todos los gates de las capas
A/B/C/D y de los niveles L1/L2 están en verde; suite completa 583 passed,
3 skipped, 0 fallos; autoridades compositivas (`produce.py`, `dark_director`,
`jazz_engine`, `forge`) intactas desde el ancla original. El proyecto DMD
Control Center v1.4 queda **completado de punta a punta, incluida la aceptación
auditiva humana**.

Queda fuera del roadmap (sin carácter de gate, honestidad del cierre, ídem
`INFORME_FINAL_ESPEC_VS_REALIDAD.md` §6): narrativa entre pistas (C-03,
pospuesta por el spec), calibración de umbrales L3/L4 por registro L4, y la
serie de 10 generaciones keep/regen del usuario (§6.6.4 — uso real del Studio,
que sigue operativo sobre esta misma base).
