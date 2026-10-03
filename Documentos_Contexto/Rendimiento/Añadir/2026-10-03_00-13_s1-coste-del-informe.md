# Cuánto tarda el informe, dónde se va el tiempo, y cómo crecerá

- **Fecha/hora:** 2026-10-03 00:13
- **Área:** Rendimiento · **Acción:** Añadir
- **Chat / página:** sesión de arranque · emitido al cerrar la Fase 1
- **Archivos afectados:** `src/melate/backtest.py`, `src/melate/audit.py`, `pyproject.toml`

## Qué se hizo

Medir, etapa por etapa, en lugar de estimar. Snapshot del 4272, 2 000 simulaciones, Intel i7-13620H
con 16 núcleos lógicos, Python 3.13.9.

| Etapa | Tiempo | % |
|---|---|---|
| Import de las librerías | 1.21 s | — |
| Carga de los 3 CSV | 0.10 s | 0 % |
| Validación (cruda + era) | 0.08 s | 0 % |
| **Auditoría Monte Carlo (3 juegos × 2 000 sims)** | **10.77 s** | **15 %** |
| Poder estadístico | 0.08 s | 0 % |
| **Backtest Melate** (2 184 sorteos) | **21.13 s** | |
| **Backtest Revancha** (2 184 sorteos) | **24.17 s** | |
| **Backtest Revanchita** (1 902 sorteos) | **16.24 s** | |
| **Backtest, los tres** | **61.53 s** | **85 %** |
| Premios mayores + valor esperado | 0.02 s | 0 % |
| **TOTAL sin imports** | **72.58 s** | |

**Pico de memoria de Python: 61 MB.** Irrelevante, y conviene dejarlo escrito para que nadie
intente optimizar por ahí.

El reparto es contundente: **el backtest es el 85 % del coste y todo lo que no es backtest ni
auditoría es cero.** Cualquier trabajo de rendimiento que no toque el backtest es tiempo perdido.

### Y la suite de tests

| Qué | Tiempo |
|---|---|
| `pytest tests -m "not lento and not red"` (31 pruebas) | **2.4 s** |
| `pytest tests` (52 pruebas) | **~105 s** |

Los 105 s son casi todo el oráculo y el paquete corriendo una vez cada uno: las fixtures son de
alcance `session` precisamente para que sea **una** vez y no una por test. Esa separación por
*markers* es lo que mantiene usable el ciclo del día a día; una suite de dos minutos deja de
ejecutarse, y una suite que no se ejecuta no protege nada.

## Cómo crecerá, y esto es lo que importa

El backtest **no crece linealmente con los sorteos.** El bucle recorre T−400 sorteos, y en cada
iteración recalcula la matriz de transición desde cero:

```python
trans = X[:t - 1].astype(float).T @ X[1:t].astype(float) + 1.0
```

Eso es O(t · 56²) por iteración, así que el total es **cuadrático en T**. A tres sorteos por semana
(unos 156 al año):

| Momento | Sorteos de Melate | Backtest de los 3, estimado |
|---|---|---|
| Hoy (4272) | 2 184 | 62 s (medido) |
| +2 años | ~2 500 | ~80 s |
| +5 años | ~2 960 | ~110 s |
| +10 años | ~3 740 | ~175 s |

Son proyecciones del término cuadrático, no mediciones. Lo accionable: **a este ritmo no hay
problema en años**, así que no hay nada que optimizar todavía.

### La optimización obvia, y por qué NO se hizo

La matriz de transición se puede actualizar de forma incremental —sumar el par (t−2, t−1) a la
matriz anterior— en vez de recalcularla entera. Daría resultados idénticos y convertiría el
cuadrático en lineal. **No se hizo, a propósito**, por dos razones:

1. **La paridad primero.** Esta fase existe para demostrar que el paquete reproduce el oráculo cifra
   por cifra. Meter una optimización en el mismo movimiento contamina ese control: si algo hubiera
   fallado, no se sabría si fue el traslado o la optimización.
2. **No hace falta.** 62 s hoy y ~110 s en cinco años no molestan a nadie. Optimizar algo que no
   duele es cómo se introducen fallos a cambio de nada.

Cuando toque, hay que hacerlo **con el test de paridad delante**: es un cambio que debe dar el mismo
JSON, bit a bit, y si no lo da es que está mal.

### Dónde NO está el problema

- **Las 2 000 simulaciones de la auditoría** cuestan 10.77 s y escalan linealmente con `--sims`. Hay
  un parámetro para bajarlas si alguna vez molesta.
- **La carga, la validación y el valor esperado** suman 0.2 s entre las tres. Cero.
- **La memoria.** 61 MB de pico.
- **El reentrenamiento** de los modelos ocurre cada 100 sorteos, no en cada iteración: unas 18 veces
  por juego. No es el cuello de botella.

## Por qué

El `backtest` de los tres juegos ronda el minuto y crecerá con cada sorteo. Sin una medición de
partida, cualquier discusión futura sobre si el proyecto "se ha vuelto lento" sería una impresión, y
cualquier optimización sería a ciegas. Esta es la línea base contra la que comparar.

## Observación aceptada (no es bug)

La primera corrida del oráculo tardó **84.5 s** y la del paquete **30.7 s**, haciendo el mismo
trabajo. No es que el paquete sea tres veces más rápido: la del oráculo fue la primera ejecución de
pandas y scikit-learn en un entorno recién instalado, con los `.pyd` fuera de la caché de ficheros
del sistema. Medidas en frío y en caliente no se comparan, y la medición de arriba es toda en
caliente. Queda registrado para que nadie lea una mejora que no existe.

## Impacto en seguridad / conexiones / datos

Sin impacto. Esta medición no cambió una línea de código.

## Cómo verificar / revertir

```powershell
# el total, de punta a punta
Measure-Command { .venv\Scripts\python.exe -m melate.informe --datos .\data\raw\2026-10-02 --salida .\reportes\x.json }

# la suite rapida, que es la que se corre a diario
Measure-Command { .venv\Scripts\python.exe -m pytest tests -m "not lento and not red" -q }

# bajar las simulaciones si la auditoria molesta
.venv\Scripts\python.exe -m melate.informe --datos .\data\raw\2026-10-02 --sims 200 --salida .\reportes\rapido.json
```

**Revertir:** no aplica. No hay cambio que deshacer.

Relacionado: `Mapa/Añadir/2026-10-03_00-13_s1-mapa-del-sistema.md`,
`Fases/2026-10-02_arranque/Cambios/2026-10-03_00-03_s1-tests.md`
