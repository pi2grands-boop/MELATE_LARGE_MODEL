# Review del lanzador — `python -m melate.app` (C3)

- **Fecha/hora:** 2026-10-04 11:39
- **Área:** Fases/2026-10-04_app-local · **Acción:** Bugs
- **Chat / página:** sesión de la Fase 4 · el lanzador que el usuario aprobó («Lo apruebo»)
- **Archivos afectados:** `src/melate/app.py` (nuevo), `src/melate/almacen.py`,
  `app/streamlit_app.py`, `.streamlit/config.toml`, `.gitignore`, `requirements.txt`,
  `tests/test_lanzador.py` (nuevo), `tests/test_app.py`, `scripts/mutar.py`
- **Estado:** CERRADO el 2026-10-04 16:20 (bloque al final)

Se abre al empezar la review #1, después de implementar y antes de la verificación en vivo. El diseño
y la prueba de concepto son los de C3 en
`Fases/2026-10-04_app-local/Decisiones/2026-10-04_11-00_s4-lo-que-decidio-el-usuario.md`.

## Limitaciones del entorno, por delante

- **Windows 11, PowerShell 5.1 y Git Bash.** Nada probado en Linux ni macOS.
- **Los tests no arrancan ningún servidor.** Sustituyen `streamlit.web.bootstrap.run`, que es lo
  último que hace `streamlit run`, y miran la configuración con la que habría arrancado. El proceso
  real escuchando se comprueba en vivo, abajo.
- **Las salidas a la red** se vigilan con el mismo proxy chivato de la review anterior, puesto como
  `HTTP_PROXY`/`HTTPS_PROXY`: ve lo que pasa por `requests`, que es con lo único que el código de
  Streamlit 1.65 sale fuera (inventario abajo).

---

## Review #1

### L1 · Streamlit lee un tercer `config.toml`, y un tercer `secrets.toml`, junto al script

Leído en `streamlit/config.py` (`get_config_files`) y `streamlit/file_util.py`: además del global
(`~/.streamlit/`) y del de la carpeta desde la que se lanza, Streamlit 1.65 lee
`<carpeta del script>/.streamlit/config.toml`, es decir `app/.streamlit/config.toml`, y con la misma
regla busca los secretos (`secrets.files`). **`.gitignore` solo cubría el `secrets.toml` de la raíz**:

```
git check-ignore -v --no-index app/.streamlit/secrets.toml   ->  (nada: se publicaría)
```

**Arreglo:** el patrón pasa a `**/.streamlit/secrets.toml`. Después, `git check-ignore` lo da por
ignorado en la raíz, en `app/` y en `tests/`. El proyecto no tiene secretos; la línea existe para
que uno creado por accidente no se publique, y ahora lo cumple.

**Test:** `test_ningun_secreto_de_streamlit_se_publica`, con su mutación. Se escribió al preparar el
cierre, cuando quedó a la vista que L1 era lo único sin test. No pudo copiar al de la base
(`test_la_base_no_se_publica`), que mira el índice de git y se salta en la copia sin repositorio de
`scripts/mutar.py`: una mutación de `.gitignore` no la habría cazado nunca. Este crea un repositorio
de usar y tirar con el mismo `.gitignore`, y `mutar.py` copia ahora también ese fichero.

**Lo que NO se hizo, y por qué:** mover `.streamlit/config.toml` a `app/.streamlit/` haría que
`streamlit run` lo leyera se lance desde donde se lance. No se movió: el lanzador ya fuerza las
opciones por línea de órdenes, que además mandan sobre las variables `STREAMLIT_*` (un fichero no
puede), y moverlo cambiaría una ruta citada en el README, el `CLAUDE.md`, la app, los tests,
`scripts/mutar.py` y tres documentos de esta fase.
`streamlit run` desde otra carpeta sigue siendo seguro: la guarda de la app se niega a enseñar nada.

### L2 · Con `enableCORS = false` en cualquier `config.toml`, el WebSocket acepta cualquier origen

Leído en `streamlit/web/server/server_util.py`: `is_url_from_allowed_origins` empieza con
`if not config.get_option("server.enableCORS"): return True`. El WebSocket, que es por donde viajan
los datos de la app, delega en ella para todo origen que no sea el propio
(`starlette_websocket.py`, `_is_origin_allowed`). Un `config.toml` global escrito para otro proyecto
—un caso corriente en una máquina de desarrollo— dejaría a cualquier página abierta en el navegador
leer la app. El diseño aprobado no fijaba esta opción.

