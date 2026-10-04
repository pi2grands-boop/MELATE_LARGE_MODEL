# Cierre de la fase: la app local

- **Fecha/hora:** 2026-10-04 16:45
- **Abierta el:** 2026-10-04 a las 00:36 · **Duración:** una sesión larga, el mismo día, con pausas
- **Cerrada con la aprobación del usuario.**

Las fases 1 a 3 dejaron el proyecto capaz de medir la urna, de juzgar una hipótesis preregistrada y de
medir a los jugadores, todo desde la línea de órdenes. Esta le pone una pantalla encima. Su riesgo no
era técnico: era que la pantalla **borrara la frontera** entre explorar y juzgar, que en la línea de
órdenes separan dos programas distintos. Está hecha para que no pueda, y cada forma en que podría
hacerlo tiene su test.

## Criterio de terminado — cumplido

| Criterio del alcance | Evidencia |
|---|---|
| 1 · La decisión de `Almacenamiento/` antes que el código | ✅ `Almacenamiento/Decisiones/2026-10-04_00-40_s4-que-entra-en-melate-duckdb.md`, a las 00:40, tras el inventario de las 00:36; `almacen.py` después |
| 2 · `melate.almacen` construye, verifica los sellos y enlaza cada veredicto; dos construcciones dan lo mismo | ✅ `test_dos_construcciones_dan_lo_mismo_y_ninguna_deja_la_base_abierta`, `test_un_preregistro_alterado_invalida_sus_veredictos` y 29 más |
| 3 · La app en solo lectura, sin recalcular ni salir a la red | ✅ un espía sobre `duckdb.connect`, y un recorrido con el cómputo y los sockets fuera de esta máquina convertidos en excepciones |
| 4 · «sin ventaja demostrada» en cada pantalla | ✅ el recorrido lo exige pantalla a pantalla; en vivo, con clics, en las cinco |
| 5 · La frontera, con test | ✅ ninguna cifra exploratoria en la pantalla del veredicto; una q = 0.01 forjada sale como candidata a preregistrar; un sello roto no llega a la cabecera |
| 6 · Solo `127.0.0.1`, comprobado en vivo con la tabla de conexiones y la IP de la red local | ✅ dos veces: con `streamlit run`, y con el lanzador en un entorno hostil. Solo `127.0.0.1:8501`; por la IP de la red y por `[::1]`, no es posible conectar |
| 7 · `pytest tests` en verde con la paridad; el bucle rápido, medido y publicado | ✅ 242 en verde; 213 en el bucle rápido, 12,6-12,7 s, publicado en el README y en `_MAPA.md` |
| 8 · El procedimiento de cierre | ✅ cada número, vuelto a medir; cada parámetro que gobierna algo, con dos valores (en las dos reviews); los tests propios, mutados: **46 de 46**; y la pregunta del índice permanente, contestada documento a documento (abajo) |
| 9 · Bitácora íntegra, colador limpio, hoja de ruta al día; el cierre lo aprueba el usuario | ✅ (abajo). El usuario aprobó el cierre y la subida |

## Lo que no estaba previsto

1. **Streamlit 1.65, sin configurar, escucha en todas las interfaces —IPv4 e IPv6— y envía
   telemetría.** Se leyó en su código antes de escribir la configuración.
2. **Ante una conexión de otro origen, le pregunta a Amazon la IP pública de la máquina,** y no es
   configurable. Lo atrapó un proxy chivato. Lo cerró un lanzador propio, que el usuario aprobó (C3).
3. **Cinco fallos los encontró mirar la app, no los tests**: la URL que se descartaba en silencio, el
   veredicto truncado, barras de escape visibles, y tablas que cortaban justo la cifra importante
   —el efecto calendario—. Los tests ven el árbol de elementos, y el árbol era correcto.
4. **El veredicto no registraba sobre qué datos juzgó** (H1). Se vio leyendo el código antes de
   escribirlo, y se arregló aquí.
