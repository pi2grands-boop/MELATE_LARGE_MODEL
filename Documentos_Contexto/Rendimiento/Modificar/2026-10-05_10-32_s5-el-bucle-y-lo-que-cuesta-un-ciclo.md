# El bucle rápido con el ciclo, y lo que cuesta incorporar un sorteo

- **Fecha/hora:** 2026-10-05 10:32
- **Área:** Rendimiento · **Acción:** Modificar
- **Chat / página:** cierre de la Fase 5 · `tests/`, `src/melate/ciclo.py`
- **Archivos afectados:** `tests/test_ciclo.py`, `tests/test_almacen.py`, `tests/test_app.py`,
  `tests/test_protocolo.py`, `tests/conftest.py`

## Las cifras

| | Al cerrar la Fase 4 | Al cerrar la Fase 5 |
|---|---|---|
| Bucle rápido (`-m "not lento and not red"`) | 213 pruebas, 12,6-12,7 s | **287 pruebas, 35 s** con B15; con 286, 37-39 s esa mañana y, con 265, 25,0 s la noche antes |
| Suite completa | 242 pruebas, 136,3 y 164,2 s | **321 pruebas, 234 s**; con 320, 188 s. 7 conexiones, como antes |
| Los lentos solos | — | 29 pruebas, 181 s |
| `scripts/mutar.py` | 46 mutaciones, 2 min 9 s - 2 min 41 s | **97 mutaciones, 450 s** con el portátil a batería; con 96, 312 s |
| Una corrida del ciclo con un sorteo nuevo | — | **62 s** con el 4273 y **63 s** con el 4274, de punta a punta |
| A mano, sobre el snapshot del 4274 | — | el informe, 30,4 s; el veredicto, 3,7 s; la popularidad, desde la caché, 1,3 s |
| El informe sobre el snapshot del 2026-10-02 | 72,6 s, medido en la Fase 1 | **31,5 y 28,9 s**, con la misma CPU y sin un cambio en el backtest desde entonces |

**Esta máquina varía mucho**, y las dos últimas filas lo dicen mejor que nada: el mismo informe, con
el mismo código, tarda hoy menos de la mitad que en la Fase 1, y el mismo bucle rápido tardaba la
noche antes un 20 % menos que esta mañana. Por eso el bucle se midió intercalado: **31 s sin los 20
tests del cierre y 37-39 s con ellos**, en la misma tanda.

## Dónde se va el tiempo nuevo

- **El ciclo: 50 pruebas, ~0,3 s cada una.** Usan los CSV reales a propósito —el sorteo nuevo es real
  y el snapshot que congela tiene que ser, byte a byte, el de la Fase 1—: descargar, comparar, validar
  y congelar, de verdad. La única grasa que había, los falsos parseando los mismos ficheros en cada
  test, se quitó con una caché (de 26,3 a 25,0 s).
- **Los 20 tests del procedimiento de cierre**, ~7 s: cada comprobación de las filas nuevas con su
  caso, el reintento del renombrado, los dos valores de la ventana y de las simulaciones, y dos de la
  base que construyen la suya.

## Por qué no se marcó nada como `lento`

Por la misma razón que en las fases 2, 3 y 4: un test fuera del bucle rápido deja de correrse a diario,
y todas las mutaciones del ciclo las cazan tests rápidos. **Y el usuario lo aceptó**, con estas
palabras: *«Si, mientras más mejor.»* (C4,
`Fases/2026-10-04_ciclo-vivo/Decisiones/2026-10-04_18-59_s5-lo-que-decidio-el-usuario.md`).

## Cómo verificar

```powershell
.venv\Scripts\python.exe -m pytest tests -m "not lento and not red" -q   # 287 pruebas, ~30-40 s
.venv\Scripts\python.exe -m pytest tests -q                              # 321 pruebas, ~3-4 min
.venv\Scripts\python.exe scripts\mutar.py                                # 97 de 97, ~5-8 min
```

## Cómo revertir

No hay nada que revertir: es una medida. Si el bucle volviera a crecer, el camino es el de siempre —
buscar dónde se va el tiempo— y no el marcador `lento`.

Relacionado: `Rendimiento/Modificar/2026-10-04_16-35_s4-el-bucle-rapido-con-la-app.md`,
`Rendimiento/Añadir/2026-10-03_00-13_s1-coste-del-informe.md`,
`Fases/2026-10-04_ciclo-vivo/Bugs/2026-10-04_20-51_s5-review-ciclo.md`.