**Arreglo:** el lanzador y `.streamlit/config.toml` fijan `enableCORS` y `enableXsrfProtection` a
`true`, que es su valor por defecto: en el uso normal no cambia nada. **Tests:**
`test_lo_que_fuerza_el_lanzador_ata_la_app_a_esta_maquina` y
`test_la_configuracion_ata_la_app_a_esta_maquina`, con su mutación cada uno.

### L3 · La primera versión de los tests reconstruía la base en cada caso: +3,5 s en el bucle rápido

Cinco estados de la base (falta, rota, de otro esquema, de otro árbol, desactualizada), y cada uno
reconstruía. Medido: una reconstrucción en caliente cuesta **0,31 s** y leer la base **0,06 s**.
Las 197 pruebas de antes, medidas a la vez, seguían en 11,7-11,9 s; con las nuevas, 15,0-15,9 s.

**Arreglo**, sin marcar nada como `lento`:

| Qué | Efecto |
|---|---|
| El diagnóstico (`por_que_construir`) se prueba en los cinco estados **sin construir** | 5 construcciones → 0 |
| Los cinco llevan al mismo camino de construcción, que se prueba **una** vez, con un clon sin base | 1 construcción |
| El estado «de otro árbol» se fabrica con un `UPDATE`, no construyendo otra base | −0,25 s |
| El árbol de partida es el de `base_real`, que la sesión ya construyó | −0,35 s |
| «Una base al día no se toca» lee el árbol compartido sin copiarlo: con `construir` prohibido, nada puede escribir | −0,15 s |

**Medido después, tres veces:** **212 pruebas en 13,0-13,9 s**. El coste que queda es el real de
probar el lanzador: una reconstrucción y cinco diagnósticos.

### Decisiones de implementación (no son fallos)

- **Una sola regla para encontrar la base.** `almacen.ruta_de_la_base(raiz)` —`MELATE_DUCKDB` o
  `melate.duckdb` en la raíz— la usan la app y el lanzador. Con dos reglas, el lanzador podría poner
  al día una base y la app enseñar otra: es la lección de B7 (cabecera y pantalla con dos vigentes).
  **Test:** `test_la_app_y_el_lanzador_buscan_la_base_en_el_mismo_sitio`.
- **La base se reconstruye con los `reportes/` y `prereg/` de su propia carpeta**, no con los de la
  raíz. Es lo que `almacen` entiende por estar al día (la base indexa el árbol en el que vive), y así
  una `MELATE_DUCKDB` que apunte a otro árbol nunca se sobrescribe con los datos reales. **Test:**
  `test_construye_con_las_carpetas_de_su_propio_arbol`.
- **Si Streamlit renombra `get_external_ip`, el lanzador se niega a arrancar.** Sustituir un
  atributo que ya no existe no falla: crearía uno nuevo y dejaría la búsqueda viva en silencio.
  **Tests:** `test_sin_la_funcion_que_sustituye_el_lanzador_no_arranca`, y
  `test_streamlit_solo_busca_su_ip_a_traves_del_modulo`, que recorre todo el Streamlit instalado: la
  sustitución solo vale si nadie se guardó una referencia propia a la función.

---

## Pendiente de verificar en vivo

1. Lanzado desde una carpeta que no es la raíz, con un `config.toml` hostil en ella y variables
   `STREAMLIT_*` hostiles: tiene que escuchar solo en `127.0.0.1`.
2. Sin `melate.duckdb`: el lanzador la construye; lanzado otra vez, la da por buena.
3. WebSocket del mismo origen → 101; de otro origen y con `Host` ajeno → 403; **registro del proxy
   vacío**.
4. Las cinco pantallas, recorridas **con clics** en un navegador real, y todas las peticiones del
   navegador hacia `127.0.0.1`.

## Verificación en vivo — ejecutada, hacia las 15:00

Entre la apertura de este documento y la verificación pasaron unas tres horas, con la sesión
detenida; los cuatro relojes de la máquina (Git Bash, PowerShell, Python local y UTC) se comprobaron
y coinciden. Las horas de abajo son locales (UTC−5).

**El escenario, hostil en todo a la vez:**

- Lanzado desde una carpeta del *scratchpad*, no desde la raíz, con un `.streamlit/config.toml` que
  pide `address = "0.0.0.0"`, `headless = false`, `allowedHosts = ["evil.example", "127.0.0.1"]`,
  `enableCORS = false`, `enableXsrfProtection = false`, `gatherUsageStats = true`,
  `serverAddress = "evil.example"` y `toolbarMode = "developer"`.
