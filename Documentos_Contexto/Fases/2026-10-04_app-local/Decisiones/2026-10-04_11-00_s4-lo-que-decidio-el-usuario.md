# Lo que decidió el usuario sobre la review de la Fase 4, y qué se hizo con cada cosa

- **Fecha/hora:** 2026-10-04 11:00
- **Área:** Fases/2026-10-04_app-local · **Acción:** Decisiones
- **Decidido por:** usuario, consultado antes de cerrar la fase · **Estado:** cerrada, salvo C3, que
  es una propuesta **pendiente de su aprobación**
- **Nota del 2026-10-04, 16:08:** C3 **aprobada** por el usuario («Lo apruebo») **e implementada**:
  `Fases/2026-10-04_app-local/Cambios/2026-10-04_16-08_s4-lanzador-propio.md`. El resto de este
  documento queda como se escribió.
- **Alcance:** `src/melate/popularity.py`, `src/melate/portfolio.py`, `src/melate/almacen.py`,
  `app/streamlit_app.py`, `scripts/colador.ps1`, `scripts/mutar.py`, `CLAUDE.md`, y los reportes
  `reportes/2026-10-03_popularidad.json`, `reportes/2026-10-04_popularidad-melate-300-sorteos.json` y
  `reportes/2026-10-03_cartera.json`

## Por qué hubo que preguntar

La review (`Fases/2026-10-04_app-local/Bugs/2026-10-04_10-05_s4-review-base-app-y-red.md`) dejó siete
asuntos que tocaban el contrato, el protocolo, código de otra fase o una preferencia del usuario.
*«Un bug no se deja sin preguntar»* (`CLAUDE.md`): se presentaron con su evidencia y **ninguno se
aplicó antes de la respuesta**. El usuario contestó a los siete y dijo que todo entra en la Fase 4.

| | Lo que se preguntó | Lo que decidió |
|---|---|---|
| C1 | Tres tablas de ganadores con todos los premios a $0.00 | «Sin premios publicados» |
| C2 | Nueve pruebas de log-loss fuera de la familia, sin documento | «Sí, hazlo, y analiza si es necesario tenerlas» |
| C3 | Una conexión de otro origen hace que Streamlit pida `checkip.amazonaws.com` | «Dime cómo se haría el lanzador; si lo apruebo, se ejecuta. Documenta» |
| C4 | La cartera no guarda con qué bolsa se valoró | «Repara» |
| C5 | `melate.duckdb` no se publica | «Lo que recomiendes, pero si se puede reparar, mucho mejor» |
| C6 | Añadir `mutar.py` y las reglas de la app al `CLAUDE.md` | «Sí, claro que sí» |
| C7 | El bucle rápido sube de ~5 s a ~11,5 s | «Totalmente aceptado: me gusta que tarde, eso significa procesamiento de datos» |

---

## C1 · Sorteos sin premios publicados

**Qué se hizo.** `popularity.premios_publicados(cats)` dice si toda categoría menor con ganadores trae
su importe. Una categoría con ganadores siempre paga algo, así que un `$0.00` ahí es un dato que
falta. `analizar` conserva esas muestras —sus ganadores dan las ventas y el efecto calendario— pero
deja en blanco sus premios menores, y el reporte gana `sorteos_sin_premios` con la lista. La CLI lo
imprime.

**Los dos reportes de popularidad se regeneraron** con las mismas órdenes, desde la caché:
**0 peticiones de red** en las dos. Así los dos los reproduce el código de hoy.

| Reporte | SHA-256 antes | SHA-256 después | Qué cambió |
|---|---|---|---|
| `reportes/2026-10-04_popularidad-melate-300-sorteos.json` | `831e203d1259…` | `169e1f2e1d38…` | Solo los premios menores (abajo), la lista nueva y la hora de descarga |
| `reportes/2026-10-03_popularidad.json` | `e4de460e8cc6…` | `0a67c622e299…` | Solo los campos nuevos (`sorteos_sin_premios: []`) y la hora: ninguna cifra |

