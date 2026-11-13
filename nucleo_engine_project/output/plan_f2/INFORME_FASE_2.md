# INFORME FASE 2 — Intérprete Universal (DMD Control Center, spec v1.4)

Fecha de cierre: 2026-11-13 · Repo: `nucleo_engine_project/` · Spec fuente:
`DMD_CONTROL_CENTER_FINAL_IMPLEMENTATION_SPECIFICATION.md` v1.4 (§7, §9, §12.1, §16.2).
Este informe es autocontenido: cada dato citado fue ejecutado y verificado en disco.

---

## 1. Resumen ejecutivo

La Fase 2 está **completada y cerrada**. El Intérprete Universal transforma una
**intención** (identidad + 6 controles opcionales + overrides Advanced) en un
**Composition Plan completo y válido** (capas A/B), lo compila a `doc.json`
dark-director/1 y produce la canción con el pipeline existente, **sin tocar la
autoridad compositiva**: `dark_director/compilador.py`, `scripts/produce.py`,
`jazz_engine/` y `forge/` quedaron intactos (verificado por diff y por la
regresión del ancla golden F1, sección 7).

Gates §16.2 de F2: **5/5 planes del gate pasan A+B**, sus **5 MIDI superan los
gates bloqueantes de capa C**, la **capa D fue aprobada por el usuario**
(2026-11-13, "apruebo los midis", acta `APROBACION_CAPA_D.md` sobre los 11
MIDI de la serie oficial). Los pendientes de evidencia quedaron cerrados con
registro: P-01 (tablas fijas declarativas), P-02 (solos: regla R30 + serie
6/6 capa C + capa D aprobada), P-04 (no se crea `decisiones.json`), P-07
parcial (sin regla nueva, comportamiento emergente intacto).

El gate de fase habilitado es `cc-f2-ok`. La Fase 3 (interfaz Guided en
Studio) permanece bloqueada y requiere autorización explícita.

## 2. Arquitectura implementada

La cadena de autoridades de F1 se conserva byte a byte; F2 añade un solo
eslabón nuevo al frente:

```
intención (JSON, usuario)
   │  1. python3 -m control_center automatic INTENCION.json --out DIR
   ▼
control_center/interprete.py   ← NUEVO (7 pasos, puro, trazable)
   │  emite plan.json completo + evidence.resolved[] (regla R×n por decisión)
   ▼
control_center/validador.py    ← F1 (capas A/B; validar(plan, fase=2))
   ▼
control_center/plan_compilador.py  ← F1 (plan → doc.json dark-director/1)
   ▼
scripts/produce.py             ← AUTORIDAD, sin cambios (doc.json único input)
   ▼
dark_director/compilador.py → jazz_engine → forge (MIDI + events.json)
   ▼
capa C (validador.verificar_capa_c sobre events.json) → capa_c.json
```

El intérprete implementa los 7 pasos de la decisión C-02 (§3/§7 de la spec),
sin duplicar validación (la validación vive en el contrato):

1. **Parse/normalizar** — `_normalizar_intencion`: vocabulario de intención
   (controles con acentos, `null` = auto), rechazo de claves desconocidas.
2. **Identidad + protagonista** — catálogo cerrado (3 recetas reales),
   protagonista melódico, derivación de seed (`derivar_seed`, §9.2).
3. **Armonía** — `language` por carácter armónico (tabla R5/R6), tonalidad por
   seed dentro del pool que pasa V110, progresiones con patrones modales
   derivados del ancla (reutiliza `_vecinas`/`_tonos_acorde` del validador:
   cero duplicación, cero drift).
4. **Forma + secciones + curva de energía** — plantillas `cancion`/`ciclos`/
   `libre`, reparto de compases, curva de energía con saltos ≤0.4 en `cancion`
   (V115), negocición bars↔bpm registrada en `evidence`.
5. **Temas/motivos/solos** — R30: el intérprete no declara solos automáticos
   del lead (hallazgo P-02); solos de protagonista no-lead permitidos.
6. **Orquestación + densidad + drums** — perfil por energía/drums (P-06:
   `original` excluido), escalera drums off→air→light→groove→heavy por sección.
7. **Emitir Plan y validar** — re-resolución ≤2 con capa B fallando, campos
   `locked` intocables durante la re-resolución (§9.1), `ErrorIntencion`
   explicativo si es irresoluble.