- Con `STREAMLIT_SERVER_ADDRESS=0.0.0.0`, `STREAMLIT_BROWSER_GATHER_USAGE_STATS=true` y
  `STREAMLIT_SERVER_ENABLE_CORS=false`.
- Sin `melate.duckdb` en la raíz: se apartó al *scratchpad* antes de lanzar.
- Con el proxy chivato como `HTTP_PROXY` y `HTTPS_PROXY`.

**✅ 1 y 2 · Escucha y base.** Salida del lanzador (la línea de la construcción imprime la ruta
completa de la base; aquí se omite):

```
melate.duckdb no existe: se construye.
… construida en 16.73 s, con 10 ficheros:
  preregistro 2026-10-03_logistica-revancha: verifica
  veredicto reportes/2026-10-03_veredicto.json: válido
  veredicto reportes/2026-10-04_veredicto.json: válido
Lo que la app enseñará en cada pantalla: sin ventaja demostrada
Solo esta máquina: http://127.0.0.1:8501 · sin telemetría · sin preguntar la IP pública.
Uvicorn server started on 127.0.0.1:8501

netstat -ano | :8501   ->  TCP 127.0.0.1:8501  LISTENING      (ninguna línea 0.0.0.0 ni [::])
```

Lanzado otra vez, desde la raíz y sin nada hostil: `melate.duckdb está al día.`, la base con la
misma fecha de escritura que antes, `/_stcore/health` en 200 a los **3 s** de la orden, y solo
`127.0.0.1:8501`.

**Los 16,73 s de la construcción no se reprodujeron.** Repetida en procesos nuevos, en las mismas
condiciones —la carpeta hostil, las mismas variables, el proxy—: 1,88-1,96 s escribiendo en el
*scratchpad* y 2,19-2,56 s escribiendo dentro de la carpeta del repositorio. Fue el primer arranque
tras esas tres horas detenida; lo más probable es un disco frío, sin verificar. Se anota como se
midió.

**✅ 3 · Red** (`scratchpad/vivo_red.py`, sin proxy, contra el servidor):

```
health 127.0.0.1        -> 200 'ok'
health [::1]            -> no es posible conectar
health <IP de la red>   -> no es posible conectar
WS Host 127.0.0.1:8501     Origin http://127.0.0.1:8501     -> 101 Switching Protocols
WS Host localhost:8501     Origin http://localhost:8501     -> 101 Switching Protocols
WS Host 127.0.0.1:8501     Origin https://evil.example      -> 403 Forbidden
WS Host 127.0.0.1:8501     Origin https://otra.example      -> 403 Forbidden
WS Host evil.example:8501  Origin http://evil.example:8501  -> 403 Forbidden
registro del proxy: 0 líneas
```

Cada 403 prueba algo distinto: el de otro origen, que `enableCORS` quedó fijado aunque el entorno
lo apagaba (L2); el de `Host` ajeno, que `allowedHosts` quedó fijado aunque el `config.toml` hostil
aceptaba `evil.example`. Y el registro vacío es la búsqueda de la IP anulada: con `streamlit run`,
el mismo caso dejó en ese registro `GET http://checkip.amazonaws.com/`
(`Fases/2026-10-04_app-local/Bugs/2026-10-04_10-05_s4-review-base-app-y-red.md`).

**✅ 4 · El recorrido con clics** (`scratchpad/recorrido_clics.py`). Edge sin interfaz, manejado
por su protocolo de depuración, pero **sin navegar por URL**: cada pantalla se abrió con un clic de
ratón en la barra lateral, el informe se cambió en su desplegable y los desplegables se abrieron con
un clic.

```
OK  abre en el veredicto, con la cabecera · la URL queda con ?pantalla=veredicto
OK  el desplegable del preregistro se abre con un clic
OK  clic en Exploración, Valor esperado, Jugadores, Procedencia y Veredicto: cada una su pantalla,
    con «sin ventaja demostrada», y la URL con su ?pantalla=
OK  el informe por defecto da q mínima 0.3060; el desplegable, con un clic, lo cambia al de 200
    simulaciones y la pantalla pasa a 0.5940
OK  el desplegable de los boletos se abre con un clic
OK  Procedencia dice «Escucha en 127.0.0.1:8501 y la telemetría de Streamlit está apagada»

peticiones del navegador: 133, a http://127.0.0.1:8501 y ws://127.0.0.1:8501
fuera de 127.0.0.1:8501: 0
17 de 17 comprobaciones en verde
```

