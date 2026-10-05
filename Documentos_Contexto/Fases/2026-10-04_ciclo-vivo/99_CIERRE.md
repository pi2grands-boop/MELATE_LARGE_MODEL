# Cierre de la fase: el ciclo vivo

- **Fecha/hora:** 2026-10-05 10:37
- **Abierta el:** 2026-10-04 a las 18:16 · **Duración:** dos sesiones, con una noche de espera al
  primer sorteo del holdout
- **Cerrada el 2026-10-05 con la aprobación del usuario**, a las 11:56, después de correr él mismo la
  guía de pruebas: *«Ya ejecuté todo, me gusta como se ve. Sube todo y la documentación también»*.

Las fases 1 a 4 trabajaron sobre una foto fija, `data/raw/2026-10-02/`, hasta el sorteo 4272. Esta
hace que el proyecto incorpore los sorteos que van llegando **sin romper la reproducibilidad**: cada
uno entra por una orden, `python -m melate.ciclo`, en un snapshot nuevo, congelado e inmutable,
validado con el oficial y dos testigos antes de usarse; y sobre él se derivan la popularidad, el valor
esperado del sorteo siguiente, el veredicto y la base de la app. El riesgo no era técnico: era que el
primer sorteo del holdout pareciera más de lo que es. **El inventario encontró que era peor**: con el
código de entonces, un solo sorteo podía dar «VENTAJA DEMOSTRADA» de verdad.

## Criterio de terminado

| Criterio del alcance | Evidencia |
|---|---|
| 1 · C1, C2 y C3, contestadas antes del primer veredicto con holdout | ✅ C1 a las 18:58 del 2026-10-04, antes del sorteo de las 22:00; C3 a las 18:59; C2 a las 20:10. En `Decisiones/` de este dossier, y C1 además en `Protocolo_Estadistico/Decisiones/` |
| 2 · La decisión del ciclo, anterior a `src/melate/ciclo.py` por hora y por `git log` | ✅ por hora: la decisión es de las 20:10 y la review del módulo, de las 20:51. Por `git log`: nada se comiteó durante la fase; en la secuencia de commits propuesta, la decisión va en un commit anterior al del código. Git solo puede probar ese orden |
| 3 · Un snapshot real congelado por la orden, byte a byte, y el test de punta a punta con los SHA-256 publicados | ✅ `data/raw/2026-10-02_4273/` y `data/raw/2026-10-04_4274/`; `test_congela_lo_que_sirve_el_oficial_byte_a_byte` reproduce hasta el `SHA256.txt` de la Fase 1 |
| 4 · Cada forma de fallar, con su test y sin nada a medias | ✅ el oficial que falla a mitad (500 y una página con 200), los juegos desalineados, el pasado cambiado, los testigos que discrepan, faltan o bloquean, nada nuevo, la carpeta que ya existe, el renombrado que falla, un CSV ilegible (B12) y una página sin números (B13) |
| 5 · Sobre el snapshot nuevo, la popularidad, el informe, el veredicto y la base; cada cifra con su snapshot | ✅ con el 4274: dos páginas pedidas y contadas, la ventana 4175-4274 sin fallos, el valor esperado del 4275 y el veredicto, todos con `2026-10-04_4274` en el nombre y su hash dentro |
| 6 · Si llega el 4274: el primer veredicto con holdout, *sin ventaja demostrada*, visto en un navegador con clics | ✅ congelado el 2026-10-05 a las 09:22 y visto a las 09:25, con clics de ratón de verdad y sin una conexión del servidor hacia fuera |
| 7 · `pytest tests` en verde con la paridad; el bucle rápido, medido y publicado; las mismas 7 conexiones | ✅ 321 en verde, 234 s, 7 conexiones; el bucle rápido, 287 en 35 s, publicado en el README, en `_MAPA.md` y en `Rendimiento/` |
| 8 · El procedimiento de cierre | ✅ cada número publicado, vuelto a medir: **uno estaba mal** (B14) y se corrigió con su marca; cada parámetro que gobierna algo, con dos valores: **cuatro no los tenían** (B8-B11); los tests, mutados: **97 de 97**, y trece de ellas no las detectaba ningún test antes del cierre; la pregunta del índice permanente, abajo |
| 9 · Bitácora íntegra, colador limpio, hoja de ruta al día; el cierre lo aprueba el usuario | ✅ abajo. **El usuario aprobó el cierre y la subida**, tras correr la guía de pruebas y recorrer la app |

## El veredicto, y lo que dice

