# Estado heredado: dos ficheros, cero infraestructura

- **Fecha/hora:** 2026-10-02 22:07
- **Área:** Fases/2026-10-02_arranque · **Acción:** Inventario
- **Chat / página:** sesión de arranque · todo el proyecto
- **Archivos afectados:** `CLAUDE.md`, `baseline_auditoria.py` (ninguno se modifica en este documento)

Este documento se escribe **antes** de crear el entorno, el snapshot o el paquete. Es la única
excepción al pipeline del `REGLAS-DOCUMENTACION.md`: el estado de partida, después, ya no se puede
reconstruir.

## Qué se hizo

Nada. Se leyó. Este documento solo registra lo que había.

### El contenido de la carpeta, completo

```
CLAUDE.md               5 651 bytes   el contrato del proyecto
baseline_auditoria.py  17 060 bytes   322 líneas, la línea base probada
```

No hay nada más: ni `src/`, ni `tests/`, ni `data/`, ni `prereg/`, ni `requirements.txt`, ni bitácora,
ni repositorio local de git.

### `baseline_auditoria.py`, función por función

Un solo fichero con 6 etapas. Esta tabla es el mapa del traslado al paquete.

| Líneas | Función | Qué hace |
|---|---|---|
| 29-36 | *(constantes)* | `N=56`, `K=6`, `C=comb(56,6)`, las dos URL plantilla, `JUEGOS`, `PRIMER_SORTEO_56=2089`, `PRECIO`, `BOLSA_MINIMA` |
| 39-53 | `_leer_texto` | Lee de carpeta local, o descarga con *fallback* oficial → espejo. Acepta la respuesta solo si `"CONCURSO"` aparece en los primeros 200 caracteres |
| 55-69 | `cargar` | Normaliza columnas a mayúsculas, elige `R1..R6` o `F1..F6`, parsea la fecha, ordena por `CONCURSO`, construye `nums`, rellena `R7` con `NaN` si no existe, guarda la fuente en `df.attrs` |
| 72-85 | `validar` | 9 comprobaciones: faltantes, duplicados, fuera de rango, filas no ordenadas, adicional repetido, huecos de más de 10 días, `BOLSA` inválida |
| 87-90 | `era_56` | Filtra `CONCURSO >= 2089` y asegura que el máximo no pasa de 56 |
| 92-96 | `matriz` | Convierte la lista de sorteos en una matriz indicadora `T × 56` de `int8` |
| 99-108 | `estadisticas` | 5 estadísticos: chi-cuadrada corregida por extracción sin reemplazo, máximo, mínimo, par más frecuente, solapamiento medio entre sorteos consecutivos |
| 110-115 | `simular` | Genera `n` sorteos uniformes de 6 de 56 con `argpartition` |
| 117-138 | `auditar` | Monte Carlo: compara los 5 estadísticos observados contra `nsim` simulaciones, p de dos colas, y aplica Benjamini-Hochberg sobre las 15 pruebas (3 juegos × 5 estadísticos) |
| 140-144 | `benjamini_hochberg` | Corrección por comparaciones múltiples, versión monótona descendente |
| 147-157 | `n_necesario`, `sesgo_minimo` | Poder estadístico: qué sesgo por esfera se podría detectar con los sorteos disponibles |
| 160-162 | *(constantes de azar)* | `MEDIA_AZAR = 36/56`, `VAR_AZAR`, `P_3_O_MAS` |
| 164-179 | `variables` | 7 variables por número: frecuencia en ventanas de 10, 25, 50 y 100 sorteos, frecuencia histórica, atraso normalizado y si salió en el sorteo anterior |
| 181-182 | `top6` | Los 6 mayores de un vector de puntuación, con desempate aleatorio de magnitud `1e-9` |
| 184-237 | `backtest` | Walk-forward desde el índice 400, reentrenando cada 100 sorteos, 8 estrategias, aciertos y log-loss, z y p contra el azar |
| 240-249 | `premios_mayores` | Una baja de `BOLSA` es un premio mayor ganado; excluye el error "baja seguida de un valor mayor que el anterior" |
| 251-262 | `valor_esperado` | EV del próximo sorteo con corrección por bolsa compartida, impuesto, y bolsa de equilibrio |
| 265-319 | `main` | Orquesta todo, imprime el resumen y escribe el JSON |

### Las cifras que el `CLAUDE.md` declara verificadas

Son el objetivo del portón de esta fase. Datos al sorteo 4272, semilla 20261001, 2 000 simulaciones:

| Qué | Melate | Revancha | Revanchita |
|---|---|---|---|
| Sorteos era 6/56 | 2 184 | 2 184 | 1 902 |
| Chi-cuadrada corregida | 52.19 (p = 0.85) | 42.03 (p = 0.21) | 54.83 (p = 0.98) |
| Premios mayores (bajas de `BOLSA`) | 69 | 61 | 35 |
| Valor esperado del 4273 | −59 % | −49 % | −12 % |

