# El mapa tras la Fase 3: entra la otra mitad del problema

- **Fecha/hora:** 2026-10-03 05-15
- **Área:** Mapa · **Acción:** Modificar

## Qué cambió en el mapa

Hasta la Fase 2 todos los módulos miraban **a la urna**: si es justa (`audit`), si algo la predice
(`backtest`, `lab`), si el dato es el que dice ser (`ingest`, `validate`). La Fase 3 añade los dos
primeros que miran **a los jugadores**.

| Módulo | Qué pregunta responde | Mira a |
|---|---|---|
| `ingest.py` | ¿De dónde salen los datos y son los que dicen ser? | el dato |
| `validate.py` | ¿Cumplen las 7 reglas del contrato? | el dato |
| `audit.py` | ¿Es justa la urna? | la urna |
| `backtest.py` | ¿Alguna estrategia bate al azar? *(exploratorio)* | la urna |
| `lab.py` | ¿Puedo **afirmar** que alguna lo hace? *(el único que juzga)* | la urna |
| `ev.py` | ¿Cuánto vale un boleto? | el dinero |
| **`popularity.py`** | **¿Qué juega la gente, y cuánto se paga de verdad?** | **los jugadores** |
| **`portfolio.py`** | **¿Qué boletos compro con este presupuesto?** | **los jugadores** |

## La frontera que esto introduce, y que importa más que los módulos

El mapa ya tenía una frontera —`Mapa/Modificar/2026-10-03_01-30_s2-entra-el-laboratorio.md`: entre
**explorar** y **juzgar**. La Fase 3 añade otra, perpendicular:

> **Entre lo que dice de la urna y lo que dice de los jugadores.**

No es una distinción de estilo. Decide si una prueba estadística entra en la familia de
Benjamini-Hochberg, y la respuesta está en
`Protocolo_Estadistico/Decisiones/2026-10-03_05-10_s3-la-popularidad-no-entra-en-la-familia.md`:
**el sorteo no sabe qué apostó nadie**, así que ninguna medición de popularidad puede convertirse
en una afirmación sobre qué va a salir, y por tanto no puede inflar el riesgo de declarar una
ventaja falsa. La familia sigue siendo de 36.

## Lo que `popularity.py` descubrió, y que cambia cómo se lee `ev.py`

El `menores_brutos` que `ev.valor_esperado` lleva escrito a mano **no es un detalle**: es
**el 65,5 % del valor esperado de un boleto de Melate**.

| Juego | Término de bolsa | Término de menores | % del EV que son menores |
|---|---|---|---|
| Melate | 2,14 | 4,07 | **65,5 %** |
| Revancha | 3,14 | 1,95 | 38,3 % |
| Revanchita | 4,38 | 0 | **0 %** |

Quien mirara `ev.py` pensando que el EV de Melate lo gobierna la bolsa estaría mirando a un tercio
del problema. Y la constante que gobierna los otros dos tercios era la que caducaba.

## Lo que `portfolio.py` NO es, medido

La cartera no mejora las probabilidades de ganar. Lo único que puede hacer es que, si ganaras,
repartieras con menos gente. Tiene un techo, y está medido:

| Juego | Techo de evitar compartir | Suelo de una combinación muy jugada |
|---|---|---|
| Melate | **+0,27 %** del precio | −14,3 % |
| Revancha | +0,58 % | −31,4 % |
| Revanchita | **+1,63 %** | −87,6 % |

**La asimetría es de 54 a 1.** Por eso el módulo está escrito como un seguro y no como una
estrategia: su trabajo es que no juegues 1-2-3-4-5-6, no hacerte ganar.

Revanchita es donde más importa, y por dos razones estructurales: solo paga 6 aciertos, así que
**todo** su valor está en la bolsa compartible, y su EV es el menos malo de los tres (−12 %).

## El camino de usuario completo, hoy

```powershell
# 1. Qué juega la gente (sale a la red la primera vez, a 1 solicitud/segundo)
.venv\Scripts\python.exe -m melate.popularity --desde 4173 --hasta 4272 `
    --datos data\raw\2026-10-02 --salida reportes\popularidad.json

# 2. El informe, ahora con el EV de premios menores MEDIDO
.venv\Scripts\python.exe -m melate.informe --datos data\raw\2026-10-02 `
    --popularidad reportes\popularidad.json

# 3. Una cartera con presupuesto fijo
.venv\Scripts\python.exe -m melate.portfolio --juego Melate --presupuesto 300 `
    --bolsa 76200000 --popularidad reportes\popularidad.json

# 4. Y lo único que puede AFIRMAR algo, que sigue diciendo que no
.venv\Scripts\python.exe -m melate.lab --prereg prereg\2026-10-03_logistica-revancha.json
```

El paso 4 sigue devolviendo `sin ventaja demostrada`, 0 de 5 condiciones. Los pasos 1 a 3 no lo
cambian ni pueden cambiarlo: **ninguno habla de la urna.**

## Cómo verificar

```powershell
.venv\Scripts\python.exe -m pytest tests -q          # 161 pruebas, 133 s
.venv\Scripts\python.exe -m pytest tests -q -m "not lento and not red"   # 132, 5 s
```

## Cómo revertir

Borrar `src/melate/popularity.py`, `src/melate/portfolio.py`, sus dos ficheros de test, la clave
`"valor_esperado_medido"` de `NUEVAS_CLAVES` en `src/melate/informe.py` y la función
`_valor_esperado_medido` con sus tres usos. La paridad con el oráculo no depende de nada de esto.

Relacionado: `Mapa/Añadir/2026-10-03_00-13_s1-mapa-del-sistema.md`,
`Mapa/Modificar/2026-10-03_01-30_s2-entra-el-laboratorio.md`,
`Protocolo_Estadistico/Decisiones/2026-10-03_05-10_s3-la-popularidad-no-entra-en-la-familia.md`,
`Fases/2026-10-03_popularidad/00_ALCANCE.md`.
