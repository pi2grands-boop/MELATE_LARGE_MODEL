# Máquina Melate (Melate · Revancha · Revanchita)

Herramienta personal de análisis para Melate, Revancha y Revanchita. El diseño completo está en el doc
"ML para Melate, Revancha y Revanchita". `baseline_auditoria.py` es la línea base probada: reprodúcela antes de cambiar nada.

## Qué es y qué no es

- Audita la urna, estima qué combinaciones juega la gente, calcula el valor esperado de cada sorteo y arma carteras de boletos con presupuesto fijo.
- El laboratorio de predicción solo declara ventaja si pasa el protocolo de abajo. Por defecto, toda salida dice "sin ventaja demostrada" y nunca habla de "números más probables".

## Fuentes de datos

| Fuente | URL | Formato y notas |
| --- | --- | --- |
| CSV oficial Melate | https://www.loterianacional.gob.mx/Documentos/Historicos/Melate.csv | NPRODUCTO, CONCURSO, R1–R6, R7 (adicional), BOLSA, FECHA (dd/mm/aaaa) |
| CSV oficial Revancha | https://www.loterianacional.gob.mx/Documentos/Historicos/Revancha.csv | NPRODUCTO, CONCURSO, R1–R6, BOLSA, FECHA |
| CSV oficial Revanchita | https://www.loterianacional.gob.mx/Documentos/Historicos/Revanchita.csv | NPRODUCTO, CONCURSO, F1–F6, BOLSA, FECHA |
| Espejo (**solo validación cruzada**, nunca carga) | https://raw.githubusercontent.com/pakinja/pakin/master/{Melate,Revancha,Revanchita}.csv | CONCURSO, ID, R1–R6 (F1–F6), [R7], BOLSA, FECHA (aaaa-mm-dd), PRIMOS, REPETIDOS, MEDIA. Tiene errores de bolsa (Revanchita 3380: 54.7 M contra 57.4 M oficial) **y un error en los números sorteados (Revancha 3827: dice 54 donde van 50)**. Puede estar parcialmente actualizado: se ha observado con dos juegos en el sorteo N+1 y uno en el N |
| Ganadores por categoría | https://resultados.melate-e.com/{melate,revancha,revanchita}/sorteo/{n} | Revisar términos y robots.txt antes de descargar en masa; caché local y 1 solicitud por segundo |

## Reglas de datos

1. Era 6/56: CONCURSO >= 2089 (12-dic-2007) en Melate y Revancha. Revanchita existe desde el 2371 (25-ago-2010).
2. BOLSA de la fila N = bolsa anunciada para el sorteo N+1. La bolsa en juego en el sorteo N es BOLSA(N-1).
   Verificado con: melate-e.com (fila 3500 = bolsa "para el sorteo 3501"), Lotería Nacional (505 M del 3681 están en la fila 3680)
   y la ASF (sorteo 2518: filas 2517 de Melate 112 M + Revancha 48 M = 160 M).
3. Una baja de BOLSA = premio mayor ganado en ese sorteo. Excluir errores: una baja seguida de un valor mayor que el anterior.
4. Errores conocidos del oficial: BOLSA = 0 en 2120, 2142 y 2234 (Melate y Revancha); Revancha 3221 = 238.6 M fuera de secuencia.
5. Hueco por pandemia: sorteo 3373 (2020-04-01) a 3374 (2020-07-26); los concursos siguen consecutivos.
6. R1–R6 vienen ordenados de menor a mayor: no hay orden de extracción. R7 sale de las 50 esferas restantes.
7. Validar siempre: 6 números distintos en 1..56, R7 fuera de los naturales, concursos consecutivos, sin duplicados, oficial igual al espejo.
   **Excepción conocida y única de la última comprobación: Revancha 3827 (26-11-2023), donde el oficial y melate-e.com dan
   `15 16 38 40 41 50` y el espejo dice `54` en lugar de `50`. Manda el oficial. Cualquier diferencia nueva es un hallazgo que
   se investiga con una tercera fuente antes de elegir un valor: este error es invisible a toda validación de una sola fuente,
   porque la fila del espejo es formalmente válida.**