La última línea de Procedencia es la configuración **en ejecución**: la app la lee de Streamlit, y
dice `127.0.0.1` con un entorno que pedía `0.0.0.0`. Las 133 peticiones cierran además algo que la
review anterior dejó sin auditar —lo que el navegador pide a terceros—: nada.

Un tropiezo del guion, no de la app: el primer selector del desplegable de informe no encontró nada.
Streamlit 1.65 hace el `selectbox` con un *ComboBox* de react-aria, no con el de baseweb, y se abre
con su botón «Open».

---

## Review #2 — limpieza

- `app/streamlit_app.py` pierde `ruta_de_la_base()` y su `import os`: la regla vive en `almacen`.
  La orden del lanzador está en una sola constante, `ORDEN_LANZADOR`, que usan la guarda y la
  pantalla de procedencia.
- `tests/test_lanzador.py` ya no construye nada que no pruebe algo (L3).
- La prueba de concepto de C3 se queda en el *scratchpad*; en el repositorio solo entra
  `src/melate/app.py`.
- `grep "streamlit run"` fuera de la bitácora: solo aparece como alternativa —en el README, el
  `CLAUDE.md`, la app, `.streamlit/config.toml` y los docstrings del lanzador y su test—, nunca como
  la orden principal.

## Review de seguridad

**Lo que el lanzador cambia en la superficie:** nada que escuche. Arranca el mismo servidor, con la
red más cerrada que `streamlit run`, y escribe solo lo que escribe `python -m melate.almacen`: la
base y su temporal `.construyendo`, en la carpeta de la base. La sustitución de
`get_external_ip` vive solo en su propio proceso.

**Cada salida a la red del Streamlit 1.65 instalado**, leída en su código (`grep` de `requests.`,
`urlopen`, `httpx`, `http.client` y conexiones de socket, fuera de `testing/`, `connections/` y
`external/`), y qué pasa con ella:

| Dónde | A quién | Con el lanzador |
|---|---|---|
| `net_util.get_external_ip` | `checkip.amazonaws.com` | **anulada**; en vivo, el proxy no registra nada |
| `net_util.get_internal_ip` | `connect` UDP a 8.8.8.8 | **no envía ningún paquete**: un `connect` UDP solo elige la interfaz |
| `runtime/credentials.py`, `_send_email` | `data.streamlit.io` | solo tras la pregunta del correo, que solo existe sin `headless`; **forzado** `headless` |
| `web/cli.py`, `_download_remote` | la URL del script | solo con `streamlit run <URL>`; el lanzador pasa un fichero local |
| `config_util.py`, `_load_theme_file` | la URL de un tema | solo si un `config.toml` pone `theme.base` en una URL: ver abajo |
| *frontend*, `MetricsManager` | `data.streamlit.io` | **forzado** `gatherUsageStats = false`; en vivo, 0 peticiones fuera |

En 1.65 **no hay** comprobación de versiones contra PyPI: `grep` de `should_show_new_version` y
`new_version` en todo el paquete, vacío. Y el inicio de sesión (`st.login`, en
`web/server/starlette/starlette_auth_routes.py`) hablaría con un proveedor de identidad, pero solo si
la app lo usara y hubiera una sección `[auth]` en un `secrets.toml`: no lo usa, y no hay secretos.

**Lo que el lanzador no fuerza, y por qué.** Todo exige que alguien escriba a propósito una
configuración, y nada de ello lo trae el valor por defecto, que es la razón para fijar las demás:

- `server.corsAllowedOrigins`: un origen que alguien añada ahí se aceptaría en el WebSocket. No se
  puede vaciar desde la línea de órdenes: Streamlit descarta una lista vacía en las opciones.
- `theme.base` con una URL: Streamlit la descargaría al leer la configuración. Fijar un tema
  cambiaría la app para todos, y esa descarga la vería el proxy.
- `global.developmentMode`: es una opción oculta; solo afloja las cabeceras CORS de HTTP —no la
  comprobación del WebSocket— y rompe el *frontend* de la app.
- `get_internal_ip` añade la IP de la red local de la máquina a los orígenes aceptados: una página
  servida desde esa IP **por un servidor de esta misma máquina** podría abrir el WebSocket. Un
  `Origin` lleva el nombre escrito en la URL, no la IP resuelta, así que un *DNS rebinding* no llega
  a esto.