Determinismo (§7.2.3): el intérprete es puro — mismos controles + misma seed ⇒
mismo `plan.json`; la fecha vive solo en `evidence.created_at` (inyectada por
parámetro `ahora` en tests). Seed automática (§9.2): sin seed aportada, se
deriva determinísticamente de identidad+controles (sha256 truncado a 8 hex →
[1, 999983]), se persiste en `plan.seed` → `doc.global.seed` → `evidencia.json`.

CLI (`control_center/cli.py`, comando nuevo `automatic`):
`automatic` (intención → plan → doc → canción + capa C), `validar` (A/B),
`compilar` (validar + compilar, sin producir). `--no-producir` y `--no-events`
disponibles. La producción invoca a `scripts/produce.py` **sin `--seed`** (la
seed viaja en `doc.global.seed`, §13) vía subprocess, sin importar produce.py.

## 3. Archivos creados/modificados

**Nuevos (código de fase):**

| Archivo | Líneas | Contenido |
|---|---|---|
| `control_center/interprete.py` | 1.175 | Intérprete de 7 pasos, reglas R0–R30, tablas fijas P-01 |
| `tests/control_center/test_interprete.py` | 518 | 46 tests unitarios/integración del intérprete |
| `tests/control_center/test_golden_automatic.py` | 94 | 3 doradas Automatic (L1 plan+doc+MIDI, capa C) |
| `tests/control_center/test_flujo_automatic.py` | 133 | Flujo por CLI real: intención→canción, L1, exit codes |
| `tests/control_center/golden_f2/` (9 JSON) | 656 | Fixtures: intenciones, planes congelados, metas sha256 |
| `scripts/f2_evidencia.py` · `scripts/f2_preparar_golden.py` | 274+ | Herramientas de evidencia de sesión (gate, P-01, P-02, índice; congelado de doradas) |
| `output/plan_f2/*` | producción | 11 canciones + índices + registros P |

**Modificados (F1):**

| Archivo | Cambio | Justificación |
|---|---|---|
| `control_center/cli.py` | +106/−9 | Subcomando `automatic` (§12.1 lo ordena); `validar`/`compilar` intactos en semántica |
| `control_center/validador.py` | +34/−20 | `validar(plan, *, fase=None)` con `FASE_ACTUAL=2`; el gate de F1 (rechazo de `automatic` en fase=1) queda íntegro y testado — ajuste de interfaz interna justificado, ningún criterio de capa A/B debilitado |
| `control_center/README.md` | +43/−8 | Documentación F2 (uso, límites, P-registros) |
| `control_center/__init__.py` | +15/−9 | Exporta `interprete`; versión de fase |
| `tests/control_center/test_validador.py` | +12/−3 | Tests evolucionados: fase=1 rechaza `automatic`, fase=2 legal, fase desconocida sigue en `ValueError` — los gates que probaban "F2 no existe" pasan a probar "F2 existe, F3 no" |

**Sin cambios (verificado con `git diff 50fcfdf..HEAD`):**
`scripts/produce.py`, `dark_director/**`, `jazz_engine/**`, `forge/**`,
`web/**`, `studio/**`, `album/**`, `esquema_plan.py`, `plan_compilador.py`.

## 4. Decisiones técnicas relevantes

1. **P-01 → tablas fijas declarativas (cerrado).** El intérprete resuelve con
   reglas R0–R30 citadas en cada entrada de `evidence.resolved[]`. Evidencia
   `p01_series.json`: 23 combinaciones de control × 3 seeds = 69 resoluciones,
   **0 fallos A/B**; los bloques estructurales (perfil, bpm, bars, nº de
   secciones, energía máxima, densidad media, niveles de drums) son estables
   entre seeds para el mismo control; solo `harmony.key` y `title` varían por
   seed — campos declarados como variables (§7.2.3 no exige inmutabilidad de
   la tonalidad, exige mismo input ⇒ mismo plan).
2. **Seed automática determinista (R0, §9.2).** `seed = 1 + sha256(identity
   +controls)[:8] mod 999983` — el intérprete es puro incluso sin seed
   aportada; fijarla en la intención (Advanced) cambia el resultado de forma
   controlada (testado).
