# INFORME FASE 3 — Interfaz Guided en Studio (DMD Control Center)

Fecha de cierre: 2026-11-13 · Spec de referencia: DMD Control Center v1.4 (§7, §12.1, §14, §16.2)
Baseline: tag `f3-pre` (commit `4d4c368`, estado F2 cerrada) · Cierre: tag `cc-f3-ok`
Modo de trabajo: autorización explícita del usuario para implementar F3 completa (inspección → decisión → implementación → pruebas → corrección → cierre).

---

## 1. Resumen ejecutivo

F3 implementa la experiencia **Guided** dentro de DMD STUDIO (puerto 8899): una persona sin
conocimientos técnicos de composición elige identidad musical, protagonista y hasta seis
controles en lenguaje humano, pulsa «Generar canción» y el backend ejecuta la **ruta real de
Fase 2** (Intérprete Universal → capas A/B → compilador → `produce.py` → capa C) dentro del
sistema de jobs de Studio. La interfaz no genera notas, no construye `doc.json`, no duplica
el intérprete y no introduce un segundo pipeline: es una capa de interacción que traduce
elecciones humanas a una intención válida del esquema F2 y presenta resultados, errores y
estados de forma comprensible.

Implementado y verificado: catálogo Guided leído en vivo de los catálogos reales F1/F2; los 6
controles (§7.1) con nombres humanos y valor «Automático» por defecto; identidad y protagonista
en banda separada (no cuentan como controles); rechazo accionable de valores inválidos y de
parámetros técnicos (C-08: sin seed/BPM/tonalidad/gain); precedencia Guiado > Automatic >
default probada con tests; seed automática R0 y determinismo intactos; artefactos completos
co-localizados (P-05); capa C aplicada automáticamente; **2 canciones guiadas doradas (L2/L3)**
con hashes grabados; **prueba end-to-end real desde la UI de Studio en el puerto 8899** con
producción completa y réplica CLI byte-idéntica. Suite completa en verde (526 passed + 3 skipped
+ 71 subtests; baseline 509 + 3 + 71 → +17 tests Guided, 0 regresiones). Autoridades musicales
y de ejecución sin un byte modificado (diff vacío vs `f3-pre` en `control_center/`,
`dark_director/`, `jazz_engine/`, `forge/`, `scripts/produce.py`, `album/`, `web/`).

Capa D (escucha humana, protocolo §6.6) **APROBADA** (2026-11-13): el usuario escuchó los 3
MIDIs de la ruta Guided (G1 «Sala de Espera», G2 «Lluvia en el Asfalto» y el tema E2E
«Cámara de Eco») y los aceptó sin dimensiones en regresión respecto a la banda F2
(«midis escuchados y aceptados», mensaje literal del usuario). Registro: `APROBACION_CAPA_D.md`.
Con ello F3 queda cerrada COMPLETAMENTE (cierre técnico + Capa D).

## 2. Arquitectura final de Guided

Guided se apoya en las piezas existentes y añade una capa nueva de traducción y de presentación:

```
Usuario (navegador, 127.0.0.1:8899)
  └─ Vista Guided  studio/static/js/views/control_center.js   (nueva)
       · catálogo desde GET /api/guided/catalog (valores reales, cero opciones inventadas)
       · identidad + protagonista arriba; 6 controles como tarjetas; botón Generar
       · estado de ejecución (poll de /api/jobs/{jid}), resultado, escucha, descargas
  └─ POST /api/projects/{pid}/guided          (endpoint nuevo, server.py)
       · intencion_desde(): cuerpo UI → intención JSON del esquema F2 (solo traduce; vacío=auto)
       · prevalidar(): interprete.resolver() REAL en pre-vuelo → error accionable 422 sin ocupar job
       · JOBS.start_job(pid, {cc:{intencion…}}) → disciplina de un solo job, 409 si ocupado
  └─ studio/jobs.py (reutilizado; enrutado mínimo)
       · spec con "cc" → subproceso `python -m studio.runner_cc` (antes `studio.runner`)
  └─ studio/runner_cc.py (nuevo; proceso hijo aislado) — LA RUTA REAL DE F2:
       interprete.resolver(intencion)            → plan completo (seed R0 persistida)
       validador.validar(plan)                   → capas A/B (rechazo ⇒ job error)
       plan_compilador.compilar + escribir_salida→ doc.json + plan.json co-localizados (P-05)
       produce.producir_cancion(doc, production=perfil, seed=None, events=True)
                                                 → MIDI + evidencia.json + events.json
                                                 (seed desde doc.global.seed, sin --seed)
       validador.verificar_capa_c(plan, events)  → capa_c.json (gates §6.3; fallo ⇒ job error)
       WAV opcional con FluidSynth (idéntico a studio/runner.py)
  └─ UI de resultados: tarjeta Guided + vista Results existente (historial, hashes, audio)
```

