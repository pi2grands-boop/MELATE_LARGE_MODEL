# Auditoría retrospectiva de las fases 1 y 2

- **Fecha/hora:** 2026-10-03 01:59
- **Área:** Protocolo_Estadistico · **Acción:** Bugs
- **Chat / página:** sesión de arranque · revisión posterior, a petición del usuario
- **Archivos afectados:** `src/melate/{lab,protocolo,informe}.py`, `tests/{test_protocolo,test_paridad}.py`,
  `Documentos_Contexto/_MAPA.md`, `README.md`,
  `Documentos_Contexto/Estructura_Carpetas/Añadir/2026-10-03_00-13_s1-arbol-del-proyecto.md`

## Qué se hizo

Buscar en las fases 1 y 2 lo que sus propias reviews no vieron. El planteamiento: **los tests
comprueban lo que alguien pensó comprobar**, así que una auditoría que solo los vuelva a ejecutar no
encuentra nada — las 92 pruebas estaban en verde al empezar esta sesión y siguieron estándolo
mientras se encontraban cinco defectos.

Lo que se hizo en su lugar fue atacar las **afirmaciones**: tomar cada campo que un documento dice
que gobierna algo y comprobar, con dos valores distintos, que de verdad lo gobierna; y tomar cada
cifra que un documento publica y volver a medirla.

**Limitaciones del entorno, por delante:** sin Linux ni macOS reales; la parte de finales de línea se
cubrió emulando el checkout. Y una limitación de fondo: el holdout real sigue vacío, así que todo lo
que toca la evaluación con datos se prueba con sellos antiguos construidos a mano.

## Review de fallas #1

### ❌ A · El preregistro declaraba un umbral y la condición 5 no lo usaba — **el más grave**

`prereg/2026-10-03_logistica-revancha.json` declara `efecto_minimo_declarado: 0.048`.
**Ningún código lo leía.** `condicion_efecto_minimo` usaba solo el mínimo detectable que se calcula
a partir del tamaño del holdout.

Eso abría un agujero con dirección concreta: **cuanto más grande el holdout, más baja el detectable,
y más fácil pasar la condición con un efecto menor que el declarado.** Demostrado:

```
delta 0.0100 | emd calculado 0.0092 | declarado en el sello 0.048
condicion 5 -> CUMPLE
```

Un efecto **cinco veces menor** que el que el documento sellado decía que haría falta, y la condición
pasando. Es exactamente el tipo de aflojamiento retroactivo que el preregistro existe para impedir,
solo que por omisión en vez de por mala fe.

→ **Corregido.** El umbral es ahora `max(detectable, declarado)`, y el motivo dice cuál de los dos
mandó. Quien se compromete por adelantado a un umbral no puede beneficiarse después de que la
muestra haya crecido.

### ❌ B y C · El sello declaraba `reentrenar_cada` y `semillas`, y se ignoraban

`_evaluar_una` tenía `reentrenar_cada=100` y la semilla fijada a `SEMILLA_BACKTEST` como valores por
defecto, y `evaluar()` **no se los pasaba desde el preregistro**. Demostrado:

```
reentrenar_cada declarado = 100  -> delta Revancha +0.066445
reentrenar_cada declarado = 25   -> delta Revancha +0.066445     <- identico
semillas.backtest declarado = 7      -> delta +0.066445
semillas.backtest declarado = 12345  -> delta +0.066445          <- identico
```

Lo insidioso no es el fallo, es **por qué no se vio**: los valores por defecto coincidían con los
declarados en el preregistro, así que todo producía el número correcto y las 92 pruebas pasaban. Un
preregistro que declarara otra cosa se habría ignorado en silencio.

→ **Corregido.** `evaluar()` toma los dos del `spec` y los devuelve en `resultados` para que se vean.

**Y un matiz que importa, medido:** para la hipótesis preregistrada —la regresión logística— ni la
semilla ni la cadencia mueven el resultado. La semilla solo decide desempates de magnitud `1e-9` en
`top6`, y las probabilidades de una logística no empatan; y una logística de 7 parámetros sobre
112 000 filas apenas se mueve con un 1 % más de datos. Así que **el impacto real sobre este
preregistro era nulo**. No lo habría sido sobre otros:

| Estrategia | ¿cambia con la semilla? | ¿cambia con `reentrenar_cada`? |
|---|---|---|
| Regresión logística | no | no |
| Calientes últimos 50 | **sí** (+0.1436 contra +0.1047) | — |
| Más frecuentes | **sí** | — |
| Gradient boosting (HGB) | no | **sí** (−0.0895 contra −0.1089) |