5. **Meter el log-loss en la familia habría sido menos prudente, no más.** Con una urna limpia, todo
   modelo que no reparta por igual pierde en log-loss; añadir esas nueve p casi nulas habría bajado
   la q de la regresión logística en Revancha de 0,306 a 0,096 (C2).
6. **La herramienta de mutación fallaba en silencio** en los ficheros con CRLF, y lo destapó ella
   misma, con una mutación «no detectada» que no había mutado nada.
7. **El test que vigila melate-e.com leía la copia guardada desde la Fase 3** (C8). Un pendiente que
   el proyecto creía vigilado no lo vigilaba nada.

## Lo que decidió el usuario

| | Asunto | Decisión |
|---|---|---|
| C1 | Tres tablas de ganadores con todos los premios a $0.00 | Sorteos sin premios publicados |
| C2 | Nueve pruebas de log-loss sin documento | Documentarlas y analizar si hacen falta: hacen falta, y fuera de la familia |
| C3 | La búsqueda de la IP pública | El lanzador propio, aprobado |
| C4 | La cartera no guardaba con qué se valoró | Reparar |
| C5 | `melate.duckdb` no se publica | Mantener, y blindarlo |
| C6 | El `CLAUDE.md` | Actualizarlo |
| C7 | El bucle rápido, de ~5 a ~13 s | Aceptado |
| C8 | El test del sitio leía la caché | Que pida la página de verdad |

Cada una, con su porqué y lo que se hizo:
`Fases/2026-10-04_app-local/Decisiones/2026-10-04_11-00_s4-lo-que-decidio-el-usuario.md`,
`Fases/2026-10-04_app-local/Cambios/2026-10-04_16-08_s4-lanzador-propio.md` y
`Fases/2026-10-04_app-local/Cambios/2026-10-04_16-35_s4-el-test-del-sitio-pide-la-pagina-de-verdad.md`.

## Qué quedó fuera, y por qué

| Fuera | Por qué |
|---|---|
| Servir la app a la red, Streamlit Community Cloud, Docker | La app es local, y es premisa de `Seguridad/Decisiones/2026-10-03_00-13_s1-bitacora-publica.md` |
| Que la app recalcule o descargue | Si tarda dos minutos en un backend, no va en una pantalla: la app enseña la orden |
| Los sorteos crudos en la base | Ninguna pantalla los necesita |
| Estrategias o pruebas nuevas | La familia sigue en 36 |
| Mover `.streamlit/config.toml` a `app/.streamlit/` | El lanzador ya fuerza las opciones, y moverla cambiaría una ruta citada en muchos sitios |
| pandas 3 y optimizar el backtest | Fuera de toda fase, como antes |

## Documentos emitidos a las áreas base

| Documento | Qué dice |
|---|---|
| `Mapa/Modificar/2026-10-04_16-35_s4-entra-la-app-local.md` | El cuarto modo, mirar, y la frontera que la app no puede borrar |
| `Estructura_Carpetas/Modificar/2026-10-04_16-35_s4-arbol-tras-la-app.md` | El árbol, y lo que no se publica |
| `Estructura_Datos/Añadir/2026-10-04_16-35_s4-esquema-de-melate-duckdb.md` | Las 16 tablas, con su naturaleza |
| `Estructura_Datos/Modificar/2026-10-04_16-35_s4-veredicto-popularidad-y-cartera.md` | Tres reportes con claves nuevas |
| `Almacenamiento/Decisiones/2026-10-04_00-40_s4-que-entra-en-melate-duckdb.md` | Escrita antes del código, por instrucción del usuario |
| `Almacenamiento/Modificar/2026-10-04_16-35_s4-la-base-la-pone-al-dia-el-lanzador.md` | Cuándo se construye la base |
| `Conexiones/Modificar/2026-10-04_16-35_s4-el-test-del-sitio-pide-la-pagina-de-verdad.md` | Quién sale de la máquina hoy |
| `Interconexion/Añadir/2026-10-04_16-35_s4-las-pantallas-de-la-app.md` | Las pantallas. El primer documento del área |
| `Red/Añadir/2026-10-04_16-35_s4-que-sirve-la-app-y-a-quien.md` | Solo a esta máquina. El primer documento del área |
| `Seguridad/Modificar/2026-10-04_16-35_s4-un-servidor-local-y-su-superficie.md` | Lo que cambia en la superficie |
| `Reproducibilidad/Arreglos_Bugs/2026-10-04_16-35_s4-el-veredicto-registra-sus-datos.md` | H1, y el entorno congelado otra vez |
| `Rendimiento/Modificar/2026-10-04_16-35_s4-el-bucle-rapido-con-la-app.md` | El bucle rápido, medido y aceptado |
| `Protocolo_Estadistico/Decisiones/2026-10-04_10-45_s4-el-log-loss-no-entra-en-la-familia.md` | Escrita durante la fase: precisa una frontera del protocolo |

