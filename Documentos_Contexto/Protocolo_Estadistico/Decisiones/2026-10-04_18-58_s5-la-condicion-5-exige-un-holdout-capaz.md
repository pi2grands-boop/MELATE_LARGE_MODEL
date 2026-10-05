# Decisión: la condición 5 exige un holdout capaz de detectar el efecto declarado

- **Fecha/hora:** 2026-10-04 18:58
- **Área:** Protocolo_Estadistico · **Acción:** Decisiones
- **Decidido por:** usuario (C1 de la Fase 5, opción A: «Opción A») · **Estado:** cerrada
- **Alcance:** `protocolo.condicion_efecto_minimo` en `src/melate/protocolo.py`, sus tests en
  `tests/test_protocolo.py`, su mutación en `scripts/mutar.py`, y todo veredicto que emita
  `melate.lab` a partir de ahora
- **Escrita ANTES** del código que la aplica y **antes del primer veredicto con holdout.** El 4274, el
  primer sorteo posterior al sello, se sortea hoy a las 22:00 de esta máquina; nadie ha calculado qué
  números elegiría para él la regresión logística, ni antes ni para tomar esta decisión.

## La decisión

**La condición 5 de la regla 5 se cumple solo si el holdout es lo bastante grande para detectar el
efecto que declaró el preregistro, y además el efecto medido lo alcanza.** En cifras: el mínimo
detectable que calcula el laboratorio con el tamaño del holdout tiene que ser menor o igual que
`efecto_minimo_declarado`, y el delta, mayor o igual que el declarado. Con el preregistro sellado
(0,048 aciertos), eso empieza en el sorteo **1 778** del holdout. Si un preregistro no declara efecto,
la condición queda como estaba.

## El problema que cierra

La condición comparaba el delta con `max(mínimo detectable del holdout, declarado)`. Con un holdout
grande, eso corrigió el defecto A de la auditoría de las fases 1 y 2. Con uno pequeño, dejaba una
puerta abierta: con un sorteo el mínimo detectable es 2,0237 aciertos, y un sorteo con tres aciertos
en Revancha da un delta de 2,3571, que lo supera. Lo encontró el inventario de la Fase 5 (H1 de
`Fases/2026-10-04_ciclo-vivo/Inventario/2026-10-04_18-16_s0-estado-de-partida.md`), medido con el
código real:

- **El laboratorio real declara «VENTAJA DEMOSTRADA, 5 de 5»** con un holdout de un sorteo en cuatro
  sorteos históricos: 2928, 3419, 3953 y 4205.
- **Bajo el azar le pasa 1 de cada 303 veces** en la primera evaluación (exacto: 0,003297).
- **Evaluando con cada sorteo**, como hará el ciclo de la Fase 5, el 1,40 % de las historias declara
  ventaja antes de reunir 1 778 sorteos de holdout.

La prueba z con aproximación normal, que es la que declara el sello, empeora el caso pequeño: con un
sorteo, tres aciertos dan p = 0,0011 donde la probabilidad exacta es 0,0126. Y la estabilidad y el
mismo signo apenas filtran con tan pocos datos.

## Alternativas descartadas

| Opción | Por qué no |
|---|---|
| B · Dejarlo como está y que la app avise | La cabecera diría VENTAJA DEMOSTRADA con un sorteo, una vez de cada 303. Un aviso no deshace una afirmación |
| C · Cambiar la prueba por una exacta o por una corrección por mirar muchas veces | Es cambiar lo que el sello declara (`"prueba"`): exigiría otro preregistro. Y no arregla la condición 5 |
| D · Una sexta condición, «holdout mínimo» | El mismo efecto que esta decisión, pero rompe «las cinco condiciones» en el `CLAUDE.md`, en el almacén —que exige cinco— y en la app |

## Consecuencias

- **Con el preregistro sellado, la condición 5 no puede cumplirse antes del sorteo 1 778 del
  holdout**: unos 11,4 años a tres sorteos por semana, 15,3 a la media histórica de la era 6/56. Hasta
  entonces el veredicto es *sin ventaja demostrada* **por construcción**, y el motivo de la condición
  dice cuántos sorteos faltan.
- **Falsos «VENTAJA DEMOSTRADA» bajo el azar, evaluando con cada sorteo** (Monte Carlo, 200 000
  historias): 0 hasta el sorteo 1 777; 0,016 % en el 1 778; **0,095 %** diez años después. Con la regla
  anterior, 1,40 % y 1,45 %.