Separación de responsabilidades intacta: Guided decide **qué quiere el usuario**; el intérprete
F2 decide **las ~40 decisiones técnicas** (cada una en `plan.evidence.resolved`); los motores
(Dark Director, Jazz Engine, MIDI Forge) siguen siendo las únicas autoridades musicales y de
ejecución; `scripts/produce.py` sigue siendo la autoridad de producción (invocado por su núcleo
`producir_cancion`, el mismo que usa el runner de Studio desde F1).

## 3. Flujo UI → intención → F2 → producción

1. El usuario abre un proyecto y la vista **Guided**; el catálogo llega de
   `GET /api/guided/catalog` (leído en vivo de `dark_director.contract` y
   `control_center.esquema_plan`).
2. Elige identidad (3 estilos × 3 accesibilidades) y protagonista (sax tenor / Rhodes /
   vibráfono); ajusta hasta 6 controles; lo que deja en «Automático» **no se envía** (§7.2.2:
   la UI nunca rellena por el intérprete). Puede poner título; **no puede** poner seed, BPM,
   tonalidad ni gain (rechazo explícito, C-08).
3. «✦ Generar canción» → `POST /api/projects/{pid}/guided` con
   `{identity, controls, title?, wav?}`.
4. El backend traduce a intención (`studio/guided.py::intencion_desde`) y **pre-valida con el
   intérprete real** (`interprete.resolver`): si la intención es inválida responde **422 con el
   mensaje accionable del intérprete** («controls.energia fuera de catálogo: 'fuertisima'
   (válidos: muy_baja, …)») sin iniciar trabajo. Cuerpos con claves técnicas se rechazan
   (400/422; pydantic `extra="forbid"` — nada se ignora en silencio).
5. Trabajo asíncrono (`studio/jobs.py`): `runner_cc` ejecuta la ruta completa de F2 con
   progreso en vivo (líneas `##`): «Resolviendo la intención…», «Capas A/B: OK»,
   «Produciendo con el pipeline real (perfil=full, seed desde doc.global.seed)»,
   «Capa C: OK (9 gates bloqueantes)».
6. Resultado en la UI: título, seed persistida, tempo, forma, perfil, duración real, compases,
   nº de decisiones resueltas, estado de capa C, sha256 copiable, escucha si hay WAV y
   descargas de artefactos; el log técnico queda disponible en un desplegable (diagnóstico sin
   dominar la experiencia). El historial Guided del proyecto lista cada generación (estado,
   título, seed, forma, gen_id) y enlaza a Results.
7. Repetir sin reconstruir: las selecciones persisten por proyecto (localStorage) y la tarjeta
   de resultado no borra el formulario.

## 4. Archivos creados y modificados

Modificados (5 — diff vs `f3-pre`, +101/−16 líneas):

