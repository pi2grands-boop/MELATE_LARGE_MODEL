# Cierre de la fase popularidad y cartera

- **Fecha/hora:** 2026-10-03 05-40
- **Abierta el:** 2026-10-03 · **Duración:** una sesión, seguida de la Fase 2

Las fases 1 y 2 enseñaron al proyecto a medir la urna y a negarse a afirmar lo que no ha pasado el
protocolo. Esta mira por primera vez **la otra mitad del problema**: no qué sale, sino **con cuánta
gente lo compartirías**. Y es la primera que le pide páginas al servidor de otra persona.

## Criterio de terminado — cumplido

| Criterio del `00_ALCANCE.md` | Evidencia |
|---|---|
| 1 · Dictamen escrito **antes** que el código | ✅ `Decisiones/2026-10-03_02-40_…` a las 02:40; `popularity.py` después |
| 2 · Descarga, caché y parseo con el límite **comprobable** | ✅ 9 tests del trato; 400 páginas, 398 peticiones, **399 s = 1,00/s** |
| 3 · `menores_brutos` medido, con procedencia, y la diferencia explicada | ✅ Melate 4,6013 · Revancha 2,6042; el 4,38 y el 2,10 reproducidos |
| 4 · Cada salida de la cartera dice que el EV es negativo | ✅ `test_toda_valoracion_lleva_el_aviso` y 4 más |
| 5 · `pytest tests` en verde con la paridad intacta | ✅ **161 pruebas, 133 s** |
| 6 · Cada cifra re-medida; cada parámetro, con dos valores | ✅ dos ventanas por cifra; 7 parámetros con dos valores cada uno |
| 7 · Bitácora íntegra, colador limpio, hoja de ruta al día | ✅ (abajo) |

## Lo que no estaba previsto

**El `menores_brutos` no es un detalle: es el 65,5 % del valor esperado de un boleto de Melate.**
El término de bolsa aporta 2,14 $ y el de premios menores 4,07 $. La constante escrita a mano
—la que caducaba— gobernaba dos tercios de la cifra, no un apéndice de ella.

**Y las dos constantes se calcularon con métodos distintos.** El 4,38 de Melate reproduce exacto
como media de las tablas 4271 y 4272. El 2,10 de Revancha es **solo** la 4271: la 4272 daba 4,41
porque su categoría de 5 aciertos tuvo 3 ganadores. Eso es invisible sin reproducirlo, y
subestima el EV de Revancha en 4,7 puntos (−49,1 % contra −44,4 % medido). Las cifras del oráculo
**no se tocaron**; el `CLAUDE.md` lleva una nota.

**La cartera salió mal a la primera, y el fallo era del objetivo, no del código.** Minimizar la
popularidad a secas cubría **27 de 56 números, todos > 31**: como todos los altos pesan igual, el
mínimo global es jugar solo números altos. El algoritmo hacía lo que se le pidió. Lo correcto lo
dictaba la asimetría que esta misma fase midió —54 a 1— : **poner un techo, no perseguir un
suelo**. Corregido, cubre 56 de 56.

**El sitio del que descargamos enlaza la fuente oficial, y la fuente oficial no sirve.** La
mascarilla de Pronósticos redirige a `loterianacional.gob.mx` —el dominio que ya usamos— pero su
capa de texto tiene **1 dígito en 25.885 caracteres**: las cifras están dibujadas. El tercero no
se usa por comodidad sino porque el dato oficial no es legible por máquina. Queda escrito para que
nadie lo redescubra.

**Y salió gratis una tercera fuente.** La página publica también los números sorteados.
Comparados con el CSV oficial en 200 sorteos: **0 discrepancias**. Es exactamente la comprobación
que le habría ahorrado al proyecto el error de Revancha 3827.

## Qué quedó fuera, y por qué

| Fuera | Por qué |
|---|---|
| Tocar `baseline_auditoria.py` o el defecto de `ev.valor_esperado` | Es el oráculo. Lo medido entra por clave nueva declarada |
| El histórico completo de tablas | 4.368 páginas, 1 h 13 min contra un servidor ajeno. No sin decisión explícita |
| Revanchita | **No tiene tabla**: solo paga 6 aciertos. Pedirla sería gastar peticiones para nada |
| OCR de la mascarilla oficial | Fuente de error nueva y silenciosa. Documentado, no intentado |
| Meter el efecto calendario en la familia de BH | Consultado: **fuera**. Habla de los jugadores, no de la urna |
| Popularidad por número individual | Los datos no dan: cada sorteo aísla **un** número. Se mide el efecto agregado, y se declara |
| La app | Fase 4 |