## Constantes

- C(56,6) = 32,468,436. Precios: Melate $15, Revancha $10, Revanchita $5. Bolsas mínimas: 30 M, 20 M y 10 M.
- Impuesto sobre premios: 1% federal + 6% estatal en el caso típico = 7%. Parametrizar por estado.
- Melate, combinaciones favorables por categoría: C(6,k) · C(1,a) · C(49, 6-k-a), con k naturales acertados y a = 1 si incluye el adicional.
- Revancha: C(6,k) · C(50, 6-k). Revanchita solo paga 6 aciertos.
- Línea base: 36/56 = 0.642857 aciertos por boleto (desviación 0.722357); log-loss 0.340500 nats por número; P(3 o más aciertos) = 1/79.06.
- Ventas de Melate, **medidas** sobre 300 sorteos (ventana 3973–4272, descarga del 2026-10-03):
  mediana 0.98 M de combinaciones por sorteo, rango 0.58 M a 1.59 M. Las ventas suben con la bolsa,
  así que un rango estrecho no las describe: solo el 16 % de esos 300 sorteos cae entre 1.06 y 1.18 M,
  que era la estimación anterior, sacada de las tablas de 2021 y 2026.
  Reporte: `reportes/2026-10-04_popularidad-melate-300-sorteos.json`; reproducir con
  `python -m melate.popularity --juegos Melate --desde 3973 --hasta 4272`.
- Efecto calendario, misma ventana: los números > 31 aparecen en un **24.5 % menos** de boletos que
  los <= 31 (t de Welch = -18.67). Mide la conducta de los jugadores, **no la urna**, y por eso no
  entra en la familia de Benjamini-Hochberg
  (`Documentos_Contexto/Protocolo_Estadistico/Decisiones/2026-10-03_05-10_s3-la-popularidad-no-entra-en-la-familia.md`).

## Protocolo de evaluación (no negociable)

1. Walk-forward: entrenar con sorteos anteriores a t y predecir t. Nada de validación cruzada aleatoria; normalizaciones y selección de variables solo con datos anteriores a t.
2. Comparar contra la línea base exacta y contra boletos aleatorios juzgados con el mismo sorteo (prueba pareada).
3. Benjamini-Hochberg sobre TODAS las pruebas corridas, también las que no se reportan.
4. Preregistro en `prereg/*.json` con su hash antes de evaluar; el holdout son los sorteos posteriores a la fecha del sello.
5. Declarar ventaja solo si se cumplen a la vez: holdout futuro positivo; q <= 0.05; estable al mover hiperparámetros;
   mismo signo en Melate, Revancha y Revanchita; efecto >= mínimo detectable (0.048 aciertos con 1,784 sorteos de prueba).
6. Guardar el hash del dataset y la semilla en cada corrida.

## Estructura sugerida

```
melate-ml/
  data/raw/  data/clean/  melate.duckdb
  src/melate/  ingest.py  validate.py  audit.py  backtest.py  ev.py  popularity.py  portfolio.py  lab.py
  app/streamlit_app.py
  prereg/  reports/  tests/
```

Stack: Python 3.11+, pandas (**<3**: la 3.0 cambia la propagación de `df.attrs`, que `baseline_auditoria.py` usa), numpy, scipy,
scikit-learn, duckdb, streamlit, pytest, requests. Opcional: pymc o numpyro (auditor bayesiano), torch (redes del laboratorio).
Versiones exactas en `requirements.txt`; las que reproducen la línea base, en `entorno/`.

## Línea base verificada (datos al sorteo 4272, 30-sep-2026)

Reproducir con `python baseline_auditoria.py --datos data/raw/2026-10-02` (semilla 20261001, 2,000 simulaciones).
**Correr siempre contra el snapshot congelado, no contra la descarga en vivo:** los CSV crecen con cada sorteo y
una descarga de hoy ya no reproduce estas cifras.