| Archivo | Cambio |
|---|---|
| `studio/server.py` (+61) | 2 endpoints nuevos: `GET /api/guided/catalog` y `POST /api/projects/{pid}/guided`; modelo `GuidedBody` con `extra="forbid"` (Guided no es bypass de Advanced); import de `studio.guided`. |
| `studio/jobs.py` (+48/−16 aprox.) | Enrutado mínimo: si el spec lleva `cc` (intención), `run_spec` cambia a `{intencion, wav, soundfont, out_dir}` y el subproceso es `python -m studio.runner_cc`; `spec_resumen` con modo guided. El flujo de generación normal queda byte a byte igual (suite Studio en verde). |
| `studio/static/index.html` (+1) | Entrada de navegación `#/guided` («✦ Guided»), primera tras Projects. |
| `studio/static/js/app.js` (+4/−1) | Registro de la vista en el router (`VIEWS.guided`) y en `REQUIRES_PROJECT`. |
| `studio/static/js/api.js` (+3) | Cliente: `guidedCatalog()`, `guidedGenerate(pid, body)`. |

Nuevos (5 de código + 2 de datos + 1 script + evidencia):

| Archivo | Contenido |
|---|---|
| `studio/guided.py` (278 l.) | Catálogo en vivo con etiquetas humanas; `intencion_desde` (traducción estricta, vacío=auto); `prevalidar` (intérprete real en pre-vuelo). Única tabla de etiquetas de la capa Guided. |
| `studio/runner_cc.py` (184 l.) | La ruta F2 en el proceso hijo de jobs (ver §2). Glue de orquestación, cero lógica musical. |
| `studio/static/js/views/control_center.js` (412 l.) | Vista Guided completa (§7.3): identidad+protagonista, 6 tarjetas de control, resumen en lenguaje humano, ejecución con poll, tarjeta de resultado, escucha, descargas, historial, persistencia de selecciones. |
| `tests/studio/test_guided_api.py` (407 l.) | 17 tests del gate F3 (§8): catálogo, traducción, precedencia, rechazos, automáticos, artefactos, determinismo, golden, vista registrada. |
| `tests/studio/golden_f3/golden_guiadas.json` | Fixture de las 2 golden guiadas (intenciones, seeds, títulos, sha256, bpm, tonalidad, perfil, capa C). |
| `scripts/f3_preparar_golden.py` | Reproduce las golden por la ruta real (server en hilo + HTTP) y regenera fixture + artefactos. |
| `output/plan_f3/` | Informe, protocolo de escucha, índice, artefactos de las 2 golden (plan/doc/capa_c/evidencia/events/config/MIDI), capturas de la UI. |

Sin modificación (verificado con `git diff --stat f3-pre -- <ruta>` vacío): `control_center/`,
`dark_director/`, `jazz_engine/`, `forge/`, `scripts/produce.py`, `album/`, `web/` (web legacy),
`tests/` existentes, goldens F1/F2.

## 5. Decisiones técnicas relevantes

1. **La resolución del intérprete corre dentro del job, no en el endpoint** (`runner_cc`). El
   endpoint solo pre-valida (errores accionables inmediatos sin ocupar el slot de producción);
   el trabajo re-resuelve determinísticamente y es lo que produce el plan persistido. Así el
   log del job muestra la cadena F2 completa y el estado de capa C queda en el resultado del
   job — igual que el CLI `automatic`, pero con el patrón de ejecución de Studio (proceso hijo
   aislado, un solo job a la vez, log persistente).
2. **`produce` se importa en proceso en `runner_cc`** (mismo núcleo `producir_cancion` que usa
   `studio/runner.py` desde F1) en vez de por subprocess como hace el CLI. El §13 del CLI
   («control_center no importa produce.py») queda intacto: `runner_cc` es un módulo de Studio,
   no del paquete control_center. Cero duplicación: el módulo de carga se reutiliza de
   `studio.runner` (`_load_produce_module`).
3. **jobs.py se tocó mínimamente para enrutar** (4 líneas efectivas). La spec listaba 3 archivos
   tocados (server.py, index.html, vista nueva); jobs.py es el 4º, justificado: reutilizar el
   sistema de jobs (spec §12.1: «Reutiliza: studio/jobs.py») exige que el spec pueda pedir el
   runner nuevo; duplicar jobs habría violado «evitar duplicación de lógica de negocio». El
   flujo de generación normal es byte a byte el mismo (regresión verde).