El 4274, primer sorteo posterior al sello, juzgado sobre su snapshot: **sin ventaja demostrada, 2 de 5
condiciones**. La logística acertó 1 de 6 en Revancha y 0 en Melate y Revanchita; con un sorteo, el
mínimo detectable es de 2,02 aciertos por boleto, y la condición 5 dice *«hacen falta 1778 sorteos
(faltan 1777)»*. Lo que significa —nada, y es lo correcto— está en
`Protocolo_Estadistico/Añadir/2026-10-05_10-26_s5-el-primer-veredicto-con-holdout.md`.

## Lo que no estaba previsto

1. **El laboratorio podía declarar ventaja con un sorteo**: una vez de cada 303 bajo el azar, y en
   cuatro sorteos históricos con los datos reales. Se cerró antes de que se sorteara el 4274 (C1).
2. **Los testigos nunca han cazado un error del oficial**: todos los errores que se le conocen los
   cazan comprobaciones que no dependen de nadie. «Tres fuentes o nada» habría dejado el ciclo en
   manos del testigo más débil durante once años (C2).
3. **Los tests suponían que `reportes/` no crece**, y el ciclo existe para hacerlo crecer (B4).
4. **`st.table` pasa sus celdas por Markdown.** Lo vio una captura, no un test (B8 de C3).
5. **La herramienta de edición escribió un carácter invisible** en el código; lo destapó una mutación.
6. **El procedimiento de cierre, adelantado mientras se esperaba al 4274, encontró trece mutaciones
   que ningún test detectaba** y dos fallos de verdad que el 4274 podía pisar: un CSV ilegible tumbaba
   el ciclo sin dejar evidencia (B12), y una página sin números lo habría dejado parado en cada
   corrida (B13). Se arreglaron antes de congelarlo.
7. **Una cifra publicada estaba mal medida**: el repositorio no crecerá 760 MB en el holdout, sino
   ~1,02 GB, porque la medida solo contaba los CSV y suponía snapshots iguales (B14).
8. **La máquina varía mucho**: el mismo informe, con el mismo código, tarda hoy 29-31 s y en la Fase 1
   72,6 s; el bucle rápido tardaba la noche antes un 20 % menos que esta mañana.
9. **La espera no se pudo automatizar del todo**: la máquina se suspendió por la noche y el vigilante
   de la sesión no llegó a pedir nada. Se miró a mano a las 09:21: el oficial se regenera a las 12:00
   UTC, como se suponía.
10. **Quedaba un «1 sorteos» en la terminal del laboratorio** (B15). Lo encontró reproducir el
    veredicto a mano para escribir la guía con la que el usuario prueba la fase. Se le consultó y se
    arregló, con su test y su mutación, antes de que lo probara.

## Lo que decidió el usuario

| | Asunto | Decisión |
|---|---|---|
| C1 | Con un sorteo de holdout se podía declarar ventaja | Opción A: la condición 5 exige un holdout capaz |
| C2 | La tercera fuente de Revanchita, y si «tres o nada» es viable | Pidió la explicación a fondo; después, «C 2.2»: un desacuerdo para, una ausencia espera, y seguir sin un testigo es explícito. C2.1, como la opción a: Revanchita con dos fuentes |
| C3 | Tocar la app y el almacén de la Fase 4 | «Ok», y «dale con C3» |
| C4 | El bucle rápido, de 13,8 a 25 s | «Si, mientras más mejor» |
| — | Esperar al 4274 antes de cerrar | «Si, esperemos al 4274» |

Cada una, con su porqué:
`Fases/2026-10-04_ciclo-vivo/Decisiones/2026-10-04_18-59_s5-lo-que-decidio-el-usuario.md`.

## Qué quedó fuera, y por qué

| Fuera | Por qué |
|---|---|
| Programar el ciclo | Pediría páginas a un tercero sin nadie delante; si bloquea, se para y se pregunta |
| Volver a pedir una página que llegó incompleta | Una excepción al dictamen que no se ha decidido. No ha pasado: la del 4274 llegó entera once horas después del sorteo |
| Guardar solo las filas nuevas de cada snapshot | Hoy no compensa; la decisión se reabre a los 100 MB, a los 216 snapshots |
| Una página de Revanchita por sorteo | El usuario la descartó (C2) |
| Estrategias o pruebas nuevas | La familia sigue en 36 |
| Un tope de tamaño a la descarga del oficial | Como en la Fase 1: es la fuente de carga |
| Probar fuera de Windows | No se puede en esta máquina |

## Documentos emitidos a las áreas base

