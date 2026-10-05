# Estado de partida de la Fase 5: lo que el ciclo encuentra antes de existir

- **Fecha/hora:** 2026-10-04 18:16
- **Área:** Fases/2026-10-04_ciclo-vivo · **Acción:** Inventario
- **Chat / página:** sesión de la Fase 5 · todo el proyecto, y las tres fuentes en vivo
- **Archivos afectados:** ninguno se modifica en este documento

Este documento se escribe **antes** de crear el módulo del ciclo, de congelar ningún snapshot o de
tocar una línea de código. Es la excepción del pipeline (`REGLAS-DOCUMENTACION.md` §1): el estado de
partida, después, ya no se puede reconstruir. Aquí menos que nunca, porque las fuentes cambian solas:
el oficial publicará el 4274 en unas horas.

## Qué se hizo

Leer, medir y preguntar a las fuentes. Ninguna orden escribió en el repositorio: las descargas fueron
a una carpeta temporal fuera de él, y `git status` sale vacío al terminar.

### El repositorio

- **Commit de partida:** `c9b5a47` (*docs: registra la subida de la fase de la app local*), árbol de
  trabajo limpio, `main` igual a `origin/main` (0 y 0). 23 commits.
- **Un solo snapshot:** `data/raw/2026-10-02/`, hasta el sorteo 4272. **Ninguna orden del repositorio
  crea snapshots:** aquel se congeló a mano, y `data/raw/2026-10-02/PROCEDENCIA.md` describe el
  procedimiento manual en «Cómo volver a crearlo».
- **La caché de melate-e.com:** 300 páginas de Melate (3973-4272) y 100 de Revancha (4173-4272).
  Ninguna de Revanchita, por el dictamen.

### Las cifras de control, medidas ahora

| Qué | Resultado |
|---|---|
| `pytest tests -m "not lento and not red"` | **213 en verde, 13,76 s** (14,9 s de reloj) |
| `pytest tests` | **242 en verde, 137,24 s** |
| Lo que la suite completa saca de la máquina, por un proxy que solo apunta lo que le llega | **7 conexiones**: 6 a `raw.githubusercontent.com` (el espejo: tres juegos en dos tests), **1 a `resultados.melate-e.com`** (el test `red` de la C8 de la Fase 4) y **0 a `loterianacional.gob.mx`** |
| `scripts/mutar.py` | **46 de 46**, 168 s |
| `scripts/colador.ps1 -Autoprueba` | **0 coincidencias sobre 131 ficheros**, autoprueba 4/4 |
| `scripts/verificar-bitacora.ps1` | **0 hallazgos**, 72 documentos |

El proxy ve los túneles `CONNECT`, no las rutas: cuenta conexiones, no peticiones. Que la de
melate-e.com sea una sola página lo comprueba el propio test (`d.peticiones == 1`).

### El entorno

Python 3.13.9 y **los mismos 66 paquetes** que fija `entorno/pip-freeze-2026-10-04.txt`, versión por
versión (comparado sin la línea de la instalación editable, que lleva el commit). A priori el ciclo no
necesita ninguna dependencia nueva: `requests` ya descarga el oficial y el espejo, y Scrapling,
melate-e.com.

### Lo publicado

| Fichero | Qué es | Corrida (UTC) | Datos | SHA-256 |
|---|---|---|---|---|
| `reportes/2026-10-02_oraculo.json` | informe del oráculo | — | snapshot 4272 | `2bf8966c7037…` |
| `reportes/2026-10-02_paquete.json` | informe | 2026-10-03 05:11 | snapshot, 2 000 sims | `7843edf8954c…` |
| `reportes/2026-10-03_vivo.json` | informe | 2026-10-03 05:37 | **descarga en vivo**, 200 sims | `8fcc37892631…` |
| `reportes/2026-10-03_informe-con-popularidad.json` | informe + EV medido | 2026-10-04 03:58 | snapshot, 2 000 sims | `d8f832f71cd8…` |
| `reportes/2026-10-03_popularidad.json` | popularidad | 2026-10-04 15:44 | ventana 4173-4272 | `0a67c622e299…` |
| `reportes/2026-10-04_popularidad-melate-300-sorteos.json` | popularidad | 2026-10-04 15:31 | ventana 3973-4272 | `169e1f2e1d38…` |
| `reportes/2026-10-03_cartera.json` | cartera | — | Melate, 300 $ | `37ad777af30d…` |
| `reportes/2026-10-03_veredicto.json` | veredicto | 2026-10-03 07:06 | **no lo registra** | `8806be0905c9…` |
| `reportes/2026-10-04_veredicto.json` | **el veredicto vigente** | 2026-10-04 05:56 | snapshot 4272 | `d68f6b55dc9a…` |
| `prereg/2026-10-03_logistica-revancha.json` | preregistro | sello 2026-10-03 06:45 | snapshot 4272 al sellar | `4858a015995f…` |

