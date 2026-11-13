# Índice — output/plan_f5 (Fase 5: Endurecimiento y verificación)

| Archivo/carpeta | Contenido |
|---|---|
| `INFORME_FINAL_ESPEC_VS_REALIDAD.md` | Informe final de la especificación vs la realidad: cada promesa del MVP verificada con evidencia |
| `serie_base/01_full/` … `serie_base/05_atmospheric/` | Las 5 canciones MVP sin seed (§5.4): plan.json (seed auto persistida), doc.json, capa_c.json, evidencia.json, MIDI |
| `serie_base/intenciones/` | Las 5 intenciones exactas (solo identidad + protagonista + 6 controles — sin seed, sin overrides técnicos) |

Código y tests nuevos de la fase (todo aditivo):

| Ruta | Contenido |
|---|---|
| `tools/diff_midi.py` | Diff estructural L2 formalizado (§11.1) sobre events.json; exit 0/1/2; métricas numéricas informativas |
| `tests/test_diff_midi.py` | 6 tests de la herramienta contra eventos reales |
| `tests/control_center/test_serie_base.py` | 6 tests golden de la serie MVP (sin seed, perfiles, capa C, L1) |
| `docs/PROTOCOLO_ESCUCHA.md` | Protocolo general de Capa D: 13 dimensiones, procedimiento §6.6, formato `escucha.md` |

Estado de la fase: **F5 CERRADA TÉCNICAMENTE** — suite completa 583 tests verdes
(571 de F4 + 12 de F5), serie MVP 5/5 con capa C OK y L1 de regeneración 5/5,
diff L2 formalizado y probado. Gate restante único: **veredicto de escucha del
usuario** (Capa D — protocolo entregado; no automatizable por definición).
