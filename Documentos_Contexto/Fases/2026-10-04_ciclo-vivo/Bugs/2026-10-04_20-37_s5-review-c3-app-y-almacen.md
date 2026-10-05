# Review de la Fase 5 — C3: la app y el almacén enlazados con los snapshots

- **Fecha/hora:** 2026-10-04 20:37
- **Área:** Fases/2026-10-04_ciclo-vivo · **Acción:** Bugs
- **Chat / página:** sesión de la Fase 5 · `src/melate/almacen.py`, `app/streamlit_app.py`, `src/melate/lab.py`
- **Archivos afectados:** `src/melate/almacen.py`, `app/streamlit_app.py`, `src/melate/lab.py`,
  `src/melate/protocolo.py`, `tests/conftest.py`, `tests/test_almacen.py`, `tests/test_app.py`,
  `tests/test_protocolo.py`, `scripts/mutar.py`
- **Estado:** CERRADO el 2026-10-04 a las 21:52 (bloque al final)

Review del segundo bloque de código de la fase: C3, aprobada por el usuario («Ok» y «dale con C3»).
Tres cambios que van juntos:

1. **El almacén** lee los `SHA256.txt` de `data/raw/` (tabla nueva `snapshots`, y cada uno en
   `fuentes`), enlaza por hash cada veredicto e informe con su snapshot, y **un veredicto cuyos datos
   no son un snapshot congelado no vale**. El esquema pasa a la versión 2: el lanzador reconstruye una
   base vieja él solo, y la app se niega a usarla.
2. **El laboratorio** publica en el veredicto `holdout_necesario`, la frontera de la condición 5 desde
   C1 (1778 con el preregistro sellado), para que la app la enseñe sin calcularla. Y `detectable(n)`
   pasa a ser la única copia de la fórmula del mínimo detectable.
3. **La app** escribe «1 sorteo»; pone al lado del holdout los sorteos que necesita la condición 5, y
   al lado del Δ los aciertos y el mínimo detectable; dice de qué snapshot sale cada veredicto e
   informe; y la orden para un veredicto nuevo es el ciclo, `python -m melate.ciclo`, no el
   laboratorio sin `--datos` (H3 y H4 del inventario). El motivo de la condición 1 también pasa al
   singular (`protocolo._sorteos`).

## Limitaciones del entorno, por delante

- **Windows 11, PowerShell 5.1 y Git Bash.** Nada probado en Linux ni macOS.
- **Todavía sin navegador.** Las pantallas se prueban con `AppTest`, que da el árbol de elementos y no
  los píxeles: la Fase 4 encontró cinco fallos mirando lo que los tests daban por bueno. **La mirada en
  vivo, con Edge sin interfaz y clics de verdad, queda pendiente** para cuando exista el primer
  veredicto real con holdout, que es lo que hay que ver.
- **El veredicto de un sorteo es un fixture**, `conftest.veredicto_de_un_sorteo`: la forma exacta del
  de `melate.lab`, con las condiciones del `declara_ventaja` real, sobre un snapshot que solo existe en
  el árbol del test. El de verdad llegará con el 4274.
- **El ciclo no existe todavía**: la app enseña su orden antes de que la orden exista. Es a propósito,
  porque la decisión que la fija está escrita
  (`Almacenamiento/Decisiones/2026-10-04_20-10_s5-el-ciclo-vivo.md`), y la fase no se cierra sin él.

## Review #1 — lo que se encontró

### B1 · El test del `SHA256.txt` roto no llegaba a la validación del hash

De sus tres líneas rotas, dos fallaban al partir la línea en dos campos, antes de la comprobación de
que el hash tiene 64 caracteres y el fichero es de un juego. Una mutación que quitara esa comprobación
habría pasado. **Arreglo:** un caso que parte bien y falla en la validación (`abc123  Melate.csv`), y
otro con un juego que no existe. **La mutación «un SHA256.txt roto congela algo», detectada** por
ese caso.

### B2 · Nada comprobaba que la construcción ignore la carpeta a medio escribir del ciclo

La frescura sí lo tenía probado; `construir`, no. Si leyera una carpeta `data/raw/.<nombre>.construyendo/`,
un veredicto podría valer por un snapshot que todavía no existe. **Arreglo:**
`test_una_carpeta_a_medio_escribir_no_congela_nada`, que esconde el snapshot real en una carpeta así y
exige que su veredicto no valga, con su mutación.

### B3 · El bucle rápido pasó de 10,5 a 17,6 s

