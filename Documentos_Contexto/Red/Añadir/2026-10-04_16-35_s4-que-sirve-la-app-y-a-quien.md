# Qué sirve la app y a quién: solo a esta máquina

- **Fecha/hora:** 2026-10-04 16:35
- **Área:** Red · **Acción:** Añadir
- **Chat / página:** cierre de la Fase 4 · `Fases/2026-10-04_app-local/`
- **Archivos afectados:** `src/melate/app.py`, `.streamlit/config.toml`, `app/streamlit_app.py`

Es el primer documento de `Red/`. Hasta la Fase 4 el proyecto no servía nada, y el dictamen de
melate-e.com lo dejó escrito: «Este proyecto no sirve nada por red (`Red/` está vacía por eso)»
(`Fases/2026-10-03_popularidad/Decisiones/2026-10-03_02-40_s3-dictamen-terminos-melate-e.md`).
**Esa frase sigue siendo verdad en lo que importa:** nada se sirve a la red. `Red/` deja de estar
vacía porque ahora hay un servidor, pero ese servidor solo atiende a la propia máquina.

## Qué se sirve

La app de Streamlit —HTTP para la página y un WebSocket en `/_stcore/stream` para los datos— en
**`127.0.0.1:8501`**, mientras el usuario la tiene abierta. El puerto se cambia con
`python -m melate.app --puerto N`; la dirección no se puede cambiar desde el lanzador.

## Cómo se garantiza: tres capas

| Capa | Qué hace | Cuándo actúa |
|---|---|---|
| **El lanzador**, `python -m melate.app` | Arranca Streamlit con ocho opciones forzadas por línea de órdenes (`RED` en `src/melate/app.py`), que mandan sobre los tres `config.toml` que lee Streamlit y sobre las variables `STREAMLIT_*` | Es la forma recomendada, desde cualquier carpeta |
| **`.streamlit/config.toml`** | Las mismas ocho opciones; un test exige que digan lo mismo que el lanzador | Solo con `streamlit run` desde la raíz del repositorio, la única carpeta desde la que se lee |
| **La guarda de la app** | Se niega a enseñar nada si la dirección de escucha no es de *loopback* o si la telemetría está encendida | Siempre, se lance como se lance |

**Por qué hacen falta:** sin `server.address`, Streamlit 1.65 escucha en `"::"` con
`IPV6_V6ONLY = 0`, es decir, en todas las interfaces, IPv4 e IPv6 (leído en
`streamlit/web/server/starlette/starlette_server.py`). Es peor que el `0.0.0.0` que el usuario
prohibió. Y la telemetría viene encendida.

Las ocho opciones: `server.address = 127.0.0.1`; `server.headless = true` (sin abrir el navegador ni
preguntar un correo); `server.allowedHosts = [127.0.0.1, localhost]` (el WebSocket rechaza cualquier
otra cabecera `Host`, que es lo que corta un *DNS rebinding*); `server.enableCORS` y
`server.enableXsrfProtection = true` (sin la primera, el WebSocket acepta cualquier origen);
`browser.serverAddress = 127.0.0.1`; `browser.gatherUsageStats = false`; y
`client.toolbarMode = viewer` (sin el botón de desplegar en la nube).

## Qué pide el servidor fuera: nada

Streamlit 1.65 sale de la máquina en dos casos de uso normal, y los dos están cerrados:

- **La telemetría del *frontend*** (`data.streamlit.io`): apagada.
- **La IP pública ante una conexión de otro origen** (`checkip.amazonaws.com`): no es configurable,
  así que el lanzador sustituye `streamlit.net_util.get_external_ip` por una función que devuelve
  `None`. La conexión de otro origen se rechaza igual. Si una versión nueva de Streamlit la
  renombra, el lanzador se niega a arrancar; y un test recorre el Streamlit instalado para
  comprobar que nadie se guardó una referencia propia a la función.

El inventario completo de las salidas a la red del Streamlit instalado está en
`Fases/2026-10-04_app-local/Bugs/2026-10-04_11-39_s4-review-lanzador.md`.

## Comprobado en vivo, en el peor caso

Lanzado desde una carpeta que no es la raíz, con un `config.toml` que pedía `0.0.0.0`, telemetría,
`allowedHosts` con `evil.example` y `enableCORS = false`, con las variables `STREAMLIT_*` pidiendo lo
mismo, y con un proxy que apunta cada petición saliente:

```
netstat -ano | :8501                                       ->  TCP 127.0.0.1:8501  LISTENING   (nada más)
health por 127.0.0.1                                       ->  200
health por [::1] y por la IP de la red local               ->  no es posible conectar
WebSocket del mismo origen (127.0.0.1 y localhost)         ->  101
WebSocket de otro origen (dos distintos)                   ->  403
WebSocket con Host: evil.example                           ->  403
registro del proxy                                         ->  0 líneas
el navegador, recorriendo las cinco pantallas con clics    ->  133 peticiones, todas a 127.0.0.1:8501
```

## Lo que no se fuerza, y por qué

Todo exige que alguien escriba a propósito una configuración; ninguno lo trae el valor por defecto,
que es la razón de fijar los demás:

- `server.corsAllowedOrigins`: un origen añadido ahí entraría en el WebSocket. Streamlit no deja
  vaciar una lista desde la línea de órdenes.
- `theme.base` con una URL: Streamlit la descargaría al leer la configuración.
- `global.developmentMode`: una opción oculta que afloja las cabeceras CORS de HTTP —no la
  comprobación del WebSocket— y rompe el *frontend*.
- La IP de la red local de la máquina cuenta como origen aceptado: una página servida desde esa IP
  por **otro servidor de esta misma máquina** podría abrir el WebSocket.

## La premisa que esto mantiene

`Seguridad/Decisiones/2026-10-03_00-13_s1-bitacora-publica.md` se reabre «si se decide que la app de
la Fase 4 deje de ser local. Hoy corre en `localhost` y eso es parte de la premisa». **Sigue siendo
local.** Servirla a la red, desplegarla en Streamlit Community Cloud o meterla en Docker quedaron
fuera de la Fase 4, y cualquiera de las tres reabriría esa decisión.

## Cómo verificar / revertir

```powershell
.venv\Scripts\python.exe -m melate.app                    # «Solo esta máquina: http://127.0.0.1:8501»
netstat -ano | findstr :8501                              # solo 127.0.0.1:8501
.venv\Scripts\python.exe -m pytest tests\test_lanzador.py tests\test_app.py -q
```

**Revertir** no se recomienda en ninguna de las tres capas: quitar una deja la app a merced del
valor por defecto de Streamlit, que escucha en todas las interfaces. Quitar el lanzador entero está
descrito paso a paso en `Fases/2026-10-04_app-local/Cambios/2026-10-04_16-08_s4-lanzador-propio.md`.

Relacionado: `Seguridad/Modificar/2026-10-04_16-35_s4-un-servidor-local-y-su-superficie.md`,
`Seguridad/Decisiones/2026-10-03_00-13_s1-bitacora-publica.md`,
`Fases/2026-10-04_app-local/Bugs/2026-10-04_10-05_s4-review-base-app-y-red.md`,
`Fases/2026-10-04_app-local/Bugs/2026-10-04_11-39_s4-review-lanzador.md`,
`Interconexion/Añadir/2026-10-04_16-35_s4-las-pantallas-de-la-app.md`.