### ❌ D · La frontera del holdout excluye el día del sello, y no estaba dicho en ninguna parte

`FECHA` no tiene hora, así que pandas la trata como medianoche: un sorteo celebrado el mismo día del
sello **nunca** es posterior al sello, sea la hora que sea. El holdout empieza al día siguiente.

```
sello 2026-09-30T00:00 -> holdout 0 sorteos
sello 2026-09-30T23:59 -> holdout 0 sorteos
sello 2026-09-29T12:00 -> holdout 1 sorteo
```

No es un bug —el error cae del lado seguro, porque no hay forma de saber si ese sorteo se celebró
antes o después de sellar— pero era una semántica sin declarar en un sitio donde un lector asumiría
lo contrario.

→ **Documentado** en el docstring de `holdout()` con el razonamiento, y **fijado con test**.

### ❌ F · La suite "rápida" tardaba 30 s en vez de 2.4 s

El `_MAPA.md` anunciaba `~5 s` para `pytest -m "not lento and not red"`. Medido: **29.85 s**.

Causa: dos tests de `test_paridad.py` que arrancan un informe completo en subproceso —el de la
carpeta de salida y el de la codificación hostil— **sin marcar `lento`**, a 14 s cada uno. 28 de los
30 s. El bucle del día a día que la Fase 1 diseñó para 2.4 s se había degradado 12 veces sin que
nadie lo notara, porque nadie vuelve a cronometrar lo que ya midió una vez.

→ **Corregido:** los dos marcados `lento`, y añadido
`test_salida_robusta_no_revienta_con_una_pagina_de_codigos_estrecha`, que cubre la misma causa raíz
—un flujo cp1252 y un `Δ`— en milisegundos y sin subproceso. Verificado con dientes: desactivando
el arreglo, falla; restaurándolo, pasa. La suite rápida vuelve a **2.5 s**.

### ❌ G · El documento del árbol del proyecto describe un árbol que ya no existe

`Estructura_Carpetas/Añadir/…arbol-del-proyecto.md` es un documento del índice permanente y afirma
sobre el presente. Lo que dice contra lo que hay:

| Dice | Hay |
|---|---|
| `tests/ 5 ficheros, 52 pruebas` | 6 ficheros, **100** pruebas |
| `src/melate/` sin `lab.py` | 10 módulos, `lab.py` incluido |
| `scripts/colador.ps1` | también `verificar-bitacora.ps1` |
| sin `prereg/` | `prereg/` existe |

La Fase 2 cambió el árbol y **no emitió `Estructura_Carpetas/Modificar/`**: su tabla de emisión no lo
contemplaba. Y la Fase 1 creó `verificar-bitacora.ps1` durante su propio cierre, después de escribir
el documento del árbol.

→ **Corregido** emitiendo `Estructura_Carpetas/Modificar/2026-10-03_01-59_arbol-tras-el-laboratorio.md`.

### ❌ H · Un número mal en un documento cerrado

`Fases/2026-10-03_protocolo/Bugs/…pendientes-heredados.md` dice "17 de 53 tests fallaban". La salida
real del clon limpio fue `1 failed, 35 passed, 16 errors` = **52**. El 53 es el total *después* de
añadir el test de codificación. → Corregido en sitio con marca, por la segunda excepción del §9 del
`REGLAS-DOCUMENTACION.md`.

### ❌ I · Cifras de rendimiento obsoletas

`Rendimiento/Añadir/…coste-del-informe.md` publica "31 pruebas / 2.4 s" y "52 pruebas / ~105 s".
Ahora son 72 rápidas en 2.5 s y 100 en ~136 s. → Se corrigen en el `Arreglos_Bugs/` de Rendimiento,
junto con el arreglo de F que las cambió.

## ✅ Lo que se comprobó y estaba bien

Importa tanto como lo anterior, porque una auditoría que solo lista defectos no dice si el resto se
puede usar.

- **Los cinco comandos de verificación que la bitácora documenta funcionan**, ejecutados uno a uno:
  las dos vistas de validación (174 contra 3), que `ESPEJO` no aparece en `_leer_bytes`, el hash del
  preregistro a mano, las 5 condiciones en el veredicto, y `git check-attr` + `hash-object` sobre el
  snapshot.
- **El laboratorio reproduce el backtest sobre el mismo tramo.** Nada lo comprobaba, y era una
  divergencia posible con consecuencias graves: si el informe y el laboratorio midieran distinto, sus
  cifras no serían comparables y nada lo diría. Sobre los 1 784 sorteos desde el índice 400:
  backtest `+0.041000`, laboratorio `+0.040999`. → **Fijado con test** (`test_el_laboratorio_reproduce_el_backtest_en_el_mismo_tramo`).