4. **Pre-vuelo con el intérprete REAL, no con un validador espejo**: `prevalidar` llama a
   `interprete.resolver` y descarta el resultado. Los mensajes de error son los del propio
   intérprete F2 (una sola fuente de verdad; cero drift de mensajes).
5. **Rechazo explícito de parámetros técnicos** (C-08): `GuidedBody` con `extra="forbid"` +
   lista blanca en `intencion_desde`. Hallazgo durante el desarrollo: pydantic **silenciaba**
   los campos extra (un `{"seed": 42}` se ignoraba y arrancaba una producción) — corregido para
   que Guided nunca actúe como bypass silencioso de Advanced.
6. **Perfiles no se exponen en Guided (cierre de P-06)**: el perfil lo resuelve el intérprete
   (paso 6) según energía/drums; la UI no muestra selector de perfil ni `original` (excluido del
   Automatic por decisión F2). El catálogo expuesto no contiene ningún parámetro técnico
   (test: sin `seed`, `bpm`, `gain`, `velocity` en el JSON del catálogo).
7. **Proyecto como espacio de trabajo**: Guided opera sobre el proyecto activo (patrón de las
   demás vistas); sus generaciones entran al historial del proyecto y a Results. El `doc.json`
   del proyecto (superficie Advanced/JSON) no interfiere: la fuente de Guided es la intención.
8. **`out_name` de carpeta**: slug del título aportado o `guided_song`; el título real lo elige
   el intérprete (banco por seed) y se muestra en el resultado — la carpeta es solo
   direccionamiento, no identidad musical.

## 6. Controles implementados y correspondencia con el contrato

Los 6 controles de §7.1, con sus valores EXACTOS de `control_center.esquema_plan.CONTROLES`
(sin inventar ninguno; test de igualdad contra el catálogo real):

| # | Control (UI) | Valores (catálogo F2) | Default UI | Resolución si auto | Campo intención |
|---|---|---|---|---|---|
| 1 | «¿Cuánta fuerza tiene la pieza?» | muy_baja, baja, media, alta, muy_alta | Automático | R1 → `media` | `controls.energia` |
| 2 | «¿Cómo se organiza?» | cancion, ciclos, libre | Automático | R15 → `cancion` | `controls.forma` |
| 3 | «¿Cuánto va a durar?» | corta, media, larga | Automático | R12 → `media` | `controls.duracion` |
| 4 | «¿Qué color tienen los acordes?» | nocturno, jazz, crudo, sombrio | Automático | R6 → por accessibility | `controls.armonia` |
| 5 | «¿Cómo es el vaivén rítmico?» | swing, recto, lento_arrastrado, latin | Automático | R29 → `swing` | `controls.pulso` |
| 6 | «¿Cuánto peso tiene la batería?» | ausente, contenida, presente, protagonista | Automático | R2 → por energía | `controls.drums` |

Identidad (banda aparte, no cuentan como controles, §7): `identity.style` ∈
`dark_triphop | doom_triphop | doom_dark_jazz` (obligatorio), `identity.accessibility` ∈
`commercial | balanced | experimental` (obligatorio), `identity.protagonist` ∈
`sax_tenor | rhodes | vibraphone` (obligatorio). Título opcional (`title`, metadata; si se
omite, el intérprete elige del banco por seed). Correspondencia verificada por tests: la
intención que llega al intérprete es exactamente la elegida (echo en `plan.controls` y en el
`job_spec.json` persistido), y cada auto queda registrado en `plan.evidence.resolved` con su
regla (R0/R1/R2/R6/R12/R15/R29).

## 7. Tests ejecutados con comandos y resultados reales