El de `Despliegue/` se escribe después de la subida, con su SHA.

## La pregunta del cierre: qué documento del índice permanente quedó desactualizado

| Documento | Qué había dejado de ser verdad | Qué se hizo |
|---|---|---|
| `Conexiones/Añadir/2026-10-03_05-15_s3-tablas-de-ganadores-melate-e.md` | Que su test `red` iba «contra el sitio real» —no iba— y sus «36 pruebas», que son 37 | Nota visible y fechada; `Conexiones/Modificar/` |
| `Seguridad/Añadir/2026-10-03_05-15_s3-trafico-saliente-a-un-tercero.md` | «Seguimos sin servir nada» | `Seguridad/Modificar/` lo cita y dice qué cambió |
| `Estructura_Datos/Añadir/2026-10-03_05-15_s3-tabla-de-ganadores-y-cartera.md` | La forma de la popularidad y de la valoración | `Estructura_Datos/Modificar/` |
| `Estructura_Carpetas/Modificar/2026-10-03_05-15_s3-arbol-tras-la-popularidad.md` | El árbol | Un `Estructura_Carpetas/Modificar/` nuevo |
| `Mapa/Modificar/2026-10-03_05-15_s3-entran-popularidad-y-cartera.md` | Las cifras de su «Cómo verificar» | Nota visible; un `Mapa/Modificar/` nuevo |
| `Protocolo_Estadistico/Arreglos_Bugs/2026-10-04_01-20_s3-auditoria-posterior-al-cierre.md` | «La mutación no está automatizada», y sus cifras de verificación | Nota visible: resuelto con `scripts/mutar.py` |
| `Reproducibilidad/Añadir/2026-10-03_00-13_s1-linea-base-reproducida.md` | «Qué registra ahora cada corrida»: el informe sí; el veredicto, que llegó en la Fase 2, no | `Reproducibilidad/Arreglos_Bugs/` |
| `Almacenamiento/Decisiones/2026-10-04_00-40_s4-que-entra-en-melate-duckdb.md` | Nada falso, pero no dice que la base la construye ahora el lanzador | `Almacenamiento/Modificar/` |
| `Rendimiento/Arreglos_Bugs/2026-10-03_05-15_s3-el-voraz-cuadratico.md` | Su «después» era el estado vigente del bucle rápido | `Rendimiento/Modificar/` |
| `Documentos_Contexto/_MAPA.md` | Las cifras de los tests, la hoja de ruta, `Red/` e `Interconexion/` «vacías», los pendientes | Actualizado en este cierre |

Fuera de la bitácora, el README y el `CLAUDE.md` decían cómo arrancar la app y cuántas pruebas hay:
actualizados durante la fase.

## Bugs abiertos que se heredan

**Ninguno.** Las dos reviews de la fase están cerradas: B1-B16 y H1 en
`Fases/2026-10-04_app-local/Bugs/2026-10-04_10-05_s4-review-base-app-y-red.md`, y L1-L3 en
`Fases/2026-10-04_app-local/Bugs/2026-10-04_11-39_s4-review-lanzador.md`. C8 se decidió y se hizo.

