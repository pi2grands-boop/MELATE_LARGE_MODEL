# Máquina Melate

**Esto no predice números.** Es una herramienta de análisis estadístico de Melate, Revancha y
Revanchita (Lotería Nacional de México) que audita si la urna es limpia, mide cuánto vale realmente
un boleto, y pone a prueba estrategias de predicción con un protocolo lo bastante estricto como para
que no puedan parecer buenas por casualidad. Hasta ahora **ninguna lo ha conseguido**, y por defecto
toda salida del programa declara *sin ventaja demostrada*.

Si llegaste buscando qué números jugar, la respuesta corta que da este repositorio es: da igual, y
además pierdes dinero en los tres juegos.

## Lo que mide, con datos al sorteo 4272 (30-sep-2026)

**La urna parece limpia.** Chi-cuadrada corregida contra 2 000 urnas simuladas: Melate 52.19
(p = 0.85), Revancha 42.29 (p = 0.22), Revanchita 54.83 (p = 0.98) sobre 56 esferas. Nada que
sugiera sesgo.

**Ninguna estrategia bate al azar.** Ocho estrategias —números calientes, fríos, más frecuentes,
repetir el sorteo anterior, cadena de Markov, regresión logística y gradient boosting, contra
boletos aleatorios— evaluadas sorteo a sorteo sobre 1 784 sorteos de prueba. El azar acierta
0.642857 números por boleto de 6. El mejor caso de todo el proyecto es la regresión logística en
Revancha, con 0.6839, y su q = 0.35 está muy lejos del 0.05 que exige el protocolo.

**Los tres juegos son apuestas perdedoras**, incluso con las bolsas acumuladas más altas de su
historia. Valor esperado por boleto, con el 7 % de impuesto y corrigiendo por el reparto de la bolsa
entre varios acertantes:

| Juego | Precio | Bolsa del 4273 | Valor esperado | Rendimiento | Con premios menores medidos | Bolsa de equilibrio |
|---|---|---|---|---|---|---|
| Melate | $15 | 76.2 M | $6.22 | **−59 %** | **−57.2 %** | ≈ 389 M |
| Revancha | $10 | 111.7 M | $5.09 | **−49 %** | **−44.4 %** | ≈ 286 M |
| Revanchita | $5 | 155.8 M | $4.38 | **−12 %** | −12.4 % | ≈ 178 M |

La penúltima columna es de la Fase 3, y es la más honesta de las dos. La columna de rendimiento usa
el premio esperado de las categorías menores que el oráculo lleva escrito a mano, sacado de dos
tablas de ganadores; la siguiente lo usa **medido sobre 100 sorteos**. La diferencia en Revancha es
de casi cinco puntos, y la razón es que ese dato no es un apéndice: **los premios menores son el
65 % del valor esperado de un boleto de Melate**, no la bolsa. Las dos columnas conviven a propósito
— la primera es la que reproduce el oráculo y la paridad es bloqueante.

La última columna es la bolsa que haría que el boleto valiera lo que cuesta. Revanchita es el menos
malo y ni así llega.

**Y la gente no elige al azar.** Medido sobre 300 sorteos: los números mayores que 31 aparecen en un
**24 % menos de boletos** que los que caben en un calendario (t de Welch = −18.7). Eso no cambia qué
sale —el sorteo no sabe qué apostó nadie— pero sí **con cuánta gente repartirías si ganaras**. Es
todo lo que puede hacer una cartera, y tiene un techo medido: **+0.27 % del precio en Melate**,
contra un suelo de −14 % si eligieras una combinación muy jugada. Una asimetría de 54 a 1, que es
por qué `melate.portfolio` está escrito como un seguro y no como una estrategia.

## Por qué deberías desconfiar de cualquier "ventaja"

Encontrar un patrón en datos de lotería es trivial si te lo permites: con 56 números, decenas de
estrategias y miles de sorteos, **algo** siempre destaca. El protocolo de este proyecto existe para
distinguir eso de un hallazgo real, y no es negociable:

1. **Walk-forward estricto.** Se entrena solo con sorteos anteriores al que se predice. Nada de
   validación cruzada aleatoria. Hay tests que permutan el futuro y exigen que el pasado no se mueva.
