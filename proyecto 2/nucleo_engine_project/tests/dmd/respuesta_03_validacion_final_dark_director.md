# RESPUESTA 03 — VALIDACIÓN FINAL DE CONSISTENCIA · `dark-director/1` (rev. 3)

> Fecha: 2026-11-07 · Instrucción 05 · Estado: **contrato rev. 3 — referencia única de implementación**
> Entrada: `respuesta_02_cierre_tecnico_dark_director.md` (rev. 2) + `auditoria_dark_music_director.md` (evidencia de motor).
> Alcance conservado: arquitectura de compilador upstream, las 10 decisiones aprobadas, el alcance v1 y **todas** las funcionalidades de la rev. 2.
> **No se agregó capacidad nueva. No se implementó código de proyecto. No se tocó `forge/`.**
> Este documento **sustituye** a la rev. 2 como referencia; la rev. 2 queda como antecedente. Notación: H.1/H.2/H.3 = ejemplos §5.1/§5.2/§5.3.

---

## 0. RESUMEN EJECUTIVO

Se aplicaron las 6 correcciones de consistencia exigidas. Resultado:

1. **Contradicción de W410 en H.1 resuelta actualizando los avisos** (el JSON no cambia): el sax usa frases (`chorus_1`) y motivo copiado (`chorus_2`), así que `instruments.sax_tenor.density` no es aplicable en esos dos bloques → **2 × W410** documentados y coherentes con §2.6.5.
2. **Tensión y resolución separadas por invariante**: la tensión solo traduce a voicings, `pad.tension` y `strings.modes`; la resolución se define exclusivamente por su cadena de precedencia (§2.4) y ningún otro campo la selecciona, modifica ni sugiere.
3. **Colisión de E106 eliminada**: E106 queda reservado a `structure` inválida; los símbolos de acorde no parseables pasan al nuevo código **E113**. Todas las referencias y tablas actualizadas.
4. **Fallback de `chromatic` corregido**: matriz de exclusividad por estrategia en §2.4 — `chromatic` jamás aplica split; `tonal`/`deceptive` jamás añaden gestos de bajo ajenos. W420/W421 redefinidos por estrategia.
5. **Density con fórmula determinista de coexistencia** (§2.6.5): la declaración por instrumento fija la **base** y la desviación de la sección aporta la **evolución musical**; los operandos son solo campos del contrato y defaults de receta, y la salida entra en la misma tabla de traducción con parámetros reales del motor.
6. **`beat` definido como 0 ≤ beat < 4** y las notas escritas deben terminar dentro de su sección (`bar·4 + beat + dur ≤ bars·4`, E111). Las copias de motivo se recortan (W407); las notas del compositor que sobrepasan son inválidas.

**Verificación ejecutada** (§8 — comprobación **documental** + parseo/validación JSON de los ejemplos; **no es una verificación de código fuente**): 3/3 ejemplos parsean y cumplen la rev. 3 con 0 errores; avisos esperados recomputados por regla y coincidentes (H.1: 4 · H.2: 3 · H.3: 1); 27/27 combinaciones aceptadas (9 con W411 informativa); 0 códigos con significado múltiple.

---

## 1. REGISTRO DE CAMBIOS (rev. 2 → rev. 3)

| # | Corrección exigida (instr. 05) | Aplicación en esta revisión |
|---|---|---|
| 1 | Resolver la contradicción de W410 en H.1 (el sax usa frases y motivos; su density no aplica en esos bloques) | **§5.1: avisos actualizados** (opción "actualizar avisos"): 2 × W410 — uno por `chorus_1` (frases propias) y uno por `chorus_2` (motif copiado). El JSON de H.1 no cambia y el ejemplo gana valor: demuestra a la vez la fórmula de coexistencia (corrección 5) y la regla de material escrito. **§2.6.5**: disparador de W410 precisado — un aviso **por sección** con bloque efectivo de material escrito, no un aviso global. |
| 2 | Separar tension de resolution | **§2.6.6 reescrita**: la tensión traduce solo a voicings / `pad.tension` / `strings.modes`; eliminada la cláusula que añadía una resolución en banda B3. **§2.5**: la resolución deja de listarse como "dispositivo de tensión". **§2.1.2**: el ajuste de la combinación `experimental` × `pop_dream_pop` ya no menciona resoluciones. **§3.4**: fila `tension` anotada. Invariante: la resolución de cada transición es **exclusivamente** el resultado de la cadena §2.4. |
| 3 | Eliminar la colisión de E106 | **E106 queda solo para `structure` inválida** (< 2 secciones o ids duplicados). Nuevo código **E113**: símbolo de acorde no parseable por la gramática de `theory.parse_chord`. Referencias actualizadas: §2.10 (tabla E1xx), §3.2 (`harmony.progressions`), §3.4 (`chords`), §4 (contadores). Un acorde que parsea pero queda fuera del vocabulario del `language` sigue siendo **W414** (se respeta), no E113. |
| 4 | Corregir el fallback de chromatic | **§2.4**: nueva matriz de **exclusividad de mecanismos por estrategia** (qué usa cada estrategia: split armónico y/o gesto de bajo) + regla vinculante: los fallbacks solo suprimen o informan, nunca añaden mecanismos de otra estrategia. Tabla de fallbacks reescrita **por estrategia**: con bass inactivo, `tonal` mantiene el split y omite el approach (W421); `chromatic` omite su gesto completo y no aplica split alguno; `deceptive`/`modal`/`open` no emiten W421. **W420** restringida a estrategias con split. Distingue con claridad `tonal` (split + approach), `deceptive` (solo split) y `chromatic` (solo gesto de bajo). |
| 5 | Precedencia de density con coexistencia | **§2.6.5**: nueva **fórmula determinista** `density_efectiva = clamp(base + desviación, 0, 1)` — la base es la density por instrumento (o la receta) y la desviación es `structure[].density − receta`; las dos configuraciones coexisten y la evolución musical entre secciones se conserva. Propiedades 1–5 demostradas. **§2.3** (excepción 3) reescrita; **§3.3/§3.4** filas `density` actualizadas; **§5.1** nota de demostración reescrita. La salida usa exclusivamente parámetros reales confirmados del motor (misma tabla de traducción). |
| 6 | `beat` como 0 ≤ beat < 4 y notas dentro de la sección | **E111** redefinida: `beat` ∈ [0, 4) (4.0 es el beat 0 del compás siguiente, inválido) + nueva condición `bar·4 + beat + dur ≤ bars·4` (tolerancia 1e−6). **§2.7.1**: las notas copiadas se recortan al final del destino (W407); las notas escritas que sobrepasan el final de su sección son inválidas (E111). **§3.5**: fila de frases actualizada. **§2.2**: comentario del contrato. |

### 1.1 Precisiones derivadas del criterio "avisos exactos" (transparencia)

Estos tres ajustes no provienen de los 6 puntos, pero son necesarios para cumplir la verificación *"los avisos esperados deben coincidir exactamente con las reglas"*; se registran explícitamente.

| # | Precisión | Justificación |
|---|---|---|
| A.1 | **Disparador de W412 precisado** (§2.4/§2.10): solo avisa si la resolución está **declarada explícitamente** en la última sección (`structure[].resolution`). Las resoluciones heredadas (global o default del `language`) no avisan: sin sección siguiente el mecanismo de transición no se invoca. | La redacción de rev. 2, aplicada literalmente, dispararía W412 en el 100 % de los proyectos (la resolución siempre tiene un valor efectivo) — una advertencia universal no informa de nada — y contradecía los avisos de los tres ejemplos de la propia rev. 2. Sin cambio de comportamiento en los ejemplos; sin capacidad nueva. |
| A.2 | **Avisos de los 3 ejemplos recalculados con exactitud** contra las reglas (nuevo §5.0 con supuestos de receta): H.1 pasa de "ninguno" a **W403 + 2×W410 + W421**; H.2 añade **W403**; H.3 queda igual (W418). | W403 (vibráfono en banda B3 con `mallet_sparse` ON) y W421 (approach del bajo omitido en `break_1 → outro`) ya estaban exigidos por reglas de rev. 2 que rev. 2 no listó al anotar los ejemplos. Se corrigen los avisos, no las reglas. |
| A.3 | **Coherencia interna de H.1**: `instruments.sax_tenor.register` [62, 84] → **[60, 84]**. | La frase escrita de H.1 contiene C4 (MIDI 60), que el registro declarado excluía — riesgo documentado de `lead_mono_range` (§7.5) sin que exista regla de contrato que lo cubra (las frases son passthrough del compositor). Se corrige el ejemplo, no se añaden reglas nuevas. |

### 1.2 Impacto por sección

| Sección | Estado en rev. 3 |
|---|---|
| §2.1, §2.1.1 (modelo y 27 combinaciones) | sin cambios |
| §2.1.2 (ajustes atípicos) | fila `experimental`×`pop_dream_pop` sin selección de resolución |
| §2.2 (contrato de un vistazo) | comentario de frases (beat y fin de sección) |
| §2.3 (precedencia general) | excepción 3 reescrita por la fórmula de density |
| §2.4 (armonía) | matriz de exclusividad + fallbacks por estrategia + W412 precisada + precisión de ciclado de acordes |
| §2.5 (instrumentos) | dispositivos de tensión sin la resolución |
| §2.6.1–§2.6.4 | sin cambios |
| §2.6.5 (density) | fórmula de coexistencia + disparadores de W410 |
| §2.6.6 (tension) | reescrita: eje independiente |
| §2.7, §2.7.1 | nota de recorte (W407) frente a nota inválida (E111) |
| §2.8, §2.9, §2.11, §2.12 | sin cambios |
| §2.10 (taxonomía) | E106 acotado; E113 añadido; E111 redefinida; W410/W412/W420/W421 actualizadas |
| §3 (tabla de campos) | filas `progressions`, `chords`, `density` (×2), `tension`, frases |
| §4 (tabla de códigos) | E1xx = E101–E113 (13); definiciones actualizadas |
| §5 (ejemplos) | §5.0 nuevo (supuestos); avisos exactos; register de H.1; nota de H.3 |
| §6, §7 | sin cambios (se reproducen por autocontención) |
| §8, §9 | verificación rev. 3 |

---

# 2. ESPECIFICACIÓN CORREGIDA COMPLETA — `dark-director/1` (rev. 3)

> Contrato declarativo y compacto. El compilador (futuro `dark_director/compiler.py`) lo expande a un proyecto
> explícito `midi-forge/1`. Sin tocar `forge/`, sin phrasegen, sin presets nuevos, sin swing, sin escala por sección.

## 2.1 Modelo de tres dimensiones (ortogonalidad total)

| Dimensión | Campo | Controla | NO controla |
|---|---|---|---|
| **Identidad** | `direction.identity` | sonido y tiempo: BPM típico, groove, timbres, instrumentación base, peso armónico | la familiaridad de la escritura ni el vocabulario de acordes |
| **Accesibilidad** | `direction.accessibility` | escritura y desarrollo: previsibilidad melódica, hooks, dispositivos de tensión, guardrails de repetición | el tempo, el groove ni el vocabulario de acordes |
| **Lenguaje armónico** | `harmony.language` | vocabulario de acordes disponible (qué acordes existen) | cómo se escriben las líneas ni cómo suena el conjunto |

**Las 27 combinaciones (3×3×3) son válidas y aceptadas. Ninguna produce error.** Las poco convencionales emiten
la recomendación **W411** y se compilan con los ajustes del §2.1.2.

