# Cómo leer esta bitácora

> Rutas de lectura, no un listado. Se actualiza al cerrar cada fase.
> Si el mapa miente, es peor que si no existe.

Esta bitácora **se publica**, al contrario de lo habitual. El porqué y las reglas que impone están
en `REGLAS-DOCUMENTACION.md` §0 y en `Seguridad/Decisiones/`.

## Si acabas de llegar

1. `README.md` (en la raíz) — qué es el proyecto y qué no. Empieza por "esto no predice números".
2. `Mapa/Añadir/2026-10-03_00-13_s1-mapa-del-sistema.md` — qué módulo responde a qué pregunta, y la
   pieza de la que depende todo: hay dos programas y dan lo mismo.
3. `Mapa/Modificar/2026-10-03_01-30_s2-entra-el-laboratorio.md` — la frontera entre **explorar** y
   **juzgar**. Las cifras del informe no bastan para afirmar nada; solo el laboratorio puede.
4. `Fases/2026-10-04_app-local/99_CIERRE.md` — dónde está el proyecto hoy y qué queda pendiente.
   Si hay una fase abierta, su alcance (`Fases/<fecha>_<nombre>/00_ALCANCE.md`) dice qué está
   cambiando ahora mismo.
5. Y para mirar en vez de leer: `.venv\Scripts\python.exe -m melate.app` abre la app local en
   `http://127.0.0.1:8501`. Enseña lo que ya está en `reportes/` y `prereg/`; no calcula nada.

## Si tienes 15 minutos y quieres entender por qué este proyecto es desconfiado

Lee estos cuatro, en orden. Cuentan la historia completa:

1. `Fases/2026-10-02_arranque/Bugs/2026-10-02_23-29_s1-porton-linea-base.md` — dos de las doce
   cifras del contrato no reproducían. No era el código: era un número mal transcrito en una fuente
   de respaldo, y había inflado el resultado más llamativo del proyecto.
2. `Protocolo_Estadistico/Decisiones/2026-10-03_00-13_s1-familias-benjamini-hochberg.md` — por qué
   un p = 0.017 se convierte en q = 0.35 cuando se cuentan las 36 pruebas, y por qué el número que
   manda se decide **antes** de ver los resultados.
3. `Protocolo_Estadistico/Añadir/2026-10-03_01-30_s2-preregistro-y-las-cinco-condiciones.md` — qué
   hace falta para poder afirmar algo, qué error mata cada una de las cinco condiciones, y cuántos
   años de datos haría falta: unos once.
4. `Fases/2026-10-03_protocolo/Bugs/2026-10-03_01-05_s2-pendientes-heredados.md` — la Fase 1 cerró
   con 52 tests en verde y 17 de ellos fallaban en otro shell. Lo que lo descubrió fue haber dejado
   escrita la lista de pendientes y haberla ejecutado.

## Si vas a tocar código

- **Antes:** las `Decisiones/` de tu área. Están cerradas y tienen su porqué.
- **Antes, si tocas `src/melate/`:** `baseline_auditoria.py` **no se modifica nunca.** Es el oráculo
  y `tests/test_paridad.py` compara contra él con tolerancia cero. Si lo tocas, el proyecto pierde su
  única referencia y no se recupera.
- **Después:** el pipeline del `REGLAS-DOCUMENTACION.md` §1. El `.md` es el último paso, nunca el
  primero.

```powershell
.venv\Scripts\python.exe -m pytest tests -m "not lento and not red" -q   # 213 pruebas, ~13 s
.venv\Scripts\python.exe -m pytest tests -q                              # 242 pruebas, ~150 s
.venv\Scripts\python.exe scripts\mutar.py                                # 46 de 46, ~2-3 min
```