```
python3 -m pytest tests/studio/test_guided_api.py -v
  → 17 passed (catalogo_guided_refleja_los_catalogos_reales,
    vista_guided_registrada_en_el_shell,
    cada_control_se_traduce_al_esquema_de_intencion[6 params],
    control_invalido_rechazado_de_forma_accionable,
    parametros_tecnicos_rechazados_guided_no_es_advanced,
    identidad_invalida_rechazada_accionable,
    valores_automaticos_se_conservan_y_se_resuelven,
    precedencia_guiado_gana_a_automatic_y_default,
    precedencia_a_seed_fija_solo_cambian_decisiones_esperadas,
    ruta_completa_genera_artefactos_y_capa_c,
    determinismo_de_f2_intacto_misma_intencion_mismo_midi,
    golden_guiadas_l2_l3)

python3 -m pytest tests/ -q --ignore=tests/dmd   → 355 passed, 3 skipped, 53 subtests
python3 -m pytest tests/dmd -q                   → 171 passed, 18 subtests
python3 -m pytest tests/control_center/test_golden_automatic.py
                 tests/control_center/test_compilador_golden.py -q
                                                 → 18 passed, 6 subtests  (goldens F1+F2, ancla L1)
python3 -m control_center automatic /tmp/f3_cli_int.json --out /tmp/f3_cli_out
  → plan resuelto (seed 4988), compilado, capa C: OK (7 gates bloqueantes)
```

Total final: **526 passed + 3 skipped + 71 subtests** (baseline `f3-pre`: 509 + 3 + 71;
delta = +17, exactamente la suite Guided nueva; 0 fallos, 0 regresiones). Los tests de Studio
existentes (incl. determinismo del pipeline normal, 7 perfiles, concurrencia, cancelación)
pasan sin cambios tras el edito de `jobs.py`.

## 8. Prueba end-to-end desde Studio

Ejecutada el 2026-11-13 contra el servidor REAL (`python3 -m studio --no-browser`, puerto
8899) con navegador headless (Chrome vía agent-browser) — sin mocks, sin terminal:

1. Abrir `http://127.0.0.1:8899/` → shell de Studio con la entrada «✦ Guided» en la
   navegación (captura: `output/plan_f3/guided_full.png`).
2. Crear proyecto «F3 E2E Guided» desde la UI → abre `#/composition`.
3. Navegar a `#/guided` → la vista pinta identidad, protagonista, título y las 6 tarjetas
   con el catálogo real.
4. Selecciones desde la UI: estilo **Doom Trip-Hop**, carácter **Experimental**,
   protagonista **Vibráfono**, título «Cámara de Eco», energía **Muy alta**, forma **Ciclos**,
   duración **Corta**, pulso **Recto** (drums y carácter armónico en Automático). El resumen
   en lenguaje humano mostró: «Doom Trip-Hop · Experimental · protagoniza Vibráfono · muy
   alta · ciclos · corta · recto».
5. «✦ Generar canción» → estado en vivo (progreso indeterminado + pasos del log) →
   **completado en ~20 s**.
6. Resultado mostrado en la UI: título **Cámara de Eco**, seed **576954**, tempo **77 BPM**,
   forma **ciclos**, perfil **full**, duración real **2:30**, 48 compases, **15 decisiones
   resueltas por el intérprete**, capa C **OK · 7 gates** (informe: 9 checks bloqueantes OK),
   sha256 copiable, botón «Abrir en Results», historial Guided actualizado.
7. Artefactos reales en disco (`studio_data/projects/f3_e2e_guided/generations/gen_0001/
   camara_de_eco/`): `plan.json`, `doc.json`, `capa_c.json`, `events.json`, `evidencia.json`,
   `config_efectiva.json`, `camara_de_eco.mid` — accesibles y descargables desde Results
   (verificado en el navegador).
8. **Fidelidad de la traducción**: `plan.controls == {energia: muy_alta, forma: ciclos,
   duracion: corta, pulso: recto, drums: presente, armonia: sombrio}` — los dos automáticos
   quedaron resueltos por regla (R6: experimental → sombrio; R2: muy_alta → presente).
