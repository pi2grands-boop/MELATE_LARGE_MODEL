# El lanzador propio: `python -m melate.app`

- **Fecha/hora:** 2026-10-04 16:08
- **Área:** Fases/2026-10-04_app-local · **Acción:** Cambios
- **Chat / página:** sesión de la Fase 4 · la decisión C3, aprobada por el usuario
- **Archivos afectados:** `src/melate/app.py` (nuevo), `src/melate/almacen.py`,
  `app/streamlit_app.py`, `.streamlit/config.toml`, `.gitignore`, `requirements.txt`,
  `tests/test_lanzador.py` (nuevo), `tests/test_app.py`, `scripts/mutar.py`, `README.md`, `CLAUDE.md`

## Qué se hizo

**`src/melate/app.py`**, 140 líneas, que se lanza con `python -m melate.app [--puerto N]` y hace
tres cosas antes de servir, en este orden:

1. **Pone la base al día.** `por_que_construir(ruta)` devuelve el motivo para construir —no existe,
   no se puede leer, es de otro esquema, no se puede comprobar si está al día, o está desactualizada
   (con cuántos ficheros nuevos, cambiados o borrados)— o `None` si está al día. `poner_al_dia(ruta)`
   construye con `almacen.main`, sobre los `reportes/` y `prereg/` **de la carpeta de la base**, que
   es contra lo que `almacen.frescura` comprueba si está al día. La ruta sale de
   `almacen.ruta_de_la_base(RAIZ)`, la misma función que usa la app.
2. **Anula la búsqueda de la IP pública.** `sin_ip_publica()` sustituye
   `streamlit.net_util.get_external_ip` por `ninguna_ip_publica`, que devuelve `None`. Si esa función
   no existe —una versión nueva de Streamlit que la renombre—, `SystemExit`: sustituir un atributo
   ausente crearía uno nuevo y dejaría la búsqueda viva en silencio.
3. **Fuerza la red por línea de órdenes.** `RED`, ocho opciones —`server.address`,
   `server.headless`, `server.allowedHosts`, `server.enableCORS`, `server.enableXsrfProtection`,
   `browser.serverAddress`, `browser.gatherUsageStats` y `client.toolbarMode`—, se convierte en
   argumentos de `streamlit run` con `argumentos()` y se pasa a `streamlit.web.cli.main`. Las opciones
   de la línea de órdenes mandan sobre los tres `config.toml` que lee Streamlit (el global, el de la
   carpeta desde la que se lanza y el que está junto al script) y sobre las variables `STREAMLIT_*`.

**Y fuera del lanzador:**

- **`almacen.ruta_de_la_base(raiz)`**, nueva: `MELATE_DUCKDB` si está fijada, o `melate.duckdb` en
  `raiz`. La app la usa en lugar de su propia regla, y pierde su `import os`.
- **La app** recomienda el lanzador en la guarda que se niega a enseñar nada y en el aviso de base
  ausente; la pantalla de procedencia enseña las dos órdenes, `melate.almacen` con la app abierta y
  `melate.app` al abrirla.
- **`.streamlit/config.toml`** fija `enableCORS` y `enableXsrfProtection`, como el lanzador, y su
  cabecera explica los dos caminos. Un test exige que los dos digan lo mismo.
- **`.gitignore`**: `**/.streamlit/secrets.toml`, que cubre también el de `app/`.
- **`requirements.txt`**: la nota de que el lanzador sustituye una función interna de Streamlit.
- **README y `CLAUDE.md`**: la orden de arranque es el lanzador; `streamlit run` queda como
  alternativa desde la raíz.

**Tests:** `tests/test_lanzador.py`, 15 pruebas; en `tests/test_app.py`, una aserción nueva en
`test_la_configuracion_ata_la_app_a_esta_maquina` y `test_ningun_secreto_de_streamlit_se_publica`.
**Mutaciones:** 13 nuevas en `scripts/mutar.py`, que copia ahora también `.gitignore`.

## Por qué

**Lo decidió el usuario.** C3 se le presentó como diseño, con su prueba de concepto fuera del
proyecto y lo que costaba, y contestó «Lo apruebo»
(`Fases/2026-10-04_app-local/Decisiones/2026-10-04_11-00_s4-lo-que-decidio-el-usuario.md`).

El lanzador cierra tres cosas que `streamlit run` no podía cerrar:

- **La búsqueda de la IP pública.** Ante una conexión de otro origen, Streamlit 1.65 pregunta su IP
  a `checkip.amazonaws.com`, y no es configurable: Amazon recibía una petición desde la IP del
  usuario cada vez que una página abierta en su navegador intentaba llegar a la app.
- **La carpeta de arranque.** `.streamlit/config.toml` solo se lee si se lanza desde la raíz, y las
  variables `STREAMLIT_*` mandan sobre cualquier fichero. La guarda de la app hacía seguro lo
  primero (se niega a enseñar nada), pero no útil.
- **La base que no se publica (C5).** Su único inconveniente era tener que construirla antes de
  abrir la app. Ahora la construye el lanzador cuando falta o se queda vieja, y la app sigue sin
  escribir nada: escribe una orden de terminal, como antes.