**De qué datos sale cada reporte lo dice el SHA-256, no la ruta.** La clave `origen` guarda lo que se
tecleó en `--datos`, y en lo publicado hay tres formas de escribir la misma carpeta
(`.\data\raw\2026-10-02\…`, `data/raw/2026-10-02\…`, `data\raw\2026-10-02\…`) y una URL. El hash es
el mismo en los cuatro, también en el informe en vivo, porque el oficial aún no había publicado el
4273. Para enlazar un reporte con su snapshot, el hash vale y la ruta no.

### Las fuentes, ahora mismo

Descargadas el 2026-10-04 a las 22:28 UTC (17:28 hora local) con el mismo `User-Agent` que
`src/melate/ingest.py`, a una carpeta fuera del repositorio:

| Fuente | Juego | HTTP | Bytes | SHA-256 | Último sorteo |
|---|---|---|---|---|---|
| oficial | Melate | 200 | 206 724 | `5dbb2ab8838f…` | **4273** (02/10/2026) |
| oficial | Revancha | 200 | 150 330 | `7f34ff933252…` | **4273** |
| oficial | Revanchita | 200 | 88 283 | `fba4afe5f233…` | **4273** |
| espejo | los tres | 200 | — | — | 4273, con los mismos números que el oficial |

**El 4274 no está en el oficial.** Se sortea hoy, domingo 2026-10-04, a las 21:00 de la Ciudad de
México: las 22:00 de esta máquina (UTC−5), las 03:00 UTC del lunes. El oficial sirve
`Last-Modified: Sun, 04 Oct 2026 12:00:04 GMT` en los tres ficheros, lo que sugiere que los regenera
una vez al día a las 12:00 UTC; si es así, el 4274 aparecerá hacia las 07:00 locales del lunes
2026-10-05. **Es una sola observación** y hay que comprobarla.

**El 4273 no abre el holdout.** Es del viernes 2026-10-02, anterior al sello (`2026-10-03T06:45Z`):
cualquier snapshot que llegue hasta el 4273 da un holdout vacío.

**El fichero oficial solo crece, y eso se puede comprobar byte a byte.** En los tres juegos la
cabecera es idéntica a la del snapshot y **el cuerpo entero del snapshot es un sufijo exacto del
fichero de hoy**. Lo nuevo es una sola línea, insertada justo después de la cabecera porque el oficial
va en orden descendente:

```
Melate      +49 bytes   40,4273,6,18,24,44,50,55,39,80000000,02/10/2026
Revancha    +46 bytes   41,4273,8,9,32,37,51,55,115000000,02/10/2026
Revanchita  +48 bytes   34,4273,16,29,31,42,48,56,158000000,02/10/2026
```

Comparadas fila a fila tras el parseo: 4 272, 3 264 y 1 902 filas comunes, **0 distintas**. Y
`validar_era` sobre el fichero de hoy da 0 concursos faltantes, 0 duplicados, 0 fuera de rango, 0
filas desordenadas, el adicional nunca entre los naturales, y la BOLSA inválida solo en los tres
concursos conocidos (2120, 2142 y 2234) de Melate y Revancha.

Esto le da al ciclo una comprobación que ninguna validación de una sola descarga tiene: **que el
pasado no cambió.** Si el oficial corrigiera una fila vieja, el sufijo dejaría de cuadrar.

## Hallazgos de la lectura, antes de escribir código

### H1 · Con un solo sorteo de holdout, el laboratorio puede declarar «VENTAJA DEMOSTRADA» — NO se toca: se consulta

Esta fase da por hecho, y el proyecto lo afirma en nueve sitios, que con un holdout pequeño el
veredicto solo puede ser *sin ventaja demostrada*: *«la condición 5 necesita del orden de 1 800
sorteos de holdout»*. **El código no lo garantiza**, y lo demuestra el laboratorio real.