| Documento | Qué dice |
|---|---|
| `Almacenamiento/Decisiones/2026-10-04_20-10_s5-el-ciclo-vivo.md` | El ciclo, **escrito antes del código**; con la corrección de B14, marcada y con hora |
| `Protocolo_Estadistico/Decisiones/2026-10-04_18-58_s5-la-condicion-5-exige-un-holdout-capaz.md` | C1, **escrita antes del sorteo del 4274** |
| `Mapa/Modificar/2026-10-05_10-04_s5-entra-el-ciclo-vivo.md` | El quinto modo: incorporar sorteos |
| `Almacenamiento/Modificar/2026-10-05_10-05_s5-los-snapshots-los-congela-el-ciclo.md` | Dónde persiste cada cosa, cuánto crece, y la base que sabe qué está congelado |
| `Conexiones/Modificar/2026-10-05_10-06_s5-el-ciclo-sale-a-tres-sitios.md` | Quién sale de la máquina y cuándo; la regla de los testigos |
| `Seguridad/Modificar/2026-10-05_10-07_s5-lo-que-entra-de-fuera-con-el-ciclo.md` | Lo que el ciclo abre, y cómo se cierra |
| `Reproducibilidad/Modificar/2026-10-05_10-09_s5-cada-cifra-dice-de-que-snapshot-sale.md` | Cada cifra con su snapshot, y cómo reproducir lo del ciclo: comprobado a mano |
| `Protocolo_Estadistico/Modificar/2026-10-05_10-15_s5-la-condicion-5-en-el-codigo.md` | La condición 5, en el código |
| `Protocolo_Estadistico/Añadir/2026-10-05_10-26_s5-el-primer-veredicto-con-holdout.md` | El primer veredicto con holdout, y lo que significa |
| `Interconexion/Modificar/2026-10-05_10-27_s5-la-app-ensena-el-holdout-y-su-snapshot.md` | Lo que dicen las pantallas |
| `Estructura_Carpetas/Modificar/2026-10-05_10-29_s5-arbol-tras-el-ciclo.md` | El árbol, y los nombres que son contrato |
| `Estructura_Datos/Modificar/2026-10-05_10-31_s5-snapshot-veredicto-y-base.md` | La forma de un snapshot, del veredicto y de la base, versión 2 |
| `Rendimiento/Modificar/2026-10-05_10-32_s5-el-bucle-y-lo-que-cuesta-un-ciclo.md` | El bucle, el ciclo, y una máquina que varía |

El de `Despliegue/` se escribe después de la subida, con su SHA.

## La pregunta del cierre: qué documento del índice permanente quedó desactualizado

| Documento | Qué había dejado de ser verdad | Qué se hizo |
|---|---|---|
| `Almacenamiento/Añadir/2026-10-03_00-13_s1-snapshots-congelados.md` | Que un snapshot se hace a mano y se nombra con la fecha de la descarga | `Almacenamiento/Modificar/` |
| `Almacenamiento/Añadir/2026-10-03_05-15_s3-cache-de-paginas.md` | Que hay una sola caché de páginas | Ídem |
| `Almacenamiento/Decisiones/2026-10-04_00-40_s4-que-entra-en-melate-duckdb.md` | Que la base es un índice de `reportes/` y `prereg/` | Ídem |
| `Almacenamiento/Decisiones/2026-10-04_20-10_s5-el-ciclo-vivo.md` | Su medida del crecimiento | Corrección visible, con su hora (B14) |
| `Conexiones/Modificar/2026-10-04_16-35_s4-el-test-del-sitio-pide-la-pagina-de-verdad.md` | Su tabla de quién sale a la red | `Conexiones/Modificar/` |
| `Seguridad/Modificar/2026-10-04_16-35_s4-un-servidor-local-y-su-superficie.md` | Nada falso; no conoce el ciclo | `Seguridad/Modificar/` |
| `Reproducibilidad/Arreglos_Bugs/2026-10-04_16-35_s4-el-veredicto-registra-sus-datos.md` | Que basta con registrar los datos: no se comprobaba que estuvieran guardados | `Reproducibilidad/Modificar/` |
| `Protocolo_Estadistico/Añadir/2026-10-03_01-30_s2-preregistro-y-las-cinco-condiciones.md` | «La condición 5 necesita ~1 800 sorteos»: el código no lo exigía | `Protocolo_Estadistico/Modificar/` |
| `Interconexion/Añadir/2026-10-04_16-35_s4-las-pantallas-de-la-app.md` | Lo que dicen la cabecera, el veredicto y la procedencia | `Interconexion/Modificar/` |
| `Estructura_Carpetas/Modificar/2026-10-04_16-35_s4-arbol-tras-la-app.md` | El árbol | `Estructura_Carpetas/Modificar/` |
| `Estructura_Datos/Añadir/2026-10-04_16-35_s4-esquema-de-melate-duckdb.md` | 16 tablas y el esquema 1 | `Estructura_Datos/Modificar/` |
| `Estructura_Datos/Modificar/2026-10-04_16-35_s4-veredicto-popularidad-y-cartera.md` | La forma del veredicto y de la popularidad | Ídem |
| `Mapa/Modificar/2026-10-04_16-35_s4-entra-la-app-local.md` | Cuatro modos de uso, y «0 de 5» | `Mapa/Modificar/` |
| `Rendimiento/Modificar/2026-10-04_16-35_s4-el-bucle-rapido-con-la-app.md` | El bucle rápido | `Rendimiento/Modificar/` |
| `Rendimiento/Añadir/2026-10-03_00-13_s1-coste-del-informe.md` | Sus 72,6 s: hoy, 29-31 s con el mismo código | `Rendimiento/Modificar/` lo mide y lo dice; la medida de entonces queda como fue |
| `_MAPA.md` | La hoja de ruta, las cifras, el veredicto, las decisiones que atan y los pendientes | Actualizado en este cierre |

