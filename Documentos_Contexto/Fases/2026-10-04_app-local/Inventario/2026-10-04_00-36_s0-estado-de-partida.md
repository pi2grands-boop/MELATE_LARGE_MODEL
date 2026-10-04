# Estado de partida de la Fase 4: lo que la app va a tener que enseñar

- **Fecha/hora:** 2026-10-04 00:36
- **Área:** Fases/2026-10-04_app-local · **Acción:** Inventario
- **Chat / página:** sesión de la Fase 4 · todo el proyecto
- **Archivos afectados:** ninguno se modifica en este documento

Este documento se escribe **antes** de instalar nada, de crear `app/` o de escribir una línea de
`melate.duckdb`. Es la excepción del pipeline (`REGLAS-DOCUMENTACION.md` §1): el estado de partida,
después, ya no se puede reconstruir.

## Qué se hizo

Leer y medir. Nada más.

### El repositorio

- **Commit de partida:** `c5eb42f` (*fix: seis defectos encontrados auditando la Fase 3 ya
  cerrada*), árbol de trabajo limpio, `main` al día con `origin/main`.
- **Ni `app/`, ni `.streamlit/`, ni `melate.duckdb` existen.** `Red/` e `Interconexion/` están
  vacías en la bitácora: esta fase escribe su primer documento en las dos.

### Las cuatro cifras de control, medidas ahora

| Qué | Resultado |
|---|---|
| `pytest tests -m "not lento and not red"` | **135 en verde, 5,34 s** (6,4 s de reloj) |
| `pytest tests` | **164 en verde, 135,23 s** |
| `scripts/colador.ps1 -Autoprueba` | **0 coincidencias sobre 98 ficheros**, autoprueba 3/3 |
| `scripts/verificar-bitacora.ps1` | **0 hallazgos**, 50 documentos |

### El entorno

Python 3.13.9 y lo que fija `entorno/pip-freeze-2026-10-03.txt`: 43 paquetes más la instalación
editable del propio proyecto (45 líneas con la cabecera, que es como la Fase 3 los contó). **Ni
`streamlit` ni `duckdb` están instalados.**

Lo que traerían, comprobado con `pip install --dry-run --only-binary :all:` usando el *freeze*
actual como restricción:

```
streamlit 1.65.0 · duckdb 1.5.6
+ 21 dependencias: altair, attrs, h11, httptools, itsdangerous, Jinja2, jsonschema,
  jsonschema-specifications, MarkupSafe, pillow, protobuf, pyarrow, pydeck, python-multipart,
  referencing, rpds-py, starlette, toml, uvicorn, watchdog, websockets
```

**23 paquetes nuevos, todos con *wheel***, y ninguno de los que ya estaban cambia de versión.

Dos cosas que importan para lo que viene:

1. **Streamlit 1.65 admite `pandas<4`.** Con las restricciones, pandas se queda en 2.3.3; sin
   ellas, un `pip install --upgrade streamlit` podría subirlo a la 3, que rompe el `df.attrs` del
   oráculo. Por eso se instala con restricciones y se fija exacto.
2. **Streamlit 1.65 ya no sirve con Tornado sino con Starlette y uvicorn.** Lo que la
   documentación antigua diga sobre su dirección de escucha no se da por bueno: se comprueba en
   vivo.

### Lo que la app va a tener que enseñar

Lo que hay en `reportes/` y `prereg/`, que es todo lo que la app puede consumir:

| Fichero | Qué es | Corrida (UTC) | Datos | SHA-256 |
|---|---|---|---|---|
| `reportes/2026-10-02_oraculo.json` | informe del oráculo | — *(no tiene bloque de reproducibilidad)* | snapshot 4272 | `2bf8966c7037…` |
| `reportes/2026-10-02_paquete.json` | informe | 2026-10-03 05:11 | snapshot, 2 000 sims | `7843edf8954c…` |
| `reportes/2026-10-03_vivo.json` | informe | 2026-10-03 05:37 | descarga en vivo, **200 sims** | `8fcc37892631…` |
| `reportes/2026-10-03_informe-con-popularidad.json` | informe + EV medido | 2026-10-04 03:58 | snapshot, 2 000 sims | `d8f832f71cd8…` |
| `reportes/2026-10-03_popularidad.json` | popularidad | 2026-10-04 03:43 | ventana 4173-4272, Melate y Revancha | `e4de460e8cc6…` |
| `reportes/2026-10-04_popularidad-melate-300-sorteos.json` | popularidad | 2026-10-04 05:03 | ventana 3973-4272, Melate | `831e203d1259…` |
| `reportes/2026-10-03_cartera.json` | cartera | — | Melate, 300 $ | `7f628ef03d49…` |
| `reportes/2026-10-03_veredicto.json` | **veredicto** | 2026-10-03 07:06 | **no lo dice** | `8806be0905c9…` |
| `prereg/2026-10-03_logistica-revancha.json` | preregistro | sello 2026-10-03 06:45 | snapshot 4272 al sellar | `4858a015995f…` |