En la ventana de 300 sorteos, comprobado campo a campo: **las ventas, el efecto calendario, los fallos
y la ventana son idénticos.** Los premios menores por bolsa:

| | Antes | Ahora |
|---|---|---|
| Sorteos que cuentan | 300 | **297** (fuera: 4107, 4111, 4119) |
| Media | 4,6035 | **4,6500** |
| Mediana | 4,6422 | **4,6465** |
| cv | 0,1156 | **0,0565** |
| Mínimo | 0,0 | **3,1007** |

El nuevo mínimo es el sorteo 4105 y su tabla está **completa**: tuvo muchísimos acertantes de 3 y 4
números, lo que infla las ventas estimadas y baja el cociente. Es el sesgo del estimador que ya
documentó la Fase 3, no un dato que falte.

**Ninguna cifra del `CLAUDE.md` cambia**: las ventas y el efecto calendario no usan premios, y el EV
medido sale de la ventana de 100. Sí se corrigió, con marca, el 4,6422 que publicaba la review de la
Fase 3 (§8 de las reglas), y la constante 4,6035 de `tests/test_cartera.py`, que era la media
contaminada.

**En la base y la app:** la tabla `popularidad` gana `sorteos_sin_premios` y la pantalla de jugadores
lo enseña («Sorteos sin premios publicados» y «Sorteos que cuentan»).

**Tests:** `test_una_tabla_sin_premios_no_cuenta_como_premios_a_cero` (dos valores: la tabla real y
la misma con los importes borrados) y el recuento en `test_el_contenido_es_el_de_los_reportes`.

## C2 · Las pruebas de log-loss

Tiene su documento en el índice permanente, porque precisa una frontera del protocolo:
`Protocolo_Estadistico/Decisiones/2026-10-04_10-45_s4-el-log-loss-no-entra-en-la-familia.md`.

En corto: **tal como se calculan, no son pruebas sobre la urna.** Con una urna limpia, todo modelo
que no reparta las probabilidades por igual pierde en log-loss (desigualdad de Gibbs), así que un
«peor que el azar» significativo es lo esperado. Las nueve Δ son positivas. Meterlas tal cual en la
familia habría dado cinco «hallazgos» que son modelos perdiendo, y habría bajado la q de la
regresión logística en Revancha **de 0,306 a 0,096**: Benjamini-Hochberg se afloja cuando se le
añaden p casi nulas. **Hace falta tenerlas**: el oráculo las calcula y la paridad lo exige, y son el
único diagnóstico de las probabilidades. Se quedan en el informe y en la app, fuera de la familia, y
la app explica por qué debajo de su tabla.

## C3 · El lanzador propio — diseñado, probado fuera del proyecto, **pendiente de aprobación**

> **Nota del 2026-10-04, 16:08:** aprobada e implementada como `src/melate/app.py`. Respecto a este
> diseño, fija además `enableCORS` y `enableXsrfProtection`, y reconstruye la base con las carpetas
> de su propio árbol. Qué se hizo y cómo se verificó:
> `Fases/2026-10-04_app-local/Cambios/2026-10-04_16-08_s4-lanzador-propio.md` y
> `Fases/2026-10-04_app-local/Bugs/2026-10-04_11-39_s4-review-lanzador.md`.

**Qué haría.** Un módulo `src/melate/app.py` que se lanzaría con `python -m melate.app`, en lugar de
`streamlit run`, y haría tres cosas antes de servir:

1. **Poner la base al día.** Si `melate.duckdb` falta, es de otro esquema o está desactualizada, la
   construye. La app seguiría sin escribir nada: escribiría el lanzador, que es una orden de terminal
   como `melate.almacen`. Esto quita el único inconveniente de no publicar la base (C5).
2. **Anular la búsqueda de la IP pública.** Sustituiría `streamlit.net_util.get_external_ip` por una
   función que devuelve `None` antes de arrancar el servidor. Es la función que hoy hace el `GET` a
   `checkip.amazonaws.com` ante una conexión de otro origen; con `None`, Streamlit rechaza esa
   conexión igual (403), sin preguntarle nada a nadie.