3. **Hallazgo spec↔recetas y resolución (armonía, R8).** Las tablas
   PROGRESIONES de las 3 recetas N1 contienen calidades funcionales (IV maj9
   dórico, V9 con sensible, iim7b5, bVI13) que no pasan el criterio de
   vecinas de la capa A en ninguna tonalidad menor — verificado
   programáticamente (0 de 12 menores × 3 lenguajes × 3 recetas); el ancla de
   la casa usa progresiones manuscritas distintas de su receta. Alternativas
   analizadas: (a) debilitar el gate — **rechazada**, una ampliación de gate
   exige registro L4 (§11.3) y no hay evidencia de escucha que lo pida;
   (b) instanciar y ajustar calidades — inventaría vocabulario. **Resolución**:
   el intérprete declara progresiones con **patrones modales derivados del
   propio ancla** (offsets [0,3,5,7,8] sobre la tónica con m9/m11/maj7/maj9/
   7sus4/add9 — todo-diatónicos, verificados en las 14 grafías menores),
   mismas funciones armónicas, menos tensiones cromáticas. Las recetas siguen
   alimentando la producción para los types no declarados:
   `dark_director/compilador.py` intacto.
4. **P-02 → regla R30 (cerrado).** Hallazgo: un solo del lead sax declarado en
   el plan puede quedar vacío (`improv.py:18` trata el silencio como decisión;
   probabilidad de frase en break = density × 0.5). Serie 1: C4s falló en
   2/2 solos de sax declarados. Resolución: el intérprete no declara solos
   automáticos del lead (R30); el protagonismo queda garantizado por V113
   (focus en ≥2 secciones) y el `section_plan` del motor. Solos de
   rhodes/vibraphone fiables (6/6 capa C). El solo del sax queda como acto
   Advanced (`solos[]`), con el hallazgo documentado.
5. **P-04 → no se crea `decisiones.json` (cerrado).** Cada decisión se explicó
   desde `plan.json` + `evidence.resolved[]` + `events.json` + `capa_c.json`.
   El diagnóstico del hallazgo P-02 se hizo sin log adicional.
6. **P-06 → `original` excluido del Automatic.** El perfil sin `jazz_engine`
   no es seleccionable por el intérprete (§4); sigue disponible en Advanced.
7. **Bloqueo `locked` real (§9.1, primera prueba).** Las secciones con
   `locked: true` aportadas en la intención se respetan tal cual; la
   re-resolución aplica ajustes dirigidos solo a secciones no-locked (V112
   pico de energía, V113 protagonista/solo, V115 saltos, V111 drums —
   matriz de re-resolución ≤2, §12.1); dos locked irreconciliables o un solo
   sobre sección locked → `ErrorIntencion` explicativo (testado).

## 5. Tests ejecutados y resultados reales

Comandos (repo `nucleo_engine_project/`, 2026-11-13):

```bash
python3 -m pytest tests/control_center/ -q        # 138 passed, 53 subtests passed (2.42s)
python3 -m pytest tests/ -q                       # 509 passed, 3 skipped, 71 subtests passed (26.59s)
python3 -m pytest tests/control_center/test_interprete.py -q   # 46 passed, 2 subtests
python3 -m pytest tests/control_center/test_golden_automatic.py tests/control_center/test_flujo_automatic.py -q   # 7 passed, 6 subtests
python3 manifests/verificar_golden.py             # VERIFICACION GOLDEN: OK (34 archivos congelados)
```

**Baseline → cierre**: el tag `f2-pre` (pre-F2) tenía **456 passed**; el
cierre tiene 509: **+53 tests** (46 de `test_interprete.py` + 5 E2E del CLI +
2 golden con sus 6 subtests). Tags disponibles: `cc-pre` (pre-F1), `f2-pre`
(pre-F2).

Cobertura específica F2 (46 tests del intérprete, selección): determinismo del
resolver; seed automática persistida y reproducible; seed explícita cambia el
resultado de forma controlada; fecha solo en `evidence`; fórmula `inputs_hash`
(§9.3); plan completo sin `null` ni `"auto"`; bloqueo real de `locked` (3
tests); re-resolución ≤2 con suavizado correcto; protagonista en ≥2 secciones;
solo automático solo de protagonista no-lead (R30); energía muy alta exige
pico; drums ausente/protagonista coherentes; intención inválida →
`ErrorIntencion` con mensaje accionable (12 casos negativos: estilo fuera de
catálogo, protagonista no melódico, control desconocido, seed negativa,
palette con `original`, key+progresiones incompatibles, forma irresoluble…).