**La demostración.** Se buscaron sorteos históricos en los que la regresión logística del
preregistro, entrenada *walk-forward*, acertó 3 o más números en Revancha y al menos 1 en Melate y en
Revanchita. Para cada uno se selló a mano —en memoria, como hacen los tests— una copia del
preregistro real con el sello el día anterior, y se corrió `lab.evaluar` sobre los datos recortados
hasta ese sorteo: **un holdout de exactamente un sorteo por juego.**

| Sorteo | Fecha | Aciertos Melate / Revancha / Revanchita | Veredicto de `lab.evaluar` |
|---|---|---|---|
| 2928 | 2015-12-27 | 1 / 3 / 1 | **VENTAJA DEMOSTRADA, 5 de 5** |
| 3419 | 2020-12-30 | 1 / 3 / 1 | **VENTAJA DEMOSTRADA, 5 de 5** |
| 3953 | 2024-09-15 | 2 / 3 / 1 | **VENTAJA DEMOSTRADA, 5 de 5** |
| 4205 | 2026-04-26 | 1 / 3 / 1 | **VENTAJA DEMOSTRADA, 5 de 5** |

Otros dos candidatos (2937 y 3796) no lo dieron: entrenada en el propio sorteo, como hace el
laboratorio, la logística acertó 2 en Revancha y no 3. Las cinco condiciones del más reciente, tal
como las escribe el laboratorio:

```
== sorteo 4205 (2026-04-26), holdout {'Melate': 1, 'Revancha': 1, 'Revanchita': 1}
   veredicto: VENTAJA DEMOSTRADA  (5 de 5)
   [si] holdout futuro positivo            delta +2.3571 aciertos sobre el azar en 1 sorteos de holdout
   [si] q <= 0.05                          q_BH_global = 0.0397 contra el umbral 0.05
   [si] estable al mover hiperparámetros   4 variantes; mismo signo: True; desvío máximo 0% del efecto base
   [si] mismo signo en los tres juegos     Melate +0.3571, Revancha +2.3571, Revanchita +0.3571
   [si] efecto >= mínimo detectable        delta +2.3571 contra 2.0237 (detectable; detectable 2.0237, declarado 0.0480)
```

**La probabilidad, bajo el azar.** Exacta para n = 1 a 6, enumerando todas las combinaciones de
aciertos de los tres juegos y llamando a `protocolo.declara_ventaja` con los mismos redondeos que
`lab._evaluar_una`. Se supone, como cota superior, que las variantes de hiperparámetros dan el mismo
delta que la base, que es lo que hizo la logística en los cuatro casos de arriba (desvío 0 %):

| Sorteos de holdout | P(VENTAJA DEMOSTRADA \| azar) |
|---|---|
| 1 | **0,003297: 1 de cada 303** |
| 2 | 0,000471 |
| 3 | 0,002071 |
| 4 | 0,000375 |
| 5 | 0,000301 |
| 6 | 0,000661 |

La de n = 1 tiene forma cerrada y se comprueba a mano: P(≥ 3 aciertos en Revancha) × P(≥ 1 en
Melate) × P(≥ 1 en Revanchita) = 0,012648 × 0,510580² = **0,003297**.

Y lo que importa para esta fase, **porque un ciclo evalúa con cada sorteo nuevo**: la probabilidad de
que *alguna* de las evaluaciones declare ventaja bajo el azar. Monte Carlo con el mismo supuesto, y
con las reglas vectorizadas y validadas contra el exacto de n = 1 (0,00324 contra 0,00330); el error
de muestreo es de unos ±0,05 puntos porcentuales:

| Evaluaciones, una por sorteo | Alguna declara VENTAJA DEMOSTRADA |
|---|---|
| 1 | 0,32 % |
| 10 | 0,65 % |
| 100 | **1,0 %** |
| 300 | 1,1-1,2 % |
| 1 777 | 1,40 % |

**Por qué pasa**, en tres piezas que solo se juntan con muestras pequeñas:

1. **La condición 5 compara el delta con el mínimo detectable del propio holdout**,
   `max(detectable(n), declarado)`. Con n = 1 el detectable es 2,0237 aciertos: enorme, pero un sorteo
   con 3 aciertos da un delta de 2,3571 y lo supera. La auditoría de las fases 1 y 2 cerró el agujero
   de los holdouts grandes —su defecto A: con n enorme el detectable baja y pasaba un efecto menor que
   el declarado— y no miró el de los pequeños.
