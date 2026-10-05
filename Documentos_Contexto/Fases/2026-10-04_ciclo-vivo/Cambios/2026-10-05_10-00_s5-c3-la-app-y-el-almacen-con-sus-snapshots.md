# La app y el almacén, enlazados con los snapshots: C3

- **Fecha/hora:** 2026-10-05 10:00
- **Área:** Fases/2026-10-04_ciclo-vivo · **Acción:** Cambios
- **Chat / página:** sesión de la Fase 5 · C3, aprobada por el usuario («Ok» y «dale con C3»)
- **Archivos afectados:** `src/melate/almacen.py`, `src/melate/lab.py`, `src/melate/protocolo.py`,
  `app/streamlit_app.py`, `tests/conftest.py`, `tests/test_almacen.py`, `tests/test_app.py`,
  `tests/test_protocolo.py`, `scripts/mutar.py`

## Qué se hizo

**El almacén** (`src/melate/almacen.py`) sabe ahora qué está congelado:

- `_leer_snapshots` (`:204`) lee los `data/raw/*/SHA256.txt` con una forma estricta —dos campos, un
  hash de 64 caracteres, un fichero de un juego— y salta las carpetas que empiezan por punto, que son
  las que el ciclo está escribiendo. Cada uno entra en `fuentes`, y sus líneas en la tabla nueva
  `snapshots`.
- `_snapshot_de_los_datos` (`:243`) enlaza cada veredicto e informe con su snapshot **por SHA-256**, no
  por la ruta: los tres juegos tienen que estar congelados, y en la misma carpeta.
- **Un veredicto cuyos datos no son un snapshot congelado no vale** (`_validar_veredicto`, `:400`), y
  dice por qué: que no registra sus datos, que no están congelados o que vienen de snapshots distintos.
- `construir` lee `--raw` (por defecto, `data/raw` junto a `reportes/`) y se niega a seguir si no
  existe; la frescura vigila también los `SHA256.txt`, así que un snapshot nuevo deja la base vieja.
- **El esquema pasa a la versión 2** (`:38`): 17 tablas. El lanzador reconstruye una base del esquema 1
  él solo, y la app se niega a usarla.

**El laboratorio** (`src/melate/lab.py`) publica en cada veredicto `holdout_necesario` (`:312`), la
frontera de la condición 5 desde C1 —1 778 con el preregistro sellado—, para que la app la enseñe sin
calcular nada. `detectable(n)` (`:158`) es ahora la única copia de la fórmula del mínimo detectable.
Y el motivo de la condición 1 dice «1 sorteo» en singular (`protocolo._sorteos`, `:119`).

**La app** (`app/streamlit_app.py`) enseña el holdout como lo que es:

- «1 sorteo», nunca «1 sorteos» (`sorteos()`, `:134`), y a su lado los que necesita la condición 5
  (`necesita()`, `:142`), en la cabecera y en la métrica.
- La tabla de condiciones es estática (`st.table`, `:257`) para que el motivo de la condición 5 no se
  corte, y sus celdas se escapan: `st.table` pasa cada una por Markdown.
- Los aciertos por boleto junto al Δ, y debajo el mínimo detectable de ese holdout y cuándo podrá
  cumplirse la condición 5.
- De qué snapshot sale cada veredicto e informe, y una tabla nueva, «Snapshots congelados»
  (`:590`), en la pantalla de procedencia.
- La orden para un veredicto nuevo es el ciclo (`ORDEN_CICLO`, `:42`), no el laboratorio sin
  `--datos`; y la de reproducir un veredicto lleva `--datos data\raw\<su snapshot>`.
- Los miles con un espacio de no separación (`entero()`, `:128`): «1 778» no se parte en dos líneas.

**Tests:** en `tests/test_almacen.py`, `tests/test_app.py` y `tests/test_protocolo.py`, más el
veredicto de un sorteo de `tests/conftest.py`, con la forma exacta del de `melate.lab`. Las bases de
prueba se construyen con lo que había al cerrar la Fase 4 (`REPORTES_FASE_4`), y un test aparte
vigila lo que haya hoy en el repositorio, crezca lo que crezca. **Mutaciones:** las «(C3)» y las «F5
app:» de `scripts/mutar.py`, y dos del cierre (`snapshots_distintos` y `--raw`).

## Por qué

H3 y H4 del inventario: un veredicto emitido sin `--datos` se juzgaría sobre bytes que no quedan
guardados, y un holdout de un sorteo podía parecer más de lo que es. C3 convierte *«nunca sobre una
descarga en vivo que no quede guardada»* de costumbre en regla con test, y hace que la app diga cuánto
falta, con el número que publica el laboratorio.

## Impacto en seguridad / conexiones / datos

- **Seguridad:** las celdas de `st.table` pasan por Markdown y se escapan como todo lo que viene de un
  fichero (B8 de la review). El almacén no interpreta nada del `SHA256.txt` fuera de su forma.
- **Conexiones:** ninguna. La app sigue sin salir a la red: 0 conexiones con el proxy, también con el
  veredicto del 4274.
- **Datos:** el veredicto de la Fase 2, que no registra sus datos, pasa a «no válido», con su motivo.
  Nunca fue el vigente: la cabecera no cambió por eso. Ninguna cifra publicada cambia.

## Lo medido

| Qué | Resultado |
|---|---|
| Review del bloque | B1-B9, cerrada el 2026-10-04 a las 21:52 (`Fases/2026-10-04_ciclo-vivo/Bugs/2026-10-04_20-37_s5-review-c3-app-y-almacen.md`) |
| Y en el cierre | B11: los juegos de snapshots distintos y `--raw`, sin test hasta entonces; ahora con dos tests y dos mutaciones |
| La app, en vivo con el 4274 | cabecera «holdout de 1 sorteo de los 1 778 que necesita la condición 5»; los cinco motivos enteros; 0 conexiones hacia fuera |
| La base real | 17 tablas, esquema 2, tres snapshots; el vigente, el veredicto del 4274 |

## Cómo verificar / revertir

```powershell
.venv\Scripts\python.exe -m pytest tests\test_almacen.py tests\test_app.py -q
.venv\Scripts\python.exe scripts\mutar.py --solo "F5"
.venv\Scripts\python.exe -m melate.almacen      # «snapshots congelados: 2026-10-02, 2026-10-02_4273, …»
```

**Revertir:** volver a `VERSION_ESQUEMA = 1` y quitar de `almacen.py` la lectura de los `SHA256.txt`,
el enlace por hash y la condición de validez; quitar `holdout_necesario` y `detectable` de `lab.py`; y
en la app, las funciones `sorteos`, `necesita` y lo que las usa. **No se recomienda:** un veredicto
sobre datos que no están guardados volvería a poder ser el vigente, y la app volvería a enseñar un
sorteo de holdout sin decir que hacen falta 1 778.

Relacionado: `Fases/2026-10-04_ciclo-vivo/Bugs/2026-10-04_20-37_s5-review-c3-app-y-almacen.md`,
`Fases/2026-10-04_ciclo-vivo/Decisiones/2026-10-04_18-59_s5-lo-que-decidio-el-usuario.md`,
`Fases/2026-10-04_ciclo-vivo/Inventario/2026-10-04_18-16_s0-estado-de-partida.md`,
`Fases/2026-10-04_ciclo-vivo/Bugs/2026-10-04_20-51_s5-review-ciclo.md`.