3. **Forzar la red por línea de órdenes.** Arrancaría Streamlit con `--server.address 127.0.0.1`,
   `--server.headless true`, `--browser.gatherUsageStats false`, `--server.allowedHosts` y
   `--client.toolbarMode viewer`. Las opciones de la línea de órdenes mandan sobre
   `.streamlit/config.toml`, así que valdría lanzado desde cualquier carpeta.

**Probado en el *scratchpad*, no en el proyecto.** Una prueba de concepto de 50 líneas, lanzada
desde una carpeta **sin** `.streamlit/config.toml` y con el proxy chivato puesto:

| Comprobación | Con `streamlit run` | Con el lanzador |
|---|---|---|
| Dirección de escucha | `127.0.0.1:8501` (solo desde la raíz) | `127.0.0.1:8502`, desde fuera de la raíz |
| Base desactualizada | la app avisa | «La base está desactualizada: se construye.» |
| WebSocket del mismo origen | 101 | 101 |
| WebSocket de otro origen (dos orígenes distintos) | 403 | 403 |
| `Host` ajeno | 403 | 403 |
| **Registro del proxy** | **`GET http://checkip.amazonaws.com/`** | **vacío** |
| Pantallas | se pintan, con la cabecera | se pintan, con la cabecera |

**Lo que costaría:**

- **Parchea una función interna de Streamlit.** Con la versión fijada (1.65.0) es estable, pero una
  actualización podría renombrarla. Mitigación: un test que falle a la vista si
  `streamlit.net_util.get_external_ip` deja de existir, y la nota que ya lleva `requirements.txt`
  (actualizar Streamlit obliga a revisar su red).
- **Cambia la orden de arranque.** `streamlit run` seguiría funcionando, con la configuración y la
  guarda, pero con la búsqueda residual. El README y el `CLAUDE.md` pasarían a recomendar el
  lanzador.
- Unas 60 líneas, sus tests, una mutación nueva, y los documentos de `Red/` y `Seguridad/`.

**Si se aprueba**, se ejecuta dentro de la Fase 4 y se documenta como cualquier otro cambio. Si no,
queda escrito como riesgo residual conocido de la dependencia.

## C4 · La valoración de la cartera — reparada

`portfolio.valorar` devuelve ahora `bolsa`, `menores_brutos` e `impuesto`, y la CLI los imprime. La
cartera se regeneró con sus parámetros originales (Melate, 300 $, bolsa 76,2 M, popularidad de la
ventana de 100: las ventas supuestas, 991 119, la delataban): **idéntica en todo** —los 20 boletos,
el EV de 128,82 $, la ganancia— **más los tres campos**. SHA-256 `7f628ef03d49…` → `37ad777af30d…`.
La base guarda los tres y la app escribe «Valorada con una bolsa de 76.2 millones, unos premios
menores de 4.6013 por boleto y un impuesto del 7 %». **Test:**
`test_la_valoracion_dice_con_que_se_hizo`, con dos bolsas.

## C5 · `melate.duckdb` no se publica — se mantiene, y se blinda

La recomendación se mantiene: no añade información, cambia de bytes en cada reconstrucción y es un
binario. **Lo que se reparó** es el punto débil de esa decisión: `.gitignore` se salta con
`git add -f`, y el colador no sabe leer un binario.

- **`scripts/colador.ps1` mira ahora el índice de git** y da por coincidencia cualquier `*.duckdb`
  versionado. Con su autoprueba, que crea un repositorio de usar y tirar y mete una base a la fuerza:
  **4 de 4**. En vivo, con los dos valores: limpio → 0 coincidencias; con `melate.duckdb` forzada al
  índice → `1 COINCIDENCIAS. NO subir`, código 1; restaurado → 0.
- **Test:** `test_la_base_no_se_publica` (el índice y `.gitignore`).
- Y si se aprueba el lanzador (C3), el paso extra de construir la base desaparece.

## C6 · El `CLAUDE.md`

Tres cambios, en «Lo que protege el proyecto de sí mismo»: el colador también caza una base
versionada; `scripts/mutar.py` entra en el procedimiento de cierre; y una sección nueva, «La app
local (Fase 4)», con sus tres reglas —solo esta máquina, no recalcula, el informe explora y el
laboratorio juzga— y que la base no se publica.

