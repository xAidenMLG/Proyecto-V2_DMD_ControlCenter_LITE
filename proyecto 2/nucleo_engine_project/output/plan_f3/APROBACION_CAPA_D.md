# Aprobación de Capa D (escucha humana) — Fase 3 · Interfaz Guided

Fecha: 2026-11-13
Alcance: los 3 MIDIs producidos por la ruta Guided durante el cierre de F3
(2 golden guiadas + el tema del E2E desde la UI de Studio).
Declarante: el usuario, tras escucha directa de los archivos MIDI
(«midis escuchados y aceptados», mensaje literal del usuario).
Documento de referencia: `PROTOCOLO_ESCUCHA_F3.md` (protocolo §6.6; gate F3
«escucha ≥ banda F2»; banda de comparación = los 11 MIDIs aprobados en
`output/plan_f2/APROBACION_CAPA_D.md`, incluida su iteración en Suno).

## Piezas evaluadas (3)

| # | Tema | Origen | Identidad declarada en Guided | Seed | SHA256(16) | Capa C | Capa D |
|---|---|---|---|---|---|---|---|
| 1 | Sala de Espera (G1) | golden guiada vía API/jobs (ruta real) | dark_triphop × balanced × sax_tenor; duración corta, forma canción | 721106 | 9dda0282c42acb66 | OK | APROBADO |
| 2 | Lluvia en el Asfalto (G2) | golden guiada vía API/jobs (ruta real) | idéntica a G1 + pulso «Recto» (único cambio) | 142257 | b56b01fa855407c8 | OK | APROBADO |
| 3 | Cámara de Eco | E2E desde la UI de Studio (puerto 8899, navegador) | doom_triphop × experimental × vibraphone; energía muy alta, ciclos, corta, pulso recto | 576954 | 572d18b59a71431c | OK | APROBADO |

Veredicto del protocolo: los 3 temas **APROBADOS**, sin dimensiones en regresión declaradas.
La aprobación cubre los tres puntos de atención del protocolo:

1. **G1 vs G2** (único cambio declarado: pulso swing→recto) — ambos temas aceptados.
2. **«Cámara de Eco»** y sus avisos experimentales del motor (`lead_mono_range` fail no
   bloqueante, `section_bounds` warn) — el material musical de esa seed queda aceptado por
   escucha humana, mismo patrón que los avisos C4b en F1/F2 (la escucha humana decide).
3. **Coherencia Guided↔resultado** (lo pedido en lenguaje humano se oye: energía «muy alta»,
   forma «ciclos», pulso «recto», carácter experimental) — aceptada.

## Estado de gates de la Fase 3 (§16.2)

| Capa / criterio | Alcance | Resultado |
|---|---|---|
| A — estructura | planes de la ruta Guided (g1, g2, E2E) | OK (3/3) |
| B — invariantes del plan | planes de la ruta Guided (g1, g2, E2E) | OK (3/3) |
| C — contenido | 3 MIDI / events.json / capa_c.json | OK (3/3; avisos experimentales no bloqueantes en el E2E, cubiertos por Capa D) |
| D — escucha humana | los 3 MIDIs de la ruta Guided | **APROBADA (este documento)** |
| Precedencia Guiado > Automatic > default | tests de la suite Guided (17) | OK |
| Solo 6 controles (revisión §7) | catálogo = contrato exacto | OK |
| Suite completa | 526 passed + 3 skipped + 71 subtests | OK, 0 regresiones |

**Estado resultante: Fase 3 cerrada COMPLETAMENTE — cierre técnico (gate `cc-f3-ok`, tag del
mismo nombre) + Capa D aprobada por escucha humana. Todos los gates de F3 cumplidos.**

**Fase 4 (Album Blueprint): BLOQUEADA.** Este registro no constituye autorización para
continuar el roadmap (spec §12, roadmap mono-dimensional); requiere autorización explícita
del usuario.