Los 3 skipped del total son de fases previas del proyecto (no tocan F2;
mismo recuento que antes de F2: nada se omitió por F2).

## 6. Evidencia de determinismo

1. **Intérprete puro**: `resolver()` dos veces sobre la misma intención ⇒
   planes idénticos (test `test_determinismo_del_resolver_sobre_las_doradas`
   + `test_mismo_input_mismo_plan`); único campo no determinista
   `evidence.created_at`, inyectado por parámetro y excluido en los golden.
2. **Seed automática reproducible**: intención sin seed ⇒ seed derivada de
   identidad+controles (misma intención ⇒ misma seed; demo en vivo:
   intención de `/tmp/intencion_demo.json` → **seed 436439**).
3. **Plan → doc → MIDI (L1)**: el golden recompila los 3 planes congelados y
   reproduce `sha256_doc` y `sha256_midi` exactos (meta_101/202/303.json);
   verificar_golden: 34 archivos congelados OK.

| Dorada | Identidad | Seed | Key | Perfil | sha256_doc (16) | sha256_midi (16) |
|---|---|---|---|---|---|---|
| f2_101 | dark_triphop/sax | 101 | F minor | full | `830fd451a77f65ba` | `34a5d4c93738ab7e` |
| f2_202 | doom_dark_jazz/rhodes | 202 | Bb minor | atmospheric | `7badba8597306702` | `e09752bbbb836535` |
| f2_303 | doom_triphop/vibes | 303 | D# minor | full | `1efcfadb7000ebf8` | `8540d2fbc9537c27` |

4. **CLI E2E**: misma intención dos veces por `automatic` ⇒ mismo `sha256_midi`
   en `evidencia.json` (test `test_regeneracion_l1_mismo_sha256`).
5. **Verificación en vivo fuera de la suite** (comando y resultado real):
   ```bash
   python3 scripts/produce.py output/plan_f2/f2_101_dark_triphop/doc.json \
           --production full --out /tmp/f2_regress_101
   # sha256 MIDI regenerado: 34a5d4c93738ab7e  ==  original 34a5d4c93738ab7e  (L1 IDENTICO)
   ```
   Nota: produce sin `--seed`; la seed (101) viaja en `doc.global.seed`
   (`produce.py:95-96`) y queda registrada en `evidencia.json`.

## 7. Golden F1 y regresiones

```bash
python3 scripts/produce.py output/plan_f1/ancla_demo_medianoche/doc.json \
        --production full --out /tmp/f1_regress
# sha256 regenerado: 32199acc254a2eeff93a12d15df3b38ec2c541a45a10a4719d493c696b29a9ff
# sha256 esperado  : 32199acc254a2eeff93a12d15df3b38ec2c541a45a10a4719d493c696b29a9ff  (L1 IDENTICO)
```

- Ancla F1 (`demo_medianoche`, seed 3113): **idéntica tras F2** en su doble
  nivel: compilación byte-idéntica (doc sha256 `b2399cc5…93b90f`, test
  `test_compilador_golden.py`) y MIDI L1 regenerado sin `--seed`
  (`32199acc…a9ff`, comando arriba).
