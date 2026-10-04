# Las pantallas de la app y cómo se enlazan

- **Fecha/hora:** 2026-10-04 16:35
- **Área:** Interconexion · **Acción:** Añadir
- **Chat / página:** cierre de la Fase 4 · `app/streamlit_app.py`
- **Archivos afectados:** `app/streamlit_app.py`

Es el primer documento de `Interconexion/`: hasta la Fase 4 no había piezas de interfaz que enlazar.

## El orden en que se pinta cada pantalla

1. **Las tres negativas, antes que nada.** Si la red no es la de esta máquina (dirección que no es
   de *loopback*, o telemetría encendida), si no hay base, o si la base es de otro esquema, la app
   pinta la cabecera por defecto —*sin ventaja demostrada*—, el motivo y la orden que lo arregla, y
   se para. Ni una cifra, ni la barra lateral.
2. **La cabecera**, en todas las pantallas: el veredicto vigente de `almacen.veredicto_vigente`, con
   de qué preregistro, cuántas condiciones, cuántos sorteos de holdout, de qué corrida y sobre qué
   datos. Sin un veredicto válido del laboratorio, el del protocolo: *sin ventaja demostrada*, «por
   defecto». Termina con «Es lo único que juzga. Ninguna cifra de las demás pantallas puede
   cambiarlo».
3. **El aviso de frescura**, si `reportes/` o `prereg/` cambiaron desde que se construyó la base.
4. **La pantalla elegida.**

## La navegación

Una radio en la barra lateral con cinco pantallas, y cada una con su URL, `?pantalla=<slug>`:
`veredicto` (la de entrada), `exploracion`, `valor-esperado`, `jugadores` y `procedencia`. Un slug que
no existe abre el veredicto. La URL se lee y se escribe a mano: la primera versión usaba
`bind="query-params"`, que exige en la URL la etiqueta y no el slug, y descartaba `?pantalla=` sin
avisar. Lo vio una captura del navegador, no un test.

## Las pantallas, y qué naturaleza tiene lo que enseñan

Cada tabla de `melate.duckdb` declara si **juzga**, **explora**, **mide** o es **procedencia**, y cada
pantalla enseña solo una naturaleza. Las que no juzgan llevan su aviso delante.

| Pantalla | Naturaleza | Lo que enseña |
|---|---|---|
| **Veredicto** | juzga | Por preregistro: el veredicto, las cinco condiciones, el holdout por juego, el preregistro tal como se selló (desplegable), la orden para un veredicto nuevo, y el historial si hay más de uno o alguno no vale. Los veredictos huérfanos, aparte. **Ninguna cifra de la exploración** (test) |
| **Exploración** | explora | El aviso «Esto explora; no juzga» delante. Un selector de informe (el más reciente por defecto); la familia de Benjamini-Hochberg con su q mínima; si alguna q ≤ 0.05, que es **una candidata a preregistrar y no una ventaja**; la auditoría, el poder, el backtest por juego y el log-loss, con por qué está fuera de la familia |
| **Valor esperado** | mide el dinero | El aviso «Esto mide dinero, no la urna». Su propio selector de informe; el valor esperado por juego con la constante del oráculo y con los premios menores medidos; los premios mayores |
| **Jugadores** | mide a los jugadores | El aviso «Esto mide a los jugadores, no la urna». Ventas, premios menores y efecto calendario de cada ventana; cada cartera con su aviso, su valoración y sus boletos (desplegable) |
| **Procedencia** | procedencia | Cuándo y con qué se construyó la base y si está al día; cada fichero leído con su SHA-256 y si vale; sobre qué datos se corrió cada informe; qué es cada tabla; dónde escucha la app; las órdenes para ponerla al día |

Los dos selectores de informe son independientes: elegir uno en Exploración no cambia el de Valor
esperado.

## Lo que comparten todas

- **Una sola función para el vigente.** La cabecera y la pantalla del veredicto lo piden a
  `almacen.veredicto_vigente`: con dos reglas llegaron a poder enseñar veredictos distintos a la vez.
- **Una sola función para las tablas,** `ver()`: enteras, sin cortar a las diez filas y con un guion
  donde falta un valor.
- **Todo texto que viene de un fichero, escapado** (`escapar()`, o `codigo()` entre comillas
  invertidas).
- **La caché de la app está atada a la fecha y el tamaño de la base:** reconstruirla con la app
  abierta cambia lo que enseña en la siguiente interacción.

## Cómo verificar

```powershell
.venv\Scripts\python.exe -m pytest tests\test_app.py -q
.venv\Scripts\python.exe -m melate.app                    # y recorrerla
```

Probado en vivo con clics de ratón reales en un navegador: cada pantalla desde la barra lateral, el
selector de informe (la q mínima pasa de 0.3060 a 0.5940 al elegir el informe de 200 simulaciones) y
los desplegables. 17 de 17 comprobaciones, en
`Fases/2026-10-04_app-local/Bugs/2026-10-04_11-39_s4-review-lanzador.md`.

## Cómo revertir

La app entera vive en `app/streamlit_app.py`: borrarla, con `tests/test_app.py` y las mutaciones de
`scripts/mutar.py` que la nombran, quita las pantallas sin tocar nada del cálculo. Lo que no se
recomienda es quitar una pieza suelta: cada una de las de arriba existe por un fallo que se vio.

Relacionado: `Red/Añadir/2026-10-04_16-35_s4-que-sirve-la-app-y-a-quien.md`,
`Estructura_Datos/Añadir/2026-10-04_16-35_s4-esquema-de-melate-duckdb.md`,
`Fases/2026-10-04_app-local/Bugs/2026-10-04_10-05_s4-review-base-app-y-red.md`,
`Mapa/Modificar/2026-10-04_16-35_s4-entra-la-app-local.md`.
