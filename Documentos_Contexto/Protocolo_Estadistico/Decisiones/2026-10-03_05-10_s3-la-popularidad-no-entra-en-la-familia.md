# Por qué medir la popularidad no agranda la familia de Benjamini-Hochberg

- **Fecha/hora:** 2026-10-03 05-10
- **Área:** Protocolo_Estadistico · **Acción:** Decisiones
- **Estado:** cerrada · **Decidida por:** usuario, consultado antes de cerrar la Fase 3

## La pregunta

La Fase 3 corre una prueba estadística nueva: el efecto calendario, que compara cuántos boletos
contienen un número ≤ 31 frente a uno > 31. Sale con **t de Welch = −18.67** sobre 300 sorteos.

La regla 3 del protocolo dice: *"Benjamini-Hochberg sobre TODAS las pruebas corridas, también las
que no se reportan"*. Leída al pie de la letra, esta prueba haría la familia 37 en vez de 36, y
habría que recalcular todas las `q`.

La decisión es que **no entra**. Este documento dice por qué, porque es la clase de frontera que,
si no se escribe, se rediscute cada vez — y cada vez con menos rigor.

## El argumento

La familia de Benjamini-Hochberg no existe para contar pruebas. Existe para controlar **una tasa
de error concreta**: la proporción de hallazgos falsos entre los que se declaran. Y la pregunta
que decide si dos pruebas comparten familia no es "¿se corrieron en el mismo proyecto?" sino
**"¿pueden sustituirse una por otra a la hora de declarar el hallazgo que importa?"**.

El hallazgo que a este proyecto le importa, y el único que el protocolo permite declarar, es que
**una estrategia bate al azar en el sorteo**. Las 36 pruebas de la familia son intercambiables para
eso: 15 buscan sesgos en la urna, 21 buscan estrategias que predicen. Si corres las 36 y reportas
la mejor, inflas el riesgo de declarar una ventaja que no existe. Por eso van juntas.

**La prueba del calendario no puede sustituir a ninguna de las 36**, y la razón no es de grado sino
de categoría:

> **El sorteo no sabe qué apostó nadie.**

Las esferas no consultan la lista de boletos vendidos. La popularidad de un número es una
propiedad de **los jugadores**, no de la urna, y las dos son independientes por construcción
física del juego. De ahí se siguen dos cosas:

1. **Ningún resultado de popularidad puede convertirse en una afirmación sobre qué va a salir.**
   Aunque el efecto calendario saliera con t = −200, eso no diría nada sobre el sorteo siguiente.
   No hay forma de usar esta prueba para declarar una ventaja predictiva, ni siquiera por error.
2. **Por tanto no puede inflar la tasa de hallazgos falsos de la familia.** Meterla dentro no
   protegería de nada: endurecería las 36 pruebas de la urna por haber medido algo que no compite
   con ellas. Eso no es ser conservador, es ser arbitrario — y abre la puerta a la arbitrariedad
   en la otra dirección el día que alguien quiera sacar una prueba de la familia.

Hay además una diferencia de naturaleza que conviene nombrar: el efecto calendario es
**directamente observable y no es una inferencia sobre un proceso aleatorio oculto**. Se mide
contando ganadores reales. Si mañana hubiera datos de ventas por combinación, se sabría sin
ninguna prueba de hipótesis. Las 36 de la familia no son así: no hay forma de "ver" si una
estrategia predice, solo de estimarlo contra el azar.

## Qué sigue valiendo exactamente igual

- **La familia son 36 pruebas** (15 de auditoría + 21 de backtest, la aleatoria es referencia y no
  hipótesis). Sin cambios.
- **`q_BH_global` mínima: 0.306.** Vuelta a medir tras la Fase 3, con el informe completo.
- **El veredicto es `sin ventaja demostrada`**, 0 de 5 condiciones, por holdout vacío.
- **Las 5 condiciones de la regla 5 no se tocan.** La popularidad no participa en ninguna.

## La frontera, en una línea

**Dentro de la familia va todo lo que hable de la urna. Fuera, todo lo que hable de los jugadores.**

Si algún día se quisiera usar la popularidad **para predecir el sorteo** —por ejemplo, suponer que
los números poco jugados "salen más"— eso sería una hipótesis sobre la urna, entraría en la
familia, y haría falta otro documento. No hay nada en el código que apunte en esa dirección y
`src/melate/portfolio.py` dice lo contrario de forma explícita, con un test que lo persigue.

## Qué premisa invalida esto (§7 de las reglas)

**Ninguna.** Se revisaron los documentos que dependen del tamaño de la familia:

| Documento | ¿Sigue válido? |
|---|---|
| `Protocolo_Estadistico/Decisiones/2026-10-03_00-13_s1-familias-benjamini-hochberg.md` | Sí: 36 pruebas, sin cambios |
| `Protocolo_Estadistico/Añadir/2026-10-03_01-30_s2-preregistro-y-las-cinco-condiciones.md` | Sí: la familia declarada en el preregistro no se toca |
| `prereg/2026-10-03_logistica-revancha.json` | Sí, y es lo importante: **un preregistro sellado no se altera**, y este declara una familia de 36 |

Ese último punto es el que cierra el asunto por sí solo: cambiar la familia habría obligado a
tocar un documento sellado, que es justo lo que el proyecto existe para impedir.

## Cómo verificar

```powershell
.venv\Scripts\python.exe -m pytest tests/test_paridad.py -q    # la familia sigue siendo 36
.venv\Scripts\python.exe -m melate.informe --datos data/raw/2026-10-02
```

El informe imprime `Protocolo: 36 pruebas en una sola familia -> SIN VENTAJA DEMOSTRADA (q mínima
0.306)`, y `test_la_familia_global_tiene_36_pruebas` lo fija con 15 + 21 = 36.

## Cómo revertir

Si se decidiera lo contrario: añadir la `p` del efecto calendario a la lista de
`protocolo.aplicar_global`, cambiar el 36 de `tests/test_paridad.py:66`, y **escribir el documento
que explique por qué una prueba sobre los jugadores corrige hipótesis sobre la urna**. El tercer
paso es el difícil, y es intencionado que lo sea.

Relacionado: `Protocolo_Estadistico/Decisiones/2026-10-03_00-13_s1-familias-benjamini-hochberg.md`,
`Fases/2026-10-03_popularidad/Bugs/2026-10-03_04-10_s3-review-popularidad-y-cartera.md`,
`Fases/2026-10-03_popularidad/00_ALCANCE.md`.
