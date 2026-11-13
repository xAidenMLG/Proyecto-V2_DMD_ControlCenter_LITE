# Protocolo de escucha — Fase 3 (capa D sobre la interfaz Guided)

Fecha: 2026-11-13 · Base: spec v1.4 §6.6 (protocolo de escucha), gate F3 «escucha ≥ banda F2»
Ámbito: los 3 MIDIs producidos por la ruta Guided durante el cierre técnico de F3.
Estado: **COMPLETADA — CAPA D F3 APROBADA** (2026-11-13): el usuario escuchó los 3 MIDIs y los
aceptó («midis escuchados y aceptados»), sin dimensiones en regresión respecto a la banda F2.
Registro formal: `APROBACION_CAPA_D.md`.

## Piezas a escuchar

| # | Tema | Origen | Identidad declarada en Guided | Seed | SHA256(16) | Capa C |
|---|---|---|---|---|---|---|
| 1 | Sala de Espera (G1) | golden guiada vía API/jobs (ruta real) | dark_triphop × balanced × sax_tenor; duración corta, forma canción | 721106 | 9dda0282c42acb66 | OK |
| 2 | Lluvia en el Asfalto (G2) | golden guiada vía API/jobs (ruta real) | idéntica a G1 + pulso «Recto» (único cambio) | 142257 | b56b01fa855407c8 | OK |
| 3 | Cámara de Eco | E2E desde la UI de Studio (puerto 8899, navegador) | doom_triphop × experimental × vibraphone; energía muy alta, ciclos, corta, pulso recto | 576954 | 572d18b59a71431c | OK |

Rutas: `output/plan_f3/golden_guiadas/g1|g2/` y
`studio_data/projects/f3_e2e_guided/generations/gen_0001/camara_de_eco/` (copias de las dos
primeras en la entrega `download/fase3_entrega/`).

## Qué evaluar (mismas 13 dimensiones del protocolo F2)

Mínimo exigido: **ninguna dimensión con regresión ≥2 respecto a la banda F2**
(serie base F2: `output/plan_f2/`, 11 MIDIs aprobados por el usuario, incluida su iteración
en Suno). Puntos de atención específicos de F3:

1. **G1 vs G2** — el único cambio declarado es el pulso (swing→recto): ¿se percibe el cambio
   de vaivén sin que la identidad de la casa se pierda? ¿Ambas siguen siendo "canción" de
   duración corta?
2. **Cámara de Eco** — identidad doom_triphop experimental con vibráfono protagonista:
   ¿el carácter experimental llega al oído? Nota registrada: `compliance_warns/fails`
   experimentales del motor (`lead_mono_range` fail no bloqueante, `section_bounds` warn);
   capa C estructural OK. Igual que los avisos C4b en F2, la escucha humana decide si el
   material musical de esa seed es aceptable.
3. **Coherencia Guided↔resultado** — ¿lo que se pidió en lenguaje humano se oye? (energía
   "muy alta", forma "ciclos", pulso "recto", carácter experimental).

## Veredicto (registrado por el usuario, 2026-11-13)

| # | Tema | Veredicto (APROBADO / RECHAZADO / observaciones) | Dimensiones en regresión |
|---|---|---|---|
| 1 | Sala de Espera | APROBADO | ninguna declarada |
| 2 | Lluvia en el Asfalto | APROBADO | ninguna declarada |
| 3 | Cámara de Eco | APROBADO | ninguna declarada |

Veredicto registrado (2026-11-13): **Capa D F3 aprobada**, anotada en este documento y en el
informe (§15). No se aplica rollback (§14): sin rechazos ni regresiones declaradas.
Registro formal: `APROBACION_CAPA_D.md`.