2. **La prueba es una z con aproximación normal**, y así la declara el sello (clave `prueba`). Con un
   sorteo, 3 aciertos dan p = 0,0011 de dos colas; la probabilidad exacta de acertar 3 o más es
   0,0126, once veces mayor. La q global sale 0,0397; con la cola exacta no bajaría de 0,45.
3. **Las otras dos condiciones apenas filtran con n pequeño.** La estabilidad no distingue la suerte
   de la señal: en los cuatro casos de arriba las cuatro variantes eligieron los mismos seis números,
   porque una logística sobre más de 100 000 filas apenas se mueve con el hiperparámetro (en los dos
   candidatos descartados, una variante sí se desvió, un 74 %). Y el mismo signo en los tres juegos
   solo pide un acierto en Melate y otro en Revanchita, que pasa la mitad de las veces en cada uno.

**Por qué no se vio.** Los tests del camino con holdout usan sellos de enero o febrero de 2026, con
decenas de sorteos, o resultados sintéticos con n de 100 a 20 000. El comentario de
`test_evaluar_con_holdout_de_verdad_mide_algo` lo dice tal cual —*«la condicion 5 no puede pasar»*—,
y con decenas de sorteos y deltas realistas es verdad. La auditoría de las fases 1 y 2 verificó los
«once años» desde el calendario (1 778 sorteos a 156 por año), no desde las condiciones. Ningún test
preguntó qué pasa con **un** sorteo, que es exactamente el caso que esta fase va a vivir mañana.

**Dónde se afirma lo contrario**, y seguirá siendo falso si no se arregla: `README.md` (*«Es imposible
declarar una ventaja hoy… harían falta del orden de 1 800 sorteos de holdout»*),
`Documentos_Contexto/_MAPA.md` (*«y seguirá sin poder afirmar nada con un sorteo»*),
`Protocolo_Estadistico/Añadir/2026-10-03_01-30_s2-preregistro-y-las-cinco-condiciones.md`, los
cierres de las fases 2, 3 y 4, y las notas del preregistro sellado, que no se pueden tocar.

**La decisión es del usuario**: es el protocolo. Se le presenta con esta evidencia como C1 del alcance
y no se aplica nada antes de su respuesta. **Y tiene fecha.** Lo que la logística elegirá para el 4274
ya está determinado por los datos hasta el 4273, que el oficial ya publica; decidir la
regla antes de conocer el resultado del 4274, o al menos sin mirarlo, es lo que la mantiene a ciegas.
Por eso este inventario **no ha calculado** qué números elegiría la logística para ese sorteo.

### H2 · Revanchita no se puede validar contra melate-e.com sin cambiar el dictamen — se consulta

La fase pide validar cada sorteo nuevo con las tres fuentes. Para Melate y Revancha sale gratis: la
página que se pide por la tabla de ganadores trae también los números, y `popularity.discrepancias`
los compara (0 discrepancias en 200 sorteos, Fase 3). Para Revanchita, **el dictamen prohíbe pedir la
página** (`SIN_TABLA`, `src/melate/popularity.py:58`): no tiene tabla de ganadores, y pedirla era
*«gastar peticiones ajenas para no obtener nada»*. Para validar números sí obtendría algo, pero ni
siquiera se sabe si esa página trae los números con la misma forma (`span.numnatural`), porque nunca
se pidió con ese fin. Con el dictamen de hoy, Revanchita tiene dos fuentes. Va al alcance como C2.

### H3 · La app, el mapa y el cierre de la Fase 4 mandan juzgar sobre una descarga que no se guarda

La pantalla del veredicto termina con *«Sin `--datos`, el laboratorio descarga los CSV del oficial: es
la única forma de que entren sorteos posteriores al sello»* (`app/streamlit_app.py:254-255`). El
`_MAPA.md` dice que *«el laboratorio sin `--datos` dará el primer veredicto con holdout»*; el
pendiente 1 de `Fases/2026-10-04_app-local/99_CIERRE.md`, *«`melate.lab` sin `--datos`»*; y la tabla
de quién sale de la máquina en
`Conexiones/Modificar/2026-10-04_16-35_s4-el-test-del-sitio-pide-la-pagina-de-verdad.md`, que el
oficial se pide *«solo sin `--datos`: el laboratorio o el informe con datos de hoy»*.

Es justo lo que esta fase prohíbe: el veredicto registraría el hash de unos bytes que no quedan en
ninguna parte. No es un fallo de la Fase 4 —cuando se escribió no había otra forma—, pero entra en el
alcance: el ciclo es la otra forma, y esos textos tienen que decirlo.

