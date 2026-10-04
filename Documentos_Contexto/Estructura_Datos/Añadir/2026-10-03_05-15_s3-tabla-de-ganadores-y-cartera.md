# La forma de una tabla de ganadores, de la popularidad y de una cartera

- **Fecha/hora:** 2026-10-03 05-15
- **Área:** Estructura_Datos · **Acción:** Añadir

## 1 · Una categoría de premio

Lo que `popularity.parsear()` saca de cada fila de la tabla:

```python
{"aciertos": 2, "adicional": False, "ganadores": 115808, "premio": 26.88,
 "favorables": 3178140, "probabilidad": 0.09788...}
```

`favorables` y `probabilidad` se resuelven al parsear, con las fórmulas del `CLAUDE.md`. Las
categorías de cada juego **particionan exactamente** el universo de `C(56,6) = 32.468.436`
combinaciones, y hay un test que lo exige: si no suman, alguna fórmula está mal y todas las
probabilidades derivadas también.

| Juego | Categorías en la página | Con adicional |
|---|---|---|
| Melate | 9 | 4 |
| Revancha | 5 | 0 — no tiene adicional |
| Revanchita | **0** | — solo paga 6 aciertos |

### La trampa del texto, que costó un test

La columna «Aciertos» **no es consistente en el sitio**. En la misma tabla del sorteo 4272 conviven:

```
"5 números naturales + adicional"      (categoría 2)
"3 números naturales y el adicional"   (categoría 6)
```

Un parser que busque `"+ adicional"` se come la mitad de las categorías **en silencio**: devuelve
una tabla con menos filas, sin error, y un `menores_brutos` más bajo. Por eso se busca la palabra
`adicional` en cualquier posición, y por eso se valida el número de categorías.

## 2 · El reporte de popularidad

`python -m melate.popularity --desde N --hasta M` escribe:

```
ventana            [4173, 4272]
juegos.<Juego>
  sorteos_usados, fallos[], ventana
  ventas                      {n, media, mediana, desviacion, cv, min, max}
  menores_brutos_directo      {idem}
  menores_brutos_por_bolsa    {idem}
  efecto_calendario           {corte, dentro_del_calendario, fuera_del_calendario,
                               cociente_fuera_entre_dentro, t_welch}
  muestras[]                  una por sorteo
procedencia        {fuente, descargado_utc, peticiones_de_red, cache, user_agent, pausa_segundos}
```

**Los dos estimadores de `menores_brutos` se publican los dos**, y no por indecisión: la diferencia
entre ellos es el hallazgo.

| | Qué calcula | cv Melate | cv Revancha |
|---|---|---|---|
| `directo` | `Σ p_c × premio_c` | 0,228 | 0,253 |
| `por_bolsa` | `Σ (ganadores_c × premio_c) / ventas` | **0,051** | **0,061** |

Son el mismo número con `ganadores/N` en lugar de `p`. El de bolsa **dispersa entre 2,1 y 5,2
veces menos** en todas las ventanas probadas, porque la bolsa de cada categoría es un porcentaje
de las ventas fijado por reglamento, mientras que el directo estalla cuando una categoría alta
tiene pocos ganadores. Por eso manda el de bolsa, y por eso se ve el otro al lado.

## 3 · La clave nueva del informe

`valor_esperado_medido`, declarada en `informe.NUEVAS_CLAVES["raiz"]`. **Siempre está**, incluso
sin `--popularidad`:

```json
{"disponible": false, "motivo": "sin --popularidad: el EV de arriba usa la constante escrita a mano…"}
```

Que esté siempre es deliberado. Una clave que aparece y desaparece haría que
`test_las_claves_nuevas_estan_todas` no pudiera vigilarla, y una clave ausente no se distingue de
una que nunca existió. Así se ve que falta y por qué.

Con datos lleva, además del mismo contenido que `valor_esperado_proximo`: `menores_brutos_usados`,
`procedencia_menores` (cuántos sorteos y con qué cv) y `ventana`.

**`valor_esperado_proximo` no cambia nunca.** Conserva la constante del oráculo porque la paridad
es bloqueante.

## 4 · Una cartera

```
juego, presupuesto, precio_boleto, boletos, coste, sobrante
numeros_cubiertos, solape_maximo_real, solape_medio, popularidad_media
tope_popularidad, candidatas_aptas, candidatas_descartadas
semilla, ventas_supuestas
detalle[]    {numeros[6], popularidad, patrones[], factor_reparto, acertantes_esperados}
valoracion   {coste, valor_esperado, rendimiento,
              valor_esperado_sin_mirar_popularidad,
              ganancia_por_evitar_compartir, ganancia_por_boleto,
              ganancia_como_porcentaje_del_precio, aviso}
```

Tres campos existen solo para que la cifra no se pueda leer mal:

- **`valor_esperado_sin_mirar_popularidad`** — la referencia. Sin ella, `valor_esperado` parecería
  un logro; al lado se ve que la diferencia es del orden del 0,1 % del precio.
- **`ganancia_como_porcentaje_del_precio`** — la magnitud en la unidad que importa. Hay un test que
  exige que esté entre 0 y 0,003.
- **`aviso`** — texto fijo que dice que el EV es negativo y que esto no cambia la probabilidad de
  acertar. Con test.

## Cómo verificar

```powershell
.venv\Scripts\python.exe -m pytest tests/test_popularidad.py tests/test_cartera.py -q
```

## Cómo revertir

Ver `Mapa/Modificar/2026-10-03_05-15_s3-entran-popularidad-y-cartera.md`.

Relacionado: `Estructura_Datos/Modificar/2026-10-03_00-13_s1-forma-del-reporte-y-doble-validacion.md`,
`Estructura_Datos/Añadir/2026-10-03_01-30_s2-formato-del-preregistro.md`,
`Mapa/Modificar/2026-10-03_05-15_s3-entran-popularidad-y-cartera.md`.