> Estas cifras se vuelven a medir al cerrar cada fase. Ya envejecieron **dos** veces: en la
> Fase 2, dos tests de subproceso sin marcar dejaron el bucle rápido en 30 s mientras este mapa
> decía 5 (`Rendimiento/Arreglos_Bugs/2026-10-03_01-59_la-suite-rapida-no-era-rapida.md`); en la
> Fase 3 un voraz cuadrático lo puso en 26 s, y se arregló el algoritmo en vez de marcar los tests
> como lentos (`Rendimiento/Arreglos_Bugs/2026-10-03_05-15_s3-el-voraz-cuadratico.md`). En la Fase 4
> pasó de ~5 a ~13 s por probar la app, sin marcar nada como lento, y el usuario lo aceptó
> (`Rendimiento/Modificar/2026-10-04_16-35_s4-el-bucle-rapido-con-la-app.md`).
>
> `scripts/mutar.py` rompe una cosa a la vez en una copia del repositorio y exige que algún test se
> entere. Lo nuevo que se proteja con un test entra también en su lista.

**Y si lo que quieres es saber si una estrategia funciona:** no mires el informe. Sella un
preregistro y espera. `Protocolo_Estadistico/Añadir/` explica por qué, y
`python -m melate.lab --prereg prereg/<fichero>.json` es el único camino que puede afirmar algo.

## Si vas a subir algo

**El colador es bloqueante.** Si imprime algo, no se sube.

```powershell
.\scripts\colador.ps1 -Autoprueba
```

## Si buscas algo concreto

| Tu pregunta | Área |
|---|---|
| ¿Cuál es el mapa del sistema? | Mapa |
| ¿Dónde vive este fichero? ¿Por qué `src/`? | Estructura_Carpetas |
| ¿Qué forma tienen los datos y el reporte? | Estructura_Datos |
| ¿Dónde se guardan los datos? ¿Por qué un snapshot? | Almacenamiento |
| ¿De dónde salen los datos? ¿Por qué el espejo no vale para cargar? | Conexiones |
| ¿Quién sale a la red, y cuándo? | Conexiones |
| ¿Cómo se enlazan las pantallas de la app? | Interconexion |
| ¿Qué cambia en la superficie de ataque? ¿Qué se publica? | Seguridad |
| ¿Qué juega la gente? ¿Cuánto paga de verdad un boleto? | Conexiones · Estructura_Datos |
| ¿Por qué una cartera no mejora mis probabilidades? | Mapa · `src/melate/portfolio.py` |
| ¿Qué sirve la app, y a quién? ¿Por qué solo a esta máquina? | Red |
| ¿Qué hay en `melate.duckdb` y por qué no se publica? | Estructura_Datos · Almacenamiento |
| ¿Se puede volver a obtener este número exacto? | Reproducibilidad |
| ¿Me puedo creer este resultado? ¿Qué hace falta para afirmar algo? | Protocolo_Estadistico |
| ¿Qué es un preregistro y por qué no se puede editar? | Protocolo_Estadistico · Almacenamiento |
| ¿Cuánto tarda y dónde se va el tiempo? | Rendimiento |
| ¿Qué se subió al repositorio y cuándo? | Despliegue |
| ¿Por qué se eligió A y no B? | `<Área>/Decisiones` |

## Hoja de ruta — en qué fase estamos y qué falta

**Ninguna fase empieza sin que el usuario la apruebe** (`CLAUDE.md`, Forma de trabajo). Esta tabla se
actualiza al cerrar cada una, y es la referencia: no hay ningún plan fuera del repositorio.