**El informe "vivo" tiene los mismos bytes de entrada que el snapshot** —los tres SHA-256
coinciden: el oficial aún no había publicado el 4273— pero da **q mínima 0,594** en vez de
**0,306**. No es un error: se corrió con 200 simulaciones en vez de 2 000, y eso mueve las `p` de la
auditoría y con ellas toda la familia global. Consecuencia para la app: **una pantalla que enseñe
"el último informe" sin decir con cuántas simulaciones se hizo enseñaría dos q mínimas distintas
para los mismos datos, sin explicación.**

## Hallazgos de la lectura, antes de escribir código

### H1 · El veredicto no registra los datos sobre los que juzgó — se arregla en esta fase

`reportes/2026-10-03_veredicto.json` trae `preregistro`, `holdout`, `resultados`, `por_juego`,
`veredicto`, `corrida_utc` y `versiones`. **No trae el hash de los datos**, ni su origen, ni el
último concurso que había. `melate.lab.evaluar` no lo escribe (`src/melate/lab.py:286-296`).

La regla 6 del protocolo es *"guardar el hash del dataset y la semilla en cada corrida"*. El
informe lo cumple (`reproducibilidad.datos`); el laboratorio, que es la pieza que **juzga**, no. Con
el holdout vacío no se nota, porque cualquier dato da 0 sorteos posteriores al sello; deja de ser
inocuo en cuanto el holdout tenga un sorteo, y eso es inminente (H4).

Para la app es bloqueante: el veredicto es lo único que puede afirmar algo, y una pantalla que lo
enseñe sin poder decir **sobre qué datos** se emitió es justo la cifra sin procedencia que el
proyecto rechaza. Entra en el alcance (punto 6).

### H2 · Tres tablas de ganadores sin premios entraron como buenas — NO se toca, se consulta

En la ventana 3973-4272, las páginas de los sorteos **4107, 4111 y 4119** traen el número de
ganadores de cada categoría pero **todos los premios a `$0.00`**. `popularity.parsear` las acepta y
esos tres sorteos entran con `menores_por_bolsa = 0`:

| `menores_brutos_por_bolsa`, Melate, ventana de 300 | Con los tres ceros | Sin ellos |
|---|---|---|
| n | 300 | 297 |
| media | **4,6035** | 4,6500 |
| mediana | **4,6422** | 4,6465 |

**Ninguna cifra del `CLAUDE.md` cambia**: las ventas y el efecto calendario salen de los ganadores,
no de los premios, y el EV medido sale de la ventana de 100 (4173-4272), que no contiene esos
sorteos. Pero `tests/test_cartera.py:187` y `:201` usan **4,6035** como "menores medidos", que es
la media contaminada, y la review de la Fase 3 publica 4,6422.

Es un fallo de la Fase 3 de la clase que el proyecto persigue —una tabla incompleta que entra en
silencio—, en un módulo que esta fase no toca. **La decisión es del usuario**
(`CLAUDE.md`: *"un bug no se deja sin preguntar"*). Se le presenta con su evidencia y no se aplica
nada antes de su respuesta.

### H3 · El `_MAPA.md` apuntaba al cierre de la Fase 2 como "dónde está el proyecto hoy"

"Si acabas de llegar", punto 4, y "Pendiente de verificar en vivo" remitían a
`Fases/2026-10-03_protocolo/99_CIERRE.md` y a sus **cinco** pendientes. La Fase 3 cerró después
con **siete**, y la auditoría posterior añadió un octavo (la mutación manual). Es exactamente la
pregunta del cierre que el usuario pide hacerse: *qué documento del índice permanente quedó
desactualizado*. Se corrige al anotar en el mapa que la Fase 4 está abierta, que es cuando hay que
tocarlo de todos modos.

### H4 · El primer sorteo del holdout se celebra hoy