9. **Equivalencia con la ruta CLI**: producir el MISMO `doc.json` guardado con el CLI
   (`python3 scripts/produce.py doc.json --production full --out /tmp/f3_replica`) reproduce
   el MIDI **byte a byte**: sha256 `572d18b59a71431cc985a8a236dea57741fc9ec7be9a6b01c2e4a85253f361ef`
   en ambas rutas — la UI no altera ni un byte de la producción.

Hallazgo registrado (no bloqueante, ver §12): la evidencia del tema E2E registra el fail
experimental `lead_mono_range` del validador de contenido de Forge (métrica no bloqueante,
C-09/C-11; capa C estructural OK; reproducible byte-idéntico por CLI — comportamiento del
motor para esa seed/energía, no de la capa Guided). La escucha humana (§15) cubre la
evaluación musical, igual que los avisos C4b en F2.

## 9. Artefactos producidos y rutas

| Artefacto | Ruta | Identidad |
|---|---|---|
| Golden guiada G1 «Sala de Espera» | `output/plan_f3/golden_guiadas/g1/` | dark_triphop × balanced × sax_tenor; controls {duracion: corta, forma: cancion}; **seed 721106**; bpm 86; **D minor**; cancion; perfil full; 54 compases; 150.7 s; capa C OK; sha256 MIDI `9dda0282c42acb66b57782963e52d102023190f2f22e1df99ca5b83a93d42650` |
| Golden guiada G2 «Lluvia en el Asfalto» | `output/plan_f3/golden_guiadas/g2/` | misma identidad y controles + **pulso: recto** (único cambio); **seed 142257** (R0 re-deriva); bpm 86 (negociación R13 con corta); **A minor**; perfil full; 54 compases; 150.7 s; capa C OK; sha256 MIDI `b56b01fa855407c820b98179d33ea5a66ed8e33e57dbee0acdd786af017b59a2` |
| Tema E2E desde UI «Cámara de Eco» | `studio_data/projects/f3_e2e_guided/generations/gen_0001/camara_de_eco/` | doom_triphop × experimental × vibraphone; seed 576954; bpm 77; F# minor; ciclos; full; 48 compases; 149.6 s; capa C OK; sha256 `572d18b59a71431cc985a8a236dea57741fc9ec7be9a6b01c2e4a85253f361ef` |
| Fixture golden (tests) | `tests/studio/golden_f3/golden_guiadas.json` | intenciones + seeds + hashes + resumen de plan (assert en cada ejecución) |
| Capturas de UI | `output/plan_f3/guided_full.png`, `guided_result.png` | vista Guided con resultado y historial |
| Informe / protocolo / índice | `output/plan_f3/INFORME_FASE_3.md`, `PROTOCOLO_ESCUCHA_F3.md`, `INDICE.md` | este informe y su anexo |

## 10. Evidencia de regresión F1/F2

* **Ancla L1 (tripwire §14)**: `tests/control_center/test_compilador_golden.py` —
  `test_producir_sin_seed_reproduce_sha256_midi` y `test_producir_dos_veces_mismo_sha256`
  reproducen `32199acc…b29a9ff` (demo_medianoche, seed de `doc.global.seed`) — **pasan** tras F3.
* **Golden F2**: `tests/control_center/test_golden_automatic.py` — las 3 doradas (seeds
  101/202/303) mantienen sus hashes — **pasan** tras F3.
* **Suite completa**: 526 passed + 3 skipped + 71 subtests, cero fallos (§7).
* **Studio existente**: `tests/studio/test_studio_api.py` completo (determinismo del pipeline
  normal, 7 perfiles, guided/native de armonía, concurrencia single-flight, cancelación,
  WAV sin FluidSynth con error claro, traversal/pid) — **pasan sin cambios**.
* **CLI Automatic**: ejecución en vivo correcta (§7).
* **Autoridades**: `git diff f3-pre` vacío en control_center, dark_director, jazz_engine,
  forge, scripts/produce.py, album, web.