Backtest, prueba desde el 2489 (Revanchita desde el 2771), reentrenando cada 100 sorteos: regresión
logística en Revancha 0.6861 aciertos (p = 0.011, q = 0.24); gradient boosting en Melate 0.6160;
aleatorio en Melate 0.6328.

Línea base del azar: 36/56 = 0.642857 aciertos por boleto, desviación 0.722357; log-loss 0.340500
nats por número; P(3 o más aciertos) = 1/79.06.

### El entorno real de la máquina

| Qué | Estado |
|---|---|
| Python | **3.13.9** del sistema. El `CLAUDE.md` pide 3.11+ |
| Instalado | `numpy` 2.3.5, `requests` 2.32.5, `torch` 2.9.1, `torchaudio` 2.9.1 |
| **Falta** | **`pandas`, `scipy`, `scikit-learn`, `pytest`** |
| git | 2.45.1 |
| `gh` (CLI de GitHub) | **no instalado** |
| Identidad git global | nombre `pi2grands-boop`, correo personal — se sobrescribe por repositorio antes del primer commit |

**Consecuencia:** `baseline_auditoria.py` **no puede ejecutarse** en el estado heredado.
"Reprodúcela antes de cambiar nada" era, al empezar, imposible.

### El repositorio remoto, antes de tocarlo

`pi2grands-boop/MELATE_LARGE_MODEL`, público, rama por defecto `main`, un commit `42700884`
("Initial commit") que contiene **solo** `LICENSE` (Apache-2.0). Sin `.gitignore`, sin `README.md`.

La descripción del repositorio, tal cual estaba: *"A LOCAL BASED MACHINE ABLE TO 'PREDICT' WITH MORE
ACCURACY THE RESULTS OF THE 'MELATE REVANCHA REVANCHITA' FROM MEXICO."* Contradice la regla del
`CLAUDE.md` de que toda salida diga "sin ventaja demostrada" y que nunca se hable de números más
probables, y la contradice la propia línea base: ninguna estrategia bate al azar. Queda anotado aquí
como estado de partida; el cambio, si se hace, es decisión del usuario.

### Evidencia de datos, comprobada contra las fuentes oficiales

Comprobado el 2026-10-02 con peticiones HTTP directas a `loterianacional.gob.mx`, sin pandas,
**antes** de confiar en ninguna cifra del contrato:

| Comprobación | Resultado | Regla del `CLAUDE.md` |
|---|---|---|
| Filas totales | Melate 4 272 (concursos 1-4272) · Revancha 3 264 (1009-4272) · Revanchita 1 902 (2371-4272) | — |
| Era 6/56 | Melate 2 184 · Revancha 2 184 · Revanchita 1 902 | **Regla 1 ✅** y coincide con el contrato |
| Concursos faltantes | 0 en los tres ficheros | **Regla 7 ✅** |
| Duplicados | 0 en los tres ficheros | **Regla 7 ✅** |
| `BOLSA` < 1 M en la era 6/56 | Exactamente `{2120, 2142, 2234}` en Melate y en Revancha; ninguna en Revanchita | **Regla 4 ✅** |
| Revancha 3221 | 238.6 M entre 280.3 M (3220) y 286.4 M (3222) | **Regla 4 ✅** — es el patrón exacto que el filtro de `premios_mayores` descarta |
| Hueco de pandemia | 3373 = 2020-04-01 → 3374 = 2020-07-26, 116 días, concursos consecutivos | **Regla 5 ✅** |
| Última fila | Concurso 4272, 2026-09-30. Bolsas anunciadas: Melate 76.2 M · Revancha 111.7 M · Revanchita 155.8 M | **Regla 2** — son las bolsas del 4273 |

Dos hallazgos sobre el formato que el contrato no menciona y que condicionan el código:

- **El CSV oficial llega en orden descendente**: la primera fila de datos es el concurso 4272.
  `cargar` lo resuelve con `sort_values("CONCURSO")` en la línea 63. La detección de formato de fecha
  de la línea 62 mira `iloc[0]` *antes* de ordenar, pero funciona igual porque solo distingue
  `dd/mm/aaaa` de `aaaa-mm-dd` por la presencia de `/`.
- **El espejo de GitHub tiene columnas extra** (`PRIMOS`, `REPETIDOS`, `MEDIA`), así que la `BOLSA` no
  está en la misma posición que en el oficial. Cualquier parseo por posición se rompe con el espejo;
  `cargar` indexa por nombre de columna, que es lo correcto. Se comprobó en carne propia durante esta
  auditoría: un parseo posicional leyó `REPETIDOS` como `BOLSA`.