El sello es `2026-10-03T06:45:00Z` y la frontera excluye el día del sello (`lab.holdout`). Con el
calendario de miércoles, viernes y domingo —comprobado en la auditoría de las fases 1 y 2: 100 de
cada uno en los últimos 300—, el **4273** fue el viernes 2026-10-02 y queda fuera, y el **4274** es
el **domingo 2026-10-04, hoy**, y queda dentro.

No es un fallo; es una fecha, y cambia la naturaleza del pendiente heredado nº 1: el holdout **no
está a años de distancia, empieza hoy**. Lo que está a años es la condición 5. Para la app significa
que el veredicto que enseñe va a quedar viejo en cuanto se publique el 4274, y que tiene que decir
siempre de qué corrida es.

### H5 · Los nombres de los documentos de la Fase 3 no siguen la hora local de sus commits

`Despliegue/Añadir/2026-10-03_05-50_s3-push-de-la-popularidad.md` documenta el commit `e7d8c50`,
hecho el 2026-10-03 a las 23:31 (UTC-5). `Protocolo_Estadistico/Arreglos_Bugs/2026-10-04_01-20_s3-auditoria-posterior-al-cierre.md`
documenta `c5eb42f`, hecho el 2026-10-04 a las 00:09: el nombre del documento es 70 minutos
**posterior** al commit que lo contiene. Las fases 1 y 2 sí usan la hora local.

No se renombra nada —los documentos finales no se editan y un renombrado rompe enlaces—, pero se
deja escrito por una consecuencia práctica: **esta fase nombra con la hora local real (UTC-5)**,
como las fases 1 y 2, así que sus documentos ordenan **antes** que el de la auditoría posterior
aunque se escribieron después. Quien reconstruya el orden, que use `git log`.

## Documentos del índice permanente que esta fase va a dejar desactualizados si no se tocan

La pregunta del cierre, preparada desde el principio:

| Documento | Qué afirma hoy que dejará de ser cierto |
|---|---|
| `_MAPA.md` | `Interconexion` *"vacía: la app es de la Fase 4"*, `Red` *"vacía: todo es local"*, la hoja de ruta |
| `README.md` | "Cómo correrlo" y "Estructura" no conocen la app ni la base |
| `Mapa/Modificar/2026-10-03_05-15_s3-entran-popularidad-y-cartera.md` | "El camino de usuario completo, hoy" tiene cuatro pasos |
| `Estructura_Carpetas/Modificar/2026-10-03_05-15_s3-arbol-tras-la-popularidad.md` | Que `app/` y `melate.duckdb` "son de la Fase 4" |
| `Estructura_Datos/Añadir/2026-10-03_01-30_s2-formato-del-preregistro.md` | La forma del veredicto, que gana los datos (H1) |
| `Fases/2026-10-03_popularidad/Decisiones/2026-10-03_02-40_s3-dictamen-terminos-melate-e.md` | *"Este proyecto no sirve nada por red (`Red/` está vacía por eso)"* |
| `requirements.txt` | Su cabecera dice "dependencias de la Fase 1" desde la Fase 3 |

Los documentos finales no se editan: lo que cambie se escribe en un `Modificar/` nuevo que lo
diga.

## Por qué

Una app que enseña cifras es la pieza del proyecto con más capacidad de engañar sin que ningún test
de los existentes lo note: las cifras pueden ser todas correctas y la pantalla, falsa. Saber
exactamente qué hay que enseñar, de dónde sale y qué le falta —H1 sobre todo— es la condición para
diseñarla bien.

## Impacto en seguridad / conexiones / datos

Ninguno: este documento no cambia nada. La única orden con red fue el `--dry-run` de `pip`, que
consulta el índice de paquetes y no instala.

## Cómo verificar

```powershell
git rev-parse --short HEAD                                              # c5eb42f
.venv\Scripts\python.exe -m pytest tests -m "not lento and not red" -q  # 135
Get-FileHash reportes\*.json, prereg\*.json -Algorithm SHA256
```

H2, con el reporte comiteado:

```powershell
.venv\Scripts\python.exe -c "import json; m=json.load(open('reportes/2026-10-04_popularidad-melate-300-sorteos.json',encoding='utf-8'))['juegos']['Melate']['muestras']; print([x['sorteo'] for x in m if x['bolsa_repartida']==0])"
```

Tiene que imprimir `[4107, 4111, 4119]`.

Relacionado: `Fases/2026-10-04_app-local/00_ALCANCE.md`,
`Fases/2026-10-03_popularidad/99_CIERRE.md`,
`Protocolo_Estadistico/Arreglos_Bugs/2026-10-04_01-20_s3-auditoria-posterior-al-cierre.md`.