## Documentos emitidos a las áreas base

| Documento | Qué dice |
|---|---|
| `Conexiones/Añadir/…tablas-de-ganadores-melate-e.md` | La fuente nueva, el contrato, y por qué un tercero |
| `Seguridad/Añadir/…trafico-saliente-a-un-tercero.md` | La postura: Scrapling viene para esconderse y se apaga |
| `Almacenamiento/Añadir/…cache-de-paginas.md` | Caché permanente, y por qué esta **no** se publica |
| `Estructura_Datos/Añadir/…tabla-de-ganadores-y-cartera.md` | La forma de todo lo nuevo, y los dos estimadores |
| `Mapa/Modificar/…entran-popularidad-y-cartera.md` | La frontera urna / jugadores |
| `Protocolo_Estadistico/Decisiones/…no-entra-en-la-familia.md` | Por qué la familia sigue siendo de 36 |
| `Rendimiento/Arreglos_Bugs/…el-voraz-cuadratico.md` | El bucle rápido, y las dos cifras re-medidas |
| `Estructura_Carpetas/Modificar/…arbol-tras-la-popularidad.md` | El árbol y la primera carpeta de datos no publicada |

## Bugs abiertos que se heredan

**Ninguno.** Los ocho del `Bugs/` están corregidos y con test, y el documento está cerrado.

## Pendiente de verificar en vivo

**Hereda la Fase 4.** Los dos primeros de la Fase 2 siguen siendo el diseño funcionando, no falta
de esfuerzo.

1. **Una evaluación preregistrada de verdad.** El holdout no existirá hasta que pasen sorteos
   posteriores al 2026-10-03T06:45Z. *(heredado)*
2. **La condición 5 no es alcanzable en años**: ~1.800 sorteos de holdout, unos 11 años. *(heredado)*
3. **El `SystemExit` de `ingest._leer_bytes`.** Sigue sin ejercitarse: el oficial no ha fallado.
   La Fase 3 lo miró y aplicó el mismo criterio al camino nuevo — `SitioBloqueado` tampoco se
   fuerza con un *mock* del servidor, se prueba con una sesión falsa. *(heredado, parcial)*
4. **Fuera de Windows**, todo lo que no sean finales de línea. *(heredado)*
5. **La descripción del repositorio** y **el correo privado en GitHub**: son de la cuenta del
   usuario. *(heredado)*
6. **Un bloqueo real del sitio.** NUEVO. No ha ocurrido. La instrucción es parar y preguntar.
7. **Que el sitio conserve la forma de su `<table>`.** NUEVO. Lo vigila un único test marcado
   `red`; si el sitio cambia, el resto de la suite seguiría en verde sobre un fixture obsoleto.

## Integridad, comprobada

- `scripts/verificar-bitacora.ps1` — **0 hallazgos** en las 5 comprobaciones, 46 documentos.
- `scripts/colador.ps1 -Autoprueba` — **0 coincidencias**, autoprueba 3/3.
- `pytest tests` — **161 en verde**, 133 s, con `test_paridad.py` intacto.
- `q_BH_global` mínima **0,306** · veredicto `sin ventaja demostrada`, 0 de 5 condiciones.

## Una nota sobre lo que esta fase significa

El proyecto ya sabía decir «no lo sé» de una forma que significa algo. Ahora sabe decir **cuánto
cuesta**, y la respuesta es más incómoda que la anterior: el valor esperado de un boleto de Melate
es −57 %, y el de Revancha −44 %, no −49 %.

Lo que **no** hace esta fase, y conviene que quede dicho en el cierre: la cartera no mejora tus
probabilidades. Su techo medido es **+0,27 % del precio en Melate** y su suelo, si eligieras una
combinación muy jugada, **−14,3 %**. Una asimetría de 54 a 1. Es un seguro contra elegir
1-2-3-4-5-6, no una forma de ganar — y el módulo está escrito para no poder sugerir lo contrario,
con un test que lee su propio código buscando promesas.

Relacionado: `00_ALCANCE.md`,
`Fases/2026-10-03_popularidad/Decisiones/2026-10-03_02-40_s3-dictamen-terminos-melate-e.md`,
`Fases/2026-10-03_popularidad/Decisiones/2026-10-03_05-10_s3-que-hacer-con-las-constantes.md`,
`Fases/2026-10-03_popularidad/Bugs/2026-10-03_04-10_s3-review-popularidad-y-cartera.md`,
`Fases/2026-10-03_protocolo/99_CIERRE.md`.
