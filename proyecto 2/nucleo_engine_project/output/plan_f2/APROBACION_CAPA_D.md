# Aprobación de Capa D (escucha humana) — Producción Fase 2

Fecha: 2026-11-13
Alcance: los 11 MIDIs de la serie oficial de `output/plan_f2/` (5 del gate §16.2 + 6 de la serie P-02)
Declarante: el usuario, tras escucha directa de los archivos MIDI ("apruebo los midis").
Refuerzo de Capa D: el usuario **iteró los 11 MIDIs en Suno** (mismo patrón que en F1 con los
4 MIDIs de la serie anterior) y **aprueba el material musical iterado** — la aprobación cubre
tanto la escucha directa de los MIDI originales como el resultado de su iteración creativa.

## Gate F2 (5 temas, §16.2)

| Tema | Título | Perfil | Seed | SHA256(16) | Capa C | Capa D |
|---|---|---|---|---|---|---|
| f2_101_dark_triphop | Bruma Lenta | full | 101 | 34a5d4c93738ab7e | OK (aviso no bloqueante C4b) | APROBADO |
| f2_202_doom_dark_jazz | Cartografía Oscura | atmospheric | 202 | e09752bbbb836535 | OK | APROBADO |
| f2_303_doom_triphop | Marea Negra | full | 303 | 8540d2fbc9537c27 | OK | APROBADO |
| f2_auto_total | Alba Tardía | full | 320569 | af57c752252d4280 | OK (avisos no bloqueantes C4b) | APROBADO |
| f2_ausente_jazz_media | Ceniza Sobre el Mar | sax_rhodes | 808 | ae985dbaf11fb445 | OK (avisos no bloqueantes C4b) | APROBADO |

Nota: los avisos C4b son diagnósticos no bloqueantes de capa C (§6.5 v1.4; hallazgo F1-C4b:
`improv.py:18` — "el scheduler puede dejar secciones SIN sax, silencio = decisión"). La
aprobación por escucha humana los cubre, igual que en F1 con `vapor_y_neon_303`.

## Serie P-02 (solos, 6 temas, §4 P-02)

| Tema | Estilo | Protagonista | Seed | SHA256(16) | Capa C | Capa D |
|---|---|---|---|---|---|---|
| p02_solos/p02_1_sax | dark_triphop | sax_tenor | 41 | 0fef1ab13c085263 | OK | APROBADO |
| p02_solos/p02_2_sax_ciclos | doom_triphop | sax_tenor | 42 | bfc3e6c1a1167c31 | OK | APROBADO |
| p02_solos/p02_3_rhodes_ciclos | doom_dark_jazz | rhodes | 43 | bad3f1390793a6e6 | OK | APROBADO |
| p02_solos/p02_4_vibes | doom_triphop | vibraphone | 44 | 4c4ba89777a85f19 | OK | APROBADO |
| p02_solos/p02_5_rhodes_ciclos | dark_triphop | rhodes | 45 | fad23f4622c0afe7 | OK | APROBADO |
| p02_solos/p02_6_vibes_libre | doom_dark_jazz | vibraphone | 46 | b27861e9eed2b1b3 | OK | APROBADO |

Nota: la carpeta `p02_solos/p02_3_rhodes/` es una iteración intermedia del mismo tema (mismo
título y seed, generada 4 minutos antes); la serie oficial usa `p02_3_rhodes_ciclos`.

## Estado de gates de la Fase 2 (§16.2)

| Capa | Alcance | Resultado |
|---|---|---|
| A — estructura | sobre los 5 planes del gate | OK (5/5) |
| B — invariantes del plan | sobre los 5 planes del gate | OK (5/5) |
| C — contenido | sobre los 5 MIDI / events.json | OK (5/5; avisos C4b no bloqueantes registrados) |
| D — escucha humana | sobre los 11 MIDIs de la serie | APROBADA (este documento) |
| Bloqueo `locked` (§9.1) | test real del intérprete | OK (`test_locked_no_se_toca_y_salto_se_corrige_por_el_otro_lado`) |
| Seed automática (§9.2) | test + demo en vivo | OK (seed derivada, persistida y reproducible) |
| P-01 tablas vs heurística | registro `p01_series.json` | CERRADO: tablas fijas declarativas |
| P-02 solos | registro `REGISTROS_PENDIENTES.md` + serie | CERRADO: capa C 6/6 + capa D aprobada (este documento) |
| P-04 decisiones.json | registro | CERRADO: no se crea (plan+events+capa_c bastan) |
| P-07 transiciones | registro | PARCIAL: sin evidencia de transición=0 en escucha, no se añade regla (MVP §15.10) |

**Estado resultante: Fase 2 cerrada — todos los gates cumplidos. Gate habilitado: `cc-f2-ok`.**

**Fase 3 (Interfaz Guided en Studio): BLOQUEADA.** Permanece sin iniciar; requiere autorización
explícita del usuario (spec §12, roadmap mono-dimensional).