| Fase | Estado | Qué entra |
|---|---|---|
| **1 · Arranque** | ✅ cerrada 2026-10-03 | Bitácora, entorno, snapshot congelado, reproducción de la línea base, paquete `src/melate/` con paridad contra el oráculo, primer push |
| **2 · Protocolo** | ✅ cerrada 2026-10-03 | `prereg/*.json` sellado, `lab.py`, las 5 condiciones de la regla 5, y los pendientes de la Fase 1 ejecutados |
| — *auditoría* | ✅ 2026-10-03 | Revisión retrospectiva de las fases 1 y 2: siete defectos con las 92 pruebas en verde |
| **3 · EV, popularidad y cartera** | ✅ cerrada 2026-10-03 | `popularity.py` con Scrapling sobre las tablas de ganadores y el dictamen escrito **antes** del código; `portfolio.py` con presupuesto fijo; el `menores_brutos` medido entra por clave nueva sin tocar el oráculo |
| **4 · App local** | ✅ cerrada 2026-10-04 | `app/streamlit_app.py` y `melate.duckdb`, los dos en esta máquina: la app escucha solo en `127.0.0.1`, nunca en `0.0.0.0`, y la abre un lanzador propio, `python -m melate.app`. Textos en español, "sin ventaja demostrada" en cada pantalla y el veredicto solo del laboratorio |

Lo que **no** está en ninguna fase y es deliberado: migrar a pandas 3 (rompe `df.attrs`, que el
oráculo usa), optimizar el backtest (es el 85 % del coste y crece de forma cuadrática, pero son 62 s
hoy y ~110 s en cinco años), y añadir estrategias nuevas (agranda la familia de Benjamini-Hochberg:
es una decisión con consecuencias estadísticas y lleva su documento).

## Fases

Un cambio normal va directo a la rejilla. Los bloques grandes viven en `Fases/<fecha>_<nombre>/` y,
al cerrarse, emiten a las áreas base **solo el estado final**. El proceso se queda en el dossier.

- `Fases/2026-10-02_arranque/` — **cerrada el 2026-10-03.** Bitácora, entorno, snapshot congelado,
  reproducción de la línea base, paquete `src/melate/` con paridad y primer push. Empieza
  por su `Fases/2026-10-02_arranque/00_ALCANCE.md`; la historia está en sus dos `Bugs/`.
- `Fases/2026-10-03_protocolo/` — **cerrada el 2026-10-03.** Los pendientes de la Fase 1 ejecutados
  (con un bug de 17 tests encontrado por el camino), `prereg/*.json` sellado, `lab.py` y las 5
  condiciones de la regla 5.
- `Fases/2026-10-03_popularidad/` — **cerrada el 2026-10-03.** La primera fase que toca un sitio de
  terceros, con su dictamen escrito antes del código. `popularity.py`, `portfolio.py`, y el
  hallazgo de que el `menores_brutos` escrito a mano gobernaba el 65 % del EV de Melate.
- `Fases/2026-10-04_app-local/` — **cerrada el 2026-10-04.** La app local, `melate.duckdb` y un
  lanzador que la ata a esta máquina aunque el entorno diga otra cosa. La primera fase con una
  pantalla, hecha para que no pueda presentar una cifra exploratoria como veredicto. Empieza por su
  `Fases/2026-10-04_app-local/99_CIERRE.md`.

## Estado ahora mismo

- **Bugs abiertos:** ninguno.
- **Fases abiertas:** ninguna. La Fase 4 se cerró el 2026-10-04 con la aprobación del usuario, y la
  siguiente no empieza sin ella (`CLAUDE.md`).
- **El veredicto del proyecto, hoy:** `sin ventaja demostrada`, 0 de 5 condiciones, porque el holdout
  del preregistro está vacío. Es la respuesta correcta y seguirá siéndolo durante años. El primer
  sorteo posterior al sello es el 4274: cuando el CSV oficial lo incluya, el laboratorio sin
  `--datos` dará el primer veredicto con holdout, y seguirá sin poder afirmar nada con un sorteo.
- **Pendiente de verificar en vivo** — los siete puntos de
  `Fases/2026-10-04_app-local/99_CIERRE.md`. Dos no son falta de esfuerzo, son el diseño
  funcionando: no habrá una evaluación preregistrada de verdad hasta que pasen sorteos, y la
  condición 5 necesita del orden de once años de datos. La mutación a mano de la auditoría posterior
  es ya `scripts/mutar.py`, y la forma de la tabla de melate-e.com la vigila de verdad su test `red`.