**Siguen siendo verdad**, buscando en ellos lo que esta fase cambió: los de `Red/` (la app no cambió
de red), las fuentes de `Conexiones/Añadir/`, la decisión de la bitácora pública y la del log-loss,
que cita su informe con su snapshot. La decisión de la popularidad de la Fase 3 dice que el veredicto
es «0 de 5, por holdout vacío»: era verdad en su fecha, una decisión cerrada no se edita, y el
veredicto de hoy lo dice `_MAPA.md`. Fuera de la bitácora, el README está al día. **El `CLAUDE.md`
no se ha tocado**: la propuesta, abajo, espera al usuario.

## Bugs abiertos que se heredan

**Ninguno.** Las tres reviews de la fase están cerradas: C1 (B1-B4) en
`Fases/2026-10-04_ciclo-vivo/Bugs/2026-10-04_19-16_s5-review-c1-condicion-5.md`, C3 (B1-B9) en
`Fases/2026-10-04_ciclo-vivo/Bugs/2026-10-04_20-37_s5-review-c3-app-y-almacen.md` y el ciclo (B1-B14)
en `Fases/2026-10-04_ciclo-vivo/Bugs/2026-10-04_20-51_s5-review-ciclo.md`. Y B15, encontrado después,
también, en `Fases/2026-10-04_ciclo-vivo/Bugs/2026-10-05_10-52_s5-b15-un-sorteo-tambien-en-la-terminal.md`.

## Pendiente de verificar en vivo

1. **Fuera de Windows.** *(heredado)*
2. **La descripción del repositorio y el correo privado en GitHub**: son de la cuenta del usuario.
   *(heredado)*
3. **Un bloqueo real de melate-e.com.** No ha ocurrido; el ciclo para con el código 4 y se pregunta.
   *(heredado)*
4. **Un testigo que discrepe de verdad, o una página que llegue incompleta.** No han pasado. El ciclo
   para o espera, y lo dice; qué hacer lo decide el usuario. *(nuevo)*
5. **La condición 5 no se alcanza antes del sorteo 1 778 del holdout**, unos once años. *(heredado,
   y ahora exacto)*

**Resueltos de la lista heredada:**

- **El primer veredicto con holdout**, congelado, juzgado y visto en un navegador.
- **El `SystemExit` de `ingest._leer_bytes`**, que el ciclo no usa: un oficial que falla a mitad se
  probó con un servidor que falla de verdad, y no queda nada escrito.
- **Que una persona mire la app.** El usuario corrió la guía de pruebas y recorrió las cinco pantallas
  con el veredicto del 4274, y mandó las capturas: la cabecera, «1 sorteo de los 1 778», los cinco
  motivos enteros, el valor esperado del 4275 y los tres snapshots. **En su navegador la barra lateral
  sale entera**: el corte de las capturas automáticas era de la captura, como se sospechaba desde la
  Fase 4.

## Propuesta para el `CLAUDE.md`, sin aplicar

Como en la Fase 4, el texto lo decide el usuario. Lo que tendría que decir:

1. En **Protocolo de evaluación**, regla 5, tras «efecto >= mínimo detectable (0.048 aciertos con
   1,784 sorteos de prueba)»: *«, medido en un holdout capaz de detectarlo: con el 0.048 declarado,
   1 778 sorteos de holdout (la condición 5 no se cumple antes, sea cual sea el delta)»*.
