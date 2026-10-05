# El primer veredicto con holdout: un sorteo, y lo que significa

- **Fecha/hora:** 2026-10-05 10:26
- **Área:** Protocolo_Estadistico · **Acción:** Añadir
- **Chat / página:** cierre de la Fase 5 · `Fases/2026-10-04_ciclo-vivo/`
- **Archivos afectados:** `reportes/2026-10-04_4274_veredicto-2026-10-03_logistica-revancha.json`,
  `data/raw/2026-10-04_4274/`

## Qué hay

El preregistro `prereg/2026-10-03_logistica-revancha.json` se selló el 2026-10-03 a las 06:45 UTC: la
regresión logística sobre 7 variables de frecuencia y atraso bate al azar en Revancha. Su holdout son
los sorteos posteriores al sello. **El primero es el 4274, del 2026-10-04**, y el ciclo lo juzgó el
2026-10-05 a las 14:22 UTC sobre el snapshot `data/raw/2026-10-04_4274/`.

**Veredicto: *sin ventaja demostrada*, 2 de 5 condiciones.**

| Juego | Aciertos de 6 | Δ sobre el azar (0,6429) |
|---|---|---|
| Melate | 0 | −0,6429 |
| **Revancha** | **1** | **+0,3571** |
| Revanchita | 0 | −0,6429 |

| # | Condición | ¿Cumple? | Por qué |
|---|---|---|---|
| 1 | holdout futuro positivo | sí | +0,3571 aciertos en 1 sorteo |
| 2 | q ≤ 0,05 | NO | q = 1,0000 |
| 3 | estable al mover hiperparámetros | sí | 4 variantes, mismo signo, desvío 0 % |
| 4 | mismo signo en los tres juegos | NO | Melate y Revanchita, negativos |
| 5 | efecto ≥ mínimo detectable | NO | con 1 sorteo, el mínimo detectable es 2,023745 aciertos; el sello declaró 0,048, y hacen falta **1 778 sorteos** (faltan 1 777) |

## Lo que significa

**Nada, y es lo correcto.** Un sorteo es un dato: con él, la diferencia más pequeña que se distingue
del azar es de dos aciertos por boleto, y lo que se busca es un efecto de 0,048. Que la logística
acertara uno en Revancha y ninguno en los otros dos juegos es exactamente lo que se espera del azar.

Las dos condiciones que «cumple» no dicen nada a favor: con un sorteo, el delta es positivo siempre
que el boleto acierte al menos un número, y eso le pasa al azar el 51 % de las veces; y la estabilidad
dice que las variantes con otros hiperparámetros dan el mismo delta, no que ese delta sea bueno.

## Lo que no significa

- **Que la estrategia funcione un poco.** Con un sorteo no hay «un poco»: el veredicto no se acerca
  ni se aleja de nada.
- **Que la condición 5 falle por mala suerte.** Falla **por construcción** hasta el sorteo 1 778 del
  holdout, desde la decisión del 2026-10-04
  (`Protocolo_Estadistico/Decisiones/2026-10-04_18-58_s5-la-condicion-5-exige-un-holdout-capaz.md`).
  Antes de ella, un sorteo con tres aciertos en Revancha y alguno en los otros dos juegos daba VENTAJA
  DEMOSTRADA, 5 de 5: le pasó al laboratorio real en cuatro sorteos históricos.

## Lo que viene

Cada sorteo nuevo que incorpore el ciclo deja otro veredicto, sobre su snapshot. **El vigente es el
que juzgó con más datos**, y la app lo enseña en todas sus pantallas con «holdout de N sorteos de los
1 778 que necesita la condición 5». La condición 5 puede cumplirse por primera vez dentro de 11,4 años
a tres sorteos por semana, o de 15,3 a la media histórica de 116 sorteos al año. Hasta entonces, el
veredicto del proyecto es *sin ventaja demostrada* pase lo que pase.

## Cómo verificar

```powershell
# Reproducirlo sobre los mismos bytes: «sin ventaja demostrada», 2 de 5
.venv\Scripts\python.exe -m melate.lab --prereg prereg/2026-10-03_logistica-revancha.json `
    --datos data\raw\2026-10-04_4274 --salida $env:TEMP\veredicto.json
.venv\Scripts\python.exe -m melate.app       # la cabecera lo dice en cada pantalla
```

Reproducido a mano al cerrar la fase: el mismo veredicto, campo por campo, salvo la hora de la corrida.

## Cómo revertir

Es un resultado publicado: no se revierte. Si el snapshot o el preregistro se alteraran, la base lo
dejaría de dar por válido.

Relacionado: `Protocolo_Estadistico/Añadir/2026-10-03_01-30_s2-preregistro-y-las-cinco-condiciones.md`,
`Protocolo_Estadistico/Modificar/2026-10-05_10-15_s5-la-condicion-5-en-el-codigo.md`,
`Protocolo_Estadistico/Decisiones/2026-10-04_18-58_s5-la-condicion-5-exige-un-holdout-capaz.md`,
`Fases/2026-10-04_ciclo-vivo/Bugs/2026-10-04_20-51_s5-review-ciclo.md`.
