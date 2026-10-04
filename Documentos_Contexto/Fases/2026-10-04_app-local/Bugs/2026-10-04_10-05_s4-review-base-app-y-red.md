# Review de la Fase 4 — la base, la app y la red

- **Fecha/hora:** 2026-10-04 10:05
- **Área:** Fases/2026-10-04_app-local · **Acción:** Bugs
- **Chat / página:** sesión de la Fase 4 · `src/melate/almacen.py`, `app/streamlit_app.py`, `.streamlit/config.toml`
- **Archivos afectados:** `src/melate/almacen.py`, `src/melate/lab.py`, `app/streamlit_app.py`,
  `.streamlit/config.toml`, `tests/test_almacen.py`, `tests/test_app.py`, `tests/conftest.py`,
  `scripts/mutar.py`, `reportes/2026-10-04_veredicto.json`, `requirements.txt`, `.gitignore`
- **Estado:** CERRADO el 2026-10-04 11:05 (bloque al final)

La review empezó hacia las 01:30, con la primera captura de la app en un navegador, y este
documento recoge su registro con la evidencia de cada punto. Se abre tarde: el pipeline pide abrirlo
al empezar la review #1, y se escribió después. Queda dicho.

## Limitaciones del entorno, por delante

- **Windows 11, PowerShell 5.1 y Git Bash.** Nada probado en Linux ni macOS.
- **Sin un navegador manejado a mano.** Las pantallas se vieron con Edge sin interfaz, por su
  protocolo de depuración en `127.0.0.1`: se navega a `?pantalla=<slug>`, se espera a que el texto
  renderizado contenga «sin ventaja demostrada» y se captura. Se ve la maquetación real, pero **nadie
  hizo clic**: los cambios de pantalla y del selector de informe se probaron por URL y con `AppTest`.
- **Las salidas a la red del servidor** se vigilaron con un proxy local que solo apunta lo que le
  llega, puesto como `HTTP_PROXY`/`HTTPS_PROXY` del proceso de Streamlit. Ve lo que pasa por
  `requests`, que es lo único con lo que el código de Streamlit 1.65 sale fuera (revisado en su
  código: `net_util`). Lo que el **navegador** pida a terceros no se auditó: no es del proyecto.
- **El holdout sigue vacío.** La app enseña «0 de 5» porque es lo que hay.

## Lo que se revisó

