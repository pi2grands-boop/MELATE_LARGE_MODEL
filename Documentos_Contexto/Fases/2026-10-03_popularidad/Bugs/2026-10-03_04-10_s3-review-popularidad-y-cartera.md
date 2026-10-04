# Review de `popularity.py` y `portfolio.py`

- **Fecha/hora:** 2026-10-03 04-10
- **Área:** Fases/2026-10-03_popularidad · **Acción:** Bugs
- **Estado:** CERRADO el 2026-10-03 05-30 (bloque al final)

## Limitaciones del entorno, por delante

- **Windows 11, PowerShell 5.1 y Git Bash.** Nada probado en Linux ni macOS, igual que en las
  fases anteriores. Es el pendiente heredado nº 4 de la Fase 2 y **sigue abierto**.
- **Un solo sitio de terceros, y respondiendo bien.** No se ha observado un bloqueo real, así que
  el camino de `SitioBloqueado` está probado con una sesión falsa, no contra el servidor.
- **Ventana de 400 páginas**, no el histórico completo. Las cifras valen para esa ventana y lo
  dicen.
- **La caché está en `.gitignore`**, así que los tests no pueden depender de ella: los fixtures
  son HTML embebido en el propio fichero de test.

## Lo que se revisó

Tres pasadas: funcional (#1), de limpieza (#2) y de seguridad, que es un modo mental distinto y
encontró cosas que las otras dos no.

---

## Fallos encontrados y corregidos

### B1 · La cartera se concentraba en media urna — el peor de todos

**Síntoma.** La primera versión de `cartera()` minimizaba la popularidad a secas. Resultado con
$300 en Melate: **27 de los 56 números cubiertos, todos > 31**.

**Causa.** Con los pesos medidos, todos los números > 31 pesan exactamente igual (0,8476), así que
el mínimo global de popularidad es *jugar solo números altos*. El algoritmo hacía exactamente lo
que se le pidió; lo mal pedido era el objetivo.

**Por qué importa, y no es estético.** Esa cartera no mejora el valor esperado —la ganancia seguía
siendo del 0,16 % del precio— y a cambio concentra todo el dinero en media urna. Es un riesgo que
nadie pidió, a cambio de nada.

**Arreglo.** El objetivo correcto lo dicta la asimetría de 54 a 1 que mide esta misma fase: **poner
un techo, no perseguir un suelo.** Se descarta lo que pase de `tope_popularidad` (1,0 por defecto,
que deja pasar el 40 % de las combinaciones) y entre las que pasan se maximiza la cobertura.

| | Antes | Después |
|---|---|---|
| Números cubiertos | 27 / 56 | **56 / 56** |
| Solape medio | 1,253 | **0,695** |
| Popularidad media | 0,383 | 0,618 |
| Ganancia sobre no mirar | +0,16 % | +0,10 % |

Se pagan 0,06 puntos de ganancia por no concentrar la cartera. Es el intercambio correcto: la
ganancia era ruido y la concentración era real.

**Test que lo impide:** `test_la_cartera_no_se_concentra_en_media_urna`.

### B2 · El bucle rápido pasó de 2,5 s a 26 s

**Síntoma.** Con los tests nuevos, `pytest -m "not lento and not red"` tardaba **26,09 s**. El
`_MAPA.md` prometía 2,5 s.

**Causa.** El voraz de `cartera()` recalculaba el solape de cada candidata contra *todas* las ya
elegidas en cada ronda: `O(boletos x candidatas x elegidas)`.

**Por qué importa.** Es **exactamente** el fallo que el proyecto ya documentó una vez
(`Rendimiento/Arreglos_Bugs/2026-10-03_01-59_la-suite-rapida-no-era-rapida.md`: dos tests sin
marcar dejaron el bucle rápido en 30 s mientras el mapa decía 5). Lo fácil habría sido marcar los
tests como `lento` y esconderlo. Eso es lo que convierte un bucle rápido en un bucle que nadie
corre.

**Arreglo.** El solape se lleva al día: tras elegir un boleto se actualiza cada candidata contra
**solo** ese boleto. `O(boletos x candidatas)`.

| | Antes | Después |
|---|---|---|
| `tests/test_cartera.py` | 10,75 s | **1,46 s** |
| Bucle rápido completo | 26,09 s | **5,08 s** |

### B3 · Un 404 se trataba como un bloqueo

**Síntoma.** `html()` levantaba `SitioBloqueado` tanto para un 403 como para un 404.

**Cómo apareció.** No lo encontró una lectura del código: lo delató el guion de cosecha, que tuvo
que escribir `if "SitioBloqueado" in type(e).__name__ and "404" not in str(e)`. **Cuando hay que
mirar si un mensaje de error contiene una subcadena para decidir qué hacer, el tipo está mal.**

**Por qué importa, y en la dirección peligrosa.** Pedir un sorteo que el sitio no tiene es normal.
Si ese caso se trata como bloqueo, quien lo capture para poder seguir acabará capturando también
los bloqueos de verdad — y el dictamen dice que ante un bloqueo **se para y se pregunta**.

**Arreglo.** `SorteoNoPublicado(LookupError)`, separada de `SitioBloqueado(RuntimeError)`.
`analizar()` captura la primera y **deja subir la segunda**.

**Tests:** `test_un_404_no_es_un_bloqueo`, `test_un_bloqueo_no_se_traga_en_el_agregado`,
`test_los_404_se_anotan_y_la_corrida_sigue`.

### B4 · `_ruta` no validaba lo que interpolaba (review de seguridad)

`self.cache / juego.lower() / f"{sorteo}.html"` con `sorteo` sin validar escribiría fuera de la
caché si alguna vez llegara un `../`. Hoy `sorteo` sale de un `range()` y `juego` de una lista
cerrada, así que **no es explotable**; se arregla porque cuesta dos líneas y `html()` es público.

**Test:** `test_no_se_puede_escribir_fuera_de_la_cache`.

### B5 · Sin tope al tamaño de la respuesta (review de seguridad)

Se escribía en la caché lo que viniera, sin límite. `MAXIMO_BYTES = 1_000_000` contra páginas
reales de 5-8 KB. No está para ajustar: está para que algo claramente distinto no entre como
bueno.

**Test:** `test_una_respuesta_enorme_no_entra_en_la_cache`.

### B6 · El test de honestidad fallaba contra la frase honesta

`test_el_modulo_no_promete_mejorar_las_probabilidades` buscaba `"mejora tus probabilidades"` como
subcadena, y saltaba contra la frase **"esto no mejora tus probabilidades de ganar"** — la más
importante del módulo.

Un test que no distingue `X` de `no X` en un fichero cuyo trabajo es negar `X` no vale. Ahora exige
que toda aparición venga negada, y además que la negación exista.

### B7 · El selector de números devolvía cadena vacía

`span.numnatural` contiene un `<b>`; `.text` del `<span>` da `''` y `int('')` revienta. Corregido a
`span.numnatural b`. **Test:** `test_lee_los_numeros_de_la_pagina`.

### B8 · `FetcherSession` sin gestor de contexto

Solo expone `.get` dentro de su `with`. `Descargador` lo entra en `_crear_sesion` y lo sale en
`cerrar()`, y es gestor de contexto él mismo.

---

## Lo que se comprobó y estaba bien

| Qué | Evidencia |
|---|---|
| Las 9 categorías de Melate y las 5 de Revancha suman `C(56,6)` exacto | `test_las_categorias_de_melate_suman_el_universo` |
| El parser aguanta las **dos** formas de escribir el adicional que conviven en la misma tabla | `test_parsea_las_dos_formas_de_escribir_el_adicional` |
| 400 páginas reales parseadas, **0 fallos** | Cosecha de la ventana 3973-4272 |
| El ritmo real: 398 peticiones en 399 s = **1,00/s** | Misma cosecha |
| El sitio contra el CSV oficial: **0 discrepancias** en 200 sorteos | `discrepancias()`, ventana 4173-4272 |
| La paridad con el oráculo, intacta | `tests/test_paridad.py`; suite completa **161 en verde, 133 s** |
| El EV de la cartera es negativo en los tres juegos | `test_el_valor_esperado_sigue_siendo_negativo` |
| Separar boletos **no** cambia la media | `test_separar_los_boletos_no_cambia_la_media` |

## Cada parámetro que gobierna algo, con dos valores distintos

Lo pide la auditoría de las fases 1 y 2
(`Protocolo_Estadistico/Bugs/2026-10-03_01-59_auditoria-retrospectiva-fases-1-y-2.md`): un
parámetro declarado que en realidad no se lee es un defecto que ningún test de humo encuentra.

| Parámetro | Valores probados | Test |
|---|---|---|
| `pausa` | 0 y 0,25 s, medido con reloj | `test_se_respeta_una_solicitud_por_segundo` |
| `corte` del calendario | 20 y 40 | `test_el_corte_del_calendario_gobierna_de_verdad` |
| `tope_popularidad` | 0,7 y 3,0 | `test_el_tope_de_popularidad_gobierna_de_verdad` |
| `solape_maximo` | 1 y 4 | `test_el_solape_maximo_gobierna_de_verdad` |
| `PATRONES` | `{}` y `todos_en_calendario=10` | `test_las_penalizaciones_de_patron_gobiernan_de_verdad` |
| `semilla` | 7 y 8 | `test_semillas_distintas_dan_carteras_distintas` |
| `cociente` de popularidad | `None`, 0, −1 y 1,0 | `test_sin_efecto_medido_los_pesos_son_todos_uno` |

## Cada cifra publicable, vuelta a medir con dos ventanas

| Cifra | Ventana 4173-4272 | Ventana 3973-4272 | ¿Aguanta? |
|---|---|---|---|
| Cociente calendario (Melate) | 0,7609 (n=100) | 0,7549 (n=300) | sí, 0,8 % |
| Calibración (debe dar ~1) | 0,9919 | 0,9956 | sí |
| `menores_brutos` Melate, por bolsa | 4,6013 | 4,6465 *(corregido en la Fase 4: decía 4,6422, con tres sorteos sin premios publicados contados como 0)* | sí, 1,0 % |
| Ventas Melate, mediana | 991.119 | 982.693 | sí, 0,9 % |

Y Revancha con 100 y con 50 sorteos: 2,6042 y 2,6063 — 0,1 % de diferencia.

**El estimador por bolsa dispersa entre 2,1 y 5,2 veces menos que el directo en todas las
ventanas.** Esa es la razón medida para preferirlo, no una preferencia.

---

## Decisiones que NO son mías — pendientes de consultar

Cuatro hallazgos tocan el `CLAUDE.md`, que es el contrato, o el protocolo. **La decisión es del
usuario** (`CLAUDE.md`: "Un bug no se deja sin preguntar"). Ninguno está aplicado.

### C1 · El `menores_brutos` de Melate se reproduce exacto; el de Revancha, no

Reproduciendo las tablas 4271 y 4272 que cita `baseline_auditoria.py:252`:

| | 4271 | 4272 | Media | Escrito a mano |
|---|---|---|---|---|
| Melate, estimador directo | 4,3494 | 4,4106 | **4,3800** | **4,38** ✅ exacto |
| Revancha, estimador directo | **2,0965** | 4,4083 | 3,2524 | **2,10** ❌ |

El 4,38 de Melate es la media de los dos sorteos, clavada. El 2,10 de Revancha es **solo el
4271**: el 4272 daba 4,4083 porque su categoría de 5 aciertos tuvo 3 ganadores y el premio
individual se disparó a 206.628 $.

No afirmo saber qué pensó quien lo escribió. Afirmo lo medible: **las dos constantes se
calcularon con métodos distintos, y la de Revancha con el sorteo que daba el número más bajo.**

Medido sobre 100 sorteos con el estimador estable: Melate **4,6013**, Revancha **2,6042**. El
efecto sobre el valor esperado publicado:

| Juego | EV publicado | EV con menores medidos | Diferencia |
|---|---|---|---|
| Melate | −58,6 % | −57,2 % | 1,4 puntos |
| Revancha | **−49,1 %** | **−44,4 %** | **4,7 puntos** |
| Revanchita | −12,4 % | −12,4 % | 0 (no tiene menores) |

**Qué NO he hecho:** tocar `baseline_auditoria.py` ni el defecto de `ev.valor_esperado`. La
paridad es bloqueante y sigue intacta. Lo medido vive en la clave nueva declarada
`valor_esperado_medido`.

**Qué hay que decidir:** si el `CLAUDE.md` —que publica −49 % para Revancha— lleva una nota.

### C2 · Las ventas que publica el `CLAUDE.md` son demasiado estrechas

El contrato dice *"1.06 a 1.18 millones de combinaciones de Melate por sorteo"*. Sobre 300
sorteos: **solo 47 (el 16 %) caen en ese rango.** Mediana 982.693, rango real 583.212 a 1.586.604.
Las ventas suben con la bolsa, así que un rango estrecho no puede describirlas.

Además, `ev.valor_esperado` usa por defecto `combinaciones_vendidas=1.2e6`, por encima de la
mediana medida. El efecto en el EV es pequeño (λ = 0,037 y S apenas se mueve), pero la cifra del
contrato es la que la gente lee.

### C3 · La prueba del efecto calendario y la familia de Benjamini-Hochberg

El efecto calendario sale con **t de Welch = −18,67** sobre 300 sorteos. Es una prueba estadística
y el usuario fue explícito: ampliar la familia de BH es una decisión con consecuencias.

**Mi lectura, para que se confirme o se corrija:** esta prueba **no pertenece a la familia**,
porque la familia corrige hipótesis sobre **la urna** —si algún número sale más, si una estrategia
predice el sorteo— y esta mide **la conducta de los jugadores**, que es un objeto distinto y
observable directamente. El sorteo no sabe qué apostó nadie: ninguna cifra de popularidad puede
convertirse en una afirmación sobre qué va a salir, y por tanto no puede inflar el riesgo de
declarar una ventaja que no existe. El veredicto sigue siendo `sin ventaja demostrada` con
`q_BH_global` mínima 0,306 sobre las mismas 36 pruebas de siempre.

**Si el usuario discrepa**, la familia pasaría de 36 a 37 y habría que recalcular. Por eso se
pregunta antes de dar la fase por cerrada.

### C4 · La fuente oficial de las tablas existe, pero no es legible

`loterianacional.gob.mx/.../Mascarillas/RESULTADOS {fecha}.pdf` — el mismo dominio del que el
proyecto ya carga los CSV. Su capa de texto trae las etiquetas pero **1 dígito en 25.885
caracteres**: las cifras están dibujadas. Sacarlas exigiría OCR, una fuente de error nueva y
silenciosa.

Está documentado en el dictamen. **Qué hay que decidir:** si se deja así o si algún día se
intenta el OCR como validación cruzada de la validación cruzada.

---

---

## Cómo verificar esta review

Los ocho fallos tienen test, así que la review se vuelve a correr entera con dos comandos:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_popularidad.py tests/test_cartera.py -q  # 62, ~3 s
.venv\Scripts\python.exe -m pytest tests -q                                            # 164, ~130 s
```

| Fallo | Test que lo fija |
|---|---|
| B1 cartera concentrada | `test_la_cartera_no_se_concentra_en_media_urna` |
| B2 voraz cuadrático | medido: `Measure-Command { pytest tests -m "not lento and not red" }` → ~5 s |
| B3 404 tratado como bloqueo | `test_un_404_no_es_un_bloqueo`, `test_un_bloqueo_no_se_traga_en_el_agregado` |
| B4 escritura fuera de la caché | `test_no_se_puede_escribir_fuera_de_la_cache` |
| B5 respuesta sin tope | `test_una_respuesta_enorme_no_entra_en_la_cache` |
| B6 grep que no leía negaciones | `test_el_modulo_no_promete_mejorar_las_probabilidades` |
| B7 selector de números | `test_lee_los_numeros_de_la_pagina` |
| B8 sesión sin gestor de contexto | cualquier test que use `Descargador` de verdad (`-m red`) |

Y las cifras de la tabla «cada cifra publicable»:

```powershell
.venv\Scripts\python.exe -m melate.popularity --desde 4173 --hasta 4272 --datos data\raw\2026-10-02
.venv\Scripts\python.exe -m melate.popularity --desde 3973 --hasta 4272 --datos data\raw\2026-10-02
```

Con la caché poblada, las dos hacen **0 peticiones de red** y lo imprimen.

## Cómo revertir

Los ocho arreglos son independientes entre sí y están todos en `src/melate/popularity.py` y
`src/melate/portfolio.py`. Revertirlos uno a uno no tiene sentido; para quitar la fase entera, ver
`Mapa/Modificar/2026-10-03_05-15_s3-entran-popularidad-y-cartera.md`.

---

## CERRADO — 2026-10-03 05-30

**Los ocho fallos, corregidos y con test.** Suite completa: **161 pruebas en verde, 133 s**, con
`tests/test_paridad.py` intacto.

**Los cuatro asuntos de arriba se consultaron con el usuario** y su decisión está registrada, con
el porqué, en
`Fases/2026-10-03_popularidad/Decisiones/2026-10-03_05-10_s3-que-hacer-con-las-constantes.md`:

| | Decisión |
|---|---|
| C1 · `menores_brutos` de Revancha | Nota al pie en el `CLAUDE.md`; las cifras del oráculo **no se tocan** |
| C2 · Rango de ventas | **Corregido** con la mediana y el rango medidos |
| C3 · Familia de BH | **Confirmado: fuera.** Sigue en 36 pruebas, `q_BH_global` mínima 0,306 |
| C4 · Mascarilla oficial en PDF | Se deja documentado; **no se intenta OCR** |

## Pendiente de verificar, que esta fase NO cierra

1. **Un bloqueo real del sitio.** No ha ocurrido. El camino está probado con una sesión falsa.
2. **Que el sitio conserve la forma de su `<table>`.** Lo vigila un solo test, y marcado `red`:
   `test_el_sitio_sigue_teniendo_la_forma_que_esperamos`.
3. **Fuera de Windows.** Heredado de la Fase 2 y sigue abierto.
4. **El histórico completo.** 4.368 páginas, 1 h 13 min. No se ha descargado y no se descargará
   sin decisión explícita.

Relacionado: `Fases/2026-10-03_popularidad/00_ALCANCE.md`,
`Fases/2026-10-03_popularidad/Decisiones/2026-10-03_02-40_s3-dictamen-terminos-melate-e.md`.