**Invariantes del compilador (obligatorios)**:
- Nunca reescribe `direction.identity`, `direction.accessibility`, `harmony.language` ni **ningún** campo declarado por el compositor.
- Nunca activa instrumentos deshabilitados.
- Los ajustes por combinación atípica solo llenan silencios (valores que el compositor no declaró); si existe declaración explícita, manda la declaración (precedencia §2.3).

### 2.1.1 Tabla de las 27 combinaciones

✓ = convencional (sin aviso) · **W411** = válida + recomendación informativa.

| Identidad | Accesibilidad | `pop_dream_pop` | `hybrid` | `experimental` |
|---|---|---|---|---|
| `dark_triphop` | `balanced` | ✓ | ✓ | ✓ |
| `dark_triphop` | `commercial` | ✓ | ✓ | **W411** |
| `dark_triphop` | `experimental` | **W411** | ✓ | ✓ |
| `doom_triphop` | `balanced` | ✓ | ✓ | ✓ |
| `doom_triphop` | `commercial` | ✓ | ✓ | **W411** |
| `doom_triphop` | `experimental` | **W411** | ✓ | ✓ |
| `doom_dark_jazz` | `balanced` | **W411** | ✓ | ✓ |
| `doom_dark_jazz` | `commercial` | **W411** | **W411** | **W411** |
| `doom_dark_jazz` | `experimental` | **W411** | ✓ | ✓ |

**Regla determinista de W411** (los únicos 4 pares atípicos; una celda es atípica si alguno de sus pares lo es):
- identidad × accesibilidad: `doom_dark_jazz` × `commercial`
- accesibilidad × lenguaje: `commercial` × `experimental` · `experimental` × `pop_dream_pop`
- identidad × lenguaje: `doom_dark_jazz` × `pop_dream_pop`

Resultado: 18 celdas convencionales, 9 con W411, 27 aceptadas. W411 es **informativa**: no modifica valores, no bloquea, no aparece en `qa.strict`.

### 2.1.2 Ajustes para combinaciones atípicas (solo llenan silencios)

| Combinación atípica | Ajuste del compilador (si el compositor no declaró lo contrario) |
|---|---|
| `doom_dark_jazz` + `commercial` | hooks = motivos instrumentales escritos (no exige forma pop ni chorus cantable); familiaridad solo en la escritura |
| `commercial` + `language: experimental` | los hooks se escriben sobre el vocabulario alterado disponible; la sorpresa armónica la aporta el `language` |
| `experimental` + `language: pop_dream_pop` | ambigüedad vía voicings (`rootless`/`bare`/`open4`) y silencios; sin acordes alterados; **la resolución sigue su propia cadena (§2.4): este ajuste no la selecciona ni la cambia** |
| `doom_dark_jazz` + `language: pop_dream_pop` | jazz lento con vocabulario consonante; el carácter lo dan identidad y desarrollo |

**No confundir**: armonía experimental ≠ desarrollo experimental; armonía familiar ≠ composición comercial.

## 2.2 El contrato de un vistazo

```jsonc
{
  "schema": "dark-director/1",              // requerido
  "meta": { "title": "...", "notes": "..." },          // opcional (metadato)
  "direction": {
    "identity": "dark_triphop|doom_triphop|doom_dark_jazz",      // requerido
    "accessibility": "commercial|balanced|experimental"          // requerido
  },
  "global": { "bpm": 86, "seed": 11, "humanize": 1.0, "velocity_cap": 110 },  // opcional
  "harmony": {
    "key": "D minor",                        // requerido (tónica + modo del motor)
    "language": "pop_dream_pop|hybrid|experimental",               // requerido
    "resolution": "tonal|modal|deceptive|chromatic|open",          // opcional (default: language)
    "harmonic_rhythm_bars": 1,               // opcional 1–8 (default: receta)
    "progressions": { "verse": ["Dm9"], "theme_a": ["Dm7b5:2"] }   // opcional; clave = type o id
  },
  "instruments": {                           // opcional; defaults por identidad
    "<inst_id>": { "enabled": true, "register": [62, 84], "density": 0.4,
                   "mix": { "volume": 100, "pan": 72, "reverb": 100, "chorus": 30, "brightness": 80 } }
    // density: base por instrumento según fórmula §2.6.5; traducción solo en
    // sax_tenor, rhodes, piano, vibraphone; en bass/drums/pad/strings → W410
    // bass admite además "type": "finger" | "upright"
  },
  "structure": [                             // requerido, ≥ 2 secciones
    { "id": "chorus_1", "type": "chorus", "bars": 16,     // requeridos
      "energy": 0.8, "tension": 0.5, "density": 0.65,    // 0..1, opcional (default: receta)
      "focus": ["sax_tenor", "drums"],                   // protagonismo, en orden (0–3, §2.6.4)
      "active": ["sax_tenor", "rhodes", "bass", "drums", "pad"],  // whitelist de la sección
      "drums": "off|air|light|groove|heavy",             // nivel semántico
      "chords": ["Dm9"], "chord_bars": 2, "resolution": "deceptive",  // overrides
      "final": true, "loop_bars": 8 }
  ],
  "development": {                           // opcional
    // frases: bar 0..bars-1, beat 0 ≤ beat < 4; la nota debe terminar dentro de la sección (E111)
    "melody":     { "phrases": { "<section_id>": [ { "bar": 0, "beat": 0, "pitch": "A4", "dur": 1.5 } ] } },
    "motifs":     { "hook_a": { "from_section": "chorus_1", "sections": ["chorus_2"], "loop_bars": 8, "transpose_st": 0 } },
    "responses":  { "vibraphone": { "responds_to": "sax_tenor", "prob": 0.45, "max_per_bar": 2 } },
    "improvisation": [ { "section": "break_1", "instrument": "sax_tenor" } ]
  },
  "ending": {                                // opcional; formato unificado (§2.9)
    "fade_out":  { "enabled": true, "bars": 6 },                  // + "exponent" opcional
    "tape_stop": { "enabled": false, "bars": 2 }                  // + "semitones"/"exponent" opcionales
    // forma abreviada: true → { "enabled": true }
  },
  "qa": { "strict": false, "guardrails": { "lead_coverage": true } }  // opcional (§2.11)
}
```

## 2.3 PRECEDENCIA GENERAL DE CONFIGURACIÓN

Todo valor del proyecto emitido se resuelve por esta escalera; cada nivel **sobrescribe a los anteriores** solo en los campos que controla, y **ningún nivel reescribe una declaración explícita del compositor**:

```
N1  Receta de identidad        (dark_director/identities/<id>.py)
    base sonora: pistas existentes, BPM default, capas de batería por nivel drums,
    sets de bajo, voicings y velocity base por tipo de sección, focus por defecto
N2  Perfil de accesibilidad    (dark_director/accessibility.py)
    escritura: defaults de guardrails (motif_repeat/lead_coverage), tratamiento de hooks,
    inclinación de voicings y dispositivos de tensión. Nunca toca BPM/groove/timbres
N3  global                     (bpm, seed, humanize, velocity_cap)
N4  harmony                    (key, language, resolution, harmonic_rhythm_bars, progressions)
N5  instruments.*              (enabled, register, density, mix, bass.type)
N6  structure[]                (energy, tension, density, focus, active, drums, chords,
                                chord_bars, resolution, final, loop_bars — por sección)
N7  development + ending + qa  (instrucciones explícitas de desarrollo, cierre y validación)
```

**Excepciones y precisiones necesarias**:
1. **Armonía interna (§2.8) prevalece sobre la escalera para acordes**: `structure[].chords` (N6) vence a `harmony.progressions` (N4) y este a la receta (N1). Igual con `resolution`: `structure[].resolution` > `harmony.resolution` > default por `language`. **Ningún campo fuera de esa cadena participa en la resolución** (§2.6.6).
2. **Ejes distintos no compiten**: `focus`/`active`/`energy` (sección) no "vencen" a `instruments.*` (existencias, registro, mezcla); se aplican sobre el resultado de los niveles inferiores.
3. **`density` se combina por fórmula determinista (§2.6.5)**: `instruments.<id>.density` (N5) fija la **base** del instrumento y la desviación de `structure[].density` (N6) respecto a la receta aporta la **evolución por sección**; si solo existe una de las dos, manda la que exista. La fórmula opera solo sobre campos del contrato y defaults de receta.
4. **`qa.guardrails` (N7) sobrescribe los defaults de accesibilidad (N2)**.
5. **W411 y los avisos W4xx nunca cambian valores**: solo informan.
6. **E3xx tolerado (sin `strict`)** sí omite la entrada no soportable — es la única omisión automática, y siempre se reporta (§2.10).

## 2.4 ARMONÍA

| Campo | Función | Traducción al motor |
|---|---|---|
| `key` | tónica + modo | `global.key` vía `theory.parse_key` (11 modos) |
| `language` | vocabulario de acordes | valida/sesga los símbolos que emite el compilador |
| `resolution` | transición al cierre de sección | `chord_overrides.split` + `approach`/slides del bajo |
| `harmonic_rhythm_bars` | duración armónica default | `section.chord_bars` |
| `progressions` | progresión por id o type | `section.chords` |