**Modos de fallo, todos cerrados:** sin la función a sustituir, `SystemExit`; sin la app,
`SystemExit`; con la base bloqueada por otro proceso, el `SystemExit` de `almacen.construir`; y una
construcción interrumpida deja un `.construyendo`, que está en `.gitignore` y que la siguiente borra.

---

## Mutación

**46 de 46 detectadas, en 2 min 9 s** (la línea base sin mutar, 13,1 s, incluida): las 33 de antes y
13 nuevas. Once son del lanzador: las tres opciones de red que importan, el paso de `RED` a la línea
de órdenes, la sustitución de la búsqueda y su guarda, la base vieja, la base rota, la base al día
que no se toca, la carpeta desde la que reconstruye y la regla única de la ruta. Las otras dos son
la protección de origen en `.streamlit/config.toml` y la de L1 en `.gitignore`, añadida al preparar
el cierre. Cada una la caza el test que dice vigilarla; la lista entera, con su test, la imprime el
guion. Después de la pasada, `grep` no encuentra ninguna mutación en el árbol de trabajo.

## Cada número publicado, vuelto a medir

| Qué | Antes del lanzador | Ahora |
|---|---|---|
| `pytest -m "not lento and not red"` | 197 pruebas, 11,2-11,8 s (11,7-11,9 s, medidas hoy en la misma máquina) | **213 pruebas, 12,6-12,7 s** (tres pasadas) |
| `pytest tests` | 226 pruebas, 133,4 s | **242 pruebas, 136,3 s**, `test_paridad.py` en verde |
| `scripts/mutar.py` | 33 de 33, 1 min 47 s | **46 de 46, 2 min 9 s** |
| `src/melate/app.py` | — | 140 líneas; su test, 248 |
| De la orden del lanzador a `/_stcore/health` = `ok`, con la base al día | — | 3 s |
| Construir la base, proceso nuevo | ~1,7 s | 1,88-1,96 s en el *scratchpad*; 2,19-2,56 s en la carpeta del repositorio; una vez 16,73 s, no reproducida |
| `scripts/colador.ps1 -Autoprueba` | 0 sobre 113 ficheros, autoprueba 4/4 | **0 sobre 117 ficheros**, autoprueba 4/4 |

## Cada parámetro del que se dice que gobierna algo, con dos valores

| Parámetro | Valores | Dónde |
|---|---|---|
| El entorno de Streamlit (`config.toml` de la carpeta y `STREAMLIT_*`) | `streamlit run` a secas → hostil (`0.0.0.0`, telemetría, sin CORS); el lanzador en el mismo entorno → `RED`, opción por opción | `test_la_red_queda_forzada_…`; en vivo, `127.0.0.1` con un entorno que pedía `0.0.0.0` |
| El estado de la base | falta, rota, de otro esquema, de otro árbol y desactualizada → su motivo; al día → `None`, y no se toca | `test_el_lanzador_sabe_…` (5), `test_una_base_al_dia_…`; en vivo, falta → construida, al día → misma fecha |
| La búsqueda de la IP | sin el lanzador → pide `checkip`; con él → nada | `test_el_lanzador_no_deja_…`; en vivo, el proxy con 0 líneas (con `streamlit run`, 1) |
| `get_external_ip` en Streamlit | existe → sustituida; no existe → `SystemExit` | `test_sin_la_funcion_…` |
| `MELATE_DUCKDB` | sin fijar → `melate.duckdb` en la raíz; fijada → esa ruta, para la app y para el lanzador | `test_la_app_y_el_lanzador_buscan_…` |
| `--puerto` | 8501 por defecto; 8765 | en vivo; `test_la_red_queda_forzada_…` |
| `enableCORS` | `true` → otro origen, 403; el entorno hostil lo apagaba → siguió en 403 | en vivo |
| El patrón de `secrets.toml` | `**/.streamlit/…` → el de `app/` excluido; `.streamlit/…` → publicable | `test_ningun_secreto_…` y su mutación |

## Cómo verificar / revertir

```powershell
.venv\Scripts\python.exe -m pytest tests\test_lanzador.py tests\test_app.py -q
.venv\Scripts\python.exe scripts\mutar.py --solo C3       # 13 de 13 detectadas
.venv\Scripts\python.exe -m melate.app                    # «melate.duckdb está al día.»
netstat -ano | findstr :8501                              # solo 127.0.0.1:8501
```

