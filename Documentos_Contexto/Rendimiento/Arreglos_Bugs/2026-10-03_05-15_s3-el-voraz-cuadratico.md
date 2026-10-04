# El bucle rápido volvió a crecer, y esta vez se arregló en vez de marcarse

- **Fecha/hora:** 2026-10-03 05-15
- **Área:** Rendimiento · **Acción:** Arreglos_Bugs

## Qué pasó

Con los 55 tests nuevos de la Fase 3, el bucle rápido pasó de **2,5 s a 26,09 s**. El `_MAPA.md`
prometía 2,5.

El culpable no eran los tests, era el algoritmo: el voraz de `portfolio.cartera()` recalculaba el
solape de cada candidata contra **todas** las ya elegidas, en cada ronda.

```
O(boletos × candidatas × elegidas)
```

Con 20 boletos y 8.000 candidatas aptas son del orden de 1,6 millones de intersecciones de
conjuntos por cartera, y los tests arman nueve.

## Por qué no se marcó como `lento`

Porque habría sido repetir el fallo que este proyecto ya documentó:
`Rendimiento/Arreglos_Bugs/2026-10-03_01-59_la-suite-rapida-no-era-rapida.md` cuenta cómo dos
tests de subproceso sin marcar dejaron el bucle rápido en 30 s mientras el mapa decía 5.

La lección de aquel documento no era «marca los tests lentos». Era que **un bucle rápido que deja
de ser rápido deja de correrse**, y entonces no protege nada. Marcar estos como `lento` habría
sacado del día a día justo los que vigilan que la cartera no prometa lo que no puede dar.

## El arreglo

El solape se lleva **al día**. Tras elegir un boleto se actualiza cada candidata contra ese boleto
y solo ese: el máximo de un conjunto al que se le añade un elemento es el máximo entre el anterior
y el nuevo.

```
O(boletos × candidatas)
```

## Lo medido

| | Antes | Después | Factor |
|---|---|---|---|
| `tests/test_cartera.py` | 10,75 s | **1,46 s** | 7,4× |
| Bucle rápido completo | 26,09 s | **5,08 s** | 5,1× |

Y las carteras que salen son **las mismas**: el cambio es de contabilidad, no de criterio. Lo fija
`test_la_misma_semilla_da_la_misma_cartera`.

## Las cifras del `_MAPA.md`, vueltas a medir

El mapa dice que estas dos se vuelven a medir al cerrar cada fase. Hechas:

| | Fase 2 | **Fase 3** |
|---|---|---|
| Bucle rápido (`-m "not lento and not red"`) | 72 pruebas, 2,5 s | **132 pruebas, 5,1 s** |
| Suite completa | 100 pruebas, ~136 s | **161 pruebas, 133 s** |

La suite completa **no creció en tiempo** pese a 61 pruebas más: las nuevas son de milisegundos y
el coste sigue dominado por el backtest, que es el 85 % y no se ha tocado.

## Dónde se va el tiempo ahora

Sin cambios respecto a la Fase 2: el backtest walk-forward de los tres juegos sigue siendo el 85 %
de la suite completa, y sigue creciendo de forma cuadrática. Optimizarlo sigue estando fuera de
toda fase a propósito (`_MAPA.md`): son 62 s hoy y ~110 s en cinco años.

`popularity.py` y `portfolio.py` no aportan coste medible a la suite completa. El coste real de
`popularity` no es de CPU sino **de red, y es deliberado**: 1 solicitud por segundo. Con la caché
poblada, cero.

## Cómo verificar

```powershell
Measure-Command { .venv\Scripts\python.exe -m pytest tests -q -m "not lento and not red" }
Measure-Command { .venv\Scripts\python.exe -m pytest tests -q }
```

## Cómo revertir

En `src/melate/portfolio.py`, sustituir el bloque que mantiene `solape` y `conj` por la llamada a
`_solape_maximo(c, elegidas)` dentro del bucle. Las carteras no cambian; el bucle rápido vuelve a
26 s.

Relacionado: `Rendimiento/Arreglos_Bugs/2026-10-03_01-59_la-suite-rapida-no-era-rapida.md`,
`Rendimiento/Añadir/2026-10-03_00-13_s1-coste-del-informe.md`,
`Fases/2026-10-03_popularidad/Bugs/2026-10-03_04-10_s3-review-popularidad-y-cartera.md`.