Cada base de prueba cuesta ~0,6-0,7 s, y el bloque añadía cinco. **Arreglo:** el test del
`SHA256.txt` roto llama a la lectura de los snapshots en vez de construir una base entera por caso;
su consecuencia de punta a punta ya la prueba B2. **15,9 s**, con 234 pruebas.

## Mirar la app, en vivo — cinco fallos más que ningún test veía

Con el ciclo ya hecho, la app se abrió con su lanzador sobre la base real —el veredicto del 4273,
holdout de 0— y sobre la del fixture de un sorteo, la que se verá con el 4274. Edge sin interfaz, con
su propio perfil, por su protocolo de depuración en 127.0.0.1: navegación por la URL, **clics de
ratón de verdad** en la barra lateral (cinco pantallas, ida y vuelta) y capturas de la página entera.
El servidor, con un proxy que solo apunta puesto como `HTTP_PROXY`/`HTTPS_PROXY`.

### B4 · El número se partía en dos líneas: «de los 1» / «778»

El separador de miles de `entero()` era un espacio normal, y la cabecera cortaba la línea justo ahí.
**Arreglo:** un espacio de no separación (`\u00a0`). **Test:** `test_un_sorteo_es_un_sorteo` exige que
`entero(1586604)` no tenga ningún espacio normal, y el de la vista de un sorteo, la cadena exacta.

### B5 · La procedencia seguía diciendo «índice de `reportes/` y `prereg/`»

La base vigila ahora también los `SHA256.txt` de `data/raw/`, y la pantalla no lo decía. **Arreglo:**
los dos textos. **Test:** `test_cada_informe_dice_de_que_snapshot_sale`.

### B6 · La columna «Por qué no» de la tabla de ficheros quedaba fuera del borde

Era la última de siete, y es la única que explica el fichero que no vale —el veredicto de la Fase 2—.
**Arreglo:** «¿Vale?» y «Por qué no» van detrás del tipo. **Test:** el orden de las cuatro primeras
columnas.

### B7 · El motivo de la condición 5 salía cortado, justo antes de lo que importa

Con un sorteo de holdout, la rejilla de `st.dataframe` cortaba la frase en una línea: «…mayor que el
0.048 declarado e…». Lo que decía cuántos sorteos faltan no se veía. **Arreglo:** la tabla de
condiciones pasa a `st.table`, que parte las frases. Captura después: la frase entera, en tres líneas.
**Test:** la vista de un sorteo exige la tabla estática y la frase completa en la celda.

### B8 · Y `st.table` pasa cada celda por Markdown — seguridad

Al mirar la captura nueva, «q <= 0.05» salía «q ≤ 0.05». Mirado en el DOM: cada celda de `st.table`
es un `stMarkdownContainer`. Un motivo con `![x](http://…)` habría hecho que el navegador pidiera una
imagen fuera de la máquina, que es exactamente lo que la Fase 4 cerró en la cabecera. **Lo introdujo
B7, y lo cazó mirar la pantalla, no un test.** **Arreglo:** los textos de la tabla pasan por
`escapar()`, como todo lo que viene de un fichero. **Test:** el fixture `base_con_ventaja` lleva ahora
la imagen maliciosa también en un motivo, y el test exige que llegue escapada a la celda.

### B9 · Un carácter invisible en el código

La herramienta de edición escribió el espacio de no separación como carácter, no como `\u00a0`: el
código funcionaba y no se veía qué hacía. La propia mutación de B4 lo destapó, porque buscaba la
secuencia escrita y no la encontraba («el texto aparece 0 veces»). **Arreglo:** la secuencia escrita,
en la app y en sus tests.

**Cinco mutaciones nuevas** («F5 app:…»), una por cada arreglo: las cinco, detectadas.

**En vivo, además:** los cinco clics llevan a su pantalla y la URL se conserva; la cabecera dice en
las dos bases el veredicto, cuántos sorteos de holdout lleva y cuántos necesita, de qué corrida y de qué
snapshot; **y el proxy no apuntó ni una conexión del servidor hacia fuera en ninguna de las dos
sesiones**, con todas las pantallas recorridas.

**Una cosa aclarada de la Fase 4:** la barra lateral cortada de las capturas es cosa de la captura.
Al estirar la ventana para capturar la página entera, Streamlit empieza a plegar la barra: su borde
pasa de 0 a −7,5 px, medido antes y después. Un clic justo después caía fuera; por eso las capturas
se hacen ahora después de los clics.

## Lo que se comprobó y estaba bien

- ✅ **Los dos tests que cambiaron de expectativa cambiaron por C3, no por un fallo**: el veredicto de
  la Fase 2, que no registra sus datos, deja de valer (`test_el_veredicto_viejo_no_vale_porque_no_dice_sobre_que_datos_juzgo`).
  Nunca fue el vigente, así que la cabecera de la app no cambia.