## 11. Diff respecto al baseline

Baseline: tag `f3-pre` (= commit `4d4c368`, cierre de F2). Diff completo del cierre:

```
git diff --stat f3-pre
 studio/jobs.py                   | 48 ++++++------   (enrutado runner_cc + spec_resumen guided)
 studio/server.py                 | 61 ++++++++++++-   (+2 endpoints, GuidedBody extra=forbid)
 studio/static/index.html         |  1 +              (nav Guided)
 studio/static/js/api.js          |  3 ++             (guidedCatalog/guidedGenerate)
 studio/static/js/app.js          |  4 +-             (VIEWS + REQUIRES_PROJECT)
 5 files changed, 101 insertions(+), 16 deletions(-)
```

Nuevos: `studio/guided.py`, `studio/runner_cc.py`,
`studio/static/js/views/control_center.js`, `tests/studio/test_guided_api.py`,
`tests/studio/golden_f3/golden_guiadas.json`, `scripts/f3_preparar_golden.py`,
`output/plan_f3/` (informe + protocolo + índice + golden + capturas).
Rollback: `git revert`/`reset` al tag `f3-pre` (o borrar los 5 archivos nuevos de código +
revertir los 5 tocados — la disciplina de jobs y todo lo anterior sigue intacta; los jobs
antiguos y las generaciones previas permanecen como datos, §14).

## 12. Limitaciones, deuda técnica y hallazgos

Limitaciones conocidas (declaradas, no defectos):
* **Escucha en la UI**: el reproductor inline suena solo si hay WAV/MP3 (FluidSynth +
  soundfont). Sin WAV, la escucha es sobre el MIDI fuera del navegador o instalando
  FluidSynth (Settings). `events.json` (Player WebAudio) queda disponible como artefacto;
  el player legacy vive en `web/` y no se migró (fuera de alcance F3).
* **Carpetas de salida**: cuando el usuario no da título, la carpeta se llama `guided_song`
  (el título real del banco se muestra en UI/plan) — direccionamiento, no identidad.
* **El protagonista con perfiles full no cambia el rol 'lead' del motor**: con protagonista
  vibráfono y perfil full, el motor sigue asignando lead a sax_tenor (comportamiento F1/F2);
  el protagonista se manifiesta vía focus/solos según las reglas del intérprete. Observado en
  el tema E2E (vibraphone=mallet, sax_tenor=lead). No es un cambio de F3.

Hallazgos:
* **H1 (corregido)**: pydantic silenciaba campos extra del cuerpo Guided — un `seed` enviado
  por la API se ignoraba y arrancaba una producción normal. Corregido con `extra="forbid"`
  (rechazo explícito) + test `parametros_tecnicos_rechazados_guided_no_es_advanced`.
* **H2 (hallazgo de contenido, no bloqueante)**: el tema E2E registra `compliance_fail:
  lead_mono_range` (métrica experimental de contenido de Forge, capa no bloqueante C-09/C-11).
  Reproducido byte-idéntico por CLI con el mismo doc ⇒ es un dato del motor para esa
  combinación seed/energía, no un efecto de la ruta Guided. Cubierto por Capa D (§15), mismo
  patrón que los avisos C4b en F2. Warn adicional: `section_bounds`.
* **H3 (observación de la spec confirmada)**: con `duracion=corta`, la negociación R13 colapsa
  el bpm de distintos pulsos al mismo valor (86 en las golden) — el control pulso sigue
  llegando al intérprete (R11 lo registra) y el MIDI sí cambia (sha distinto). La aserción
  «solo cambian decisiones esperadas» usa el conjunto de consecuencias posibles, no impone
  que bpm cambie siempre.
* **Deuda técnica menor**: `spec_resumen` de jobs guided no incluye el perfil (se resuelve
  dentro del job); el historial Guided se construye filtrando jobs (los pre-F3 no llevan la
  marca `guided`). Ninguna afecta al gate.