## Pendiente de verificar en vivo

1. **El primer veredicto con holdout.** El sorteo 4274 es el primero posterior al sello. Cuando el CSV
   oficial lo incluya: `melate.lab` sin `--datos`, y abrir la app. La cabecera tiene que decir
   «holdout de 1 sorteo» y seguir en *sin ventaja demostrada*. *(heredado, y ya con fecha)*
2. **La condición 5 no se alcanza en años**: ~1 800 sorteos de holdout, unos once años. *(heredado)*
3. **El `SystemExit` de `ingest._leer_bytes`**, sin ejercitar contra el oficial, que no ha fallado.
   *(heredado)*
4. **Fuera de Windows.** *(heredado)*
5. **La descripción del repositorio y el correo privado en GitHub**: son de la cuenta del usuario.
   *(heredado)*
6. **Un bloqueo real de melate-e.com.** No ha ocurrido. Desde C8, la suite completa le hace una
   petición en cada pasada, así que es ahí donde se vería primero; la instrucción no cambia: parar y
   preguntar. *(heredado)*
7. **Que una persona mire la app.** El recorrido se hizo con clics de ratón reales en un navegador
   real, 17 de 17; falta el ojo humano, y confirmar que la barra lateral cortada de las capturas es
   cosa de la captura. *(nuevo)*

**Resueltos de la lista heredada:** el 7 de la Fase 3, que el sitio conserve la forma de su tabla,
lo vigila ahora de verdad el test `red` (C8); y el de la auditoría posterior, la mutación a mano, es
`scripts/mutar.py`.

## Integridad, comprobada

- `scripts/verificar-bitacora.ps1` — **0 hallazgos** en las 5 comprobaciones, 71 documentos.
- `scripts/colador.ps1 -Autoprueba` — **0 coincidencias sobre 130 ficheros**, autoprueba 4/4.
- `pytest tests` — **242 en verde**, 136,3 y 164,2 s en dos pasadas, con `test_paridad.py` intacto.
- `pytest -m "not lento and not red"` — **213 en verde**, 12,6-12,7 s.
- `scripts/mutar.py` — **46 de 46**, 2 min 9 s y 2 min 41 s en dos pasadas.
- El veredicto: **sin ventaja demostrada**, 0 de 5 condiciones.

## Una nota sobre lo que esta fase significa

El proyecto tiene por fin una pantalla, y la pantalla es la parte más fácil de usar mal: una cifra
bien puesta convence más que cien líneas de terminal. Por eso cada pantalla dice arriba lo único que
el proyecto puede afirmar hoy —*sin ventaja demostrada*— y solo el laboratorio puede cambiarlo.

Lo más importante que encontró esta fase no lo veía ningún test: un servidor que por defecto escucha
en todas las interfaces, una petición a Amazon que nadie había pedido, cinco fallos que solo se veían
en el navegador, y un test que decía ir contra el sitio y leía una copia. Es la misma lección de las
fases anteriores, con otra cara: **un test en verde dice lo que comprueba, no lo que uno cree que
comprueba.** Lo que la cerró fue mirar, en vivo y con un proxy, lo que de verdad pasaba.

Relacionado: `Fases/2026-10-04_app-local/00_ALCANCE.md`,
`Fases/2026-10-04_app-local/Inventario/2026-10-04_00-36_s0-estado-de-partida.md`,
`Fases/2026-10-04_app-local/Decisiones/2026-10-04_11-00_s4-lo-que-decidio-el-usuario.md`,
`Fases/2026-10-04_app-local/Bugs/2026-10-04_10-05_s4-review-base-app-y-red.md`,
`Fases/2026-10-04_app-local/Bugs/2026-10-04_11-39_s4-review-lanzador.md`,
`Fases/2026-10-03_popularidad/99_CIERRE.md`.
