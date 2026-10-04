# Por qué las nueve pruebas de log-loss no entran en la familia, y si hace falta tenerlas

- **Fecha/hora:** 2026-10-04 10:45
- **Área:** Protocolo_Estadistico · **Acción:** Decisiones
- **Estado:** cerrada · **Decidida por:** usuario, sobre el análisis de este documento («sí, hazlo, y
  analiza si es necesario tenerlas»)
- **Alcance:** el bloque `logloss` del backtest (`src/melate/backtest.py:89-109`,
  `baseline_auditoria.py:218-237`), la familia global de `src/melate/protocolo.py`, y cómo lo enseña
  `app/streamlit_app.py`

## La pregunta

El backtest corre, además de las 21 pruebas de aciertos, **nueve pruebas de log-loss**: tres modelos
(«Más frecuentes», regresión logística, gradient boosting) en tres juegos. Cada una tiene su `t` y su
`p` de dos colas, se publica en el informe, y **ningún documento las contaba en la familia ni decía
por qué no**. La regla 3 del protocolo dice: *Benjamini-Hochberg sobre TODAS las pruebas corridas,
también las que no se reportan*. La encontró la review de la Fase 4 (C2 de
`Fases/2026-10-04_app-local/Bugs/2026-10-04_10-05_s4-review-base-app-y-red.md`).

## El argumento: tal como se calculan, no son pruebas sobre la urna

El log-loss mide lo bien repartidas que están las probabilidades que un modelo asigna a los 56
números. La prueba compara el de cada modelo con el del reparto uniforme (6/56 cada número) y su
hipótesis nula es «los dos son iguales».

**Con una urna limpia, esa nula es falsa para cualquier modelo que no sea el uniforme.** Es la
desigualdad de Gibbs: si cada número sale con probabilidad 6/56, la pérdida esperada es mínima
exactamente en 6/56, y cualquier otro reparto pierde más. Así que con una urna perfectamente limpia
todo modelo que se aparte del uniforme pierde en log-loss, y con muestra suficiente la prueba sale
significativa. **Un «peor que el azar» significativo es lo esperado; no dice nada de la urna.** Lo
único que contradiría una urna limpia es un «mejor que el azar».

La familia de Benjamini-Hochberg existe para las pruebas de hipótesis sobre la urna
(`Protocolo_Estadistico/Decisiones/2026-10-03_05-10_s3-la-popularidad-no-entra-en-la-familia.md`).
Una prueba cuya nula es falsa aunque la urna sea limpia no es una de ellas.

## Lo medido, con las cifras publicadas

De `reportes/2026-10-03_informe-con-popularidad.json` (snapshot del 4272, 2 000 simulaciones). La
última columna es la prueba en su forma de una cola, «el modelo pierde menos que el azar», calculada
con la `t` y los grados de libertad publicados:

| Juego | Modelo | Δ log-loss | t | p (dos colas) | p (mejor que el azar) |
|---|---|---|---|---|---|
| Melate | Más frecuentes | +0,000447 | +5,19 | 0,0000 | 1,0000 |
| Melate | Regresión logística | +0,000048 | +1,77 | 0,0765 | 0,9616 |
| Melate | Gradient boosting | +0,000180 | +3,49 | 0,0005 | 0,9998 |
| Revancha | Más frecuentes | +0,000441 | +4,92 | 0,0000 | 1,0000 |
| Revancha | Regresión logística | +0,000030 | +0,57 | 0,5697 | 0,7156 |
| Revancha | Gradient boosting | +0,000211 | +2,97 | 0,0030 | 0,9985 |
| Revanchita | Más frecuentes | +0,000533 | +5,14 | 0,0000 | 1,0000 |
| Revanchita | Regresión logística | +0,000055 | +2,44 | 0,0149 | 0,9926 |
| Revanchita | Gradient boosting | +0,000078 | +1,73 | 0,0844 | 0,9581 |

**Las nueve Δ son positivas**: los tres modelos pierden frente al azar en los tres juegos, como
predice la desigualdad de Gibbs. La regresión logística es la que menos pierde porque sus
probabilidades apenas se separan del uniforme.

### Qué pasaría con la familia en cada caso

| Familia | Pruebas | q mínima de las 36 de siempre | Pasan q ≤ 0,05 |
|---|---|---|---|
| A · La de hoy | 36 | **0,306** | ninguna |
| B · Con el log-loss tal como se calcula (dos colas) | 45 | **0,096** | **5**, las cinco de log-loss con p ≈ 0 — todas *peores* que el azar |
| C · Con el log-loss en una cola (mejor que el azar) | 45 | **0,383** | ninguna |

El caso B es el hallazgo de este análisis. **Meterlas tal cual no habría sido más prudente, sino
menos.** El informe diría «revisar: hay pruebas con q ≤ 0,05» por cinco modelos que pierden contra el
azar. Y, peor, Benjamini-Hochberg es un procedimiento por rangos: añadir cinco p casi nulas empuja
hacia arriba el rango de todas las demás, y la q de la regresión logística en Revancha **bajaría de
0,306 a 0,096** sin que nada de esa hipótesis hubiera cambiado. Una corrección por comparaciones
múltiples que se afloja al sumarle pruebas irrelevantes es lo contrario de lo que se busca.

