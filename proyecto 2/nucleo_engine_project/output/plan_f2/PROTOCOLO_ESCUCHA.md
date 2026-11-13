# Protocolo de escucha — Capa D de la serie F2 (spec v1.4, §6.4-§6.6)

La capa D no es automatizable: la decide la persona (§6.4). Este documento
prepara la escucha de la producción del intérprete (F2) para que el veredicto
sea comparable y acumulable.

## Serie a escuchar (comparada, §6.6)

- **Ancla de referencia**: `output/produccion/demo_medianoche/` (seed 3113,
  `full`) — la calidad mínima conocida de la casa, para comparar cada tema.
- **Gate F2 (5 temas)**: `output/plan_f2/f2_101_dark_triphop`,
  `f2_202_doom_dark_jazz`, `f2_303_doom_triphop`, `f2_auto_total`,
  `f2_ausente_jazz_media`.
- **Serie P-02 (solos, 6 temas)**: `output/plan_f2/p02_solos/p02_*`.

## Escala por dimensión (13 dimensiones, §6.5)

0 = inaceptable · 1 = aceptable · 2 = bueno. Pregunta por dimensión:

| # | Dimensión | Pregunta |
|---|---|---|
| 1 | Coherencia armónica | ¿Las progresiones suenan dentro del mismo mundo? |
| 2 | Estructura | ¿Se reconoce el recorrido sin analizarlo? |
| 3 | Desarrollo musical | ¿La 2ª vuelta suena distinta a la 1ª? |
| 4 | Motivo | ¿Queda una idea que "vuelve"? |
| 5 | Riff | ¿Hay un gesto memorable? |
| 6 | Melodía | ¿La línea principal es cantable y con aire? |
| 7 | Solo | ¿El solo aporta o estorba? |
| 8 | Orquestación | ¿Cada instrumento tiene un papel claro? |
| 9 | Densidad | ¿Hay respiración o es muro constante? |
| 10 | Variación | ¿Dos canciones con distinta seed suenan distintas? |
| 11 | Identidad musical | ¿Suena a "la casa" (DMD) o genérico? |
| 12 | Duración | ¿La pieza se acaba a tiempo, ni antes ni arrastrada? |
| 13 | Transiciones | ¿Las uniones fluyen o hay golpes? |

**Una canción pasa capa D si ≥8 dimensiones ≥1 y ninguna = 0** (§6.4).

## Plantilla de registro (una por canción)

```
# escucha — <carpeta> (seed <n>, perfil <p>)
Fecha: ____ · Oyente: ____
Dimensiones: 1:__ 2:__ 3:__ 4:__ 5:__ 6:__ 7:__ 8:__ 9:__ 10:__ 11:__ 12:__ 13:__
Veredicto: [ ] pasa (≥8 dim ≥1, ninguna 0)   Keep/Regen: ____
Notas: ______________________________________________
```

## Uso del veredicto

- **Gate F2** (§16.2): escucha D ≥8/13 dim ≥1 sobre la serie → habilita el
  tag `cc-f2-ok` (el resto de gates ya está cumplido: 5/5 A+B, capa C,
  bloqueo locked, seed automática, P-01/P-04 cerrados, P-02 con registro).
- **Contraste entre seeds** (§6.6.3): comparar `f2_101` (F minor) contra el
  ancla (F# minor) y entre temas: ≥3 dimensiones medibles distintas.
- **P-02**: escuchar la serie `p02_*` centrada en la dimensión 7 (Solo) para
  cerrar si los solos de rhodes/vibraphone "aportan o estorban".
