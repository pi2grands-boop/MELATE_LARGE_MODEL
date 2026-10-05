# Entra el ciclo vivo: un quinto modo, incorporar los sorteos nuevos

- **Fecha/hora:** 2026-10-05 10:04
- **Área:** Mapa · **Acción:** Modificar
- **Chat / página:** cierre de la Fase 5 · `Fases/2026-10-04_ciclo-vivo/`
- **Archivos afectados:** `src/melate/ciclo.py`, `src/melate/almacen.py`, `src/melate/lab.py`,
  `src/melate/protocolo.py`, `app/streamlit_app.py`

## Qué cambia en el mapa

Hasta la Fase 4 el proyecto trabajaba sobre una foto fija, `data/raw/2026-10-02/`, hasta el sorteo
4272, y se usaba de cuatro formas: **explorar** (`melate.informe`), **juzgar** (`melate.lab`),
**medir a los jugadores** (`melate.popularity`, `melate.portfolio`) y **mirar** (`melate.app`). La
Fase 5 añade la que alimenta a las demás: **incorporar los sorteos que van llegando**.

```powershell
.venv\Scripts\python.exe -m melate.ciclo
```

| Pregunta | Quién responde |
|---|---|
| ¿Hay sorteos nuevos, y son buenos? | `melate.ciclo`: el oficial, el pasado byte a byte, la validación y los testigos |
| ¿Sobre qué bytes se calculó esta cifra? | El snapshot cuyo nombre lleva el reporte, y su `SHA256.txt` |
| ¿Qué dice el preregistro con los sorteos posteriores a su sello? | El veredicto que el ciclo deriva sobre cada snapshot nuevo |

**La cadena:** el oficial → `melate.ciclo` → `data/raw/<fecha>_<sorteo>/`, congelado e inmutable →
sobre él, la popularidad, el informe y el veredicto de cada preregistro, en `reportes/<snapshot>_*.json`
→ `melate.almacen`, que enlaza cada reporte con su snapshot **por SHA-256** → `melate.duckdb` → la app.

## Lo que el ciclo no cambia de las fronteras

- **El ciclo no es un sexto juez.** Llama al laboratorio, que sigue siendo lo único que juzga; el ciclo
  solo garantiza que juzgue sobre bytes congelados.
- **La app no lanza el ciclo**: ni descarga, ni recalcula, ni escribe. Enseña su orden.
- **El ciclo no se automatiza.** Es una orden de terminal que se lanza a mano: pide páginas a un
  tercero, y si bloquea, se para y se pregunta.

## Los contratos nuevos entre módulos

- `melate.ciclo` importa `ingest`, `validate`, `popularity`, `informe`, `lab` y `almacen`, y ninguno
  de ellos lo importa a él.
- `melate.lab` publica en el veredicto `holdout_necesario`, y la condición 5 exige un holdout capaz de
  ver el efecto declarado (C1:
  `Protocolo_Estadistico/Decisiones/2026-10-04_18-58_s5-la-condicion-5-exige-un-holdout-capaz.md`).
- `melate.almacen` solo da por válido un veredicto cuyos datos son un snapshot congelado.

## Qué NO cambia

- **El veredicto: *sin ventaja demostrada*.** El primero con holdout —un sorteo, el 4274— lo dice con
  2 de 5 condiciones, y lo dirá por construcción hasta el sorteo 1 778 del holdout.
- `baseline_auditoria.py`, la paridad con tolerancia cero y las cifras de la línea base del
  `CLAUDE.md`, que siguen siendo las del snapshot del 2026-10-02.
- La familia de 36 pruebas.

## Cómo verificar

```powershell
.venv\Scripts\python.exe -m melate.ciclo --comprobar
.venv\Scripts\python.exe -m pytest tests\test_ciclo.py tests\test_almacen.py -q
```

## Cómo revertir

Quitar el ciclo está descrito en
`Fases/2026-10-04_ciclo-vivo/Cambios/2026-10-05_10-03_s5-el-ciclo-vivo.md`. No se recomienda: el
proyecto volvería a una foto fija, y cada sorteo, a congelarse a mano.

Relacionado: `Mapa/Modificar/2026-10-04_16-35_s4-entra-la-app-local.md`,
`Almacenamiento/Decisiones/2026-10-04_20-10_s5-el-ciclo-vivo.md`,
`Almacenamiento/Modificar/2026-10-05_10-05_s5-los-snapshots-los-congela-el-ciclo.md`,
`Fases/2026-10-04_ciclo-vivo/99_CIERRE.md`.
