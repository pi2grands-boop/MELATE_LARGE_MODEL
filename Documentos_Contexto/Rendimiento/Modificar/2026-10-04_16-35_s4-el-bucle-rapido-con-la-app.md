# El bucle rápido con la app: de ~5 s a ~13 s, aceptado por el usuario

- **Fecha/hora:** 2026-10-04 16:35
- **Área:** Rendimiento · **Acción:** Modificar
- **Chat / página:** cierre de la Fase 4 · `tests/`
- **Archivos afectados:** `tests/conftest.py`, `tests/test_almacen.py`, `tests/test_app.py`,
  `tests/test_lanzador.py`, `src/melate/almacen.py`

## Las cifras

| | Al cerrar la Fase 3 | Al cerrar la Fase 4 |
|---|---|---|
| Bucle rápido (`-m "not lento and not red"`) | 135 pruebas, 5,34 s | **213 pruebas, 12,6-12,7 s** (cuatro pasadas) |
| Las que no son de la Fase 4, solas | 135 pruebas, 5,34 s | 137 pruebas (2 nuevas en sus ficheros), 5,1-5,6 s: no se hicieron más lentas |
| Suite completa | 164 pruebas, 135,2 s | **242 pruebas, 136,3 y 164,2 s** (dos pasadas) |
| `scripts/mutar.py` | no existía | **46 mutaciones, 2 min 9 s - 2 min 41 s** |
| Construir `melate.duckdb`, dentro del proceso | — | 0,16-0,31 s |
| Construirla con su orden, proceso nuevo | — | 1,9-2,6 s: casi todo es importar el laboratorio, que verifica los sellos (1,8 s medidos con `-X importtime`, la mitad SciPy) |
| Del lanzador a la app respondiendo, con la base al día | — | 3 s |

La suite completa varía mucho en esta máquina —la Fase 3 ya midió entre 128,7 y 153,9 s—, así que
se publica como «~150 s» y con el rango aquí.

## Dónde se va el tiempo nuevo

Lo que no se pudo quitar es el coste real de probar un subsistema nuevo: importar Streamlit y DuckDB
(~1,6 s), construir las bases de prueba y las instancias de `AppTest`. Lo que sí se quitó:

| Qué | Efecto |
|---|---|
| Construir la base en una sola transacción | 0,31 s → 0,16 s por base, medido al hacerlo |
| Bases adversarias compartidas por sesión: una reúne todo lo que no debe llegar a la cabecera | ~20 construcciones → 5 |
| Un único recorrido de `AppTest` para las cinco pantallas, la frontera y la prohibición de cómputo y red | 20 instancias → 12 |
| En los tests, no buscar componentes personalizados de Streamlit: era **el 80 % del coste de cada `AppTest`**, recorriendo los metadatos de los 69 paquetes instalados | ~15 s → ~11,5 s |
| Los tests del lanzador prueban el diagnóstico de la base en cinco estados **sin construir**, y la construcción una sola vez | +3,5 s → +1,5 s |

Probado y descartado: insertar desde un DataFrame (0,157 s contra 0,157 s) y bloques de 16 KB (la
base pasa de 5 MB a 1 MB pero solo es un 12 % más rápida).

## Por qué no se marcó nada como `lento`

Es lo que este proyecto decidió no hacer dos veces
(`Rendimiento/Arreglos_Bugs/2026-10-03_01-59_la-suite-rapida-no-era-rapida.md` y
`Rendimiento/Arreglos_Bugs/2026-10-03_05-15_s3-el-voraz-cuadratico.md`): un test sacado del bucle
rápido deja de correrse a diario. Los de la app son los que vigilan que no mienta.

**Y el usuario lo aceptó** (C7 de
`Fases/2026-10-04_app-local/Decisiones/2026-10-04_11-00_s4-lo-que-decidio-el-usuario.md`), con estas
palabras: *«me gusta que tarde y no sea tan rápido, eso significa procesamiento de datos»*. Queda
escrito para que nadie lo «arregle» sacando los tests de la app del bucle.

## Cómo verificar

```powershell
.venv\Scripts\python.exe -m pytest tests -m "not lento and not red" -q   # 213 pruebas, ~13 s
.venv\Scripts\python.exe -m pytest tests -q                              # 242 pruebas, ~150 s
.venv\Scripts\python.exe scripts\mutar.py                                # 46 de 46, ~2-3 min
```

## Cómo revertir

No hay nada que revertir aquí: es una medida. Si el bucle rápido volviera a crecer, el camino es el
de las dos veces anteriores —buscar dónde se va el tiempo— y no el marcador `lento`.

Relacionado: `Rendimiento/Arreglos_Bugs/2026-10-03_05-15_s3-el-voraz-cuadratico.md`,
`Rendimiento/Arreglos_Bugs/2026-10-03_01-59_la-suite-rapida-no-era-rapida.md`,
`Fases/2026-10-04_app-local/Bugs/2026-10-04_10-05_s4-review-base-app-y-red.md`,
`Fases/2026-10-04_app-local/Bugs/2026-10-04_11-39_s4-review-lanzador.md`.
