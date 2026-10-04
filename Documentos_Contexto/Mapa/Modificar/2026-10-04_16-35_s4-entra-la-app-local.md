# Entra la app local: un modo de mirar que no explora ni juzga

- **Fecha/hora:** 2026-10-04 16:35
- **Área:** Mapa · **Acción:** Modificar
- **Chat / página:** cierre de la Fase 4 · `Fases/2026-10-04_app-local/`
- **Archivos afectados:** `src/melate/almacen.py`, `src/melate/app.py`, `app/streamlit_app.py`,
  `.streamlit/config.toml`, `src/melate/lab.py`

## Qué cambia en el mapa

Hasta la Fase 3 el proyecto se usaba de tres formas, todas desde la línea de órdenes:
**explorar** (`melate.informe`), **juzgar** (`melate.lab`) y **medir a los jugadores**
(`melate.popularity`, `melate.portfolio`). La Fase 4 añade una cuarta: **mirar**.

```powershell
.venv\Scripts\python.exe -m melate.app      # http://127.0.0.1:8501
```

| Pregunta | Quién responde |
|---|---|
| ¿Qué dicen los reportes publicados, en una pantalla? | `app/streamlit_app.py`, que abre `src/melate/app.py` |
| ¿Qué hay en `reportes/` y `prereg/`, y qué de eso vale? | `src/melate/almacen.py`, que lo indexa en `melate.duckdb` |

**La cadena:** `reportes/*.json` y `prereg/*.json` → `almacen.construir`, que clasifica cada fichero,
verifica los sellos con la función del propio laboratorio y enlaza cada veredicto con su
preregistro → `melate.duckdb`, 16 tablas, cada una declarada como juzga, explora, mide o
procedencia → `almacen.leer`, en solo lectura → la app. Delante, el lanzador: pone la base al día,
anula la búsqueda de la IP pública de Streamlit y lo arranca atado a `127.0.0.1`.

**Mirar no calcula.** La app no recalcula, no descarga y no escribe; si algo tarda dos minutos en un
backend, no va en una pantalla, y la app enseña la orden que lo hace.

## La frontera, que la app no puede borrar

En la línea de órdenes, `melate.informe` y `melate.lab` son dos programas y nadie los confunde. En una
pantalla, una p = 0.0165 y un veredicto podían acabar en la misma tabla. Por eso:

- **La cabecera de todas las pantallas sale solo del laboratorio**, de `almacen.veredicto_vigente`,
  que lee únicamente veredictos válidos —sello que verifica, coherentes— y ni siquiera mira la tabla
  de informes. Sin uno, *sin ventaja demostrada* por defecto.
- **Lo exploratorio vive en su pantalla**, con su aviso delante, y se llama «resumen exploratorio»,
  nunca veredicto. Una q ≤ 0.05 en la exploración es **una candidata a preregistrar**, no una ventaja.
- Las dos cosas tienen test, con un informe forjado de q = 0.01 y con un veredicto forjado que
  proclama la ventaja sin cumplir sus condiciones.

## Los contratos entre módulos

- La app importa solo `datetime`, `pathlib`, `pandas`, `streamlit`, `melate.almacen` y
  `melate.protocolo` (test sobre su árbol sintáctico).
- `almacen` arriba solo importa la biblioteca estándar, `constantes` y `protocolo`; el laboratorio
  entra únicamente dentro de `construir`, para verificar sellos (test).
- `melate.lab` registra ahora sobre qué datos juzgó, porque la cabecera tiene que decirlo
  (`Reproducibilidad/Arreglos_Bugs/2026-10-04_16-35_s4-el-veredicto-registra-sus-datos.md`).

## Qué NO cambia

- **El veredicto: *sin ventaja demostrada*, 0 de 5 condiciones.** La app lo enseña; no puede
  cambiarlo.
- `baseline_auditoria.py` y la paridad con tolerancia cero.
- La familia de 36 pruebas. Las nueve de log-loss se quedan fuera, con su porqué
  (`Protocolo_Estadistico/Decisiones/2026-10-04_10-45_s4-el-log-loss-no-entra-en-la-familia.md`).
- Ningún número de la app lo calcula la app.

## Cómo verificar

```powershell
.venv\Scripts\python.exe -m melate.app
.venv\Scripts\python.exe -m pytest tests\test_almacen.py tests\test_app.py tests\test_lanzador.py -q
```

## Cómo revertir

Borrar `app/`, `.streamlit/`, `src/melate/almacen.py`, `src/melate/app.py`, sus tres ficheros de test
y las mutaciones de `scripts/mutar.py` que los nombran. El cálculo no depende de nada de esto. Lo que
conviene conservar aunque se quite la app: que el veredicto registre sus datos.

Relacionado: `Mapa/Modificar/2026-10-03_05-15_s3-entran-popularidad-y-cartera.md`,
`Mapa/Modificar/2026-10-03_01-30_s2-entra-el-laboratorio.md`,
`Interconexion/Añadir/2026-10-04_16-35_s4-las-pantallas-de-la-app.md`,
`Red/Añadir/2026-10-04_16-35_s4-que-sirve-la-app-y-a-quien.md`,
`Almacenamiento/Decisiones/2026-10-04_00-40_s4-que-entra-en-melate-duckdb.md`,
`Fases/2026-10-04_app-local/99_CIERRE.md`.