**Vocabulario por `language`** (gramática = `theory.parse_chord`):
- `pop_dream_pop`: tríadas, 6, add9, maj7, maj9, m7, m9, sus2/4, 7sus4, slash.
- `hybrid`: lo anterior + 9/11/13, m7b5 puntual, 7#11, power.
- `experimental`: todo lo que parsea el motor (7b9, 7#5b9, 13b9, mMaj7, ø, dim7, b5/#5, #9, #11/b13).

**Duración de acordes**: `harmonic_rhythm_bars` global + override por sección (`chord_bars`) + forma compacta `"Bbmaj7:2"` (motor: `engine.py:78-92`). La lista de acordes (explícita o de receta) **cicla** hasta llenar la sección; si la última repetición no cabe entera, el último acorde se recorta a lo que queda → **W417** (determinista). Un símbolo que no parsea → **E113**; uno que parsea fuera del vocabulario → **W414** (se respeta).

### 2.4.1 Resoluciones: mecanismos y exclusividad (corrección 4)

Defaults por `language`: pop→`tonal`, hybrid→`modal`, experimental→`chromatic`. Override por sección permitido.

| Valor | Qué hace el compilador | Mecanismo armónico (split) | Mecanismo de bajo |
|---|---|---|---|
| `tonal` | prepara el dominante en el último compás | **Sí** — `chord_overrides.split` | approach cromático del bajo (token `A`) hacia el acorde siguiente |
| `deceptive` | V→bVI/bVII al cierre | **Sí** — `chord_overrides.split` | ninguno propio |
| `chromatic` | **aproximación cromática de la línea de bajo** al root del acorde siguiente | **No** — la estrategia no incluye split | token `A` del bajo + `slide_in/slide_out` |
| `modal` | cierra sobre acordes del modo, sin sensibles | No | approach desactivado explícitamente |
| `open` | cierre sin resolver (sus/power/pedal) | No | ninguno |

**Regla de exclusividad (vinculante, corrección 4)**: cada estrategia aplica **exclusivamente** los mecanismos de su fila. Los fallbacks (abajo) solo **suprimen** gestos o **informan**; **jamás añaden mecanismos de otra estrategia**: `chromatic` nunca aplica un split armónico; `tonal`/`deceptive` nunca añaden slides; `deceptive` nunca añade approach.

**`chromatic` — aclaración vinculante**: `chromatic` **no promete una resolución armónica completa**. Garantiza únicamente que la línea del bajo se mueve cromáticamente hacia el root del siguiente acorde (aproximación + slide). Los acordes de la sección siguiente son exactamente los que la precedencia determine; el compilador no los altera para "resolver". Si el bajo no suena en la sección de origen, solo se pierde el gesto cromático del bajo (W421) — la progresión suena tal cual.

### 2.4.2 Fallbacks de `resolution` por estrategia y contexto (correcciones 9 y 4)

| Contexto | `tonal` | `deceptive` | `chromatic` | `modal` | `open` |
|---|---|---|---|---|---|
| Última sección, resolución **explícita** en ella | split + approach omitidos; acorde final entero → **W412** | split omitido → **W412** | gesto cromático omitido → **W412** | sin gesto propio; declaración explícita → **W412** | → **W412** |
| Última sección, resolución **heredada** (global o default del language) | el mecanismo de transición no se invoca: sin aviso (A.1) | idem | idem | idem | idem |
| Transición cuyo origen tiene < 2 compases | split omitido (no hay compás final que dividir) → **W420** | split omitido → **W420** | no requiere split: el gesto de bajo se aplica si el bass suena en el origen | — | — |
| Transición con bass inactivo en el origen | split **sí** se aplica (es mecanismo de acordes); approach del bajo omitido → **W421** | split **sí** se aplica; sin gesto de bajo propio → sin aviso | **sin split** (no forma parte de la estrategia): gesto cromático omitido; la progresión suena tal cual → **W421** | sin efecto → sin aviso | sin efecto → sin aviso |
| Toda transición resuelta | INFO: "sección X termina con Y → siguiente empieza con Z"; el compilador no juzga la corrección musical de la unión | idem | idem | idem | idem |

La resolución efectiva de cada transición es **únicamente** `structure[origen].resolution` > `harmony.resolution` > default del `language`. Ningún otro campo (incluida `tension`, §2.6.6) interviene.
## 2.5 INSTRUMENTOS

**Catálogo cerrado v1** (otro id → **E110**): `sax_tenor`, `rhodes`, `vibraphone`, `bass`, `drums`, `piano`, `pad`, `strings`. Una pista existe si la receta de identidad la incluye o si `instruments.<id>.enabled=true`.

| Id | Rol motor | Programas | Mecanismos reales disponibles | Notas |
|---|---|---|---|---|
| `sax_tenor` | `lead` (mono) | 66 | `phrases`, `generative`, `hold` + bends scoop/fall, `loop_bars`, transpose, accent | protegido por `lead_mono_range`, `lead_coverage`, `lead_mallet_overlap` |
| `rhodes` | `keys` | 4 | `hold`, `broken`, `tail` + voicing (11 perfiles; `rootless`/`shell` = color dark jazz) | voice leading Viterbi global |
| `vibraphone` | `mallet` | 11 | `replies`, `pings` | `respond_to`, `prob`, `max_per_bar`; guardrail `mallet_sparse` |
| `bass` | `bass` | finger 38 / upright 32 | `pattern` (tokens R/F/O/T/S/A), `long` + `fifth_at` | `approach` cromática, slides; guardrail `bass_kick` |
| `drums` | `drums` ch10 | — | capas declarativas + fills + humanización por pieza | guardrail `four_on_floor` |
| `piano` | `keys` | 0 | `hold`, `broken`, `tail` | igual que Rhodes |
| `pad` | `pad` | 91 / 89 | `sustain` + `tension` (clusters con `when`) | swells CC11 por receta |
| `strings` | `strings` | 50 | `sustain` con `modes`/`modes_by_cycle` (full/bare), `stabs` | swells por modos |

**Articulación real (declarada, no inventada)**: sax = scoop/fall/accent + CC73/72 (growl, subtone, respiración **no existen** en el motor); contrabajo = slides; batería = humanización por pieza; Rhodes/piano = voicings + restrike; vibráfono = duración/grados (sin pedal). No hay campo formal para pedir lo inexistente: si se escribiera, es **E109**.

**Dispositivos de tensión reales en v1**: `pad.tension` (clusters), perfiles de voicing en keys (`shell`/`rootless`/`bare`) y `strings.modes` (bare/full). **La `resolution` no es un dispositivo de tensión**: es un eje independiente con su propia cadena de precedencia (§2.4). No hay pista arp en el catálogo → **no hay dyads**.

## 2.6 ESTRUCTURA

### 2.6.1 Campos por sección
`id` (string único) · `type` ∈ {`intro`, `verse`, `pre_chorus`, `chorus`, `bridge`, `break`, `outro`} (→ `kind`; `pre_chorus`→`pre`) · `bars` entero ≥ 1 · opcionales: `energy`, `tension`, `density` (0..1), `focus` (0–3), `active`, `drums`, `chords`, `chord_bars` (1–8), `resolution`, `final`, `loop_bars` (1–32).

**Semántica de `active` (whitelist)**: si está presente, es la lista completa de instrumentos que suenan en esa sección; todo instrumento omitido queda silencioso. Si se omite, suenan los del set base de la identidad (menos los `enabled=false` globales). Entradas de `active`/`focus` que refieren un instrumento deshabilitado → **W406** (ignoradas); entradas fuera del catálogo → **E110**.

### 2.6.2 Energy — una sola traducción
`energy` se traduce **exclusivamente** a la rampa de velocidad de la sección. No toca `vel_scale` ni ningún otro parámetro.

| `energy` | velocity `[v0, v1]` |
|---|---|
| ≤ 0.25 | [55, 65] |
| 0.26–0.50 | [68, 80] |
| 0.51–0.75 | [82, 96] |
| > 0.75 | [98, 110] |

Siempre recortada por `global.velocity_cap` (default 110). La receta puede sumar +4 en chorus (constante documentada). El volumen de la batería viene de su propio eje (`drums`, §2.6.3), nunca de `energy`.

### 2.6.3 Drums por nivel semántico

| Nivel | Capas (receta identidad) | `vel_scale` |
|---|---|---|
| `off` | bloque silencioso | — |
| `air` | crash + hats decaídos | 0.85 |
| `light` | kick + rim + open hats | 0.95 |
| `groove` | beat roto | 1.0 |
| `heavy` | beat denso + fills | 1.1 |

`doom_triphop` suma +0.05 a todos los niveles (constante de receta). En `doom_dark_jazz` los niveles se reinterpretan como kit esparso (rim/ride + kick suave); nunca breakbeat.

### 2.6.4 Focus — algoritmo determinista

**Traducción única y verificable: deltas de velocity sobre los bloques** (+ `vel_scale` de batería). Sin pan, sin reverb, sin CC11, sin cambios de prioridad de choques (esa prioridad es fija por rol en el motor).

```
ENTRADA: sección S; focus declarado = [f1 … fk]  (k > 3 → E105, bloquea)
0. CUALQUIER f fuera del catálogo → E110 (bloquea).
1. FILTRADO (nunca se activa un instrumento apagado):
   f suena en S  ⟺  (f es pista existente: receta o enabled=true)
                    ∧ (active ausente ∨ f ∈ active)
   f que no suena → se descarta del focus + W406. No se habilita, no se añade a active.
2. PRIORIDAD RELATIVA: el orden declarado es la prioridad (1º > 2º > 3º).
   El focus filtrado se re-indexa por posición i ∈ {0, 1, 2} en orden declarado.
3. TRADUCCIÓN por posición i:
   f == "drums"  →  drums.vel_scale += [0.06, 0.03, 0.015][i]   (tope 1.2)
   resto         →  velocity del bloque de f = clamp(vel_receta + [8, 4, 2][i], 1, velocity_cap)
4. INSTRUMENTOS NO INCLUIDOS EN FOCUS: suenan igual, con sus valores de receta
   (focus no silencia ni reduce a nadie; silenciar es trabajo de `active`).
5. CASOS BORDE:
   focus ausente        → la receta define focus por defecto según `type` (tabla de receta).
   focus [] explícito   → sin deltas; todas las pistas activas a nivel de receta.
   focus que queda vacío tras filtrar → sin deltas (cada descarte ya emitió su W406).
```

| Posición (tras filtrar) | Delta velocity (tonales) | Delta `vel_scale` (drums) |
|---|---|---|
| 1º | +8 | +0.06 |
| 2º | +4 | +0.03 |
| 3º | +2 | +0.015 |

**Lo que focus NO hace en v1**: no activa instrumentos apagados, no cambia pan/reverb/volumen de mezcla, no genera automatización, no altera la prioridad de reparación de choques, no silencia a los no incluidos.

### 2.6.5 Density — fórmula determinista de coexistencia + traducción por rol (corrección 5)

Bandas deterministas: **B1** ≤ 0.33 · **B2** 0.34–0.66 · **B3** ≥ 0.67.

**Combinación instrumento × sección (una declaración por instrumento y otra por sección coexisten sin anular la evolución musical)**:

```
D_receta(S) = default de receta para el type de S              (0..1)
D_inst(i)   = instruments.<i>.density        (si se declara)
D_secc(S)   = structure[S].density           (si se declara)

desv(S)     = 0                          si S no declara density
              D_secc(S) − D_receta(S)    si S la declara     (desviación respecto a la receta)

base(i, S)  = D_inst(i)                   si i la declara
              D_receta(S)                 si no

density_efectiva(i, S) = clamp( base(i, S) + desv(S), 0.0, 1.0 )
```

**Propiedades (deterministas, demostrables)**:
1. **Solo sección declarada** → efectiva = `D_secc(S)` exacta (la base de receta se cancela con la desviación).
2. **Solo instrumento declarado** → efectiva = `D_inst(i)` en todas las secciones (sin desviaciones).
3. **Ambas declaradas** → base del instrumento + desviación de la sección: **la evolución musical entre secciones se conserva** sobre la base declarada. Ninguna declaración elimina a la otra.
4. **Sin mezclas opacas**: los tres operandos son campos del contrato o defaults de receta; sin promedios; el resultado entra en la **misma tabla de traducción** de abajo, que solo usa parámetros reales confirmados del motor.
5. La bandificación cuantiza: dos valores de la misma banda producen el mismo bloque (determinismo y estabilidad).

**Traducción por instrumento (solo parámetros reales del motor):**

| Instrumento | ¿Admite density v1? | Traducción concreta |
|---|---|---|
| `sax_tenor` | **Sí** (solo si el bloque efectivo del lead es generativo) | `lead.density` = 0.20 / 0.40 / 0.60 (valores > 0.60 se recortan a 0.60 para proteger `lead_coverage`) |
| `rhodes` | **Sí** | `hold`: `restrike_beats` = 0 / 4 / 2 · `broken`: `rest_prob` = 0.45 / 0.25 / 0.05 · `tail`: `notes_per_chord` = 1 / 2 / 2 |
| `piano` | **Sí** | idéntico a rhodes (mismo rol `keys`) |
| `vibraphone` | **Sí** | `replies`: `prob` = 0.25 / 0.45 / 0.60, `max_per_bar` = 1 / 2 / 2 · `pings`: recuento = 1 / 2 / 3 |
| `bass` | **No** | su densidad la fijan la receta (set de patrones por tipo de sección) y el eje `drums` — sin parámetro de density en el motor → **W410** si se declara a nivel instrumento |
| `drums` | **No** | su eje es `drums` (§2.6.3) — → **W410** si se declara |
| `pad` | **No** | su intensidad viene de `tension` y la rampa de `energy` — → **W410** si se declara |
| `strings` | **No** | su densidad viene de `modes` (receta) — → **W410** si se declara |

Notas:
- `sax_tenor` en secciones cuyo bloque efectivo es `phrases`/`hold` (material escrito propio o copiado vía motif): la density no es aplicable ahí → **una W410 por sección** (la fórmula no se evalúa para ese instrumento en esa sección).
- `vibraphone` con density efectiva en B3 y `mallet_sparse` ON → **W403**.
- **Disparadores exactos de W410**: (i) `instruments.<id>.density` declarada en bass/drums/pad/strings → 1 aviso por declaración, ignorada en todas las secciones; (ii) `instruments.sax_tenor.density` declarada + sección con bloque efectivo de material escrito → 1 aviso por sección, ignorada en esa sección. **La density de sección nunca emite W410**: la sección es válida; los instrumentos sin traducción simplemente obedecen a sus propios ejes.

### 2.6.6 Tension — eje independiente de la resolución (corrección 2)

**Separación vinculante**: `structure[].tension` y la resolución son ejes independientes. La tensión **nunca** selecciona, modifica, sugiere ni condiciona una `resolution` — ni una declarada por el compositor ni una implícita. La resolución efectiva de cada transición es exclusivamente el resultado de la cadena §2.4 (`structure[].resolution` > `harmony.resolution` > default del `language`); ningún otro campo participa en ella.

Traducción de `tension` por bandas (solo mecanismos reales):

| Banda | Traducción |
|---|---|
| B1 ≤ 0.33 | voicings estables en keys (`full`/`triad`) |
| B2 0.34–0.66 | `shell` en keys · `strings.modes` alternados |
| B3 ≥ 0.67 | voicings `rootless`/`bare`/`open4` · `pad.tension` (clusters) si pad activo |

**Sin pad y sin strings activos** → los dispositivos de las bandas B2/B3 se limitan a los voicings de keys → **W409** (no error).

## 2.7 DESARROLLO MUSICAL

| Mecanismo | Campo | Traducción real | Reglas v1 |
|---|---|---|---|
| Variación entre secciones | valores por sección + `occurrence` del motor | el compilador emite bloques explícitos | sin campos extra |
| Motivos recurrentes | `motifs.<name>: {from_section, sections, loop_bars?, transpose_st?}` | copia determinista de `lead.phrases` de la fuente a los destinos + `loop_bars` en el bloque lead | validación completa (abajo) |
| Respuestas | `responses.<inst>: {responds_to, prob?, max_per_bar?}` | `mallet.replies` | solo vibráfono (E303 si otro; E302 si responde a no-lead) |
| Silencios | `active` (whitelist) + guardrail `lead_coverage` | bloques `enabled=false` | — |
| Improvisación | `improvisation: [{section, instrument}]` | bloque lead → `generative` + drums bajados un nivel (tope: `off`) | solo `sax_tenor` (E301); drums ya `off` → W418 |
| Frases a mano | `melody.phrases.<section_id>: [{bar, beat, pitch, dur, vel?}]` | passthrough a `project.lead.phrases` | material del compositor, NO phrasegen; E111: beat ∈ [0,4) y la nota termina dentro de la sección |

### 2.7.1 Validación completa de motivos

Para cada `motifs.<name>`:

| Aspecto | Regla | Código |
|---|---|---|
| **Fuente** — existencia | `from_section` debe existir en `structure` | **E107** |
| **Fuente** — material | la fuente debe tener frases en `melody.phrases` (v1 sin phrasegen: el compilador no fabrica material). Fix: escribir frases | **E108** |
| **Destino** — existencia | cada id de `sections` debe existir en `structure` | **E107** |
| **Destino** — actividad | el lead (sax) debe sonar en cada destino (receta+enabled ∧ whitelist). Fix: añadir sax a `active` o quitar el destino | **E204** |
| **Longitud** — material > destino | se copian solo las notas que caben (truncado determinista por orden de escritura) | **W407** (con N notas truncadas) |
| **Longitud** — `loop_bars` > destino | el material suena una vez y se corta al acabar la sección | **W419** |
| **Transposición** — rango | `transpose_st` entero en **−24…+24** semitonos | **E105** |
| **Transposición** — registro | notas que quedan fuera del registro del lead se **descartan** (protege `lead_mono_range`); nunca se re-transpone automáticamente | **W413** (con N descartadas) |
| **Límites de sección** | `loop_bars` 1–32; los destinos heredan la tonalidad/armonía propios de su sección (la copia es de ritmo+contorno en pitches absolutos + `transpose_st`) | **E105** |
| **Guardrail** | `loop_bars ≠ 8` interactúa con `motif_repeat` según §2.11 | **W408** |

Única transformación v1: `transpose_st`. No existen campos para inversión/aumentación/retrogradación: escribirlos es **E109**.

**No hay generador de hooks en v1** (decisión 7). Hooks = (a) frases escritas, o (b) generativo existente con `motif_bars`/`loop_bars`.

**Límites de sección — copias frente a notas escritas (corrección 6)**: las notas **copiadas** por un motivo se **recortan** deterministamente al final de la sección destino (W407); una nota **escrita** por el compositor que sobrepase el final de su sección (`bar·4 + beat + dur > bars·4`) no se recorta: es inválida (**E111**).

## 2.8 PRECEDENCIA ARMÓNICA (exacta)

```
1. structure[].chords                    (explícito del compositor; admite "Sym:N" y {chord, bars})
2. harmony.progressions[<section id>]    (coincidencia exacta de id)
3. harmony.progressions[<type>]          (verse, chorus, ...)
4. Receta de identidad                   (tablas fijas por identidad×language×type, deterministas)
```

- Las claves de `progressions` pueden ser id o type; **el id gana** si ambos existen. Una clave que no es id ni type existente → **E107**.
- Dos secciones del mismo type comparten progresión (la variación entre repeticiones la aportan `occurrence`, `final` y `resolution`; no se inventan progresiones nuevas).
- Acordes explícitos fuera del vocabulario del `language` → **se respetan** (precedencia del compositor) + **W414**.
- Acordes con sintaxis no parseable → **E113** (§2.10).
- Por construcción (nivel 4), **siempre existe una progresión** para cada (type, language): las recetas están validadas por pares, así que nunca hay sección sin acordes.

## 2.9 ENDING (formato unificado)

```jsonc
"ending": {
  "fade_out":  { "enabled": true,  "bars": 6 },   // default: enabled false, bars 4
  "tape_stop": { "enabled": false, "bars": 2 }    // default: enabled false, bars 2
}
```

- **Forma unificada**: ambos son objetos `{enabled, bars}`. Forma abreviada: `"fade_out": true` ≡ `{"enabled": true}` con bars por defecto.
- **Parámetros adicionales** (única vía; todos confirmados en el motor):
  - `fade_out.exponent` (number 1.0–4.0; si se omite, usa el exponente por defecto del motor en el fade CC11).
  - `tape_stop.semitones` (entero 1–12) y `tape_stop.exponent` (1.0–4.0); si se omiten, defaults del mecanismo RPN/bend del motor (`compute_bends`, tape-stop).
  - **No se exponen otros parámetros**: todo lo demás del ending del motor es interno de las recetas.
- `fade_out.bars` = compases de fade hacia atrás desde el final; el compilador calcula `start = {section: última, bar: bars_última − N}` (CC11).
- `tape_stop.bars` = compases de frenada.
- **Validación (E112)**: `bars` no entero o < 1; `bars` mayor que los compases de la última sección. `exponent`/`semitones` fuera de rango → E105.
- Ambos `enabled: true` → se aplican ambos (CC11 de volumen + bend de tape-stop son mecanismos independientes del motor) con **W416** recomendando elegir uno.

## 2.10 VALIDACIÓN — TAXONOMÍA DEFINITIVA

Los checks viven en `dark_director/qa.py` (decisión 9); la regresión post-generación reutiliza `forge.validate()`.

**Principio de campo formal**: una funcionalidad sin campo formal en el contrato no tiene código de error propio: escribirla es escribir un campo desconocido → **E109**. No existen "claves reservadas". **E3xx solo aplica a campos formales** cuyo valor (bien formado) pide una capacidad que el motor no expone en v1.

**Obligatorios**: `schema`, `direction.identity`, `direction.accessibility`, `harmony.key`, `harmony.language`, `structure` (≥ 2 secciones con `id`/`type`/`bars`). Todo lo demás es opcional con default documentado (§3.1).

### E1xx — Error estructural (bloquea siempre)

| Código | Check |
|---|---|
| E101 | JSON malformado o raíz no-objeto |
| E102 | `schema` ausente o ≠ `dark-director/1` |
| E103 | campo requerido ausente (`direction.identity`, `direction.accessibility`, `harmony.key`, `harmony.language`, `structure`) |
| E104 | tipo incorrecto en cualquier campo (string/lista/número/bool/objeto esperado) |
| E105 | valor fuera de rango o fuera de enum — incluye: enums de `identity`/`accessibility`/`language`/`resolution`/`drums`; `bpm` (20–300), `humanize` (0–2), `velocity_cap` (40–127), `seed` (< 0), `energy`/`tension`/`density` (0–1), `bars` (< 1), `chord_bars`/`harmonic_rhythm_bars` (1–8), `loop_bars` (1–32), `transpose_st` (±24), `register` (no son 2 enteros 0–127 con low < high), `mix` (0–127), `prob` (0–1), `max_per_bar` (1–4), `focus` (> 3), `ending.exponent` (1.0–4.0), `tape_stop.semitones` (1–12), `velocity` de frase (1–127), `dur` (≤ 0 o > 16), `harmony.key` no parseable |
| E106 | **exclusivamente** `structure` inválida: < 2 secciones o ids duplicados |
| E107 | referencia rota a **sección inexistente**: claves de `progressions` que no son id ni type; claves de `melody.phrases`; `motifs.*.from_section`; `motifs.*.sections[]`; `improvisation[].section` |
| E108 | **motif con fuente sin frases** (`from_section` existe pero `melody.phrases` no tiene material para ella; v1 sin phrasegen). Fix: escribir frases |
| E109 | **campo desconocido** sin prefijo `x_` (en cualquier nivel, con sugerencia del campo más cercano). Incluye toda funcionalidad futura sin campo formal: `swing`, `groove`, `scales_by_section`, `section_tempo`, `section_program`, `articulations`, `transform`/`invert`/`augment`, `walking_bass`, `phrasegen`, etc. |
| E110 | id de instrumento fuera del catálogo de 8 (en `instruments`, `focus`, `active`, `responses.*`, `responses.*.responds_to`, `improvisation[].instrument`) |
| E111 | nota de frase inválida: `bar` fuera de 0..bars−1; **`beat` fuera de [0, 4)** — en 4/4 fijo, 4.0 es el beat 0 del compás siguiente; **la nota sobrepasa el final de la sección**: `bar·4 + beat + dur > bars·4` (tolerancia 1e−6); `pitch` no parsea (nota "C4" o MIDI 0–127); `dur` ≤ 0 o > 16; `vel` fuera de 1–127 |
| E112 | `ending` inválido: `bars` no entero o < 1, o mayor que los compases de la última sección |
| E113 | **símbolo de acorde no parseable** por la gramática de `theory.parse_chord` (en `harmony.progressions` o `structure[].chords`): sintaxis malformada en `"Sym"`, `"Sym:N"` o `{chord, bars}`. Fix: usar la gramática §2.4. Un acorde que parsea pero queda fuera del vocabulario del `language` **no** es E113: se respeta con W414 |

### E2xx — Contradicción explícita entre declaraciones del compositor (bloquea, con fix sugerido)

| Código | Check |
|---|---|
| E201 | **RETIRADO** (rev. 1/borradores). No se reasigna: las combinaciones son válidas (§2.1) y el motif sin material es **E108** |
| E202 | **RETIRADO** (rev. 1/borradores). No se reasigna: la improvisación contra whitelist es **E203** |
| E203 | improvisación en una sección cuyo `active` excluye explícitamente al instrumento. Fix: añadir el instrumento a `active` o eliminar la entrada |
| E204 | **desarrollo sobre pista que no suena**: frases (`melody.phrases`) o destino de motif en una sección donde el lead está inactivo; `responses` con el vibráfono deshabilitado; `improvisation` con instrumento deshabilitado. Fix: habilitar la pista / añadir a `active` / eliminar la referencia |

### E3xx — Capacidad no soportada sobre campo formal (no bloquea; bloquea con `qa.strict=true`)

Sin `strict`: la entrada se omite y se reporta en el informe (única omisión automática del contrato, §2.3).

| Código | Check | Mecanismo que falta |
|---|---|---|
| E301 | `development.improvisation[].instrument` ≠ `sax_tenor` (campo formal; el generativo solo existe en el rol lead) | no hay generativo fuera de `lead` (`engine.py:682-738`) |
| E302 | `responses.<inst>.responds_to` apunta a un instrumento que no es el lead | `replies` responde al lead (`engine.py:475-539`) |
| E303 | `responses` declarado sobre un instrumento sin mecanismo `replies` (solo el vibráfono es mallet en el catálogo) | no hay replies en keys/pad/strings |

### W4xx — Recomendación (no bloquea nunca; nunca cambia valores)

| Código | Check |
|---|---|
| W401 | BPM fuera del rango típico de la identidad (se compila igual) |
| W402 | ritmo armónico 1:1 en `doom_dark_jazz` (se sugiere ≥ 2) |
| W403 | vibráfono con density efectiva en banda B3 y `mallet_sparse` ON |
| W404 | `commercial` sin material de hook en ningún chorus (ni phrases, ni motif, ni `loop_bars`) |
| W405 | `velocity_cap` > 110 en identidades doom |
| W406 | `active`/`focus` referencia un instrumento que no suena en la sección (deshabilitado o excluido por whitelist) → entrada ignorada |
| W407 | material del motif más largo que la sección destino (N notas truncadas) |
| W408 | `motif_repeat` con motifs de `loop_bars` ≠ 8 (ventana fija de 8 compases del guardrail, `validate.py:150-153`) → ver regla §2.11 |
| W409 | `tension` en banda B3 sin pad ni strings activos (dispositivos limitados a voicings) |
| W410 | `density` sin traducción: `instruments.<id>.density` declarada para bass/drums/pad/strings (1 aviso por declaración), o para `sax_tenor` en secciones cuyo bloque efectivo del lead es material escrito (1 aviso por sección) → ignorada donde no aplica (§2.6.5) |
| W411 | combinación identidad×accessibility×language poco convencional (9/27 celdas; se compila igual; informativa) |
| W412 | `structure[].resolution` **explícita** en la última sección (no hay transición siguiente → gesto omitido, acorde final entero). Las resoluciones heredadas no avisan: el mecanismo de transición no se invoca (§2.4.2) |
| W413 | `transpose_st` deja notas fuera del registro del lead (N notas descartadas) |
| W414 | acordes explícitos fuera del vocabulario del `language` (se respetan por precedencia) |
| W415 | `final: true` en más de una sección (gana la última en orden) |
| W416 | `fade_out` y `tape_stop` ambos activos (se aplican ambos; se sugiere elegir uno) |
| W417 | `chord_bars`/`harmonic_rhythm_bars` no divide los compases de la sección o excede `bars` (último acorde recortado, determinista) |
| W418 | improvisación en sección con `drums: off` (no hay nivel que bajar; drums permanece off) |
| W419 | `loop_bars` de motif mayor que los compases del destino (el material suena una vez y se corta) |
| W420 | resolución basada en split (`tonal`/`deceptive`) en transición cuyo origen tiene < 2 compases (split omitido; acorde entero). Las estrategias sin split no la disparan (§2.4.2) |
| W421 | transición con gesto de bajo imposible: `tonal` con bass inactivo en el origen (approach omitido; el split **sí** se aplica) · `chromatic` con bass inactivo (gesto cromático omitido por completo: la estrategia no incluye split; la progresión suena tal cual). `deceptive`/`modal`/`open` no la disparan (§2.4.2) |

## 2.11 GUARDRAILS (defaults y regla de `motif_repeat`)

Los 8 guardrails reales de `validate.py` se exponen en `qa.guardrails` (bool por nombre; nombre desconocido → E109):

**Siempre ON por defecto**: `mallet_sparse`, `lead_mallet_overlap`, `lead_mono_range`, `bass_kick`, `four_on_floor`, `section_bounds`.
**Por accesibilidad**: `motif_repeat` y `lead_coverage` ON en `commercial`, ON en `balanced`, OFF en `experimental`.

**Regla determinista de `motif_repeat`** (el guardrail del motor compara bucles con ventana fija de 8 compases — `validate.py:150-153` — y produce falsos positivos con otras longitudes):

```
mr_derivado = default del perfil de accesibilidad
mr_efectivo = qa.guardrails.motif_repeat  si el compositor lo declara
              si no, mr_derivado

SI mr_efectivo == ON Y existe ≥ 1 motif con loop_bars ≠ 8:
   · si el valor venía DERIVADO (no declarado) → el compilador emite motif_repeat = OFF
     y reporta W408 (causa: ventana fija de 8; no se activa indiscriminadamente).
   · si el compositor lo DECLARÓ ON explícitamente → se respeta su elección
     y se reporta W408 (falsos positivos posibles; limitación §7.4).
SI mr_efectivo == OFF → se emite OFF sin aviso.
```

La mitigación complementaria (hooks de 8 compases en coros) queda como recomendación de escritura, no como regla.

## 2.12 VERSIONADO Y EXTENSIÓN

- `schema: "dark-director/1"`: cambios aditivos con defaults nuevos siguen en `/1`; breaking → `/2`.
- Campos `x_*`: prefijo de extensión del compositor; viajan incrustados en `meta.director` del proyecto emitido (roundtrip verificado por la auditoría). Nunca afectan a la música.
- Todo campo sin prefijo `x_` que no esté en §3 es **E109**.
---

# 3. TABLA DEFINITIVA DE CAMPOS Y TRADUCCIONES

Leyenda de omisión: "requerido" = ausencia → E103 · "—" = al omitirse no hay efecto. Toda traducción cita el mecanismo real del motor (auditoría; referencias de código verificadas en la revisión de rev. 1).

## 3.1 Raíz, dirección y global

| Campo | Tipo | Rango/valores | Default | Si se omite | Traducción al motor |
|---|---|---|---|---|---|
| `schema` | string literal | `"dark-director/1"` | — | **requerido** (E102) | `project.schema="midi-forge/1"`; el original viaja en `meta.director` (roundtrip verificado) |
| `meta.title` | string | libre | `""` | sin efecto | `meta.name` (metadato) |
| `meta.notes` | string | libre | `""` | sin efecto | `meta.note` (metadato) |
| `direction.identity` | enum | `dark_triphop` · `doom_triphop` · `doom_dark_jazz` | — | **requerido** (E103/E105) | selección de receta (`dark_director/identities/`) |
| `direction.accessibility` | enum | `commercial` · `balanced` · `experimental` | — | **requerido** (E103/E105) | perfil `accessibility.py` |
| `global.bpm` | number | 20–300 (fuera → E105; fuera del rango típico de identidad → W401) | BPM típico de la receta | receta | `global.bpm` |
| `global.seed` | entero | ≥ 0 | 0 | 0 (determinismo garantizado) | `global.seed` (RNG por bloque) |
| `global.humanize` | number | 0.0–2.0 | 1.0 | 1.0 | `global.humanize` |
| `global.velocity_cap` | entero | 40–127 (W405 si > 110 en doom) | 110 | 110 | tope de todas las velocidades emitidas (recetas y deltas) |

## 3.2 Armonía

| Campo | Tipo | Rango/valores | Default | Si se omite | Traducción al motor |
|---|---|---|---|---|---|
| `harmony.key` | string | `"Tónica modo"` con los 11 modos de `parse_key` (no parsea → E105) | — | **requerido** | `global.key` vía `theory.parse_key` |
| `harmony.language` | enum | `pop_dream_pop` · `hybrid` · `experimental` | — | **requerido** | vocabulario de símbolos emitidos |
| `harmony.resolution` | enum | `tonal` · `modal` · `deceptive` · `chromatic` · `open` | por `language` (pop→tonal, hybrid→modal, experimental→chromatic) | default del language | mecanismos de §2.4.1 (fallbacks §2.4.2) |
| `harmony.harmonic_rhythm_bars` | entero | 1–8 (W417 si no divide) | receta (por identidad) | receta | `section.chord_bars` |
| `harmony.progressions` | objeto | claves = id de sección o type (otra → E107); valores = lista de `"Sym"`, `"Sym:N"`, `{chord, bars}` (**no parsea → E113**; vacía → E105) | — | receta por (type, language) | `section.chords` |

## 3.3 Instrumentos (`instruments.<inst_id>`; id fuera del catálogo → E110)

| Campo | Tipo | Rango/valores | Default | Si se omite | Traducción al motor |
|---|---|---|---|---|---|
| `<inst>.enabled` | bool | true/false | receta (pistas base ON; otras OFF) | receta | presencia/ausencia de `track` |
| `<inst>.register` | [int, int] | 0–127, low < high (E105) | rango de la receta por rol | receta | `track.range` (+ mono del rol lead) |
| `<inst>.density` | number | 0.0–1.0; **base** por instrumento según la fórmula §2.6.5, con traducción solo en `sax_tenor`, `rhodes`, `piano`, `vibraphone` (en bass/drums/pad/strings → W410, ignorada) | sigue la fórmula §2.6.5 | §2.6.5 | sax→`lead.density`; keys→`restrike_beats`/`rest_prob`/`notes_per_chord`; mallet→`replies.prob/max_per_bar` + `pings` |
| `<inst>.mix.volume` | entero | 0–127 | receta | receta | `track.volume` |
| `<inst>.mix.pan` | entero | 0–127 | receta | receta | `track.pan` |
| `<inst>.mix.reverb` | entero | 0–127 | receta | receta | `track.reverb` (CC91) |
| `<inst>.mix.chorus` | entero | 0–127 | receta | receta | `track.chorus` (CC93) |
| `<inst>.mix.brightness` | entero | 0–127 | receta | receta | `cc_extra {74}` (CC74) |
| `bass.type` | enum | `finger` · `upright` | `finger` | finger (programa 38) | `track.program` 38/32 |

## 3.4 Secciones (`structure[]`; ≥ 2, ids únicos — E106)

| Campo | Tipo | Rango/valores | Default | Si se omite | Traducción al motor |
|---|---|---|---|---|---|
| `id` | string | único (E106) | — | **requerido** | id de sección + clave de anclas de automatización |
| `type` | enum | `intro`·`verse`·`pre_chorus`·`chorus`·`bridge`·`break`·`outro` (E105) | — | **requerido** | `section.kind` (`pre_chorus`→`pre`) |
| `bars` | entero | ≥ 1 (E105; recomendado ≤ 64, `section_bounds` vigila) | — | **requerido** | `section.bars` |
| `energy` | number | 0.0–1.0 | receta por type | receta | **solo** rampa `section.velocity [v0,v1]` (tabla §2.6.2) |
| `tension` | number | 0.0–1.0 | receta por type | receta | voicings, `pad.tension[]`, `strings.modes` (§2.6.6) — **no participa en la resolución** |
| `density` | number | 0.0–1.0 | receta por type | receta | **desviación determinista** sobre la base de cada instrumento (fórmula §2.6.5; traducción por rol) |
| `focus` | lista | 0–3 ids del catálogo que suenen (>3 → E105; no suena → W406) | receta por type | receta | deltas de velocity (+8/+4/+2) y `drums.vel_scale` (+0.06/+0.03/+0.015), §2.6.4 |
| `active` | lista | ids del catálogo (E110 si desconocido; deshabilitado → W406) | set base de la receta | receta | `sections[].blocks[<track>].enabled` |
| `drums` | enum | `off`·`air`·`light`·`groove`·`heavy` | receta por type | receta | `drums block.params.preset/layers` + `vel_scale` por nivel (§2.6.3) |
| `chords` | lista | símbolos `"Sym"`, `"Sym:N"`, `{chord, bars}` (**no parsea → E113**) | precedencia §2.8 | niveles 2–4 | `section.chords` |
| `chord_bars` | entero | 1–8 (W417 si no divide o > bars) | `harmonic_rhythm_bars` | global | `section.chord_bars` |
| `resolution` | enum | 5 valores | `harmony.resolution` | global | mecanismos de §2.4.1 (fallbacks §2.4.2) |
| `final` | bool | — | false | false (varios → W415, gana el último) | `section.final` |
| `loop_bars` | entero | 1–32 | sin loop | sin loop | `block params.loop_bars` (lead) |

## 3.5 Desarrollo, ending y qa

| Campo | Tipo | Rango/valores | Default | Si se omite | Traducción al motor |
|---|---|---|---|---|---|
| `development.melody.phrases.<section_id>` | lista de notas | nota: `{bar: 0..bars−1, beat: 0 ≤ beat < 4, pitch: "C4"/0–127, dur: >0 ≤16, vel: 1–127?}`; la nota debe terminar dentro de la sección: `bar·4 + beat + dur ≤ bars·4` (tolerancia 1e−6) (E111/E107) | — | sin frases | passthrough 1:1 a `project.lead.phrases` |
| `development.motifs.<name>.from_section` | string | id existente (E107) con frases (E108) | — | sin motif | origen de la copia |
| `development.motifs.<name>.sections` | lista de ids | existentes (E107) con lead activo (E204); no vacía (E105) | — | sin motif | `lead.phrases` en los destinos (+ `loop_bars`) |
| `development.motifs.<name>.loop_bars` | entero | 1–32 (E105; W419 si > destino; W408 si ≠ 8 con motif_repeat) | sin loop | sin loop | `loop_bars` del bloque lead en destinos |
| `development.motifs.<name>.transpose_st` | entero | −24…+24 (E105; W413 fuera de registro) | 0 | sin transposición | suma a los pitches de la copia |
| `development.responses.<inst>` | objeto | solo `vibraphone` (E303); habilitado (E204) | — | sin respuestas | `mallet params.respond_to/prob/max_per_bar` |
| `development.responses.<inst>.responds_to` | string | el id del lead (no-lead → E302; desconocido → E110) | lead de la receta | lead | `respond_to` |
| `development.responses.<inst>.prob` | number | 0.0–1.0 | 0.4 | 0.4 | `replies.prob` |
| `development.responses.<inst>.max_per_bar` | entero | 1–4 | 2 | 2 | `replies.max_per_bar` |
| `development.improvisation[]` | lista | `{section: id existente (E107), instrument: `sax_tenor` (E301; no suena → E203/E204)}` | — | sin improvisación | bloque lead `style:"generative"` + drums −1 nivel (tope off; W418) |
| `ending.fade_out` | objeto o `true` | `{enabled: bool=false, bars: int=4, exponent?: 1.0–4.0}`; bars ≤ bars de la última sección (E112) | disabled | sin fade | `ending.fade_out` CC11 con exponente |
| `ending.tape_stop` | objeto o `true` | `{enabled: bool=false, bars: int=2, semitones?: 1–12, exponent?: 1.0–4.0}` (E112/E105) | disabled | sin tape-stop | `ending.tape_stop` RPN bend (`compute_bends`) |
| `qa.strict` | bool | — | false | false | comportamiento del compilador ante E3xx |
| `qa.guardrails.<nombre>` | bool | solo los 8 nombres reales (otro → E109) | §2.11 | §2.11 | `project.guardrails` |
| `x_*` | cualquiera | — | — | — | incrustado en `meta.director` (roundtrip verificado) |

---

# 4. TABLA DEFINITIVA DE ERRORES Y ADVERTENCIAS (consolidada)

Resumen de control; el detalle completo con definiciones es §2.10.

| Familia | Códigos | Semántica | Cantidad |
|---|---|---|---|
| **E1xx** estructural (bloquea) | E101–E113 | JSON, schema, requeridos, tipos, rangos/enums, structure, referencias rotas, material inexistente, campos desconocidos, catálogo, frases, ending, símbolos de acorde | 13 |
| **E2xx** contradicción explícita (bloquea, con fix) | E203, E204 | improvisación contra whitelist; desarrollo sobre pista que no suena. **E201/E202 retirados sin reasignar** | 2 |
| **E3xx** capacidad no soportada sobre campo formal (bloquea solo con `qa.strict=true`; si no, omite+reporta) | E301–E303 | improvisación no-lead; `responds_to` ≠ lead; replies fuera de mallet | 3 |
| **W4xx** recomendación (nunca bloquea, nunca cambia valores) | W401–W421 | BPM, ritmo armónico, mallet B3, hooks, velocity_cap, referencias ignoradas, motifs, tension, density, W411, resoluciones, final múltiple, endings, chord_bars, drums off, loops, split sin espacio, gesto de bajo imposible | 21 |

Propiedades verificadas de la taxonomía:
- **Contigua y sin colisiones**: cada código tiene exactamente un significado — **E106 = solo `structure` inválida; E113 = solo acordes no parseables**; los retirados (E201/E202) siguen marcados y sin reasignar.
- **Sin errores de combinación de dimensiones**: ninguna regla E/w depende de identidad×accesibilidad×lenguaje salvo W411 (informativa).
- **Sin errores para funcionalidades sin campo formal**: esas escrituras son E109 (principio §2.10).
- **Resolución con cadena exclusiva**: solo `structure[].resolution` > `harmony.resolution` > default del `language` la determinan (§2.4.2); ningún otro campo interviene.
- Todo E3xx cita el mecanismo del motor que falta; toda W4xx describe el comportamiento determinista resultante.
---

# 5. EJEMPLOS (los 3, conformes al contrato rev. 3)

## 5.0 Supuestos de receta para la verificación exacta de avisos

Los avisos esperados de los ejemplos dependen de defaults de receta (sets base de pistas, bloque efectivo del lead, density por tipo de sección). Para que el cálculo sea determinista y verificable, la verificación de §8 usa estos supuestos, declarados aquí:

1. **Set base por identidad** (pistas que suenan sin `active` ni `enabled` explícitos):
   - `dark_triphop`: sax_tenor, rhodes, vibraphone, bass, drums, pad
   - `doom_triphop`: sax_tenor, rhodes, vibraphone, bass, drums, pad, strings
   - `doom_dark_jazz`: sax_tenor, rhodes, vibraphone, bass, drums, **piano**, **strings** (pad OFF)
2. **Bloque efectivo del lead**: generativo en toda sección sin material escrito; material escrito donde el ejemplo declara frases propias o recibe la copia de un motif.
3. **`D_receta(type)`** (default de density por tipo de sección): la density declarada en la **primera sección de ese type** dentro del propio ejemplo (los ejemplos son coherentes con su receta; las demás secciones de un mismo type se leen como desviaciones, que es exactamente lo que la fórmula §2.6.5 combina).
4. **Guardrails por defecto**: `mallet_sparse` siempre ON; `motif_repeat`/`lead_coverage` derivados del perfil de accesibilidad (§2.11).
5. **W401** (BPM típico de la identidad) depende de datos de receta no fijados por el contrato: los BPM de los ejemplos (86 / 70 / 62) se asumen dentro del rango típico de su identidad.

Con estos supuestos, los avisos esperados listados bajo cada ejemplo son exactos y recomputados por regla (§8).

## 5.1 (H.1) — Dark Trip Hop + Commercial (+ pop_dream_pop)

```json
{
  "schema": "dark-director/1",
  "meta": { "title": "Midnight Tape", "notes": "Trip hop oscuro con hook de sax escrito a mano." },
  "direction": { "identity": "dark_triphop", "accessibility": "commercial" },
  "global": { "bpm": 86, "seed": 11 },
  "harmony": {
    "key": "D minor",
    "language": "pop_dream_pop",
    "resolution": "tonal",
    "harmonic_rhythm_bars": 1,
    "progressions": {
      "verse":  ["Dm9", "Bbmaj7", "Fmaj9", "C7sus4"],
      "chorus": ["Bbmaj9", "Fmaj9", "Gm9", "A7sus4"]
    }
  },
  "instruments": { "sax_tenor": { "density": 0.45, "register": [60, 84] } },
  "structure": [
    { "id": "intro",    "type": "intro",      "bars": 8,  "energy": 0.25, "tension": 0.2, "density": 0.25, "focus": ["rhodes", "pad"], "drums": "air" },
    { "id": "verse_1",  "type": "verse",      "bars": 16, "energy": 0.45, "tension": 0.35, "density": 0.45, "focus": ["sax_tenor", "drums"], "drums": "groove" },
    { "id": "pre_1",    "type": "pre_chorus", "bars": 8,  "energy": 0.6,  "tension": 0.55, "density": 0.55, "focus": ["pad", "vibraphone"], "drums": "light" },
    { "id": "chorus_1", "type": "chorus",     "bars": 16, "energy": 0.8,  "tension": 0.5, "density": 0.65, "focus": ["sax_tenor", "drums", "bass"], "drums": "heavy" },
    { "id": "verse_2",  "type": "verse",      "bars": 16, "energy": 0.5,  "tension": 0.4, "density": 0.5,  "focus": ["sax_tenor"], "drums": "groove" },
    { "id": "chorus_2", "type": "chorus",     "bars": 16, "energy": 0.85, "tension": 0.55, "density": 0.7,  "focus": ["sax_tenor", "drums"], "drums": "heavy", "final": true },
    { "id": "break_1",  "type": "break",      "bars": 8,  "energy": 0.35, "tension": 0.6, "density": 0.3,  "focus": ["vibraphone"], "drums": "light", "active": ["vibraphone", "rhodes", "pad"] },
    { "id": "outro",    "type": "outro",      "bars": 8,  "energy": 0.2,  "tension": 0.15, "density": 0.2,  "focus": ["rhodes"], "drums": "air" }
  ],
  "development": {
    "melody": { "phrases": { "chorus_1": [
      { "bar": 0, "beat": 0.0, "pitch": "A4", "dur": 1.5 },
      { "bar": 0, "beat": 2.0, "pitch": "G4", "dur": 1.0 },
      { "bar": 1, "beat": 0.0, "pitch": "F4", "dur": 2.5 },
      { "bar": 2, "beat": 1.5, "pitch": "D4", "dur": 1.0 },
      { "bar": 3, "beat": 0.0, "pitch": "C4", "dur": 3.0 }
    ] } },
    "motifs": { "hook_a": { "from_section": "chorus_1", "sections": ["chorus_2"], "loop_bars": 8 } },
    "responses": { "vibraphone": { "responds_to": "sax_tenor", "prob": 0.4 } }
  },
  "ending": { "fade_out": { "enabled": true, "bars": 6 } }
}
```

**Avisos esperados (4, exactos según §2.6.5, §2.6.6, §2.4.2 y supuestos §5.0)**:

| Aviso | Dónde | Regla aplicada |
|---|---|---|
| **W410** ×2 | `chorus_1` y `chorus_2` | `instruments.sax_tenor.density = 0.45` no es aplicable ahí: en `chorus_1` el bloque efectivo del lead es material escrito (frases propias) y en `chorus_2` es material copiado (motif `hook_a`). Un aviso por sección; ignorada solo en esas dos secciones (§2.6.5). |
| **W403** ×1 | `chorus_2` | density efectiva del vibráfono = 0.65 + (0.7 − 0.65) = 0.7 → banda B3 con `mallet_sparse` ON (siempre ON, §5.0). Se compila igual; recomendación de suavizar respuestas. |
| **W421** ×1 | transición `break_1 → outro` | resolución efectiva `tonal` (heredada) con gesto de bajo, pero el bass no suena en `break_1` (whitelist): approach del bajo omitido; **el split armónico sí se aplica** (mecanismo de acordes, §2.4.2). |

Notas de verificación: combinación convencional (sin W411); hook presente → sin W404; `loop_bars: 8` con `motif_repeat` derivado ON → sin W408; fade 6 ≤ 8 de `outro` → sin E112; `outro` no declara resolución explícita → sin W412 (A.1); las notas escritas cumplen beat ∈ [0,4) y terminan dentro de `chorus_1` (bar·4 + beat + dur ≤ 64); todas las notas (60–69) caen dentro del registro [60, 84] → sin W413.

Demonstración de la fórmula §2.6.5 (corrección 5): la base del sax (0.45) y las densities de sección **coexisten** — p. ej. `verse_2`: 0.45 + (0.5 − 0.45) = 0.50 → banda B2 → `lead.density` 0.40; `verse_1`: 0.45 + 0 = 0.45 → B2. La evolución entre secciones se conserva sobre la base declarada.

## 5.2 (H.2) — Doom Trip Hop + Balanced (+ hybrid)

```json
{
  "schema": "dark-director/1",
  "meta": { "title": "Iron Lung", "notes": "Doom trip hop híbrido; escalada con caída en el break." },
  "direction": { "identity": "doom_triphop", "accessibility": "balanced" },
  "global": { "bpm": 70, "seed": 23 },
  "harmony": {
    "key": "D minor",
    "language": "hybrid",
    "resolution": "modal",
    "harmonic_rhythm_bars": 2,
    "progressions": {
      "verse":  ["Dm9", "Bbmaj7", "Ebm7b5", "A7b9"],
      "chorus": ["Dm9", "Gm9", "Bb13", "C7sus4"]
    }
  },
  "structure": [
    { "id": "intro",    "type": "intro",  "bars": 8,  "energy": 0.2,  "tension": 0.3, "density": 0.2,  "focus": ["pad", "strings"], "drums": "air" },
    { "id": "verse_1",  "type": "verse",  "bars": 16, "energy": 0.4,  "tension": 0.5, "density": 0.4,  "focus": ["bass", "drums"], "drums": "groove" },
    { "id": "verse_2",  "type": "verse",  "bars": 16, "energy": 0.55, "tension": 0.6, "density": 0.5,  "focus": ["sax_tenor", "bass"], "drums": "groove" },
    { "id": "break_1",  "type": "break",  "bars": 8,  "energy": 0.25, "tension": 0.75, "density": 0.25, "focus": ["vibraphone"], "drums": "light",
      "chords": ["Dm7b5", "A7b9"] },
    { "id": "chorus_1", "type": "chorus", "bars": 16, "energy": 0.8,  "tension": 0.65, "density": 0.65, "focus": ["sax_tenor", "drums", "bass"], "drums": "heavy" },
    { "id": "chorus_2", "type": "chorus", "bars": 16, "energy": 0.9,  "tension": 0.7,  "density": 0.7,  "focus": ["sax_tenor", "drums"], "drums": "heavy", "final": true, "resolution": "deceptive" },
    { "id": "outro",    "type": "outro",  "bars": 8,  "energy": 0.2,  "tension": 0.2, "density": 0.15, "focus": ["strings"], "drums": "air" }
  ],
  "development": {
    "responses": { "vibraphone": { "responds_to": "sax_tenor", "prob": 0.5, "max_per_bar": 2 } },
    "improvisation": [ { "section": "break_1", "instrument": "sax_tenor" } ]
  },
  "ending": { "tape_stop": { "enabled": true, "bars": 2 } }
}
```

**Avisos esperados (3, exactos)**:

| Aviso | Dónde | Regla aplicada |
|---|---|---|
| **W414** ×2 | `harmony.progressions.verse` y `break_1.chords` | `A7b9` está fuera del vocabulario `hybrid` (7b9 es experimental); parsea → no es E113; se respeta por precedencia del compositor (§2.8). |
| **W403** ×1 | `chorus_2` | density efectiva del vibráfono = 0.65 + (0.7 − 0.65) = 0.7 → banda B3 con `mallet_sparse` ON. |

Notas de verificación: combinación convencional (sin W411); `Ebm7b5` es válido en hybrid (m7b5 puntual) y `Bb13` también (13); `chorus_2` tiene `resolution: deceptive` **explícita** pero no es la última sección → se aplica sin W412; `outro` hereda `modal` → sin aviso (A.1); `modal`/`deceptive` no emiten W421 (deceptive: split es mecanismo de acordes y el bass suena en todas las secciones); improvisación en `break_1` con drums `light` → drums baja a `air` sin aviso (W418 solo con drums off); `break_1` tension 0.75 (B3) con pad y strings activos → sin W409; `tape_stop` 2 ≤ 8 de `outro` → OK; ritmo armónico 2 divide 8 y 16 → sin W417 (la lista de 2 acordes de `break_1` cicla: 2 × 2 compases, repetidos hasta llenar los 8).

## 5.3 (H.3) — Doom Dark Jazz + Experimental (+ experimental)

```json
{
  "schema": "dark-director/1",
  "meta": { "title": "Cold Harbor", "notes": "Cinematográfico, sin breakbeats; improvisación central." },
  "direction": { "identity": "doom_dark_jazz", "accessibility": "experimental" },
  "global": { "bpm": 62, "seed": 47 },
  "harmony": {
    "key": "D phrygian",
    "language": "experimental",
    "resolution": "chromatic",
    "harmonic_rhythm_bars": 2,
    "progressions": {
      "theme_a": ["Dm7b5", "G7#5b9", "BbmMaj7", "A7b9"],
      "theme_b": ["Ebø7", "Ab13b9", "Dm7b5", "E7#9"]
    }
  },
  "instruments": {
    "sax_tenor": { "density": 0.25, "register": [58, 79] },
    "bass": { "type": "upright" },
    "vibraphone": { "density": 0.2 }
  },
  "structure": [
    { "id": "intro",   "type": "intro", "bars": 8,  "energy": 0.15, "tension": 0.4, "density": 0.15, "focus": ["strings", "rhodes"], "drums": "air" },
    { "id": "theme_a", "type": "verse", "bars": 16, "energy": 0.3,  "tension": 0.55, "density": 0.3,  "focus": ["rhodes", "bass"], "drums": "off" },
    { "id": "theme_b", "type": "verse", "bars": 16, "energy": 0.4,  "tension": 0.65, "density": 0.35, "focus": ["sax_tenor", "strings"], "drums": "off" },
    { "id": "break_1", "type": "break", "bars": 16, "energy": 0.35, "tension": 0.7, "density": 0.3,  "focus": ["sax_tenor"], "drums": "off" },
    { "id": "outro",   "type": "outro", "bars": 8,  "energy": 0.1,  "tension": 0.3, "density": 0.1,  "focus": ["strings", "vibraphone"], "drums": "air" }
  ],
  "development": {
    "responses": { "vibraphone": { "responds_to": "sax_tenor", "prob": 0.3, "max_per_bar": 1 } },
    "improvisation": [ { "section": "break_1", "instrument": "sax_tenor" } ]
  },
  "ending": { "fade_out": { "enabled": true, "bars": 8 } }
}
```

**Avisos esperados (1, exacto)**:

| Aviso | Dónde | Regla aplicada |
|---|---|---|
| **W418** ×1 | `break_1` | improvisación en sección con `drums: off` (no hay nivel que bajar; drums permanece off). |

Notas de verificación: combinación convencional (sin W411); todos los acordes parsean y son vocabulario experimental (incluidos `E7#9` — la alteración `#9` existe en la gramática del motor — y `Ab13b9`) → sin W414 ni E113; `resolution: chromatic` es la global: en `outro` (última sección) no hay transición siguiente y `outro` no declara resolución explícita → **sin W412** (A.1); el bass suena en todas las secciones → las transiciones cromáticas se aplican sin W421; density por instrumento (sax 0.25, vibes 0.2) actúa como **base** y las densities de sección como desviaciones (fórmula §2.6.5) — sin frases ni motivos no hay W410; vibes siempre en B1 → sin W403; `break_1` tension 0.7 (B3) con strings activo → sin W409; `harmonic_rhythm_bars: 2` en `doom_dark_jazz` → sin W402; `fade_out` 8 ≤ 8 de `outro` → OK. Base `doom_dark_jazz` según §5.0: piano ON, pad OFF, strings ON (el ejemplo no los declara: compacidad).

---

# 6. CAPACIDADES: SOPORTADAS vs EXCLUIDAS DE v1 (sin cambios en rev. 3)

## 6.1 Realmente soportadas y usadas por la ruta de compilación v1 (con mecanismo)

| # | Capacidad | Mecanismo real del motor |
|---|---|---|
| 1 | 11 modos + `parse_key`; gramática completa de `parse_chord` (7b9, 7#5b9, 13b9, mMaj7, ø, dim7, sus, slash, power, #9) | `theory.py` (verificado 20/20 acordes dark) |
| 2 | Spans de acorde: `"Sym:N"`, `{chord, bars}`, `chord_bars`, `chord_overrides` con `split` + `when` | `engine.py:78-92` (Ctx/sec) |
| 3 | Voicings: 11 perfiles + voice leading Viterbi global | `voicing.py:3-156` |
| 4 | Bajo: tokens R/F/O/T/S/**A**, aproximación cromática, slides (bend), `long` + `fifth_at` | `engine.py:552-608` |
| 5 | Batería: capas declarativas (`at/pick/grid`, `when`, `prob`, `omit`, `drag`, `vel`, `rolls`, `fills`), humanización por pieza | `styles.py:82-162`, `engine.py:819-909`, `adapter.py:373-397` |
| 6 | Lead: `phrases` (bar/beat/pitch/dur/vel), `loop_bars`, generativo (`density`/`long_prob`/`motif_bars`/`contour`), bends scoop/fall, accent | `engine.py:682-797` |
| 7 | Vibráfono: `replies` (`respond_to/prob/min_gap/margin/glint_gap/fragment/degrees/range/min_distance/max_per_bar`) y `pings` | `engine.py:475-539` |
| 8 | Keys: `hold`/`broken`/`tail` con voicing, `restrike`, `rest_prob`, `ring`, `notes_per_chord` | rol `keys` (revisión de código rev. 1) |
| 9 | Pad `sustain` + `tension`; Strings `sustain` con `modes`/`modes_by_cycle`/`mode_cycle` y `stabs` | roles `pad`/`strings` |
| 10 | Mezcla por pista: CC7/10/91/93, attack/release (CC73/72), brightness (CC74), `cc_extra`, detune, jitter | `engine.py:1094-1141` (probe: CC1 y CC74 escritos) |
| 11 | Automatización CC con anclas por sección (v0/v1/step/curve) — usada por las recetas (swells, fade) | `engine.py:1094-1141` |
| 12 | Guardrails: 8 checks reales (`validate.py`) | `validate.py:83-153` |
| 13 | Ending: fade CC11 con exponente; tape-stop vía cambio de RPN | `engine.py:994-1058` (`compute_bends`) |
| 14 | Roundtrip de metadatos ajenos (`meta.director`, `x_*`) | verificado por probe de la auditoría |
| 15 | Determinismo por seed + aislamiento por bloque | tests `test_deterministic`, `test_block_independence` |
| 16 | Reparación de choques con prioridad fija por rol | `engine.py:923-991` |

## 6.2 Explícitamente FUERA de v1

| # | Capacidad | Estado en el contrato |
|---|---|---|
| 1 | Phrasegen / generador de hooks (decisión 7) | no existe campo; hooks = frases escritas o generativo |
| 2 | Swing / groove template (decisión 8) | sin campo formal → escribirlo = **E109** |
| 3 | Escala/modo por sección para el generativo (decisión 8; `engine.py:685` usa escala global) | sin campo formal → **E109** |
| 4 | Tempo/compás/programa GM por sección (un solo tempo/programa en tick 0, `engine.py:1232-1252`) | sin campo formal → **E109** |
| 5 | Articulaciones no-MIDI (growl, subtone, respiración, pedal de vibráfono) | sin campo formal → **E109** (o `x_*` metadato) |
| 6 | Walking bass generativo | sin campo formal → **E109**; hoy: patrones explícitos + token `A` |
| 7 | Interacciones más allá de vibráfono↔lead | solo `replies` + guardrail `bass_kick` |
| 8 | Transformaciones de motivo ≠ `transpose_st` (inversión, aumentación, retrogradación) | sin campo formal → **E109** |
| 9 | Improvisación en instrumentos no-lead | campo formal, capacidad no soportada → **E301** |
| 10 | Dyads del rol arp | no hay pista arp en el catálogo v1 |
| 11 | `identity_overrides` | recetas cerradas (decisión aprobada) |
| 12 | Render FX / LUFS / stems | existen en el motor (`render`, `audio.py`) pero **no se exponen** en el contrato v1 |
| 13 | Swells/CC11 desde `focus` | v1 usa solo deltas de velocity; automatización reservada a recetas |
| 14 | Modificar `styles.py`/presets | decisión 3: el compilador emite todo explícito |

---

# 7. LIMITACIONES NO RESOLVIBLES SIN MODIFICAR MIDI FORGE (sin cambios en rev. 3)

Declaración explícita exigida. Ninguna de estas se puede corregir desde el compilador; requieren cambios de `forge/` (fuera del alcance v1):

1. **Un solo tempo/compás/programa por canción** (`engine.py:1232-1252` escribe tempo/TS/programa en tick 0): el contrato v1 no expone ni podrá exponer cambios por sección sin tocar el motor.
2. **Escala global para el generativo** (`engine.py:685`): el lead generativo usa la escala de `key` en toda la canción; no hay intercambio modal por sección.
3. **Sin swing real**: `drag` es retraso aleatorio por pieza, no grilla ternaria; cualquier "swing" contratado sería falso.
4. **`motif_repeat` con ventana fija de 8 compases** (`validate.py:150-153`): no parametrizable; de ahí la regla §2.11 (forzado OFF o aviso W408). Los falsos positivos con `loop_bars ≠ 8` no se pueden eliminar sin tocar `validate.py`.
5. **Micro-solapes del lead mono** (hallazgo de auditoría §6): la combinación `phrases` + `loop_bars` puede duplicar una nota (trim mono deja ~0.014 beat de solape y hace fallar `lead_mono_range`). Mitigación del compilador: deduplicar/validar colisiones de frases antes de emitir (en `qa.py`); la causa raíz está en `_lead_notes`.
6. **Sin articulaciones no-MIDI** para sax (growl, subtone, respiración) ni pedal de vibráfono: aproximación solo con scoop/fall, accent y CC73/72/74.
7. **Interacción instrumental limitada a lead↔mallet**: no hay coordinación bass↔drums más allá del guardrail `bass_kick`.
8. **Prioridad de choques fija por rol**: ni `focus` ni ningún campo v1 altera `repair_clashes`.
9. **`pings` (recuento por compás)**: parámetro confirmado solo a nivel de revisión de código (rev. 1); la auditoría enumera `replies` con detalle pero no los parámetros internos de `pings`. Si al implementar no se confirma el recuento, la density del vibráfono degrada a `replies.prob/max_per_bar` + W410 (regla de degradación declarada).
10. **Soundfont**: el carácter sax/Rhodes/vibes depende del soundfont; el motor no lo controla (documentar el recomendado).
---

# 8. VERIFICACIÓN EJECUTADA (documental + parseo JSON — **no es una verificación de código fuente**)

**Alcance declarado**: toda la verificación de esta sección es una **comprobación documental** del entregable más el **parseo y validación de los tres ejemplos JSON** contra las reglas del contrato rev. 3. **No se verificó código fuente**: no se ejecutó el motor, `forge/` no fue abierto para modificación, y el compilador `dark_director/compiler.py` todavía no existe (decisiones 4 y 10). Las traducciones del contrato citan mecanismos heredados de la auditoría y de las revisiones rev. 1/rev. 2; ninguna capacidad nueva fue "verificada" porque ninguna fue añadida.

Herramienta: script QA desechable `scripts/validar_respuesta_03.py` (fuera del proyecto; **no** es el compilador ni código de `dark_director/`). Extrae los JSON de este documento y ejecuta cinco comprobaciones:

1. **Los 3 ejemplos: JSON válido + cumplimiento del contrato rev. 3** (requeridos, enums, rangos E105, `beat` ∈ [0,4) y notas dentro de la sección (E111), acordes parseables (E113), vocabulario por `language` (W414), referencias (E107/E108/E204), campos desconocidos (E109), endings (E112)).
2. **Recomputación de avisos por regla** (W403/W404/W408/W410/W412/W413/W414/W415/W416/W417/W418/W419/W420/W421/W402/W405/W406/W409/W411) sobre los supuestos §5.0, comparada con las tablas de avisos de §5.1–§5.3.
3. **Las 27 combinaciones** identity × accessibility × language contra la regla de los 4 pares atípicos.
4. **Unicidad de códigos**: registro completo de los 39 códigos (E101–E113, E203–E204, E301–E303, W401–W421) sin significados duplicados; E201/E202 retirados y sin reasignar; escaneo del documento para detectar residuos de la colisión de E106 y de las redacciones antiguas (acople tension-resolution, beat 0–4, density ganador único).
5. **Coherencia del entregable**: los bloques JSON incrustados en este documento se re-extraen y validan como fuente única.

Resultado de la ejecución:

```
========================================================================
COMPROBACIÓN 1 — Los 3 ejemplos: JSON válido + contrato rev. 3
========================================================================
  ✓ 3 bloques JSON extraídos del documento (encontrados: 3)

— Midnight Tape
  ✓ 0 errores de contrato
  ✓ avisos exactos: ['W403', 'W410', 'W410', 'W421'] == esperados ['W403', 'W410', 'W410', 'W421']

— Iron Lung
  ✓ 0 errores de contrato
  ✓ avisos exactos: ['W403', 'W414', 'W414'] == esperados ['W403', 'W414', 'W414']

— Cold Harbor
  ✓ 0 errores de contrato
  ✓ avisos exactos: ['W418'] == esperados ['W418']

========================================================================
COMPROBACIÓN 2 — Las 27 combinaciones identity × accessibility × language
========================================================================
  Aceptadas: 27/27 · con W411 (informativa): 9 · convencionales: 18
  ✓ 27/27 aceptadas, 9 W411, 18 convencionales, 0 errores

========================================================================
COMPROBACIÓN 3 — Unicidad de códigos y retirados
========================================================================
  ✓ 39 códigos registrados (E101–E113, E203–E204, E301–E303, W401–W421)
  ✓ E201/E202 retirados y sin reasignar
  ✓ cada código aparece una sola vez

========================================================================
COMPROBACIÓN 4 — Escaneos documentales anti-residuo (rev. 2)
========================================================================
  ✓ ausente: «no parsea → E106» (colisión E106/acordes)
  ✓ ausente: «fuera de 0–4» (beat 0–4 antiguo)
  ✓ ausente: «resolución cromática/deceptive» (acople tensión→resolución)
  ✓ ausente: «y la propia `resolution`» (resolución como dispositivo de tensión)
  ✓ ausente: «resolución `deceptive`/`open` y silencios» (ajuste atípico con resolución)
  ✓ ausente: «gana a `structure[].density`» (density ganador único)
  ✓ ausente: «split armónico aplicado; approach del bajo omitido» (W421 genérica antigua)
  ✓ ausente: «W412 si se intentara aplicar» (ambigüedad W412 en H.3)
  ✓ presente: E113 · «beat: 0 ≤ beat < 4» · «bar·4 + beat + dur ≤ bars·4»
  ✓ presente: «jamás añaden mecanismos de otra estrategia» (exclusividad fallbacks)
  ✓ presente: «selecciona, modifica, sugiere ni condiciona una `resolution`»
  ✓ presente: fórmula «density_efectiva(i, S) = clamp( base(i, S) + desv(S), 0.0, 1.0 )»
  ✓ presente: «La density de sección nunca emite W410» (disparadores exactos)
  ✓ ninguna asignación «→ E106» · fila canónica «E106 = exclusivamente structure»
  ✓ E113 citado 18 veces (definición + referencias)
  · Menciones de E106 (9): todas de estructura (registro de cambios §1, tabla E1xx
    §2.10, cabecera y fila id de §3.4, propiedades §4, §8)

========================================================================
RESULTADO GLOBAL
========================================================================
✓ TODO VERDE — verificación documental + JSON completa sin fallos
```

**Límites de esta verificación (honestidad de alcance)**: W401 (BPM típico por identidad) depende de datos de receta no fijados por el contrato y se maneja por supuesto declarado (§5.0.5), no por cómputo. La conformidad de los mecanismos citados (`split`, token `A`, `replies`, guardrails) es la evidencia documental de la auditoría y de la revisión rev. 1; su confirmación runtime llegará con la Fase 0 (test de contrato) y la Fase 1 (compilador).

---

# 9. CONFORMIDAD CON LAS VERIFICACIONES OBLIGATORIAS (instr. 05)

| Verificación exigida | Resultado |
|---|---|
| Los tres ejemplos siguen siendo JSON válido | ✅ 3/3 parsean (§8.1) |
| Los avisos esperados coinciden exactamente con las reglas | ✅ recomputados por regla sobre supuestos declarados (§5.0): H.1 = W403 + 2×W410 + W421 · H.2 = W403 + 2×W414 · H.3 = W418 — coincidencia exacta con §5.1–§5.3 |
| No hay códigos de error con significados múltiples | ✅ registro de 39 códigos único; E106 acotado a `structure`; E113 nuevo para acordes no parseables; E201/E202 retirados; escaneos documentales en verde (§8.4) |
| Las 27 combinaciones siguen siendo válidas | ✅ 27/27 aceptadas, 9 con W411 informativa, 18 convencionales, 0 errores |
| No modificar `forge/` | ✅ sin escrituras ni creación de código de proyecto |
| No crear código del compilador | ✅ solo script QA desechable fuera del proyecto, para verificar este documento |
| No declarar verificación de código fuente indebida | ✅ §8 declara expresamente que la verificación es documental + JSON; no se ejecutó el motor |

---

**Próximo paso (tras aprobación de esta validación)**: Fase 0 del roadmap — fijar el contrato rev. 3 en el proyecto + test de contrato (roundtrip de metadatos + validación del schema), sin tocar `forge/`. Cierre de regresión: 4 ejemplos + 36 tests en verde.