- Sorteos 6/56: Melate 2,184; Revancha 2,184; Revanchita 1,902.
- Chi-cuadrada corregida: Melate 52.19 (p = 0.85); Revancha 42.29 (p = 0.22); Revanchita 54.83 (p = 0.98).
- Backtest (prueba desde el 2489; Revanchita desde el 2771; reentrenar cada 100 sorteos):
  regresión logística en Revancha 0.6839 aciertos (p = 0.017, q = 0.35); gradient boosting en Melate 0.6160; aleatorio en Melate 0.6328.
- Premios mayores detectados por bajas de BOLSA: Melate 69, Revancha 61, Revanchita 35.
- Valor esperado del sorteo 4273 (lambda = 0.037, impuesto 7%): Melate -59%, Revancha -49%, Revanchita -12%.

Ninguna estrategia bate al azar: el mejor caso es la regresión logística en Revancha, y su q = 0.35 está muy lejos
del 0.05 que el protocolo exige. El veredicto es **sin ventaja demostrada**.

### Procedencia de estas cifras (regla 6 del protocolo)

Datos: `data/raw/2026-10-02/`, último concurso 4272. SHA-256:

```
51de5afd3b7d348bff2b3032c1d125fa6870d7176f8006a1dd9baf12ae1891cc  Melate.csv
5d1b191e3c8bc52de154124b3b0d6d5f730ebd0a1f6006f9d48f2776bf811581  Revancha.csv
06beda9ab84cf015951756ade4c8df4d894ebdf5e7dda64ef20f21e81e913b5a  Revanchita.csv
```

Semillas: 20261001 (auditoría Monte Carlo), 7 (desempates del backtest), `random_state=0` (gradient boosting).
Entorno: Python 3.13.9 · numpy 2.5.3 · pandas 2.3.3 · scipy 1.18.1 · scikit-learn 1.9.1.

> **Nota del 2026-10-03 (Fase 3), sobre el valor esperado.** Las tres cifras de EV de arriba usan el
> `menores_brutos` escrito a mano en `baseline_auditoria.py:252`. La Fase 3 lo reprodujo y lo midió:
> el 4.38 de Melate es exactamente la media de las tablas 4271 y 4272; el **2.10 de Revancha es solo
> la tabla 4271**, porque la 4272 daba 4.41 (su categoría de 5 aciertos tuvo 3 ganadores y el premio
> individual se disparó). Las dos constantes se calcularon con métodos distintos. Medido sobre 100
> sorteos con el estimador estable (ventana 4173-4272, `reportes/2026-10-03_popularidad.json`):
> Melate 4.6013 y Revancha 2.6042, con lo que el EV real es
> **Melate −57.2 % y Revancha −44.4 %** (Revanchita no cambia: solo paga 6 aciertos).
> **Las cifras de arriba NO se tocan**: son las que reproduce el oráculo y la paridad es bloqueante.
> Lo medido vive en la clave `valor_esperado_medido` del informe
> (`python -m melate.informe --popularidad reportes/<fichero>.json`). Evidencia en
> `Documentos_Contexto/Fases/2026-10-03_popularidad/Bugs/2026-10-03_04-10_s3-review-popularidad-y-cartera.md`.

> **Corregido el 2026-10-02.** La versión anterior de esta sección daba 42.03 para la chi-cuadrada de Revancha y
> 0.6861 (p = 0.011, q = 0.24) para la regresión logística. Ambas se habían calculado con el espejo de GitHub, que
> tiene mal el sexto número de Revancha 3827. Con el dato oficial —confirmado por melate-e.com— salen las cifras
> de arriba. El veredicto no cambia, pero el número más llamativo del proyecto estaba inflado por un error de un
> tercero. Evidencia completa en `Documentos_Contexto/Fases/2026-10-02_arranque/Bugs/2026-10-02_23-29_s1-porton-linea-base.md`.

## Forma de trabajo

- Pruebas pytest para cada regla de datos y para reproducir la línea base.
- Reportes y textos de la app en español.
- No avanzar de fase sin que el usuario lo apruebe.

### Documentación: usa la skill `bitacora`, siempre