## 13. Procedimiento de reproducción y verificación

```
cd nucleo_engine_project

# 1) suite completa (incluida la Guided)
python3 -m pytest tests/ -q --ignore=tests/dmd     # 355 passed, 3 skipped, 53 subtests
python3 -m pytest tests/dmd -q                     # 171 passed, 18 subtests

# 2) goldens F1/F2 (ancla L1)
python3 -m pytest tests/control_center/test_compilador_golden.py \
                  tests/control_center/test_golden_automatic.py -q   # 18 passed, 6 subtests

# 3) Studio real y prueba Guided desde el navegador
python3 -m studio --no-browser                     # http://127.0.0.1:8899
#   → crear/abrir proyecto → ✦ Guided → elegir identidad/protagonista/controles
#   → «✦ Generar canción» → tarjeta de resultado + Results

# 4) regenerar las golden guiadas por la ruta real (reescribe fixture y artefactos)
python3 scripts/f3_preparar_golden.py              # seeds/hashes esperados en el output

# 5) verificación de equivalencia con CLI (cualquier generación Guided)
python3 scripts/produce.py <gen>/camara_de_eco/doc.json --production full --out /tmp/replica
#   sha256 del MIDI == sha256 registrado en evidencia.json
```

## 14. Rollback de F3

* Tag de inicio: `f3-pre` (estado F2 cerrado, commit `4d4c368`). Cierre: `cc-f3-ok`.
* Reversión completa: `git reset --hard f3-pre` (o revert del commit de cierre). Los 5 archivos
  nuevos de código/datos desaparecen y los 5 tocados vuelven a su estado F2.
* Efecto residual aceptable (§14): los jobs y generaciones ya producidos (studio_data) quedan
  como datos; ninguna autoridad cambia; los contratos F1/F2 no se tocaron.
* Disparadores de rollback de la spec: la escucha con regresión ≥2 dimensiones respecto a F2
  aplicaría al contenido guiado; ningún disparador técnico aplicable (suite verde, goldens
  intactos, capas A/B/C en verde).

## 15. Estado explícito del gate `cc-f3-ok`

| Criterio (§16.2 F3) | Estado |
|---|---|
| Precedencia testeada | **CUMPLE** — `test_precedencia_guiado_gana_a_automatic_y_default` + `test_precedencia_a_seed_fija_solo_cambian_decisiones_esperadas` (Álbum no existe aún: llega en F4, no se puede testear precedencia con álbum en F3) |
| 2 canciones guiadas doradas (L2/L3) | **CUMPLE** — G1/G2 con seeds y sha256 grabados, re-ejecución byte-idéntica (L2), diff de plan confinado a decisiones esperadas; ruta real via API + jobs |
| Solo 6 controles (revisión §7) | **CUMPLE** — catálogo = 6 controles EXACTOS del contrato, identidad+protagonista en banda aparte, cero parámetros técnicos (test), rechazo explícito de seed/bpm/tonalidad/gain |
| Escucha ≥ banda F2 | **CUMPLE** — Capa D aprobada por el usuario (2026-11-13): 3/3 temas APROBADOS, sin dimensiones en regresión declaradas; veredicto en `PROTOCOLO_ESCUCHA_F3.md`, acta en `APROBACION_CAPA_D.md` |
| Regresión de escucha ≥2 dim ⇒ rollback | No aplica — la escucha aprobó el material sin regresiones declaradas |

**Estado resultante: Fase 3 cerrada COMPLETAMENTE — Guided integrada en Studio sobre la ruta
F2 real, E2E desde la UI verificada, suite completa en verde, autoridades intactas, y Capa D
(escucha humana) aprobada por el usuario (2026-11-13) sin regresiones respecto a la banda F2.**
Gate `cc-f3-ok` completo. **Fase 4 (Album Blueprint): BLOQUEADA** — este cierre no
constituye autorización para continuar el roadmap.