2. **Comparación pareada contra boletos aleatorios** juzgados con el mismo sorteo.
3. **Benjamini-Hochberg sobre todas las pruebas corridas**, incluidas las que no se reportan. Son 36.
4. **Preregistro** con su hash antes de evaluar: el holdout son los sorteos posteriores al sello.
5. Para declarar ventaja hay que cumplir **a la vez**: holdout futuro positivo, q ≤ 0.05, estabilidad
   al mover hiperparámetros, mismo signo en los tres juegos, y un efecto por encima del mínimo
   detectable (0.048 aciertos con 1 784 sorteos de prueba).
6. **Hash del dataset y semillas en cada corrida.**

El punto 3 es el que más duele y el más importante. La regresión logística en Revancha tiene
p = 0.017, que a simple vista parece un hallazgo; con la corrección por las 36 pruebas se convierte
en q = 0.35, que no es nada.

**Y hay una frontera que importa: el informe explora, el laboratorio juzga.** Las cifras de
`melate.informe` son exploratorias y no bastan para afirmar nada. Solo `melate.lab` puede, y exige
un preregistro sellado: un JSON que declara la hipótesis, el umbral y la familia de corrección
**antes** de que existan los datos que la juzgarán, con un hash que lo invalida si se altera. El
holdout son los sorteos posteriores al sello, así que el veredicto de hoy es:

```
sin ventaja demostrada  (0 de 5 condiciones)
  [NO] holdout futuro positivo   holdout vacío: 0 sorteos posteriores al sello
```

Es imposible declarar una ventaja hoy, por construcción. Con un efecto mínimo detectable de 0.048
aciertos harían falta del orden de 1 800 sorteos de holdout — unos once años a tres por semana. No
es un defecto del diseño: es la medida honesta de cuánta evidencia haría falta.

## Cómo correrlo

Todo es local. No hace falta Docker ni compilar nada: las dependencias tienen *wheel* precompilado.

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt    # Linux/macOS: .venv/bin/python
.venv/Scripts/python -m pip install -e .

# Informe exploratorio contra el snapshot congelado (~70 s)
.venv/Scripts/python -m melate.informe --datos data/raw/2026-10-02 --salida reportes/informe.json

# Contra los datos de hoy, descargando del oficial
.venv/Scripts/python -m melate.informe --salida reportes/hoy.json

# El veredicto de una hipotesis preregistrada: el unico camino que puede afirmar algo
.venv/Scripts/python -m melate.lab --prereg prereg/2026-10-03_logistica-revancha.json \
    --datos data/raw/2026-10-02

# Sellar una hipotesis nueva (no sobrescribe, y no sella en el pasado)
.venv/Scripts/python -m melate.lab --sellar borrador.json --salida prereg/<fecha>_<slug>.json

# Que juega la gente: tablas de ganadores por categoria. La primera vez sale a la red,
# a UNA solicitud por segundo; despues va de la cache y no vuelve a pedir nada.
.venv/Scripts/python -m melate.popularity --desde 4173 --hasta 4272 \
    --datos data/raw/2026-10-02 --salida reportes/popularidad.json

# El informe con los premios menores medidos en vez de la constante
.venv/Scripts/python -m melate.informe --datos data/raw/2026-10-02 \
    --popularidad reportes/popularidad.json

# Una cartera con presupuesto fijo. NO mejora tus probabilidades de ganar.
.venv/Scripts/python -m melate.portfolio --juego Melate --presupuesto 300 \
    --bolsa 76200000 --popularidad reportes/popularidad.json
```

Todo esto está probado solo en Windows: los comandos usan `.venv/Scripts/` y los dos scripts de
verificación (`scripts/colador.ps1` y `scripts/verificar-bitacora.ps1`) son PowerShell.

Los tests:

```bash
.venv/Scripts/python -m pytest tests -m "not lento and not red" -q   # 132 pruebas, ~5 s
.venv/Scripts/python -m pytest tests -q                              # 161 pruebas, ~2.5 min
```

## Estructura

```
baseline_auditoria.py     el oráculo: la línea base probada, en un solo fichero. No se modifica.
src/melate/
  constantes.py           reglas del juego y línea base del azar
  ingest.py               descarga y normalización; hash de lo que se cargó
  validate.py             las 7 reglas de datos
  audit.py                auditoría de la urna por Monte Carlo, y poder estadístico
  protocolo.py            Benjamini-Hochberg, las familias, y las 5 condiciones
  backtest.py             walk-forward de las 8 estrategias
  ev.py                   premios mayores y valor esperado
  popularity.py           qué juega la gente, de las tablas de ganadores. 1 solicitud/segundo
  portfolio.py            carteras con presupuesto fijo. No mejora tus probabilidades
  informe.py              `python -m melate.informe` — explora
  lab.py                  `python -m melate.lab` — juzga. Sin preregistro no evalúa