2. Una sección nueva, **El ciclo vivo (Fase 5)**, como la de la app: `python -m melate.ciclo` es la
   única orden que incorpora sorteos, y `--comprobar` valida sin escribir; los snapshots nuevos son
   `data/raw/<fecha>_<sorteo>/` y nunca se escriben encima; un testigo que discrepa para el ciclo, uno
   que falta hace esperar, y seguir sin él es `--sin-testigo`, que queda escrito; un veredicto sobre
   datos no congelados no cuenta; el ciclo no se programa; y sus códigos de salida, 0 a 4.
3. En **Línea base verificada**, una línea: las cifras nuevas viven en los reportes del ciclo, con su
   snapshot en el nombre, y las de esta sección no cambian.

## Lo que tiene que hacer el usuario

1. ~~Aprobar, o no, el cierre de la fase.~~ **Aprobado el 2026-10-05 a las 11:56.**
2. ~~Decidir los commits y la subida.~~ **Autorizada** con el cierre. Para que `git log` pruebe que las
   decisiones van antes que su código: primero el inventario, el alcance y las decisiones; después el
   código con sus tests; después los datos y reportes que produjo el ciclo; y al final la bitácora. Y
   antes de subir, `scripts/colador.ps1 -Autoprueba`. El SHA, en `Despliegue/`.
3. **Decidir el texto del `CLAUDE.md`.** Sigue pendiente: la propuesta no se ha aplicado, así que no se
   sube.
4. **Correr el ciclo cuando quiera incorporar sorteos.** La cadencia es suya. Si para, dice por qué y
   con qué código; un hallazgo deja la descarga en `data/cuarentena/` y se investiga antes de elegir
   nada.

## Integridad, comprobada

- `scripts/verificar-bitacora.ps1` — **0 hallazgos** en las 5 comprobaciones, 96 documentos. La
  primera pasada dio 5: un «PROCEDENCIA.md» a secas, que no resuelve a ningún fichero; se escribió con
  su carpeta.
- `scripts/colador.ps1 -Autoprueba` — **0 coincidencias sobre 173 ficheros**, autoprueba 4/4.
- `pytest tests` — **321 en verde**, 234 s, con `test_paridad.py` intacto; por el proxy, 7 conexiones.
  Antes de B15, 320 en 188 s.
- `pytest -m "not lento and not red"` — **287 en verde**, 35 s.
- `scripts/mutar.py` — **97 de 97**, 450 s con el portátil a batería; antes de B15, 96 de 96 en 312 s.
- `baseline_auditoria.py`, `tests/test_paridad.py`, `src/melate/ev.py`, el preregistro y
  `data/raw/2026-10-02/`: **sin tocar** (`git status`).
- El veredicto: **sin ventaja demostrada**, 2 de 5, con un holdout de 1 sorteo de los 1 778.

## Una nota sobre lo que esta fase significa

El proyecto ya no es una foto: es un registro que crece, sorteo a sorteo, sin que ninguna cifra
publicada pierda los bytes de los que salió. Y el primer veredicto con holdout dice lo único que puede
decir un sorteo: nada.

Lo más importante de esta fase no fue el ciclo, sino lo que se encontró antes de poder usarlo. **El
proyecto llevaba cuatro fases afirmando que hacían falta unos 1 800 sorteos para poder afirmar algo, y
el código no lo exigía.** Se encontró leyendo el código antes de escribir el primero que lo iba a
usar, y se cerró antes de que existiera el dato que podía haberlo aprovechado. Es la misma lección de
siempre con otra cara: lo que un documento afirma y lo que un programa hace son dos cosas, y la
distancia entre ellas solo se ve si alguien la mide.

Relacionado: `Fases/2026-10-04_ciclo-vivo/00_ALCANCE.md`,
`Fases/2026-10-04_ciclo-vivo/Inventario/2026-10-04_18-16_s0-estado-de-partida.md`,
`Fases/2026-10-04_ciclo-vivo/Decisiones/2026-10-04_18-59_s5-lo-que-decidio-el-usuario.md`,
`Fases/2026-10-04_ciclo-vivo/Bugs/2026-10-04_19-16_s5-review-c1-condicion-5.md`,
`Fases/2026-10-04_ciclo-vivo/Bugs/2026-10-04_20-37_s5-review-c3-app-y-almacen.md`,
`Fases/2026-10-04_ciclo-vivo/Bugs/2026-10-04_20-51_s5-review-ciclo.md`,
`Fases/2026-10-04_ciclo-vivo/Bugs/2026-10-05_10-52_s5-b15-un-sorteo-tambien-en-la-terminal.md`,
`Fases/2026-10-04_app-local/99_CIERRE.md`.