### H4 · La app presentaría un holdout de un sorteo con la misma cara que uno de mil

La cabecera escribe *«holdout de {n} sorteos»* (`app/streamlit_app.py:170-172`) y la pantalla del
veredicto, un `st.metric` con *«{n} sorteos»* (`:222`): con el 4274 dirán «holdout de 1 sorteos». La
tabla de deltas enseña el delta en bruto, y con un sorteo dos aciertos son **+1,3571**, veintiocho
veces el efecto mínimo declarado (0,048), sin nada al lado que diga que con un sorteo cualquier valor
entre −0,64 y +5,36 es compatible con el azar. Ningún número es falso; la pantalla, sí. Entra en el
alcance: es lo que pide el usuario.

### H5 · La caché permanente puede congelar una página de melate-e.com pedida demasiado pronto

`Descargador.html` escribe en la caché cualquier respuesta 200 que traiga `<table>`
(`src/melate/popularity.py:285-296`), y lo que está en la caché no se vuelve a pedir nunca. Para los
400 sorteos de la Fase 3 no importaba: se pidieron con meses de retraso. Un ciclo pide sorteos de
ayer, y **no se sabe** qué sirve el sitio entre el sorteo y la publicación de los premios. Si sirve la
tabla a medias, quedaría congelada para siempre. `premios_publicados` caza los premios a `$0.00`, no
unos ganadores incompletos. Es una restricción del diseño del ciclo, no un fallo de la Fase 3.

### H6 · `melate.lab --salida` y `melate.informe --salida` escriben encima sin avisar

`open(salida, "w")` en `src/melate/lab.py:371` y `src/melate/informe.py:224`. A mano no importaba;
un ciclo que nombre sus reportes por fecha y se corra dos veces el mismo día reescribiría un
veredicto publicado. Restricción del diseño: el ciclo nunca escribe sobre un fichero que existe, como
`lab.sellar` con los preregistros.

### H7 · El pendiente heredado nº 3 pasa a tener que contestarse

`ingest._leer_bytes` sale con `SystemExit` si el oficial falla (`src/melate/ingest.py:50-60`), y nunca
se ha ejercitado contra el oficial porque el oficial no ha fallado. Un `SystemExit` a mitad de tres
descargas deja abierta la pregunta de qué se queda en disco. La decisión del ciclo tiene que
contestarla, y un test, ejercitarla con un servidor que falle a propósito.

### Observación aceptada: las ventas que supone el valor esperado

`ev.valor_esperado` supone 1,2 millones de combinaciones vendidas (λ = 0,037), y la mediana medida es
de 0,98 millones. Lo anotó la Fase 3 (su C2) y el efecto es pequeño. El ciclo publicará el EV con ese
supuesto, como el oráculo, y no se toca.

## Documentos del índice permanente que esta fase va a dejar desactualizados si no se tocan

La pregunta del cierre, preparada desde el principio:

| Documento | Qué afirma hoy que dejará de ser cierto |
|---|---|
| `Documentos_Contexto/_MAPA.md` | La hoja de ruta sin la Fase 5; «el laboratorio sin `--datos` dará el primer veredicto»; «Fases abiertas: ninguna»; los pendientes; y la condición 5 a «once años» si C1 no se arregla |
| `README.md` | «Lo que mide, con datos al sorteo 4272»; la tabla del EV del 4273; «Es imposible declarar una ventaja hoy» (H1); «Cómo correrlo» sin el ciclo, y con un informe «contra los datos de hoy, descargando del oficial» |
| `Almacenamiento/Añadir/2026-10-03_00-13_s1-snapshots-congelados.md` | Que un snapshot nuevo se hace a mano |
| `Conexiones/Modificar/2026-10-04_16-35_s4-el-test-del-sitio-pide-la-pagina-de-verdad.md` | Quién sale de la máquina y cuándo (H3) |
| `Protocolo_Estadistico/Añadir/2026-10-03_01-30_s2-preregistro-y-las-cinco-condiciones.md` | «La condición 5 necesita del orden de 1 800 sorteos», según decida el usuario (H1) |
| `Interconexion/Añadir/2026-10-04_16-35_s4-las-pantallas-de-la-app.md` | Lo que enseña la pantalla del veredicto, incluida «la orden para un veredicto nuevo» |
| `Mapa/Modificar/2026-10-04_16-35_s4-entra-la-app-local.md` | Los modos de usar el proyecto: falta el que incorpora sorteos |
| `Estructura_Carpetas/Modificar/2026-10-04_16-35_s4-arbol-tras-la-app.md` | El árbol |
| `CLAUDE.md` | No conoce el ciclo. Sus cifras de la línea base **no cambian**, por instrucción del usuario |

