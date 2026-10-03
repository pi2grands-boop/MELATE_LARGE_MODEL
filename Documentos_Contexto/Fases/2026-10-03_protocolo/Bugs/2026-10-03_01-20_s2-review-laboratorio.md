# Review s2 — el laboratorio: preregistro, holdout y las 5 condiciones

- **Fecha/hora:** 2026-10-03 01:20
- **Área:** Fases/2026-10-03_protocolo · **Acción:** Bugs
- **Chat / página:** sesión de arranque · etapas 2 a 5 del alcance
- **Archivos afectados:** `src/melate/lab.py`, `src/melate/protocolo.py`,
  `prereg/2026-10-03_logistica-revancha.json`, `tests/test_protocolo.py`

## Qué se hizo

Review del código del laboratorio: `lab.py`, las 5 condiciones añadidas a `protocolo.py`, el
preregistro sellado y sus 41 pruebas.

**Limitaciones del entorno, por delante:** sin linter. La revisión fue lectura línea a línea más los
tests. Y una limitación de fondo que no se puede resolver con esfuerzo: **el holdout real de hoy
está vacío**, así que todo el camino afirmativo se prueba con fixtures de sello antiguo construidas
a mano. Es un sustituto honesto —usa los mismos datos y el mismo código— pero no es una evaluación
preregistrada de verdad, y no lo será hasta que pasen sorteos.

## Review de fallas #1

### ❌ La condición 2 no podía pasar nunca — la puerta estaba cerrada por el motivo equivocado

El fallo grave de este ciclo, y se vio al mirar los números en vez de los tests.

`lab.evaluar` no calculaba `q_BH_global`: lo leía de un campo `q_BH_global_observado` que nada
rellenaba. Así que `condicion_q` devolvía siempre *"sin q de la familia global: no se puede juzgar"*,
y por tanto **`declara_ventaja` era incapaz de devolver "VENTAJA DEMOSTRADA" en ningún escenario**,
ni con un holdout perfecto.

Eso es peor que un falso negativo: es un sistema que parece prudente y está roto, y las dos cosas son
indistinguibles desde fuera. Un laboratorio que no puede decir "sí" ni en el caso ideal no está
siendo riguroso, está averiado.

→ **Corregido.** `_evaluar_una` calcula ahora la `p` de dos colas desde la `z`, y `evaluar` aplica
Benjamini-Hochberg sobre las pruebas del holdout —una por juego— corrigiendo contra la familia que
el preregistro **declaró**, no contra las 3 que se acaban de correr.

→ Eso obligó a **`benjamini_hochberg(ps, m=None)`**. Con `m` explícito la corrección es contra una
familia declarada por adelantado, más conservadora. Y **`m < len(ps)` se rechaza**, porque sería
exactamente la forma de hacer trampa: declarar una familia pequeña después de ver los resultados.
Con `m=None` da bit a bit lo de siempre, y hay un test que lo exige — si no, se rompería la paridad
de la Fase 1.

→ **Y las variantes de hiperparámetros NO cuentan como pruebas.** Son comprobaciones de robustez de
la misma hipótesis; contarlas inflaría la familia sin añadir ninguna hipótesis nueva. Está comentado
en el código porque es el tipo de decisión que alguien "corregiría" sin darse cuenta.

### ❌ El preregistro sellado no declaraba el tamaño de familia como número

Consecuencia del anterior. El preregistro decía `"familia_de_correccion": "global de 36 pruebas…"`,
en prosa. Y **parsear prosa para decidir un umbral estadístico no es una opción.**

→ **Se re-selló** con `tamano_familia: 36` como entero.

**Y aquí hay que ser explícito, porque es delicado:** re-sellar un preregistro es precisamente lo que
este módulo existe para impedir. Fue legítimo por una razón concreta y verificable — **el borrador
nunca se había comiteado ni subido**, así que nada dependía de él:

```
git log --oneline -- prereg/    -> sin salida
git status --short prereg/      -> ?? prereg/
```

Encontrar un defecto de formato mientras se escribe el evaluador es el momento correcto de
encontrarlo. **Hacer esto después de publicar habría sido inaceptable**, y el propio `sellar()` lo
impide: se niega a sobrescribir. Queda aquí registrado para que nadie use este precedente como
excusa: la pregunta que lo autoriza no es "¿es un borrador?" sino "¿se puede demostrar que nadie lo
ha visto?".

### ❌ Un BOM rompía la carga con un error que no decía nada