Todo cambio se documenta en `Documentos_Contexto/` con la skill `bitacora`. Las reglas completas —la
rejilla de áreas, el pipeline, los nombres, las plantillas— están en `REGLAS-DOCUMENTACION.md`, y las
rutas de lectura en `Documentos_Contexto/_MAPA.md`. Empieza por ahí antes de tocar nada.

Lo que no se negocia:

- **El `.md` es el ÚLTIMO paso**, después de implementar y de las dos reviews. Documentar antes de
  verificar produce documentación que miente.
- **Esta bitácora se publica**, al contrario de lo habitual (`REGLAS-DOCUMENTACION.md` §0). Rutas
  siempre relativas, nunca rutas absolutas de la máquina ni correos.
- **Un bug no se deja sin preguntar.** La decisión es del usuario.

### Lo que protege el proyecto de sí mismo

- **`baseline_auditoria.py` es el oráculo y NO se modifica nunca.** `tests/test_paridad.py` compara
  el paquete contra él con tolerancia cero, y es bloqueante. Es lo que hace demostrable cualquier
  refactor; si se toca, el proyecto pierde su única referencia y no se recupera.
- **Dos scripts bloqueantes**, y los dos traen su propia comprobación porque una herramienta de
  verificación que nadie ha verificado no es una garantía, es una opinión:
  - `scripts/colador.ps1 -Autoprueba` → antes de cada push. Si imprime algo, no se sube. También
    caza una base de datos metida a la fuerza en el índice de git, que es un binario que no sabe leer.
  - `scripts/verificar-bitacora.ps1` → antes de cerrar una fase. Tiene que dar 0 hallazgos.
- **Al cerrar una fase no basta con que los tests pasen.** Hay que volver a medir cada número que se
  publique y dar dos valores distintos a cada parámetro del que se diga que gobierna algo. La
  auditoría de las fases 1 y 2 encontró siete defectos con las 92 pruebas en verde, todos en el hueco
  de lo que nadie pensó comprobar. Procedimiento en
  `Documentos_Contexto/Protocolo_Estadistico/Bugs/2026-10-03_01-59_auditoria-retrospectiva-fases-1-y-2.md`.
- **Y se mutan los tests: `scripts/mutar.py`.** Rompe una cosa a la vez en una copia del repositorio
  —nunca en el árbol de trabajo— y exige que algún test se entere. Al cerrar una fase tienen que
  detectarse todas: una mutación que no se detecta es un test que no vigila nada. Lo nuevo que se
  proteja con un test entra también en su lista.
- **Y la pregunta del cierre no es "¿qué áreas toqué?" sino "¿qué documento del índice permanente
  acabo de dejar desactualizado?"**. Son conjuntos distintos. Un documento del índice que miente es
  peor que uno que falta: el que falta se busca en otro sitio, el que miente se cree.

### La app local (Fase 4)

`python -m melate.app` la abre. Es el lanzador: pone al día `melate.duckdb` —la construye
`python -m melate.almacen` desde `reportes/` y `prereg/`— y arranca Streamlit con la red forzada por
línea de órdenes, se lance desde donde se lance. Tres reglas que no se negocian, cada una con su test:

- **Solo esta máquina.** Escucha en `127.0.0.1`, nunca en `0.0.0.0`, sin telemetría y sin
  preguntarle a nadie la IP pública. Lo fuerza el lanzador; lo dice `.streamlit/config.toml` para
  quien use `streamlit run` desde la raíz (un test exige que los dos digan lo mismo); y una guarda
  dentro de la app se niega a enseñar nada si no es así. El lanzador sustituye una función interna
  de Streamlit 1.65: actualizar Streamlit obliga a revisar su red (`requirements.txt`).
- **No recalcula, no descarga y no escribe.** Lee `melate.duckdb` en solo lectura. Si algo tarda dos
  minutos en un backend, no va en una pantalla: la app enseña la orden. `melate.duckdb` no se publica.
- **El informe explora; el laboratorio juzga.** El veredicto de la cabecera, en todas las pantallas,
  sale solo de `melate.lab` y de un preregistro cuyo sello verifica. Ninguna cifra exploratoria se
  presenta como veredicto, y una q ≤ 0.05 de la exploración es una candidata a preregistrar.