### Los dos puntos donde el orden de consumo del RNG fija los resultados

Esto es lo que puede romper la paridad del refactor en silencio, sin error ni aviso:

1. **`auditar` comparte un único `rng` entre los tres juegos**, secuencialmente, en el orden de
   `JUEGOS` (línea 119). Cambiar el orden de iteración, o paralelizar los juegos, cambia **todos** los
   p-valores de la auditoría.
2. **`backtest` crea su propio `trng = default_rng(7)` por juego** (línea 189), así que entre juegos
   es independiente. Pero dentro del bucle, el orden de las 8 asignaciones del diccionario `elec`
   (líneas 205-215) fija el consumo: `trng.choice` primero, y después cada `top6` consume
   `rng.random(56)`. Reordenar el diccionario cambia los resultados de todas las estrategias que
   vienen después del cambio.

### Ausencia de fuga temporal, verificada por lectura

El protocolo del `CLAUDE.md` exige walk-forward estricto. Se leyeron las tres piezas que podrían
filtrar el futuro y las tres están limpias en el estado heredado:

- **`variables` (164-179).** `cs` lleva una fila de ceros al principio, así que `cs[t]` es la suma de
  `X[0..t-1]`: todas las ventanas usan solo el pasado. `atraso[t]` se calcula antes de actualizar
  `ultimo` con `X[t]`. La variable 6 es `X[t-1]`.
- **Entrenamiento (200-201).** `filas = range(100, t)`, estrictamente anterior a `t`.
- **Markov (210).** `X[:t-1].T @ X[1:t]` usa pares de sorteos consecutivos hasta `t-1`.

Esto no es un certificado permanente: es el estado de partida. El test de no-fuga de esta fase existe
para que siga siendo verdad.

### Los dos huecos frente al protocolo del propio contrato

| Regla del `CLAUDE.md` | Lo que hace el código heredado |
|---|---|
| **Regla 6** — "guardar el hash del dataset y la semilla en cada corrida" | No guarda ninguno de los dos. Usa `default_rng(20261001)` (línea 271), `default_rng(7)` (189) y `random_state=0` (203), y ninguno aparece en el JSON de salida |
| **Regla 3** — "Benjamini-Hochberg sobre TODAS las pruebas corridas, también las que no se reportan" | Lo aplica en **dos familias separadas**: 15 pruebas de auditoría (134-137) y 21 de backtest (293-296). No hay familia global de 36 |

### Un tercer detalle, menor pero ruidoso

`validar` corre sobre el fichero crudo, no sobre la era 6/56. En Melate eso significa incluir
1984-2007, donde las bolsas eran mucho menores: el informe reporta **174 filas con `BOLSA` < 1 M**,
de las que solo 3 son errores reales. El dato correcto queda sepultado en el ruido.

## Por qué

El `CLAUDE.md` ordena reproducir la línea base antes de cambiar nada, y la skill de documentación
obliga a escribir el inventario antes de tocar el estado heredado. Sin este documento, en cuanto se
cree el `.venv` y se instalen las dependencias ya no se podrá decir con certeza qué había al empezar
ni, por tanto, qué cambió por culpa de qué.

## Impacto en seguridad / conexiones / datos

- **Seguridad:** sin impacto — no se ha ejecutado ni modificado nada. Se registra que el proyecto no
  tiene secretos: ambas fuentes son HTTP GET público sin autenticación, y no hay `.env` ni
  credenciales de ninguna clase.
- **Conexiones:** sin impacto. Se documentan las que el código heredado ya tenía: dos plantillas de
  URL con *fallback* oficial → espejo.
- **Datos:** sin impacto. Las lecturas de esta auditoría fueron peticiones HTTP de solo lectura; no
  se escribió ningún fichero de datos.

## Cómo verificar / revertir

**Verificar** que este inventario describe el estado real de partida, mientras no se haya tocado
nada:

```powershell
Get-ChildItem -Force | Select-Object Name, Length          # -> solo CLAUDE.md y baseline_auditoria.py
(Get-Content baseline_auditoria.py | Measure-Object -Line).Lines   # -> 322
python -m pip list | Select-String 'pandas|scipy|scikit'   # -> sin salida
```

Y que las cifras de datos siguen cuadrando — ojo, **crecerán con cada sorteo nuevo**, así que a
partir del 4273 esta comprobación hay que hacerla contra el snapshot congelado, no contra la
descarga en vivo.

**Revertir:** no aplica. Este documento no cambió nada. Si hubiera que deshacer la fase entera:
borrar `Documentos_Contexto/`, `REGLAS-DOCUMENTACION.md`, y lo que las secciones siguientes creen —
cada una deja su propio "cómo revertir".

Relacionado: `Fases/2026-10-02_arranque/00_ALCANCE.md`