Los dos guiones de la verificación en vivo (`vivo_red.py` y `recorrido_clics.py`) y el proxy chivato
viven en el *scratchpad* de la sesión, no en el repositorio: son herramientas de una comprobación,
no del proyecto. Lo que comprueban está escrito arriba con su salida.

**Revertir:** cada arreglo vive en un fichero y tiene su test —L1 en `.gitignore`, L2 en
`src/melate/app.py` y `.streamlit/config.toml`, L3 en `tests/test_lanzador.py`—. Para quitar el
lanzador entero, los pasos literales están en
`Fases/2026-10-04_app-local/Cambios/2026-10-04_16-08_s4-lanzador-propio.md`.

Relacionado: `Fases/2026-10-04_app-local/Cambios/2026-10-04_16-08_s4-lanzador-propio.md`,
`Fases/2026-10-04_app-local/Decisiones/2026-10-04_11-00_s4-lo-que-decidio-el-usuario.md`,
`Fases/2026-10-04_app-local/Bugs/2026-10-04_10-05_s4-review-base-app-y-red.md`.

---

## Un hallazgo fuera de esta review: el test que vigila melate-e.com lee la caché

Encontrado al preparar la explicación de los pendientes heredados para el usuario. El pendiente 7
de `Fases/2026-10-03_popularidad/99_CIERRE.md` dice que la forma de la tabla del sitio la vigila «un
único test marcado `red`»: `test_el_sitio_sigue_teniendo_la_forma_que_esperamos`, en
`tests/test_popularidad.py`. Ese test pide el sorteo 4272 con `Descargador()`, cuya caché por defecto
es `data/cache/melate-e`, y `Descargador.html` devuelve la página guardada si existe
(`src/melate/popularity.py:267`). **`data/cache/melate-e/melate/4272.html` existe desde la Fase 3**,
así que el test lee la copia guardada y no el sitio: si el sitio cambiara su tabla, seguiría en
verde. Comprobado haciendo lo mismo que el test con una sesión que falla si se usa: 9 categorías,
los 115 808 ganadores que el test espera, y `peticiones = 0`.

**No se tocó.** Es código de la Fase 3, y arreglarlo —una caché temporal en ese test— significa una
petición real a un sitio de terceros en cada pasada de la suite completa, que el dictamen de ese
sitio no contempla. Es decisión del usuario: se le consulta como C8.

---

## Resultado — CERRADO el 2026-10-04 a las 16:20

**El lanzador está hecho, probado y verificado en vivo en el peor caso.** Tres fallos de la review,
corregidos y con test: L1 (el `secrets.toml` junto al script), L2 (`enableCORS` sin fijar) y L3 (los
tests reconstruían la base sin necesidad). La lista de verificación en vivo, ejecutada entera.

- `pytest tests`: **242 en verde**, 136,3 s, con `test_paridad.py` intacto.
- `pytest -m "not lento and not red"`: **213 en verde**, 12,6-12,7 s.
- `scripts/mutar.py`: **46 de 46** detectadas, 2 min 9 s.
- `scripts/colador.ps1 -Autoprueba`: **0 coincidencias sobre 117 ficheros**, autoprueba 4/4.
- `scripts/verificar-bitacora.ps1`: **0 hallazgos**, 58 documentos.
- En vivo, con un entorno que pedía `0.0.0.0`, telemetría y sin protección de origen: solo
  `127.0.0.1:8501`; otro origen y `Host` ajeno, 403; el proxy, sin ninguna petición; el navegador,
  133 peticiones, todas a `127.0.0.1:8501`.
- El veredicto del proyecto no cambia: **sin ventaja demostrada**, 0 de 5 condiciones.

**Lo que queda, y no es un fallo de esta review:**

1. **C8**, el test de melate-e.com que lee la caché (arriba): consultado al usuario.
   *Nota de las 16:35: eligió la caché de usar y tirar; hecho en
   `Fases/2026-10-04_app-local/Cambios/2026-10-04_16-35_s4-el-test-del-sitio-pide-la-pagina-de-verdad.md`.*
2. **El recorrido a mano** de la review anterior queda hecho con clics de ratón reales en un
   navegador real; solo falta que lo mire una persona.
3. **El primer veredicto con holdout**, cuando el oficial publique el sorteo 4274.
4. **Fuera de Windows**, heredado.