El caso C es la forma correcta de esas pruebas como pruebas sobre la urna, y es inofensivo: ninguna
pasa y la familia se endurece (0,306 → 0,383).

## ¿Hace falta tenerlas?

**Sí, y por dos razones distintas.**

1. **No se pueden quitar.** El oráculo las calcula (`baseline_auditoria.py:218-237`) y
   `tests/test_paridad.py` exige que el paquete reproduzca su reporte con tolerancia cero. Quitarlas
   del informe rompería la paridad, y el oráculo no se modifica.
2. **Sirven, como diagnóstico.** Son la única medida del proyecto que mira las **probabilidades** y
   no solo los seis números elegidos. Dicen dos cosas: que «Más frecuentes» y gradient boosting están
   sobreajustados —reparten las probabilidades con una confianza que los datos no sostienen—, y que
   la regresión logística, la única con una p baja en aciertos, casi no se separa del uniforme. Las
   dos cosas son coherentes con una urna sin patrón que explotar.

Lo que **no** hacen es juzgar: ninguna condición de la regla 5 las usa, el preregistro sellado
declara como métrica los aciertos por boleto, y su forma de dos colas no puede apoyar una ventaja.

## La decisión

**Las nueve pruebas de log-loss se quedan en el informe y en la app, como diagnóstico, y fuera de la
familia.** La familia sigue siendo de 36. La app lo dice debajo de su tabla, con el porqué: un Δ
positivo es lo esperado con una urna limpia, y solo uno negativo y significativo diría algo de ella.

No se añade la versión de una cola al informe: hoy no la usa ninguna regla, y añadir una prueba a la
familia es una decisión del usuario con consecuencias
(`Protocolo_Estadistico/Decisiones/2026-10-03_00-13_s1-familias-benjamini-hochberg.md`).

## Alternativas descartadas

| Opción | Por qué no |
|---|---|
| Meterlas en la familia tal como están | Caso B: cinco «hallazgos» que son modelos perdiendo, y una familia que se afloja para las hipótesis de verdad |
| Meterlas en una cola | Correcto pero innecesario hoy: ninguna regla las usa. Es el camino si un día el log-loss pasa a ser métrica de ventaja |
| Quitarlas del informe | Rompe la paridad con el oráculo, que es bloqueante |
| Esconderlas en la app | Están en el informe publicado; esconderlas en la pantalla sería peor que explicarlas |

## Premisas que esta decisión toca (§7 de las reglas)

| Documento | Estado |
|---|---|
| `Protocolo_Estadistico/Decisiones/2026-10-03_05-10_s3-la-popularidad-no-entra-en-la-familia.md` | **Sigue valiendo, y se precisa.** Su frontera —«dentro va todo lo que hable de la urna»— se refiere a pruebas de hipótesis sobre la urna. Una prueba cuya nula es falsa aunque la urna sea limpia no lo es |
| `Protocolo_Estadistico/Decisiones/2026-10-03_00-13_s1-familias-benjamini-hochberg.md` | Sigue valiendo: 15 + 21 = 36. Este documento explica lo que aquel no contaba |
| `prereg/2026-10-03_logistica-revancha.json` | Intacto. Declara una familia de 36 y la métrica de aciertos |
| `_MAPA.md`, «Decisiones cerradas» | Al cerrar la Fase 4 se añade la precisión de la frontera |

## Cuándo reabrirla

- Si alguien quisiera usar el log-loss —o cualquier medida de probabilidades— para declarar una
  ventaja: haría falta su preregistro, una prueba de una cola, un mínimo detectable en su unidad, y
  entonces sí entraría en la familia (caso C). Con consulta.
- Si el oráculo cambiara, que no cambia.

## Cómo verificar

Las cifras de este documento salen del informe publicado; no hace falta correr el backtest:

```powershell
.venv\Scripts\python.exe -c "import json; from scipy import stats; from melate import protocolo as p; d=json.load(open('reportes/2026-10-03_informe-con-popularidad.json',encoding='utf-8')); a,b=d['auditoria'],d['backtest']; base=[a[j][k]['p_dos_colas'] for j,k in p.claves_auditoria(a)]+[b[j]['estrategias'][s]['p'] for j,s in p.claves_backtest(b)]; ll=[(r['p'],float(stats.t.cdf(r['t'],b[j]['sorteos_prueba']-1))) for j in b for s,r in b[j]['logloss'].items() if s!='azar']; [print(n, round(min(p.benjamini_hochberg(ps)[:36]),4)) for n,ps in (('A',base),('B',base+[x for x,_ in ll]),('C',base+[y for _,y in ll]))]"
```

Tiene que imprimir `A 0.306`, `B 0.0956` y `C 0.3825`.

Relacionado: `Protocolo_Estadistico/Decisiones/2026-10-03_05-10_s3-la-popularidad-no-entra-en-la-familia.md`,
`Protocolo_Estadistico/Decisiones/2026-10-03_00-13_s1-familias-benjamini-hochberg.md`,
`Fases/2026-10-04_app-local/Bugs/2026-10-04_10-05_s4-review-base-app-y-red.md`.