- **Solo endurece.** Ningún veredicto que la regla anterior negaba pasa ahora a afirmarse. Los dos
  veredictos publicados, con el holdout vacío, no cambian.
- **No toca el preregistro**, cuyo sello sigue verificando; ni el oráculo, ni la paridad, ni la familia
  de 36, ni las otras cuatro condiciones.
- **El tamaño mínimo depende del efecto declarado**, como el cuadrado de su inverso: 0,048 exige 1 778
  sorteos; 0,10, 410; 0,20, 103. Declarar un efecto mayor acorta la espera, y esa elección se hace
  antes de sellar.
- **Lo que no arregla.** Las evaluaciones repetidas después del sorteo 1 778, cuyo riesgo queda medido
  arriba: 0,095 % en diez años. Y la aproximación normal de la prueba, que con 1 778 sorteos ya no
  importa.

## Premisas que esta decisión invalida (§7 de las reglas)

**Ninguna queda falsa; varias pasan a ser ciertas.** Revisados los documentos que hablaban de la
condición 5:

| Documento | Estado |
|---|---|
| `Protocolo_Estadistico/Añadir/2026-10-03_01-30_s2-preregistro-y-las-cinco-condiciones.md` | «La condición 5 necesita del orden de 1 800 sorteos de holdout» era una estimación; ahora es una regla. Su tabla («Medir algo más pequeño que el error de medición») se precisa aquí: también impide juzgar con una muestra que no puede ver el efecto declarado |
| `Protocolo_Estadistico/Bugs/2026-10-03_01-59_auditoria-retrospectiva-fases-1-y-2.md` | Su defecto A sigue arreglado: esta decisión cierra el otro extremo |
| `prereg/2026-10-03_logistica-revancha.json` | Intacto. Sus notas —«necesita del orden de 1.800 sorteos de holdout para ser alcanzable»— pasan a ser literalmente ciertas |
| `README.md` y `Documentos_Contexto/_MAPA.md` | Lo que afirman sobre los ~1 800 sorteos pasa a ser cierto. La nota de la apertura de la Fase 5 en el mapa se resuelve al cerrarla |
| `CLAUDE.md`, regla 5 del protocolo | No se contradice. Al cerrar la Fase 5 se propondrá, sin aplicarla, una redacción que lo diga |

## Cuándo reabrirla

- Si un preregistro quiere poder declarar antes, tiene que declarar un efecto mayor **antes de
  sellar**, nunca después.
- Si se sella un preregistro con otra prueba —exacta, o secuencial con su corrección—, que tendría su
  propio criterio para muestras pequeñas.
- **Un preregistro sin `efecto_minimo_declarado` conserva la regla anterior**, y con ella el riesgo de
  declarar con un sorteo. Hoy no hay ninguno. El próximo que se selle debería declararlo; si no lo
  hace, esta decisión se reabre antes de evaluarlo.

## Cómo verificar

Con el código ya cambiado, el mismo caso que demostró el problema tiene que dar ahora *sin ventaja
demostrada*, con 4 de 5. Desde la raíz del repositorio, sin escribir nada:

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
spec[lab.CLAVE_HASH] = lab.hash_preregistro(spec)
r = lab.evaluar(spec, {j: d[d.CONCURSO <= 4205].reset_index(drop=True) for j, d in era.items()})
print(r["veredicto"]["veredicto"], r["veredicto"]["cumplidas"], "|", r["veredicto"]["condiciones"][4]["motivo"])
'@ | .venv\Scripts\python.exe -
```

Antes de esta decisión imprimía `VENTAJA DEMOSTRADA 5`. Y la mutación que deshace la regla tiene que
detectarse:

```powershell
.venv\Scripts\python.exe scripts\mutar.py --solo "holdout incapaz"
```

Relacionado: `Fases/2026-10-04_ciclo-vivo/Inventario/2026-10-04_18-16_s0-estado-de-partida.md`,
`Fases/2026-10-04_ciclo-vivo/00_ALCANCE.md`,
`Protocolo_Estadistico/Añadir/2026-10-03_01-30_s2-preregistro-y-las-cinco-condiciones.md`,
`Protocolo_Estadistico/Bugs/2026-10-03_01-59_auditoria-retrospectiva-fases-1-y-2.md`.