data/raw/<fecha>/         snapshots congelados, con su SHA-256 y su procedencia
data/cache/               páginas descargadas. NO se publica: son de un tercero
prereg/                   hipótesis preregistradas, selladas e inmutables
tests/                    reglas de datos, línea base, paridad, no-fuga temporal, protocolo,
                          popularidad y cartera
Documentos_Contexto/      la bitácora: por qué cada cosa es como es
```

`baseline_auditoria.py` y `src/melate/` producen **el mismo reporte, cifra por cifra**, y
`tests/test_paridad.py` lo exige con tolerancia cero. El primero es la referencia inmóvil; el
segundo es donde se trabaja.

## Datos

| Fuente | Uso |
|---|---|
| [CSV oficiales de Lotería Nacional](https://www.loterianacional.gob.mx/Documentos/Historicos/Melate.csv) | La única fuente de carga |
| [Espejo en GitHub](https://github.com/pakinja/pakin) | **Solo validación cruzada**, nunca carga |
| [resultados.melate-e.com](https://resultados.melate-e.com/) | Tablas de ganadores por categoría, y **tercera fuente** para validar los números |

Los CSV oficiales llegan en orden descendente y traen errores conocidos que el código trata sin
esconderlos: `BOLSA = 0` en los sorteos 2120, 2142 y 2234, y Revancha 3221 fuera de secuencia.

El espejo **no se usa como respaldo de carga, a propósito**: tiene mal el sexto número de Revancha
3827 —dice 54 donde el oficial y melate-e.com dan 50— y puede estar parcialmente actualizado, con
unos juegos en un sorteo y otros en el anterior. Ese error es invisible a cualquier validación de una
sola fuente, porque la fila es formalmente válida: seis números distintos, en rango y ordenados.
Solo lo detecta la comparación entre fuentes, que vive en `tests/test_reglas_datos.py`.

Es la clase de error que importa: dos de las cifras publicadas originalmente en este proyecto se
habían calculado con ese dato malo, y una de ellas era precisamente el resultado más llamativo.
Está documentado entero en `Documentos_Contexto/Fases/2026-10-02_arranque/Bugs/`.

**La tercera fuente llegó en la Fase 3**, y de regalo: las páginas de melate-e.com publican también
los números sorteados. Comparados con el CSV oficial en 200 sorteos, **0 discrepancias**. Es
exactamente el tipo de comprobación que habría atrapado el error de Revancha 3827 el primer día.

Con ese sitio, que es privado y pequeño, el trato se escribió **antes** del código que lo usa: una
solicitud por segundo, caché permanente, `User-Agent` que nos identifica y enlaza este repositorio,
sin suplantar ningún navegador, y si bloquean se para y se pregunta. Está en
`Documentos_Contexto/Fases/2026-10-03_popularidad/Decisiones/`, y cada regla tiene su test. La
diferencia entre una herramienta personal y un raspador no está en la tecnología —es el mismo GET—
sino en el límite que se pone antes de empezar.

## Reproducibilidad

Una cifra sin su procedencia no es un resultado, es una anécdota. Cada corrida registra el SHA-256 de
los tres CSV de entrada, las tres semillas, el número de simulaciones y las versiones de Python,
numpy, pandas, scipy y scikit-learn. Los snapshots se congelan por fecha y no se vuelven a tocar:
los CSV crecen con cada sorteo, así que sin snapshot ninguna cifra publicada se puede volver a
comprobar.

Las cifras de arriba salen de `data/raw/2026-10-02/` con Python 3.13.9, numpy 2.5.3, pandas 2.3.3,
scipy 1.18.1 y scikit-learn 1.9.1. Las versiones exactas están en `entorno/`.

## Documentación

`Documentos_Contexto/` es la bitácora del proyecto: qué se decidió, por qué, qué se verificó y cómo
volver atrás. Empieza por `Documentos_Contexto/_MAPA.md`, que son rutas de lectura y no un listado.
En la mayoría de proyectos esta carpeta no se publica; aquí sí, a propósito, y
`REGLAS-DOCUMENTACION.md` explica las reglas que eso impone.

## Licencia

Apache-2.0. Ver [LICENSE](LICENSE).

---

*Herramienta personal de análisis. No es consejo financiero ni de juego. El valor esperado de los
tres juegos es negativo: jugar cuesta dinero, en promedio, y este repositorio existe en parte para
medir exactamente cuánto.*
