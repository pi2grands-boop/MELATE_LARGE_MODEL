# El veredicto registra sobre qué datos juzgó

- **Fecha/hora:** 2026-10-04 16:35
- **Área:** Reproducibilidad · **Acción:** Arreglos_Bugs
- **Chat / página:** cierre de la Fase 4 · `src/melate/lab.py`
- **Archivos afectados:** `src/melate/lab.py`, `reportes/2026-10-04_veredicto.json`,
  `tests/test_almacen.py`, `entorno/pip-freeze-2026-10-04.txt`

## El fallo

La regla 6 del protocolo es *«guardar el hash del dataset y la semilla en cada corrida»*. El informe
la cumplía desde la Fase 1 (`reproducibilidad.datos`,
`Reproducibilidad/Añadir/2026-10-03_00-13_s1-linea-base-reproducida.md`). **El laboratorio no**, y
es la pieza que juzga: `reportes/2026-10-03_veredicto.json` no dice con qué datos se emitió, ni su
hash, ni su origen, ni el último sorteo que había.

Con el holdout vacío no se notaba: cualquier dato da 0 sorteos posteriores al sello. Deja de ser
inocuo con el primer sorteo del holdout, que es el 4274. Se encontró **leyendo el código antes de
empezar la Fase 4** (`Fases/2026-10-04_app-local/Inventario/2026-10-04_00-36_s0-estado-de-partida.md`,
H1), porque la app tenía que decir sobre qué datos se juzgó y no había de dónde sacarlo.

## El arreglo

`lab._datos` escribe, por juego, el SHA-256, el origen, los bytes, el último sorteo y su fecha, en
la clave nueva `datos` del veredicto, y la orden lo imprime («== Datos sobre los que se juzga»). El
hash sale de los bytes que se cargaron (`attrs`, la misma regla que el informe), nunca de una segunda
lectura que podría traer ya el sorteo siguiente.

`reportes/2026-10-04_veredicto.json` es el primer veredicto que lo registra: datos hasta el sorteo
4272, con los tres SHA-256 del snapshot. El de la Fase 2 se conserva tal cual —un reporte publicado
no se reescribe— y la app dice de él que no registra sus datos. La forma nueva está en
`Estructura_Datos/Modificar/2026-10-04_16-35_s4-veredicto-popularidad-y-cartera.md`.

**Test:** `test_el_veredicto_registra_los_datos_sobre_los_que_juzga`, con dos valores: sobre el
snapshot dice 4272, y sobre los mismos datos recortados dice 4262. Si el campo saliera de una
constante o de otra lectura, los dos darían lo mismo. Tiene su mutación en `scripts/mutar.py`.

## El entorno, congelado otra vez

`entorno/pip-freeze-2026-10-04.txt`: **66 paquetes** (eran 43) más la instalación editable. Los 23
nuevos son `streamlit==1.65.0`, `duckdb==1.5.6` y sus dependencias. **Ninguna versión de las que
reproducen la línea base se movió**: Python 3.13.9, numpy 2.5.3, pandas 2.3.3, scipy 1.18.1 y
scikit-learn 1.9.1. `tests/test_paridad.py` sigue en verde con tolerancia cero. Los congelados
anteriores se conservan: el de 2026-10-02 es el que reproduce la línea base.

## Cómo verificar

```powershell
.venv\Scripts\python.exe -m melate.lab --prereg prereg\2026-10-03_logistica-revancha.json --datos data\raw\2026-10-02
#   == Datos sobre los que se juzga: los tres juegos, hasta el 4272, con su SHA-256
.venv\Scripts\python.exe -m pytest tests\test_almacen.py -k registra_los_datos -q
```

## Cómo revertir

Quitar `_datos` y la clave `datos` de `lab.evaluar`. **No se recomienda**: el veredicto volvería a
ser la única salida del proyecto sin la procedencia que exige su regla 6.

Relacionado: `Reproducibilidad/Añadir/2026-10-03_00-13_s1-linea-base-reproducida.md`,
`Estructura_Datos/Modificar/2026-10-04_16-35_s4-veredicto-popularidad-y-cartera.md`,
`Fases/2026-10-04_app-local/Inventario/2026-10-04_00-36_s0-estado-de-partida.md`.