Descubierto al intentar manipular el preregistro para comprobar que se rechaza: PowerShell guardó el
fichero con BOM y la carga murió con `Unexpected UTF-8 BOM`, no con el mensaje del sello. Un
preregistro guardado con cualquier editor de Windows daría ese error confuso.

→ **Corregido:** se lee con `utf-8-sig`. El BOM **no afecta al sello**, porque el hash se calcula
sobre el JSON canónico del contenido ya parseado y no sobre los bytes del fichero. Hay test de las
dos cosas.

### ✅ Lo que sí se negó a la primera

- Sin preregistro no se evalúa: `evaluar()` exige el campo del sello y rechaza un dict a pelo.
- Un preregistro sin hash no es un preregistro.
- Faltar un campo obligatorio lo invalida.
- **No se puede sellar en el pasado.** `MARGEN_SELLO` de una hora absorbe desfases de reloj sin
  abrir la puerta a antedatar. Un preregistro antedatado no preregistra nada: su holdout incluiría
  sorteos que ya se pueden mirar.
- **No se sobrescribe un sello.**
- Cuatro formas de manipular el fichero real —aflojar `umbral_q`, encoger `tamano_familia`,
  antedatar `sello_utc`, cambiar `juego_principal`— las cuatro rechazadas con "el sello NO cuadra".

### ✅ El holdout solo mira hacia delante

Comprobado con tres sellos distintos y en los tres juegos: ningún índice del holdout tiene `FECHA`
anterior al sello. Y su contraprueba, que importa igual: **con un sello de 2024 el holdout tiene 430
sorteos**, no cero. Sin eso, "el holdout está vacío" podría estar pasando porque el cálculo esté
roto.

### ✅ Y no hay fuga en la evaluación del holdout

`test_la_evaluacion_no_mira_el_futuro`: las variables del primer sorteo del holdout son idénticas
construidas con la serie completa o con la serie recortada ahí. Es el test de no-fuga de la Fase 1
aplicado al laboratorio.

## Optimización

- `declara_ventaja` **no** colapsa las condiciones en un `and`. Cada una devuelve su veredicto y su
  motivo en texto, y se evalúan **todas** aunque la primera falle. Cuando algo no pasa, lo útil es
  saber qué; cortocircuitar habría sido más rápido y menos útil.
- `_evaluar_una` reutiliza `variables` y `top6` de `backtest.py` en lugar de duplicar la lógica de
  predicción. Si la de `backtest` cambiara, la del laboratorio cambia con ella — que es lo que se
  quiere, porque evalúan la misma cosa.
- Las condiciones son funciones públicas sueltas (`condicion_q`, `condicion_mismo_signo`…) y no
  métodos privados, para poder probarlas una a una sin montar un escenario completo. 20 de los 41
  tests son eso.

**Lo que se decidió NO hacer:** `_predecir` no soporta todas las estrategias del backtest —levanta
`ValueError` con las que no conoce—. Añadirlas sin que haya un preregistro que las use sería código
sin consumidor, y el `ValueError` es explícito.

## Review de fallas #2 + review de seguridad

- ✅ **La paridad de la Fase 1 intacta:** 92 tests en verde, `test_paridad.py` incluido. El cambio en
  `benjamini_hochberg` es compatible hacia atrás y hay un test que lo fija.
- ✅ **`declara_ventaja` no lanza nunca.** Si falta un dato, la condición no se cumple y lo dice. Un
  sistema que se cae cuando le faltan datos invita a saltárselo.
- ✅ **El veredicto por defecto es el restrictivo.** `declara_ventaja({}, {})` devuelve 0 de 5 y "sin
  ventaja demostrada": el estado por omisión es el que no afirma nada.
- ✅ **Nada se ejecuta al importar** ninguno de los dos módulos.
- ✅ **`prereg/` no contiene nada antedatado.** El único fichero tiene sello 2026-10-03T06:45Z, que
  es de hace minutos.
- ✅ **Superficie de red sin cambios.** `lab.py` solo llega a la red si se le llama sin `--datos`, y
  entonces pasa por `ingest.cargar`, que solo habla con el oficial.
- ✅ **Sin credenciales, sin variables de entorno, sin ficheros de configuración.**
- ✅ **Colador limpio** sobre 60 ficheros, autoprueba 3/3.

## Observación aceptada (no es bug)

Con el holdout de prueba de 430 sorteos, la condición 3 (estabilidad) **pasa por los pelos**: el
desvío máximo es del 45 % contra una tolerancia del 50 %, y lo provoca la variante `C=0.1`, que
reduce el efecto a la mitad. No es un fallo del código ni de la tolerancia: es una señal real de que
el modelo depende bastante de la regularización. Queda registrado porque si algún día esa condición
pasa limpiamente habrá que preguntarse por qué, y porque es exactamente el tipo de fragilidad que el
protocolo quiere sacar a la luz antes de que nadie se entusiasme.