Tres pasadas, como en las fases anteriores: funcional (#1), de limpieza (#2) y de seguridad. Y una
cuarta que esta fase no tenía hasta hoy: **mirar la app**. Encontró cinco fallos que ningún test
veía, porque eran correctos en el árbol de elementos y falsos en la pantalla.

---

## Review #1 — fallos encontrados y corregidos

### B1 · Streamlit 1.65 escucha en todas las interfaces, IPv4 e IPv6, si no se le dice otra cosa

Leído en su código antes de escribir la configuración
(`streamlit/web/server/starlette/starlette_server.py`, `_get_bind_address`): sin `server.address`,
liga `"::"` con `IPV6_V6ONLY = 0`. Es peor que el `0.0.0.0` que el usuario prohibió: incluye IPv6.

**Arreglo:** `server.address = "127.0.0.1"` en `.streamlit/config.toml`, y una guarda dentro de la
app que se niega a enseñar nada si la dirección no es de loopback (la configuración solo se lee si se
lanza desde la raíz; la guarda vale se lance como se lance). **Comprobado en vivo:**

```
netstat -ano | grep :8501      ->  TCP 127.0.0.1:8501  LISTENING      (ninguna línea 0.0.0.0 ni [::])
http://<IP de la red local>:8501/_stcore/health  ->  no es posible conectar
http://[::1]:8501/_stcore/health                 ->  no es posible conectar
http://127.0.0.1:8501/_stcore/health             ->  200 'ok'
```

**Tests:** `test_la_app_se_niega_fuera_de_loopback_o_con_telemetria`, `test_solo_loopback_se_acepta`
(8 direcciones), `test_la_configuracion_ata_la_app_a_esta_maquina`.

### B2 · Streamlit envía estadísticas de uso a un tercero por defecto

`browser.gatherUsageStats` vale `true` por defecto, y el *frontend* pide entonces
`https://data.streamlit.io/metrics.json` (leído en su `MetricsManager`). Para un proyecto que
escribió un documento entero sobre su tráfico saliente
(`Seguridad/Añadir/2026-10-03_05-15_s3-trafico-saliente-a-un-tercero.md`), no.

**Arreglo:** apagada en la configuración, y la guarda también se niega si está encendida. Además
`headless = true`, que evita la pregunta del correo electrónico la primera vez (comprobado: no se
creó ninguna carpeta `.streamlit` en el perfil del usuario), y `toolbarMode = "viewer"`, que quita el
botón de desplegar en la nube. **Test:** el mismo de B1, con la telemetría encendida.

### B3 · `?pantalla=` se descartaba en silencio — lo vio una captura, no un test

La primera versión ligaba la radio a la URL con `bind="query-params"`. Las cinco capturas salieron
**iguales** y la URL perdía el parámetro: Streamlit exige en la URL la **etiqueta** formateada
(«Exploración»), no el valor («exploracion»), y descarta lo demás sin avisar. `AppTest` no simula la
URL de un widget ligado, así que los tests pasaban.

**Arreglo:** la app lee y escribe `st.query_params` a mano. **Test:**
`test_la_url_elige_la_pantalla` (dos valores: una pantalla y una que no existe). **En vivo:** las
cinco URL conservan su `?pantalla=` y cada una pinta su pantalla.

### B4 · El `st.metric` truncaba el veredicto a «sin ventaja demos…»

En la pantalla que juzga, la palabra que importa salía cortada. **Arreglo:** el veredicto va en un
encabezado de texto; los dos metric que quedan son cifras cortas.

### B5 · Rutas escapadas dentro de comillas invertidas: `2026\-10\-04\_veredicto\.json`

Dentro de un bloque de código Markdown no procesa los escapes, y las barras se ven. **Arreglo:**
`codigo()`, que solo impide otra comilla invertida; `escapar()` queda para el texto normal.

### B6 · Tablas que cortaban justo la cifra importante

Visto en las capturas: la tabla de popularidad cortaba el **efecto calendario** (−24,5 %,
t = −18,67), que es la cifra más importante de esa pantalla; la del valor esperado cortaba la bolsa
de equilibrio y mezclaba en una columna la de las dos variantes; las de más de diez filas se
cortaban con barra; y las celdas vacías decían `None`.

**Arreglo:** un único `ver()` para todas las tablas (`height="content"`, `placeholder="—"`), el
efecto calendario en su propia tabla y el valor esperado en formato largo, una fila por juego y
variante. Las capturas finales enseñan las cinco pantallas enteras.

### B7 · La cabecera y la pantalla del veredicto elegían el vigente con reglas distintas

La cabecera usaba `almacen.veredicto_vigente`; la pantalla, `iloc[-1]` tras ordenar por fecha. Con
los datos de hoy coincidían; con otros, la app habría enseñado dos veredictos distintos a la vez.
**Arreglo:** la pantalla recibe el vigente de la misma función. **Test:** la base forjada trae un
veredicto que separa las dos reglas, y `test_una_q_exploratoria_…` comprueba que cabecera y pantalla
enseñan el mismo.

### B8 · El vigente era «el último que se corrió»

Volver a correr el laboratorio sobre el snapshot viejo —para reproducir una cifra, por ejemplo—
habría desplazado a un veredicto con sorteos de holdout. **Arreglo:** vale el que juzgó con **más
datos**; a igualdad, el más reciente; uno que no registra sus datos solo si no hay otro. **Tests:**
`test_el_vigente_es_el_que_juzgo_con_mas_datos` y `test_el_criterio_del_vigente` (4 casos).

### B9 · Un reporte malformado tumbaba la construcción entera

La decisión de `Almacenamiento/` promete que lo que no se entiende entra como no válido sin romper
nada. Era verdad para un JSON ilegible, no para uno que se clasifica bien y tiene la forma rota.
**Arreglo:** cada fichero escribe en su propio lote, que solo se suma si sale entero. **Test:**
`test_lo_que_no_se_reconoce_no_rompe_la_construccion` (cuatro ficheros, y ninguna fila a medias).

### B10 · Lanzada desde otra carpeta, la orden construía una base vacía en silencio

**Arreglo:** si `reportes/` o `prereg/` no existen, `SystemExit` antes de escribir nada.
**Test:** `test_sin_carpetas_no_se_construye_nada`.

### B11 · Un preregistro dentro de `reportes/` habría contado como preregistro

**Arreglo:** entra como no válido, con el motivo. **Test:** el de B9.

### B12 · Fechas comparadas como texto, y un veredicto sin fecha habría sido «el más reciente»

**Arreglo:** `_utc()` normaliza toda fecha a UTC y segundos antes de guardarla, y un veredicto sin
fecha de corrida no es válido. **Tests:** `test_las_fechas_se_normalizan_antes_de_ordenarlas`,
`test_un_veredicto_sin_fecha_no_cuenta`.

### B13 · Una base de una versión anterior pasaba la comprobación de esquema

Apareció al añadir una columna: la `melate.duckdb` de la raíz, construida una hora antes, tenía
todas las tablas y le faltaba la columna, y la app habría muerto con un `KeyError`. **Arreglo:**
`problema_de_esquema` compara también las columnas. Comprobado sobre la base vieja real:
`a la tabla veredictos le faltan columnas: ultimo_concurso_datos_min`. **Test:**
`test_una_base_de_otro_esquema_se_rechaza`.

### B14 · Dos textos de un veredicto llegaban a Markdown sin escapar

`ultima_fecha_datos` y `juego_principal`. Un `![x](http://…)` en un veredicto válido habría hecho al
navegador pedir esa URL. **Arreglo:** escapados. **Test:** `test_el_camino_afirmativo_llega_a_la_cabecera`,
con una fecha maliciosa en un veredicto válido.

### B15 · El bucle rápido pasó de 5,3 s a 14,5 s con los tests nuevos, y a ~15 s al final

Es el fallo que este proyecto ya documentó dos veces. No se marcó nada como `lento`:

| Qué | Efecto |
|---|---|
| Construir dentro de una sola transacción | 0,31 s → 0,16 s por base |
| Bases adversarias compartidas por sesión (una con todos los casos que no deben llegar a la cabecera) | ~20 construcciones → 5 |
| Un único recorrido de `AppTest` para las cinco pantallas, la frontera y la prohibición de cómputo y red | 20 instancias → 12 |
| En los tests de la app, no buscar componentes personalizados de Streamlit | ~15 s → **~11,5 s** |

El último merece una línea: perfilada una `AppTest`, **el 80 % de su coste** era Streamlit
recorriendo los metadatos de los 69 paquetes instalados en busca de componentes personalizados
(`components/v2/manifest_scanner.py`), en cada instancia nueva. La app no usa ninguno, así que los
tests se lo ahorran con un fixture; la app real no se toca.

**Medido al final, tres veces:** las 135 pruebas que ya existían siguen en **5,2-5,4 s**, y el bucle
completo da **190 pruebas en 11,4-11,8 s**. Lo que no se pudo quitar es el coste real de probar un
subsistema nuevo: importar Streamlit y DuckDB (~1,6 s), construir cinco bases (~2 s) y las
`AppTest`.

**Probado y descartado:** insertar cada tabla desde un DataFrame en vez de `executemany` (0,157 s
contra 0,157 s con los datos reales; se revirtió) y bloques de 16 KB en vez de 256 KB (la base pasa
de 5 MB a 1 MB pero solo es un 12 % más rápida; no compensa otra forma de abrirla).

### B16 · Un nombre local tapaba al ayudante `ver()`

Introducido y cazado en el mismo ciclo: el recorrido de la app falló con
`'DataFrame' object is not callable` en la pantalla del veredicto. Se registra porque es la
evidencia de que el recorrido completo vigila de verdad.

### H1 · El veredicto no registraba los datos sobre los que juzgó — arreglado

Del inventario. `lab.evaluar` escribe ahora `datos` (SHA-256, origen, bytes, último sorteo y fecha
por juego) y la CLI los imprime. `reportes/2026-10-04_veredicto.json` es el primero que los lleva;
el de la Fase 2 se conserva tal cual y la app dice que no los registra. **Test:**
`test_el_veredicto_registra_los_datos_sobre_los_que_juzga`, con dos valores (4272 y 4262).

---

## Review #2 — limpieza

- **Sin código muerto:** el fixture `arbol` quedó sin uso al compartir bases y se quitó; el
  experimento del DataFrame se revirtió entero; `tabla()` y `ver()` son los dos únicos ayudantes de
  presentación.
- **Una sola fuente para cada regla:** el vigente sale de `almacen.veredicto_vigente`; el texto de
  «sin ventaja demostrada» de `protocolo.SIN_VENTAJA`; el texto afirmativo de `almacen.VENTAJA`, con
  un test que lo ata a lo que escribe `protocolo.declara_ventaja`.
- **Lo que se decidió NO tocar:** `baseline_auditoria.py`, `ev.py`, `protocolo.py`, el preregistro
  y `popularity.py`. El único cambio fuera de los ficheros nuevos es `lab.py` (H1).

## Review de seguridad

- ✅ **Escucha solo en loopback**, con configuración, guarda y comprobación en vivo (B1).
- ✅ **Sin telemetría** (B2). Con la telemetría apagada el *frontend* no pide `metrics.json`; la
  otra URL de `data.streamlit.io` en el paquete solo se usa con `?staticAppId=`, que la app no usa.
- ✅ **El WebSocket, que es por donde viajan los datos, solo acepta esta máquina.**
  `server.allowedHosts = ["127.0.0.1", "localhost"]` corta un *DNS rebinding*. En vivo:

  ```
  Host 127.0.0.1  Origin http://127.0.0.1:8501   ->  101 Switching Protocols
  Host localhost  Origin http://localhost:8501   ->  101 Switching Protocols
  Host 127.0.0.1  Origin https://evil.example    ->  403 Forbidden
  Host evil.example Origin http://evil.example   ->  403 Forbidden
  ```

- ⚠️ **Pero el tercer caso hace salir al servidor a la red.** Ante un WebSocket de otro origen,
  Streamlit busca la IP pública de la máquina para compararla, con un `GET
  http://checkip.amazonaws.com/` (HTTP plano). El proxy lo atrapó. No es configurable. Ver C3.
- ✅ **En el uso normal, ninguna salida.** Con el proxy puesto durante dos arranques del servidor y
  21 cargas de pantalla, su registro tiene una sola línea: la de la prueba de otro origen.
- ✅ **La app no escribe** (test que lee su fuente), abre la base en solo lectura (test con un espía
  sobre `duckdb.connect`), y no importa nada que calcule o salga a la red (test sobre su árbol
  sintáctico, y otro que convierte el cómputo y los sockets fuera de loopback en excepciones).
- ✅ **Texto de los ficheros escapado** antes de llegar a Markdown; nunca `unsafe_allow_html` ni HTML
  crudo (`grep` vacío). Ver B14.
- ✅ **La base no se publica** (`.gitignore`), no guarda rutas absolutas (test), y el colador sigue
  leyendo los JSON de los que sale. `.streamlit/secrets.toml` entra también en `.gitignore`: no hay
  secretos, y así no se puede publicar uno por accidente.
- ✅ **Dependencias:** 23 paquetes nuevos, todos con *wheel*, fijados en `requirements.txt` y en
  `entorno/pip-freeze-2026-10-04.txt`; ninguna versión anterior se movió (pandas sigue en 2.3.3).

## Observación aceptada (no es bug)

- **`melate.duckdb` pesa 5 MB para 250 KB de JSON.** Son los bloques de 256 KB de DuckDB, uno por
  tabla como mínimo. No se publica y se reconstruye en 0,16 s: no merece una forma especial de abrirla.
- **En algunas capturas la barra lateral sale cortada.** Es la animación de la barra cuando la página
  es más alta que la ventana emulada; con el mismo código, la captura de la pantalla de jugadores la
  enseña entera.

---

## Mutación: los tests propios, rotos uno a uno

`scripts/mutar.py` es nuevo y cierra el pendiente heredado nº 8: la mutación de la Fase 3 se hizo a
mano con un guion que no quedó en el repositorio. Este **copia** el repositorio a una carpeta
temporal y muta la copia, así que no puede dejar un fichero mutado ni finales de línea cambiados —lo
que le pasó a aquella auditoría—. Primero exige que los tests elegidos pasen sin mutar.

Las 9 mutaciones de la Fase 3 y 21 nuevas: **30 de 30 detectadas, en 1 min 43 s** (la línea base
sin mutar, 12,3 s, incluida). La lista entera, con el test que caza cada una, la imprime el propio
guion. Después de la pasada, `grep` sobre `src/`, `app/` y `.streamlit/` no encuentra ninguna de las
mutaciones: el árbol de trabajo no se tocó.

Tras las decisiones del usuario son **33 de 33** (tres nuevas para C1 y C4), y la herramienta tiene
su propia prueba: al añadirlas destapó un fallo suyo —en un fichero con CRLF, una mutación con salto
de línea no se aplicaba—, contado y arreglado en
`Fases/2026-10-04_app-local/Decisiones/2026-10-04_11-00_s4-lo-que-decidio-el-usuario.md`.

## Cada número publicado, vuelto a medir

| Qué | Al empezar la fase | Ahora |
|---|---|---|
| `pytest -m "not lento and not red"` | 135 pruebas, 5,34 s | **197 pruebas, 11,2-11,8 s** (tres pasadas, tras las decisiones); las 135 de antes, 5,2-5,4 s |
| `pytest tests` | 164 pruebas, 135,2 s | **226 pruebas, 133,4 s** tras las decisiones (antes de ellas, 219 en 135,5 y 152,7 s), `test_paridad.py` en verde |
| `scripts/mutar.py` | no existía | **33 de 33**, 1 min 47 s, tras las decisiones (antes, 30 de 30 en 1 min 43 s) |
| Construir `melate.duckdb` | — | 0,16 s en caliente; ~1,7 s la orden entera, por las importaciones; 4 993 024 bytes |
| Arrancar la app hasta `/_stcore/health` = `ok` | — | ~1 s |
| `scripts/colador.ps1 -Autoprueba` | 0 sobre 98 ficheros | **0 sobre 110 ficheros**, autoprueba 3/3 |
| `scripts/verificar-bitacora.ps1` | 0 hallazgos, 50 documentos | 1 hallazgo, 54 documentos: este `Bugs/`, abierto a propósito |
| Paquetes del entorno | 43 más la instalación editable (`entorno/pip-freeze-2026-10-03.txt`) | **66** más la instalación editable (`entorno/pip-freeze-2026-10-04.txt`) |

## Cada parámetro del que se dice que gobierna algo, con dos valores

| Parámetro | Valores | Dónde |
|---|---|---|
| `server.address` | 3 de loopback aceptadas; `0.0.0.0`, `::`, vacía, sin fijar y una IP de la red, rechazadas | `test_solo_loopback_se_acepta`, y en vivo |
| `browser.gatherUsageStats` | `false` se acepta; `true` se rechaza | `test_la_app_se_niega_…` |
| `server.allowedHosts` | `Host: 127.0.0.1` → 101; `Host: evil.example` → 403 | en vivo |
| `?pantalla=` | `jugadores` abre Jugadores; `no-existe`, el veredicto | `test_la_url_elige_la_pantalla`, y las cinco en vivo |
| Selector de informe | 2 000 simulaciones → q mínima 0.3060; 200 → 0.5940 | `test_el_selector_de_informe_gobierna_la_pantalla` |
| `MELATE_DUCKDB` | base real → sin ventaja; base con ventaja → VENTAJA; inexistente → aviso | tests de la app |
| La firma de la caché | dos bases en la misma ruta → dos cabeceras | `test_reconstruir_la_base_cambia_lo_que_ensena` |
| Datos del vigente | más datos gana aunque sea más viejo; a igualdad, el más reciente | `test_el_criterio_del_vigente` |
| `--reportes` / `--prereg` | existentes → base; inexistentes → `SystemExit` | `test_sin_carpetas_no_se_construye_nada` |
| Datos de `lab.evaluar` | snapshot → 4272; recortados → 4262 | `test_el_veredicto_registra_los_datos_…` |

---

## Decisiones que NO son mías — pendientes de consultar

**C1 · Tres tablas de ganadores sin premios (H2 del inventario).** Los sorteos 4107, 4111 y 4119
entraron con todos los premios a `$0.00`. Propuesta: que `popularity.parsear` marque esos sorteos
como sin premios publicados, conservando sus ganadores (las ventas y el efecto calendario no usan
premios). Efecto, medido: los menores de la ventana de 300 pasan a n = 297, media 4,6500 y mediana
4,6465. Ninguna cifra del `CLAUDE.md` cambia. Es código de la Fase 3.

**C2 · Nueve pruebas que se corren y no están en la familia de 36.** El backtest calcula una t y una
p de log-loss para tres modelos en tres juegos. Ningún documento las cuenta en la familia ni dice por
qué no. Son de dos colas y sus p bajas dicen **peor** que el azar («Más frecuentes»: p ≈ 0): meterlas
tal cual haría que el informe dijera «revisar» por un modelo que pierde. La app las enseña con esa
lectura y diciendo que están fuera de la familia. **La familia es decisión del usuario**, y el
preregistro sellado declara 36 en cualquier caso.

**C3 · Una conexión de otro origen hace que el servidor pida `checkip.amazonaws.com`.** Lo que
cuesta: Amazon recibe una petición desde la IP del usuario cuando una página abierta en su navegador
intenta conectar con `127.0.0.1:8501`. El ataque no obtiene nada (403). Opciones: dejarlo
documentado como comportamiento de la dependencia, o arrancar la app con un lanzador propio que
desactive esa búsqueda antes de levantar el servidor, a cambio de no usar `streamlit run` a secas y
de parchear una función interna de una versión fijada.

**C4 · La valoración de la cartera no registra con qué bolsa se hizo.** `portfolio.valorar` no
guarda la bolsa ni los menores que recibió. La app lo dice. Arreglarlo es una línea en código de la
Fase 3.

**C5 · `melate.duckdb` no se publica.** Lo decidió el proyecto dentro del criterio del usuario
(`Almacenamiento/Decisiones/2026-10-04_00-40_s4-que-entra-en-melate-duckdb.md`). Se puede revertir.

**C6 · El `CLAUDE.md`.** No se ha tocado. Propuesta: que «Lo que protege el proyecto de sí mismo»
nombre `scripts/mutar.py` junto a los dos scripts bloqueantes, y las tres reglas de la app (solo
loopback, no recalcula, el veredicto solo del laboratorio).

**C7 · El bucle rápido sube de ~5 s a ~11,5 s.** Es el coste de probar la app (B15). La alternativa
—sacar los tests de la app del bucle con un marcador— es exactamente lo que este proyecto decidió no
hacer dos veces.

## Pendiente de verificar en vivo

1. **Abrir la app y recorrerla a mano**: los clics en la barra lateral, el selector de informe y los
   desplegables. Las capturas navegaron por URL. Un minuto.
2. **El primer veredicto con holdout.** El 4274 se celebra hoy; después de que el oficial lo publique,
   `melate.lab` sin `--datos` y `melate.almacen`, y la app tiene que enseñar 1 sorteo de holdout.
3. **Fuera de Windows.** Heredado.
4. **C1 a C7.**

## Cómo verificar / revertir

```powershell
.venv\Scripts\python.exe -m pytest tests\test_almacen.py tests\test_app.py -q
.venv\Scripts\python.exe scripts\mutar.py                     # 30 de 30 detectadas
.venv\Scripts\python.exe -m melate.almacen
.venv\Scripts\python.exe -m streamlit run app\streamlit_app.py
netstat -ano | findstr :8501                                  # solo 127.0.0.1:8501
```

**Revertir:** cada arreglo vive en `src/melate/almacen.py`, `app/streamlit_app.py` o
`.streamlit/config.toml` y tiene su test; para quitar la fase entera, ver el cierre del dossier
cuando exista.

Relacionado: `Fases/2026-10-04_app-local/00_ALCANCE.md`,
`Fases/2026-10-04_app-local/Inventario/2026-10-04_00-36_s0-estado-de-partida.md`,
`Almacenamiento/Decisiones/2026-10-04_00-40_s4-que-entra-en-melate-duckdb.md`.

---

## Resultado — CERRADO el 2026-10-04 a las 11:05

**Los dieciséis fallos de la review, más H1, corregidos y con test.** Las siete decisiones se
consultaron al usuario, que contestó a todas; su respuesta, con el porqué y lo que se hizo con cada
una, está en `Fases/2026-10-04_app-local/Decisiones/2026-10-04_11-00_s4-lo-que-decidio-el-usuario.md`.

| | Decisión | Estado |
|---|---|---|
| C1 · Tablas sin premios | Sin premios publicados | **Hecho.** 297 sorteos con premios; ventas y efecto calendario intactos |
| C2 · Log-loss | Documentar y analizar si hacen falta | **Hecho**, en `Protocolo_Estadistico/Decisiones/2026-10-04_10-45_s4-el-log-loss-no-entra-en-la-familia.md` |
| C3 · Lanzador propio | Diseñarlo; se ejecuta si lo aprueba | **Diseñado y probado fuera del proyecto; pendiente de su aprobación** |
| C4 · Valoración de la cartera | Reparar | **Hecho.** La cartera regenerada es idéntica más tres campos |
| C5 · La base no se publica | Mantener, y reparar lo que se pueda | **Hecho.** El colador caza una base versionada; test |
| C6 · `CLAUDE.md` | Sí | **Hecho** |
| C7 · Bucle rápido de ~11 s | Aceptado | Registrado |

**Y un fallo que no estaba en la lista**, encontrado por la propia herramienta: `scripts/mutar.py` no
aplicaba en ficheros con CRLF las mutaciones con salto de línea. Arreglado, y con su prueba en
`tests/test_herramientas.py`.

**Estado al cerrar, medido:**

- `pytest tests`: **226 en verde**, 133,4 s, con `test_paridad.py` intacto.
- `pytest -m "not lento and not red"`: **197 en verde**, 11,2-11,8 s.
- `scripts/mutar.py`: **33 de 33** detectadas, 1 min 47 s.
- `scripts/colador.ps1 -Autoprueba`: **0 coincidencias sobre 113 ficheros**, autoprueba 4/4.
- `scripts/verificar-bitacora.ps1`: **0 hallazgos**, 56 documentos.
- El veredicto del proyecto no cambia: **sin ventaja demostrada**, 0 de 5 condiciones.

**Ningún bug abierto.** Lo que sigue pendiente no es un fallo de esta review:

1. **C3**, a la espera de la aprobación del usuario.
2. **El recorrido de la app a mano**, con clics: las capturas navegaron por URL.
3. **El primer veredicto con holdout**, cuando el oficial publique el sorteo 4274.
4. **Fuera de Windows**, heredado.
