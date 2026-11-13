# Protocolo de escucha F4 — «Ecos de Neblina» (3 pistas)

Gate de Capa D de la Fase 4 (spec v1.4 §12.1: «escucha comparada ≥ banda»; protocolo §6.6).
Este gate NO es automatizable: corresponde al oído del usuario. Todo lo demás de la fase
está cerrado y verificado (ver `INFORME_FASE_4.md`).

## Reproducción exacta (determinista; mismo blueprint ⇒ mismos MIDIs)

```bash
cd nucleo_engine_project

# álbum completo (ya producido; regenera byte a byte)
python3 -m album producir albumes/ecos_de_neblina/album.json --out output/plan_f4/ecos_de_neblina
```

Para AUDIO: los MIDIs se convierten con cualquier reproductor/SF2 del entorno del usuario
(mismo flujo que F2/F3 — p. ej. Suno, o el comando `fluidsynth_windows` documentado por
pista en `manifiesto.json` y `evidencia.json` de cada pista):

| # | Archivo MIDI | Qué escuchar primero |
|---|---|---|
| 1 | `01_umbral_de_neblina.mid` (2:30, atmospheric) | la frase firma del sax en el verse (compases 9–12) y su retorno en el chorus |
| 2 | `02_camara_de_espejos.mid` (5:00, full) | el vibraphone en el puente (clímax); la firma está +5 semitonos (Bb minor) y reaparece en el segundo coro |
| 3 | `03_marea_baja_de_neon.mid` (5:00, sax_rhodes, sin drums) | el rhodes toma el momento (puente); el sax acompaña; SIN motivo firma — el cierre respira |

## Dimensiones de escucha comparada (≥ banda F2, como pide el gate)

1. **Identidad audible**: ¿las 3 suenan a la misma casa (dark triphop: sax tenor + rhodes + pad)?
2. **Variación real**: ¿se distinguen entre sí (perfil, registro, energía) sin parecer de otro álbum?
3. **Arco**: ¿apertura → clímax → cierre se percibe como arco de energía?
4. **Motivo firma**: ¿se reconoce el contorno que reaparece (pistas 1–2)? ¿La pista 3 se siente como respiro, no como otra cosa?
5. **Fatiga / saturación**: ¿alguna pista satura o aburre (comparar contra el álbum previo `noches_largas` si se desea)?

## Veredicto (registro)

- [ ] APROBADO — el álbum supera la banda de escucha comparada; F4 cierra COMPLETAMENTE.
- [ ] APROBADO CON OBSERVACIONES — registrar qué dimensión y qué pista; se decide si entra a F5 como ajuste.
- [ ] RECHAZADO — registrar dimensiones por debajo de banda; rollback/regeneración según §14 del spec.

Fecha de veredicto: __________  · Firmante: usuario (Capa D)
