# PROTOCOLO DE ESCUCHA — Capa D (spec DMD Control Center v1.4, §6.5–§6.6)

Documento general de la Fase 5. La Capa D (escucha humana) NO es automatizable
en este MVP y no se disfraza de scoring numérico (C-09, C-11): este protocolo
define QUÉ preguntar, CÓMO comparar y DÓNDE registrar, para que las fases
comparen contra la banda previa (§12: gates por fase).

## 1. Las 13 dimensiones — preguntas de escucha (capa D)

Las capas A (plan estructural), B (plan musical) y C (MIDI/events) son
automáticas; la columna D es la pregunta que el oyente responde. Cada dimensión
se puntúa: **0 inaceptable · 1 aceptable · 2 bueno**.

| # | Dimensión | Pregunta de escucha |
|---|---|---|
| 1 | Coherencia armónica | ¿Las progresiones suenan dentro del mismo mundo? |
| 2 | Estructura | ¿Se reconoce el recorrido sin analizarlo? |
| 3 | Desarrollo musical | ¿La 2ª vuelta suena distinta a la 1ª? |
| 4 | Motivo | ¿Queda una idea que «vuelve»? |
| 5 | Riff | ¿Hay un gesto memorable? |
| 6 | Melodía | ¿La línea principal es cantable y con aire? |
| 7 | Solo | ¿El solo aporta o estorba? |
| 8 | Orquestación | ¿Cada instrumento tiene un papel claro? |
| 9 | Densidad | ¿Hay respiración o es muro constante? |
| 10 | Variación | ¿Dos canciones con distinta seed suenan distintas? |
| 11 | Identidad musical | ¿Suena a «la casa» (DMD) o genérico? |
| 12 | Duración | ¿La pieza se acaba a tiempo, ni antes ni arrastrada? |
| 13 | Transiciones | ¿Las uniones entre secciones fluyen o hay golpes? |

**Umbral de aceptación global (§5.4/§6.5):** ≥8 de 13 dimensiones con nota ≥1 y
ninguna con 0. **Regla de oro:** el SHA256 (L1) es estándar de determinismo, NO
de calidad; la calidad solo se declara con L3+D o L4 (§11.1).

## 2. Procedimiento práctico (§6.6)

1. **Serie base**: 3 canciones Automatic con seeds fijas **101/202/303**
   (comparabilidad; el modo Automatic nunca pide seed al usuario — existen en
   `tests/control_center/golden_f2/`).
2. **Serie MVP sin seed** (§5.4, Fase 5): 5 canciones con solo identidad +
   controles, seed auto-generada y persistida — `output/plan_f5/serie_base/`
   (perfiles: full, sax, drums, sax_vibes, atmospheric).
3. **Comparación con ancla**: cada pieza se escucha contra la ancla dorada de la
   casa `demo_medianoche/full/3113` (referencia de calidad mínima conocida).
4. **Contraste entre seeds**: dos canciones con la misma identidad y seeds
   distintas deben diferir en ≥3 dimensiones medibles de capa C (densidad,
   curva, riff) — prueba contra la monotonía.
5. **Ciclo de regeneración**: de cada pieza se anota **keep / regen**. El
   Automatic «suficiente para producción personal» se define como: en una serie
   de 10 generaciones reales del usuario, ≥7 keep y ninguna inaceptable (0 en
   capa D) — no como un score técnico.
6. **Registro acumulable**: cada veredicto se guarda con fecha, seed y notas por
   dimensión, para comparar contra la banda previa en la fase siguiente.

## 3. Formato de registro (`escucha.md` por pieza)

```markdown
# Escucha — <título> (seed <seed>, perfil <perfil>, <fecha>)
| Dimensión | Nota (0/1/2) | Nota breve |
|---|---|---|
| 1. Coherencia armónica | | |
| ... (las 13) | | |
Veredicto: APROBADO / APROBADO CON OBSERVACIONES / RECHAZADO
keep/regen: keep | regen
Comentarios: <libre>
```

## 4. Piezas pendientes de veredicto (estado F5)

| Pieza | Dónde | Protocolo específico |
|---|---|---|
| Álbum «Ecos de Neblina» (3 pistas) | `output/plan_f4/ecos_de_neblina/` | `output/plan_f4/PROTOCOLO_ESCUCHA_F4.md` (escucha comparada) |
| Serie base MVP (5 pistas) | `output/plan_f5/serie_base/` | este documento (§1–§3) |

El veredicto es el ÚNICO gate que resta a las fases 4–5: todo lo automatizable
(L1/L2/L3, capas A/B/C, reglas de álbum, diversidad) está ejecutado y en verde.