## C7 · El bucle rápido, aceptado

Con las palabras del usuario: *«me gusta que tarde y no sea tan rápido, eso significa
procesamiento de datos»*. Queda escrito para que nadie lo «arregle» sacando los tests de la app del
bucle.

---

## Y uno que no estaba en la lista: `mutar.py` fallaba en silencio

Al añadir la mutación de C4, la herramienta dijo **«no detectada»**. El test estaba bien: la mutación
**no se había aplicado**. `mutar.py` comprobaba el texto a buscar con los saltos normalizados (`\n`) y
lo sustituía en los bytes; `portfolio.py` y `popularity.py` tienen CRLF, así que un texto con salto
de línea «estaba una vez» y la sustitución no cambiaba nada. Aquí salió como «no detectada»; en otro
caso habría podido salir como «detectada» sin haber mutado nada.

**Arreglo:** busca y sustituye sobre el texto normalizado, escribe con el final de línea del fichero,
y **se niega a contar una mutación que no cambió ningún byte**. Antes de empezar aplica y deshace las
33 para comprobarlo. **Tests:** `tests/test_herramientas.py` —con LF y con CRLF, los tres casos en que
debe negarse, y que cada mutación de la lista está bien definida sobre el fichero real—. Es la misma
lección del colador y del verificador: una herramienta de verificación sin su propia prueba es una
opinión.

## Qué premisa toca esto (§7 de las reglas)

| Documento | Estado |
|---|---|
| `CLAUDE.md` — ventas y efecto calendario de la ventana de 300 | Siguen valiendo: las cifras no cambian y el reporte que cita las reproduce |
| `CLAUDE.md` — EV medido (ventana de 100) | Sigue valiendo: el reporte regenerado da las mismas cifras |
| `Fases/2026-10-03_popularidad/Bugs/2026-10-03_04-10_s3-review-popularidad-y-cartera.md` | Corregido el 4,6422 → 4,6465, con marca |
| `Protocolo_Estadistico/Decisiones/2026-10-03_05-10_s3-la-popularidad-no-entra-en-la-familia.md` | Sigue valiendo; su frontera se precisa en el documento del log-loss |
| `Almacenamiento/Decisiones/2026-10-04_00-40_s4-que-entra-en-melate-duckdb.md` | Sigue valiendo; el colador cubre ahora su razón número 2 |

## Cómo verificar

```powershell
.venv\Scripts\python.exe -m pytest tests -m "not lento and not red" -q
.venv\Scripts\python.exe scripts\mutar.py                     # 33 de 33
.\scripts\colador.ps1 -Autoprueba                             # autoprueba 4/4, 0 coincidencias
.venv\Scripts\python.exe -m melate.popularity --juegos Melate --desde 3973 --hasta 4272 `
    --datos data\raw\2026-10-02 --salida reportes\comprobacion.json   # 3 sin premios, 0 peticiones
```

## Cómo revertir

Cada cambio es independiente:

- **C1:** quitar `premios_publicados` y su uso en `analizar`, y regenerar los dos reportes. Vuelven los
  tres ceros.
- **C4:** quitar las tres claves de `valorar` y regenerar la cartera.
- **C5:** quitar de `colador.ps1` la función `Versionados`, su uso y su autoprueba.
- **C6:** quitar del `CLAUDE.md` la sección de la app y las dos líneas de las herramientas.
- **El arreglo de `mutar.py`:** no se recomienda; vuelve a contar mutaciones que no mutan.

Relacionado: `Fases/2026-10-04_app-local/Bugs/2026-10-04_10-05_s4-review-base-app-y-red.md`,
`Protocolo_Estadistico/Decisiones/2026-10-04_10-45_s4-el-log-loss-no-entra-en-la-familia.md`,
`Almacenamiento/Decisiones/2026-10-04_00-40_s4-que-entra-en-melate-duckdb.md`,
`Fases/2026-10-04_app-local/00_ALCANCE.md`.