- **Decisiones cerradas que atan el proyecto:**
  - `baseline_auditoria.py` es el oráculo y no se modifica.
  - El espejo es solo validación cruzada, nunca carga.
  - Para declarar ventaja manda `q_BH_global`, la familia de 36 pruebas. **Dentro de esa familia va
    todo lo que hable de la urna; fuera, todo lo que hable de los jugadores** — por eso la
    popularidad no la agranda
    (`Protocolo_Estadistico/Decisiones/2026-10-03_05-10_s3-la-popularidad-no-entra-en-la-familia.md`).
  - Las nueve pruebas de log-loss **no** entran en la familia: no son pruebas sobre la urna, y
    meterlas aflojaría la corrección
    (`Protocolo_Estadistico/Decisiones/2026-10-04_10-45_s4-el-log-loss-no-entra-en-la-familia.md`).
  - Con el sitio de terceros: 1 solicitud/segundo, caché permanente, identificación honesta, y si
    bloquean **se para y se pregunta**
    (`Fases/2026-10-03_popularidad/Decisiones/2026-10-03_02-40_s3-dictamen-terminos-melate-e.md`).
    Una única excepción, decidida por el usuario: la suite completa pide una página real para
    vigilar la forma del sitio
    (`Conexiones/Modificar/2026-10-04_16-35_s4-el-test-del-sitio-pide-la-pagina-de-verdad.md`).
  - Un preregistro no se sobrescribe, no se sella en el pasado, y alterarlo lo invalida.
  - **La app es local:** solo `127.0.0.1`, sin telemetría y sin preguntarle a nadie la IP pública; la
    abre `python -m melate.app` (`Red/Añadir/2026-10-04_16-35_s4-que-sirve-la-app-y-a-quien.md`).
  - **La app enseña y no calcula:** no recalcula, no descarga ni escribe, y su cabecera sale solo de
    un veredicto del laboratorio con un sello que verifica. `melate.duckdb` no se publica
    (`Almacenamiento/Decisiones/2026-10-04_00-40_s4-que-entra-en-melate-duckdb.md`).
  - La bitácora se publica; nada personal sale de la máquina, y las rutas son siempre relativas.
  - `pandas < 3` mientras el oráculo use `df.attrs`.

## Receta de integridad

Antes de dar una fase por cerrada:

```powershell
$b = 'Documentos_Contexto'
$md = Get-ChildItem $b -Recurse -Filter *.md
"documentos: $($md.Count)"

# nombres fuera de patron (los 00_ALCANCE.md y 99_CIERRE.md estan exentos)
$md | Where-Object { $_.Name -notmatch '^([0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{2}-[0-9]{2}_[a-z0-9-]+|_MAPA|00_ALCANCE|99_CIERRE)\.md$' } | ForEach-Object Name

# cabecera y seccion de verificacion
$md | Where-Object { $t = [IO.File]::ReadAllText($_.FullName,[Text.Encoding]::UTF8)
  ($t -notmatch 'Fecha/hora') -or ($t -notmatch 'rea:') } | ForEach-Object Name

# documentos vivos sin cerrar
$md | Where-Object { $_.Directory.Name -eq 'Bugs' -and
  ([IO.File]::ReadAllText($_.FullName,[Text.Encoding]::UTF8) -notmatch 'CERRADO') } | ForEach-Object Name
```

Y los enlaces `Relacionado:` rotos, que es el que más importa: la bitácora es un grafo y un enlace
muerto lo parte. El script está en `scripts/verificar-bitacora.ps1`.

Y los tests, mutados: `scripts/mutar.py` tiene que detectar todas sus mutaciones (46 de 46 al cerrar
la Fase 4). Una mutación que no se detecta es un test que no vigila nada.
