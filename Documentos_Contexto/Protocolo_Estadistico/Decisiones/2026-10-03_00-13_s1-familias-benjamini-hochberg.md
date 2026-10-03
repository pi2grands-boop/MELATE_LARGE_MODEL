# Decisión: dos familias de Benjamini-Hochberg más la global, y manda la global

- **Fecha/hora:** 2026-10-03 00:13
- **Área:** Protocolo_Estadistico · **Acción:** Decisiones
- **Decidido por:** usuario · **Estado:** cerrada
- **Alcance:** `src/melate/protocolo.py`, la clave `q_BH_global` del reporte, y cualquier declaración
  futura de ventaja

## La decisión

Conservar las dos familias de Benjamini-Hochberg que produce el oráculo, **añadir** la familia global
de 36 pruebas, y **para declarar ventaja manda la global**.

## El problema

La regla 3 del protocolo del `CLAUDE.md` dice: *"Benjamini-Hochberg sobre TODAS las pruebas corridas,
también las que no se reportan."*

`baseline_auditoria.py` no hace eso. Lo aplica en **dos familias separadas**:

- 15 pruebas de auditoría (3 juegos × 5 estadísticos), en las líneas 134-137.
- 21 pruebas de backtest (3 juegos × 7 estrategias), en las líneas 293-296. La estrategia aleatoria
  no cuenta: es la referencia contra la que se compara, no una hipótesis.

Corregir 36 pruebas en una familia es **más estricto** que corregir 15 y 21 por separado. Con las
familias partidas, una prueba puede pasar un umbral que no habría pasado en la familia completa, y
eso es exactamente lo que la regla 3 quiere evitar.

## Alternativas descartadas

| Opción | Por qué no |
|---|---|
| Cambiar a familia global y punto | Los `q` publicados en el `CLAUDE.md` salen de las dos familias. Sustituirlos sin más haría irreproducible la línea base y obligaría a corregir el documento por una razón distinta de la del error de datos, mezclando dos cambios en uno |
| Dejar las dos familias, sin más | Incumple la regla 3, que es no negociable, y deja el proyecto con un criterio más laxo que el que él mismo se impuso |
| Renombrar `q_BH` a `q_BH_familia` y añadir `q_BH_global` | Rompería la paridad con el oráculo y, peor, haría irreproducibles los `q` ya publicados. Una clave de reporte publicada es una interfaz |

## Consecuencias

- `protocolo.py` es el dueño único de la corrección. `benjamini_hochberg` estaba duplicada de hecho
  entre auditoría y backtest.
- `aplicar_familias()` escribe `q_BH` — idéntica a la del oráculo, con las dos familias.
- `aplicar_global()` escribe `q_BH_global` y devuelve `protocolo_global`, con el tamaño de la familia,
  la q mínima, la lista de pruebas que sobreviven a q ≤ 0.05 y el veredicto en texto.
- `q_BH` **no se renombra nunca.** Es lo que produce las cifras publicadas.
- **Las dos coexisten en el reporte a propósito**, y conviene que se vean juntas: enseñan cuánto
  cambia una conclusión según cómo se cuente la familia, que es la lección estadística central de
  este proyecto.

### Qué sale con los datos del sorteo 4272

| | Dos familias (`q_BH`) | Global de 36 (`q_BH_global`) |
|---|---|---|
| Regresión logística en Revancha | 0.3465 | **0.306** |
| q mínima de las 36 pruebas | — | **0.306** |
| Pruebas que sobreviven a q ≤ 0.05 | ninguna | **ninguna** |

El veredicto es **sin ventaja demostrada** con cualquiera de los dos criterios, así que esta decisión
no cambia ninguna conclusión hoy. Importa para el día en que algo parezca funcionar: ese día, el
número que manda ya está decidido de antemano, y no se elige a posteriori el que más convenga. Es
justo lo que una corrección por comparaciones múltiples debe impedir.

Curiosidad instructiva: la q global de esa prueba (0.306) es **menor** que su q de familia (0.3465).
Benjamini-Hochberg no garantiza una desigualdad prueba a prueba —depende de la distribución completa
de p-valores—, así que la familia global no es uniformemente más severa en cada celda. Lo que sí
controla, y es lo que importa, es la **proporción de falsos descubrimientos del conjunto**.

## Premisas que esta decisión invalida

Ninguna. Es la primera decisión de protocolo del proyecto.

Sí deja una premisa escrita para la Fase 2: `lab.py::declara_ventaja()` tendrá que leer
`q_BH_global`, no `q_BH`, al evaluar la condición "q ≤ 0.05" de la regla 5. Vivirá en este mismo
módulo.

## Cuándo reabrirla

- Si se añaden estrategias o estadísticos: la familia global crece y hay que recalcularla entera,
  nunca añadir la prueba nueva a una familia pequeña.
- Si llega el preregistro de la Fase 2. Una prueba preregistrada tiene un papel distinto de una
  exploratoria, y puede justificar una familia aparte **declarada por adelantado** — nunca elegida
  después de ver los resultados.

## Cómo verificar

```powershell
.venv\Scripts\python.exe -m pytest tests\test_paridad.py -k global -v
.venv\Scripts\python.exe -m pytest tests\test_linea_base.py -k bate_al_azar -v
```

Hay tests que exigen que la familia global tenga exactamente 15 + 21 = 36 pruebas, que no sobreviva
ninguna a q ≤ 0.05, y que `q_BH` siga llamándose `q_BH`.

Relacionado: `Reproducibilidad/Añadir/2026-10-03_00-13_s1-linea-base-reproducida.md`,
`Fases/2026-10-02_arranque/Cambios/2026-10-03_00-03_s1-paquete-src-melate.md`,
`Mapa/Añadir/2026-10-03_00-13_s1-mapa-del-sistema.md`