## Resultado

**Bugs abiertos: ninguno.** Los tres encontrados se corrigieron en este ciclo y los tres tienen test.
Ninguno se dejó a propósito.

41 tests nuevos. Suite completa: **92 en verde**, 113 s.

**El veredicto de hoy, con el preregistro real:** `sin ventaja demostrada`, 0 de 5 condiciones, y la
primera dice *"holdout vacío: 0 sorteos posteriores al sello"*. Eso es exactamente lo que tiene que
decir, y es el criterio de terminado número 3 del alcance.

## Cómo verificar / revertir

```powershell
.venv\Scripts\python.exe -m melate.lab --prereg .\prereg\2026-10-03_logistica-revancha.json --datos .\data\raw\2026-10-02
.venv\Scripts\python.exe -m pytest tests\test_protocolo.py -q      # 41 pruebas
.venv\Scripts\python.exe -m pytest tests -q                        # 92, paridad incluida
```

Que el camino afirmativo existe y es alcanzable:

```powershell
.venv\Scripts\python.exe -m pytest tests\test_protocolo.py -k camino_afirmativo -v
```

**Revertir:** borrar `src/melate/lab.py`, `prereg/`, `tests/test_protocolo.py` y el bloque de las 5
condiciones de `protocolo.py`; devolver `benjamini_hochberg` a su firma de un argumento. **Lo que se
reintroduce:** un proyecto capaz de medir pero sin ningún mecanismo que impida declarar una ventaja
que no ha pasado el protocolo, que es la situación que la Fase 1 dejó y el motivo de esta fase.

**Pendiente de verificar** — por construcción, no por falta de esfuerzo:

1. **Una evaluación preregistrada de verdad.** El holdout no existirá hasta que pasen sorteos
   posteriores al 2026-10-03T06:45Z. Todo el camino con holdout está probado con fixtures de sello
   antiguo, que usan los mismos datos y el mismo código pero no son un preregistro legítimo.
2. **La condición 5 no es alcanzable en años.** Con 0.048 aciertos de efecto mínimo hacen falta del
   orden de 1 800 sorteos de holdout, unos 11 años a tres por semana. Está declarado en las notas del
   preregistro: no es un defecto, es la medida honesta de cuánta evidencia haría falta.

Relacionado: `Fases/2026-10-03_protocolo/00_ALCANCE.md`,
`Fases/2026-10-03_protocolo/Bugs/2026-10-03_01-05_s2-pendientes-heredados.md`,
`Protocolo_Estadistico/Decisiones/2026-10-03_00-13_s1-familias-benjamini-hochberg.md`

---

## Resultado — CERRADO el 2026-10-03 a las 01:30

Los tres bugs corregidos en el ciclo, los tres con test:

| Bug | Test que lo vigila |
|---|---|
| La condición 2 no podía pasar nunca: `q_BH_global` no se calculaba | `test_evaluar_con_holdout_de_verdad_mide_algo` exige que la condición 2 **se evalúe**, no solo que falle |
| El preregistro no declaraba el tamaño de familia como número | `test_el_preregistro_del_repositorio_esta_sellado_y_verifica` exige `tamano_familia == 36` |
| Un BOM rompía la carga con un error que no decía nada | `test_un_bom_no_rompe_el_sello` |

Y tres tests que protegen el mecanismo de BH frente a su propio uso indebido:
`test_bh_con_familia_declarada_es_mas_estricto`, `test_bh_sin_m_es_identico_al_oraculo` y
`test_bh_no_se_puede_aflojar`.

**Estado al cerrar:** 41 pruebas nuevas, **92 en verde** en la suite completa con la paridad de la
Fase 1 intacta, colador limpio sobre 60 ficheros. Ningún bug dejado a propósito.

**El veredicto real del proyecto, hoy:** `sin ventaja demostrada`, 0 de 5 condiciones, motivo
*"holdout vacío: 0 sorteos posteriores al sello"*. Es el criterio de terminado número 3 del alcance,
y es la respuesta correcta.

Siguen pendientes, por construcción y no por falta de esfuerzo, los dos puntos de arriba: una
evaluación preregistrada de verdad —que necesita que pasen sorteos— y la condición 5, que con 0.048
de efecto mínimo no es alcanzable en años. Pasan a
`Fases/2026-10-03_protocolo/99_CIERRE.md`.