Y lo que se queda como está, a propósito: `data/raw/2026-10-02/PROCEDENCIA.md` describe el congelado a
mano, pero es parte de un snapshot y los snapshots no se tocan; el procedimiento nuevo se documentará
en otro sitio. Las notas del preregistro sellado tampoco se tocan. Y los dossiers cerrados cuentan lo
que era cierto cuando se escribieron.

## Por qué

Hasta hoy el proyecto trabajaba sobre una foto fija, y una foto fija no puede equivocarse con los
datos nuevos porque no los tiene. Un ciclo vivo sí: puede congelar media descarga, mezclar un oficial
a medio actualizar con un espejo atrasado, guardar una página antes de tiempo o publicar un veredicto
sobre bytes que nadie guardó. Y puede, sobre todo, enseñar el primer sorteo del holdout como si
significara algo. H1 dice que hoy el código no solo podría enseñarlo así: podría *afirmarlo*. Saberlo
antes del primer veredicto con holdout es la diferencia entre decidirlo a ciegas y decidirlo después
de ver el resultado.

## Impacto en seguridad / conexiones / datos

Ninguno sobre el repositorio. Salieron de la máquina: 3 peticiones al oficial y 3 al espejo, para
saber dónde están las fuentes, y las 7 conexiones de la suite completa, entre ellas la de melate-e.com
que decidió el usuario. **Ninguna petición más a melate-e.com.**

## Cómo verificar

```powershell
git rev-parse --short HEAD                                              # c9b5a47
.venv\Scripts\python.exe -m pytest tests -m "not lento and not red" -q  # 213
Get-FileHash reportes\*.json, prereg\*.json -Algorithm SHA256
```

H1, con el código real y desde la raíz del repositorio. No escribe nada: el preregistro de la
demostración vive en memoria.

```powershell
@'
from melate import lab
from melate.constantes import JUEGOS
from melate.ingest import cargar
from melate.validate import era_56
era = {j: era_56(j, cargar(j, "data/raw/2026-10-02")) for j in JUEGOS}
real = lab.cargar_preregistro("prereg/2026-10-03_logistica-revancha.json")
spec = {k: v for k, v in real.items() if k != lab.CLAVE_HASH}
spec.update(id="demostracion-4205", sello_utc="2026-04-25T12:00:00+00:00")
spec[lab.CLAVE_HASH] = lab.hash_preregistro(spec)   # sellado a mano y en memoria, como los tests
recortado = {j: d[d.CONCURSO <= 4205].reset_index(drop=True) for j, d in era.items()}
r = lab.evaluar(spec, recortado)
print({j: h["sorteos"] for j, h in r["holdout"].items()}, r["veredicto"]["veredicto"], r["veredicto"]["cumplidas"])
'@ | .venv\Scripts\python.exe -
```

Tiene que imprimir `{'Melate': 1, 'Revancha': 1, 'Revanchita': 1} VENTAJA DEMOSTRADA 5`.

La probabilidad de n = 1, sin el laboratorio:

```powershell
.venv\Scripts\python.exe -c "from math import comb; p=[comb(6,k)*comb(50,6-k)/comb(56,6) for k in range(7)]; print(round(sum(p[3:])*(1-p[0])**2, 6))"
```

Tiene que imprimir `0.003297`.

Que el oficial solo crece no se puede volver a comprobar contra la descarga de hoy, que no se guardó
a propósito. Se comprobará contra el primer snapshot que congele el ciclo: el cuerpo de
`data/raw/2026-10-02/Melate.csv`, sin su cabecera, tiene que ser un sufijo exacto del suyo.

Relacionado: `Fases/2026-10-04_ciclo-vivo/00_ALCANCE.md`,
`Fases/2026-10-04_app-local/99_CIERRE.md`,
`Almacenamiento/Añadir/2026-10-03_00-13_s1-snapshots-congelados.md`,
`Protocolo_Estadistico/Añadir/2026-10-03_01-30_s2-preregistro-y-las-cinco-condiciones.md`,
`Protocolo_Estadistico/Bugs/2026-10-03_01-59_auditoria-retrospectiva-fases-1-y-2.md`.