- ✅ **El informe en vivo de la Fase 1 sale del snapshot del 2026-10-02**, por el hash: descargó los
  mismos bytes. La ruta no lo habría dicho.
- ✅ **Las 12 mutaciones de la fase, detectadas**, las 10 nuevas de este bloque incluidas.
- ✅ **El lanzador y la app siguen en verde** con el esquema nuevo: una base del esquema 1 se
  reconstruye o se rechaza, no se usa a medias.

## Review #2 — limpieza

- `sorteos()` y `necesita()` son las dos funciones puras nuevas de la app, con su test. `entero()`
  dice en su docstring por qué el espacio no es un espacio.
- **La app sigue sin calcular**: «de los 1 778» lo publica el laboratorio (`holdout_necesario`) y el
  mínimo detectable ya estaba en el veredicto. La app solo los pone uno al lado del otro.
- `test_la_app_solo_importa_lo_que_lee` y `test_la_app_no_escribe` siguen en verde: ningún import
  nuevo, ninguna escritura.

## Review de seguridad

- ✅ **Lo que viene de un fichero se escapa en todas partes**, también en la tabla nueva (B8). El nombre
  de un snapshot va siempre por `codigo()`, que impide cerrar las comillas invertidas; en las órdenes
  de `st.code` es texto literal.
- ✅ **El almacén lee los `SHA256.txt` con una forma estricta**: dos campos, un hash de 64 caracteres y
  un fichero de un juego; cualquier otra cosa no congela nada.
- ✅ **Sin red**: el proxy, vacío en las dos sesiones.

## Pendiente de verificar en vivo

1. **La pantalla del veredicto con el primer holdout real, el del 4274.** Hecho con el fixture de un
   sorteo, que tiene su forma exacta; con el de verdad, pasa a la review del ciclo, que lo congelará.
2. ~~La base real con el esquema 2~~: hecho. `python -m melate.almacen` en 2,09 s; el veredicto vigente
   pasó a ser el del 4273 cuando el ciclo lo congeló, con su snapshot; el de la Fase 2, no válido y con
   su motivo.

## Resultado — CERRADO el 2026-10-04 a las 21:52

| # | Hallazgo | Arreglo | Lo fija |
|---|---|---|---|
| B1 | El test del `SHA256.txt` roto no llegaba a la validación | un caso que sí llega | mutación «un SHA256.txt roto congela algo» |
| B2 | La construcción leía, sin test, la carpeta a medio escribir | `test_una_carpeta_a_medio_escribir_no_congela_nada` | su mutación |
| B3 | El bucle rápido, 17,6 s | test unitario en vez de cinco bases | 15,9 s entonces |
| B4 | «de los 1» / «778» | espacio de no separación | `test_un_sorteo_es_un_sorteo` |
| B5 | La procedencia no decía que vigila `data/raw/` | dos textos | `test_cada_informe_dice_de_que_snapshot_sale` |
| B6 | «Por qué no», fuera del borde | delante | ídem |
| B7 | El motivo de la condición 5, cortado | `st.table` | `test_un_holdout_de_un_sorteo_se_ve_como_lo_que_es` |
| B8 | `st.table` interpreta Markdown | `escapar()` en sus celdas | `test_el_camino_afirmativo_llega_a_la_cabecera` |
| B9 | Un carácter invisible en el código | `\u00a0` escrito | la mutación de B4 |

**Medido al cerrar:** `tests/test_app.py` y `tests/test_almacen.py`, 69 en verde; las mutaciones de C3,
de C1 y las cinco de la app, detectadas. **Bugs abiertos: ninguno.** Pasa a la review del ciclo el
pendiente 1, ver el primer holdout real en un navegador.

## Cómo verificar

```powershell
.venv\Scripts\python.exe -m pytest tests\test_almacen.py tests\test_app.py -q
.venv\Scripts\python.exe scripts\mutar.py --solo "F5"      # las de la Fase 5; «(C3)» cogería también las del lanzador
```

Relacionado: `Fases/2026-10-04_ciclo-vivo/Decisiones/2026-10-04_18-59_s5-lo-que-decidio-el-usuario.md`,
`Almacenamiento/Decisiones/2026-10-04_20-10_s5-el-ciclo-vivo.md`,
`Almacenamiento/Decisiones/2026-10-04_00-40_s4-que-entra-en-melate-duckdb.md`,
`Fases/2026-10-04_ciclo-vivo/Inventario/2026-10-04_18-16_s0-estado-de-partida.md`.