- **La estimación de "unos once años" es correcta.** Se verificó la premisa: los sorteos son
  miércoles, viernes y domingo —100 de cada uno en los últimos 300—, así que 3 por semana es exacto,
  y 1 778 sorteos a 156 por año son 11.4 años. *Matiz:* la media histórica de la era 6/56 es de 2.23
  por semana (116/año) por los huecos, lo que daría 15.3 años. Las dos cifras son defendibles; la de
  11 asume que la cadencia actual se mantiene.
- **El sello del preregistro sobrevive al clon**, con otros bytes y otro SHA-256 de fichero. Ya
  estaba comprobado al cerrar la Fase 2 y se vuelve a confirmar.
- **Los hashes del snapshot cuadran** tras un clon que emula Linux.
- **El veredicto del proyecto no cambia** con ninguno de los arreglos: sigue siendo *sin ventaja
  demostrada*, 0 de 5, por holdout vacío.

## Optimización

Nada que optimizar. Los arreglos suman unas 40 líneas de código y 7 tests.

**Lo que se decidió NO hacer:**

- **No se re-sella el preregistro.** `efecto_minimo_declarado` ya estaba en él; el fallo era que
  nadie lo leía. No hacía falta tocar el documento sellado, y era importante que no hiciera falta.
- **No se cambia la nota de los "once años" del preregistro sellado**, aunque la media histórica dé
  15. Es una nota informativa, no un criterio: no afecta a la evaluación. Y re-sellar un documento ya
  publicado por un matiz de redacción sería precisamente el precedente que la Fase 2 se cuidó de no
  sentar.
- **No se corrigen los "52 tests" de los documentos de la Fase 1** que hablan de su propio cierre.
  Allí son un dato histórico correcto. Solo se corrigen los que afirman sobre el presente.

## Review de fallas #2 + review de seguridad

- ✅ **La paridad de la Fase 1 sigue intacta.** `test_paridad.py` en verde: ninguno de los arreglos
  toca el reporte del informe.
- ✅ **El veredicto por defecto sigue siendo el restrictivo.** `declara_ventaja({}, {})` → 0 de 5.
- ✅ **El nuevo parámetro no puede aflojar nada.** `condicion_efecto_minimo` toma el **máximo** de los
  dos umbrales; pasar `declarado=None` deja el comportamiento anterior, y pasar un valor solo puede
  endurecerlo.
- ✅ **Sin cambios en la superficie de red** ni en los datos. Ningún fichero de `data/` ni de
  `prereg/` se tocó.
- ✅ **Colador limpio**, autoprueba 3/3. **Bitácora íntegra**, 0 hallazgos.
- ✅ **100 tests en verde**, 136 s.

## Observación aceptada (no es bug)

Dos de los tests que escribí para pillar B y C **fallaron por una premisa mía equivocada**:
comparaban deltas con la regresión logística, y resultó que ni la semilla ni la cadencia la mueven.
El arreglo estaba bien; el test, mal. Se reescribieron para medir el efecto donde es real —"Calientes
últimos 50" para la semilla, gradient boosting para la cadencia— y para comprobar aparte que los
valores declarados llegan al resultado. Queda registrado porque la lección es concreta: **un test
que compara dos salidas solo prueba algo si el parámetro puede cambiarlas**, y eso hay que medirlo
antes de escribir el test, no suponerlo.

## Resultado

**Siete defectos encontrados, siete corregidos.** Ninguno dejado a propósito, así que no hubo nada
que consultar. Tres eran de código (A, B+C, D-sin-documentar), uno de arnés de pruebas (F) y tres de
documentación (G, H, I).

Ninguno cambia el veredicto del proyecto. El más grave, A, habría cambiado el veredicto de una
evaluación futura con un holdout grande — es decir, habría mordido exactamente el día en que las
cifras empezaran a importar.

**La conclusión metodológica:** las 92 pruebas estaban en verde al empezar y se encontraron siete
defectos. Los tests protegen contra lo que alguien pensó comprobar; lo que encuentra el resto es
tomar las **afirmaciones** del proyecto —"este campo gobierna la corrida", "esto tarda 2.4 s", "el
árbol es así"— y comprobarlas una por una con un valor distinto o un cronómetro.

## Cómo verificar / revertir

```powershell
.venv\Scripts\python.exe -m pytest tests -q                                   # 100 en verde
.venv\Scripts\python.exe -m pytest tests -m "not lento and not red" -q        # 72, ~2.5 s
```

Los tests que fijan cada arreglo:

```powershell
.venv\Scripts\python.exe -m pytest tests -k "efecto_minimo_declarado or efecto_declarado" -v   # A
.venv\Scripts\python.exe -m pytest tests -k "sello_llegan or cambiar_un_parametro" -v           # B, C
.venv\Scripts\python.exe -m pytest tests -k frontera -v                                         # D
.venv\Scripts\python.exe -m pytest tests -k pagina_de_codigos -v                                # F
.venv\Scripts\python.exe -m pytest tests -k reproduce_el_backtest -v                            # la propiedad buena
```

**Revertir:** cada arreglo tiene su `Arreglos_Bugs/` con su propio apartado. En conjunto: devolver
`condicion_efecto_minimo` a un solo umbral, quitar `reentrenar_cada` y `semilla` del paso desde el
`spec`, y desmarcar los dos tests `lento`. **No se recomienda ninguno**, y menos el primero.

**Pendiente de verificar:** nada nuevo. Siguen los cinco puntos de
`Fases/2026-10-03_protocolo/99_CIERRE.md`.

Relacionado: `Protocolo_Estadistico/Arreglos_Bugs/2026-10-03_01-59_el-sello-no-gobernaba-la-corrida.md`,
`Rendimiento/Arreglos_Bugs/2026-10-03_01-59_la-suite-rapida-no-era-rapida.md`,
`Estructura_Carpetas/Modificar/2026-10-03_01-59_arbol-tras-el-laboratorio.md`

---

## Resultado — CERRADO el 2026-10-03 a las 02:10

Los siete defectos, con dónde quedó cada uno:

| # | Defecto | Arreglo | Test que lo fija |
|---|---|---|---|
| A | La condición 5 ignoraba `efecto_minimo_declarado` | `max(detectable, declarado)` | `test_condicion_efecto_minimo_respeta_el_umbral_declarado`, `test_declara_ventaja_propaga_el_efecto_declarado` |
| B | `reentrenar_cada` del sello ignorado | `evaluar()` lo pasa | `test_los_parametros_del_sello_llegan_al_resultado`, `test_cambiar_un_parametro_del_sello_cambia_el_resultado` |
| C | `semillas` del sello ignorado | ídem | ídem |
| D | Frontera del holdout sin documentar | docstring con el razonamiento | `test_la_frontera_excluye_el_dia_del_sello` |
| F | Suite rápida de 30 s anunciada como 5 | dos tests a `lento` + uno rápido equivalente | `test_salida_robusta_no_revienta_con_una_pagina_de_codigos_estrecha` |
| G | El árbol del índice permanente mentía | `Estructura_Carpetas/Modificar/` | — |
| H, I | Cifras mal en documentos | corregidas con marca | — |

Y la propiedad buena que no estaba vigilada, ahora sí:
`test_el_laboratorio_reproduce_el_backtest_en_el_mismo_tramo`.

**Estado al cerrar:**

- **100 tests en verde**, 136 s. La suite rápida: 72 pruebas, **2.5 s**.
- `scripts/verificar-bitacora.ps1` → 0 hallazgos. `scripts/colador.ps1 -Autoprueba` → 0
  coincidencias, autoprueba 3/3.
- Paridad de la Fase 1 intacta.
- **El veredicto del proyecto no cambia:** `sin ventaja demostrada`, 0 de 5, holdout vacío.

**Ningún bug abierto y ninguno dejado a propósito.**

### Lo que esta auditoría dice sobre el método

Las 92 pruebas estaban en verde al empezar y siguieron estándolo mientras se encontraban siete
defectos. Ninguno se habría encontrado volviendo a correr los tests, porque **un test comprueba lo
que alguien pensó comprobar**, y los siete estaban justo en el hueco de lo que nadie pensó.

Lo que los encontró fue tomar las afirmaciones del proyecto y ponerlas a prueba una por una:

- *"Este campo del preregistro gobierna la corrida"* → darle dos valores distintos y comparar.
  Tres fallos.
- *"Esto tarda 2.4 s"* → cronometrarlo. Un fallo, por un factor de doce.
- *"El árbol es así"* → listarlo. Un fallo.
- *"Unos once años"* → recalcularlo desde los datos. Correcto, con un matiz.

Es un procedimiento repetible y conviene que la Fase 3 lo herede: **al cerrar, no basta con que los
tests pasen; hay que volver a medir cada número publicado y dar dos valores a cada parámetro que se
dice que manda.**

Y una cosa más, porque fue la parte más incómoda: dos de los tests que escribí para pillar B y C
fallaron por una premisa mía equivocada. El arreglo estaba bien y el test estaba mal. **Un test que
compara dos salidas solo prueba algo si el parámetro puede cambiarlas**, y eso se mide antes de
escribir el test.