- Los 3 planes manuales de F1 (101/202/303) siguen pasando A/B (tests verdes;
  solo 2 tests evolucionados declarados en §3, que pasan de probar "F2 no
  existe" a probar "F2 existe, F3 no").
- Suite completa del proyecto: 509 passed (baseline `f2-pre` 456 + 53 nuevos;
  los 3 skipped son pre-F2).
- `git diff f2-pre..HEAD -- scripts/produce.py dark_director/ jazz_engine/ forge/ web/ studio/ album/` → vacío (autoridades intactas).
- Nota de entorno: el sandbox restaurado alteró bits de permisos de algunos
  archivos (solo metadatos, cero contenido — verificado con `git diff --numstat`);
  permisos restaurados y hashes re-verificados en disco.

## 8. Ejemplos reales intención → Plan → doc → MIDI

**Ejemplo A — intención con controles completos (tema del gate, seed fijada por test):**

```bash
# intención (tests/control_center/golden_f2/intencion_101.json):
#   identity: dark_triphop / balanced / sax_tenor
#   controls: energia=media, forma=cancion, duracion=corta,
#             armonia=nocturno, pulso=swing, drums=presente; seed 101
python3 -m control_center automatic tests/control_center/golden_f2/intencion_101.json \
        --out output/plan_f2/f2_101_dark_triphop
# → CAPA A/B: OK · plan resuelto (seed 101 persistida) · doc dark-director/1
#   · MIDI · capa C: OK (7 gates bloqueantes)
```

Resultado real (`plan.json` → "Bruma Lenta"): perfil `full`, bpm 80, F minor,
language `pop_dream_pop`, 50 compases (intro 8/air · verse 13/groove ·
pre_chorus 6/light · chorus 15/heavy · outro 8/air), fade-out, `solos: []`
(R30). `doc.json` sha256 `830fd451a77f65ba3fcb4dcd…`; MIDI sha256
`34a5d4c93738ab7e…`; 150.0 s; 12 decisiones trazadas en `evidence.resolved[]`
(con regla R y entrada de cada una).

**Ejemplo B — intención mínima con seed automática (demo en vivo, sin seed):**

```bash
cat > /tmp/intencion_demo.json <<'EOF'
{
  "identity": {"style": "doom_triphop", "accessibility": "balanced",
               "protagonist": "vibraphone"},
  "controls": {"energia": "baja", "forma": "ciclos", "duracion": "media",
               "drums": "contenida"}
}
EOF
python3 -m control_center automatic /tmp/intencion_demo.json \
        --out output/experimentos/f2_demo_autoseed
# → seed 436439 derivada y persistida · doc dark-director/1 · MIDI 300.0 s
#   (bpm 72, 90 compases) · capa C: OK → sha256(16) 8432b3854bf4598d
```

**Ejemplo C — intención total, todo automático, sin seed ni título (del gate):**

```bash
python3 -m control_center automatic output/plan_f2/intenciones/f2_auto_total.json \
        --out output/plan_f2/f2_auto_total
# → seed auto-derivada 320569 · "Alba Tardía" · full · C# minor · 86 BPM ·
#   108 compases · 301.4 s · capa C OK · MIDI sha256(16) af57c752252d4280
```

Otros comandos reales del gate (con intención en `output/plan_f2/intenciones/`):
f2_303_doom_triphop (alta/ciclos/crudo/recto/drums protagonista, seed 303 →
D# minor, solo de vibraphone, 8540d2fb…) y f2_ausente_jazz_media (drums
ausente → perfil sin drums `sax_rhodes`, todas las secciones `off`,
ae985dba…). Cada carpeta de canción contiene la cadena co-localizada completa
(P-05): plan.json + doc.json + config_efectiva.json + .mid + evidencia.json +
events.json + capa_c.json, con `evidence.resolved[]` de ~12-18 entradas
{campo, regla R0-R30, entrada, detalle}.

**Ejemplo D — intención inválida (rechazo accionable):**
estilo desconocido → `ERROR: … identity.style` y exit 1 **sin escribir
archivos** (test `test_intencion_invalida_exit_1_sin_archivos`).

Índice completo de la serie: `output/plan_f2/INDICE.md` (5 gate + 6 P-02, con
hashes y capa C). Acta de escucha: `output/plan_f2/APROBACION_CAPA_D.md`.

## 9. Limitaciones y deuda técnica

1. **Avisos C4b no bloqueantes** en 3 de los 5 temas del gate (focus de una
   sección sin notas: silencio = decisión de `improv.py:18`). Diagnóstico, no
   gate; cubiertos por la capa D aprobada. Quedan como advertencia conocida
   (heredada de F1, `vapor_y_neon_303`).
2. **Solo del lead sax solo vía Advanced** (`solos[]`): el intérprete no lo
   declara (R30) porque puede salir vacío (P-02, hallazgo en código
   `improv.py`/`profiles.py` — probabilidad de frase en break = density × 0.5).
   Cualquier mejora pertenece a `jazz_engine/improv.py` (fuera del alcance de
   F2: no se toca el motor).
3. **Tonalidad y título son los únicos campos variables entre seeds** para la
   misma intención (decisión P-01); el resto es estable. Si en F3+ se quiere
   variación musical mayor, es una decisión de spec, no un bug del intérprete.
4. **P-07 parcial**: transiciones entre secciones sin promesa MVP; el criterio
   de recuperación (≥2 canciones con transición=0 en escucha) no se activó en
   la capa D aprobada; queda observación disponible para F3-F5.
5. **Vocabulario del intérprete acotado a los catálogos cerrados** (3
   identidades, 6 perfiles con motor, modo menor). Ampliar vocabulario no es
   MVP (D-15, §15).
6. **`scripts/f2_evidencia.py` / `f2_preparar_golden.py`** son herramientas de
   sesión con rutas absolutas del sandbox (`ROOT=/home/z/my-project/
   nucleo_engine_project`); sirven para regenerar la evidencia en este
   entorno, no son parte del paquete de fase.
7. La aprobación de capa D fue registrada como **veredicto global** del
   usuario sobre la serie (mismo patrón que el acta de F1), no como puntación
   13-dimensiones por tema; el protocolo `PROTOCOLO_ESCUCHA.md` queda como
   plantilla para escuchas comparadas futuras (F3+). El usuario además
   **iteró los 11 MIDIs en Suno** y aprobó el material iterado (patrón F1) —
   refuerzo registrado en el acta.
8. **Bug latente heredado (fuera de F2)**: `validador._vecinas` excluye la
   tonalidad paralela por comparación de grafía en claves MAYORES — sin
   impacto en F2 (el pool del intérprete es menor; los docs de la casa están
   en menor), documentado para F5, no se tocó (no es código de fase).
9. **Color dórico pendiente de decisión L4**: si algún día se quiere el IVmaj9
   de las recetas en el intérprete, es una ampliación de gate con registro L4
   documentado (escucha primero, §11.3).
10. **Cosmético**: la instanciación de acordes usa la tabla de bemoles de la
   casa (`_instanciar_simbolo`): en tonalidades sostenidas el doc muestra
   `Db7sus4` donde un músico escribiría `C#7sus4` — pc-correcto y parseable.
11. **`title`/`notes` automáticos**: metadata generada sin consumidor musical;
    el banco de títulos es pequeño (10 por identidad).

## 10. Estado de F2: completada

| Gate §16.2 F2 | Resultado |
|---|---|
| 5/5 planes pasan A+B | OK |
| 5 MIDI superan gates bloqueantes de C | OK (métricas en `capa_c.json`) |
| Escucha D ≥8/13 dim ≥1 | APROBADA por el usuario (2026-11-13, acta; veredicto global sobre la serie §9.7, reforzada por iteración de los 11 MIDIs en Suno) |
| P-01/P-02/P-04 cerradas, P-07 parcial | OK (registros en `REGISTROS_PENDIENTES.md`) |
| Determinismo (mismo input ⇒ mismo plan; L1 doc/MIDI) | OK (secciones 6-7) |
| Seed automática persistida y reproducible | OK (test + demo 436439) |
| Bloqueo real de `locked` (§9.1) | OK (3 tests) |
| Sin regresiones F1 (ancla L1 + suite) | OK (sección 7) |
| Rollback F2 (≥2 canciones con capa C rota) | No aplicó — 0 capas C rotas en la serie |

**Estado: FASE 2 COMPLETADA. Gate `cc-f2-ok` habilitado.**
Próxima fase del roadmap (§12): **Fase 3 — Interfaz Guided en Studio**, única
fase que toca archivos de UI existentes. Permanece **bloqueada** hasta nueva
autorización explícita del usuario.

**Rollback de F2 (§14, si alguna vez hiciera falta)**: borrar
`control_center/interprete.py` + revertir `cli.py`, `validador.py`,
`__init__.py`, `README.md` y los 2 tests evolucionados (commit `f2-pre` como
punto de retorno) — ningún motor ni artefacto pre-F2 afectado.

Comandos de reproducción rápida (repo `nucleo_engine_project/`):

```bash
python3 -m pytest tests/control_center/ -q
python3 -m control_center automatic tests/control_center/golden_f2/intencion_101.json \
        --out /tmp/rp_101 && python3 -m pytest tests/control_center/test_golden_automatic.py -q
python3 manifests/verificar_golden.py
```