**Lo que no hace:** no cambia nada de lo que la app enseña ni de cómo lo lee, no le da a la app
ninguna capacidad nueva, y no añade ninguna dependencia.

**Dos cosas que el diseño aprobado no traía, y por qué entraron** (L1 y L2 de la review): fijar
`enableCORS` —sin ella, un `config.toml` global de otro proyecto dejaría a cualquier página leer la
app por el WebSocket— y cubrir el `secrets.toml` de `app/`, que Streamlit también lee. Las dos están
en la misma dirección que lo aprobado: la red de la app, independiente de la configuración de la
máquina.

## Impacto en seguridad / conexiones / datos

- **Seguridad:** la superficie se estrecha. Lo que queda, todo dependiente de que alguien escriba a
  propósito una configuración (`corsAllowedOrigins`, un tema remoto, el modo de desarrollo), está
  inventariado con su porqué en la review.
- **Conexiones:** una salida menos, la de `checkip.amazonaws.com`. Comprobado en vivo en el peor
  caso —entorno hostil y conexiones de otro origen—: el proxy chivato no registró **ninguna**
  petición, y el navegador hizo **133**, todas a `127.0.0.1:8501`.
- **Datos:** el lanzador escribe `melate.duckdb`, y solo cuando hace falta, con la misma función que
  `python -m melate.almacen`. Una base al día no se toca: en vivo, misma fecha de escritura.

## Qué premisa toca esto (§7 de las reglas)

| Documento | Estado |
|---|---|
| `Fases/2026-10-04_app-local/Decisiones/2026-10-04_11-00_s4-lo-que-decidio-el-usuario.md` | Decía C3 «pendiente de aprobación». Lleva una nota visible y fechada que apunta aquí |
| `Fases/2026-10-04_app-local/00_ALCANCE.md` | Su punto 3 y su criterio 6 hablan de `streamlit run`. Siguen valiendo, y se cumplen además con el lanzador; el cierre de la fase lo dirá |
| `Almacenamiento/Decisiones/2026-10-04_00-40_s4-que-entra-en-melate-duckdb.md` | Sigue valiendo: el lanzador construye con la misma función, y la base sigue sin publicarse |
| `Fases/2026-10-04_app-local/Bugs/2026-10-04_10-05_s4-review-base-app-y-red.md` | Cerrado a las 11:05 con C3 pendiente: es un registro con su hora, no se toca. Su riesgo residual (C3) queda resuelto aquí |
| README, `CLAUDE.md`, `requirements.txt`, `.streamlit/config.toml` y el docstring de la app | Actualizados en este mismo cambio |

## Cómo verificar / revertir

```powershell
.venv\Scripts\python.exe -m pytest tests\test_lanzador.py tests\test_app.py -q
.venv\Scripts\python.exe scripts\mutar.py --solo C3       # 13 de 13 detectadas
.venv\Scripts\python.exe -m melate.app                    # «melate.duckdb está al día.» · http://127.0.0.1:8501
netstat -ano | findstr :8501                              # solo 127.0.0.1:8501
```

La verificación en vivo completa, con un entorno hostil y el recorrido con clics, está en
`Fases/2026-10-04_app-local/Bugs/2026-10-04_11-39_s4-review-lanzador.md`.

**Revertir:**

1. Borrar `src/melate/app.py`.
2. Mover `test_la_app_y_el_lanzador_buscan_la_base_en_el_mismo_sitio` a `tests/test_almacen.py`
   (prueba `almacen.ruta_de_la_base`, que se conserva) y borrar `tests/test_lanzador.py`.
3. En `scripts/mutar.py`, borrar las diez mutaciones cuyo único fichero de test es
   `tests/test_lanzador.py`; en «la configuración apaga la protección de origen», dejar solo
   `tests/test_app.py` y la expresión `configuracion`; y en «la app y el lanzador miran bases
   distintas», cambiar el fichero de test a `tests/test_almacen.py`.
4. Volver a poner la orden `streamlit run` desde la raíz en la guarda de la app, en
   `ORDEN_REPRODUCIR`, en el README y en el `CLAUDE.md`, y quitar la nota de `requirements.txt`.

**Lo que se reintroduce:** la petición a `checkip.amazonaws.com` ante una conexión de otro origen,
la dependencia de la carpeta de arranque y de las variables `STREAMLIT_*`, y la construcción de la
base a mano. **Lo que conviene conservar**, porque no depende del lanzador:
`almacen.ruta_de_la_base`, `enableCORS` y `enableXsrfProtection` en `.streamlit/config.toml`, y
`**/.streamlit/secrets.toml` en `.gitignore`, cada uno con su test y su mutación.

Relacionado: `Fases/2026-10-04_app-local/Bugs/2026-10-04_11-39_s4-review-lanzador.md`,
`Fases/2026-10-04_app-local/Decisiones/2026-10-04_11-00_s4-lo-que-decidio-el-usuario.md`,
`Fases/2026-10-04_app-local/Bugs/2026-10-04_10-05_s4-review-base-app-y-red.md`,
`Almacenamiento/Decisiones/2026-10-04_00-40_s4-que-entra-en-melate-duckdb.md`,
`Fases/2026-10-04_app-local/00_ALCANCE.md`.
