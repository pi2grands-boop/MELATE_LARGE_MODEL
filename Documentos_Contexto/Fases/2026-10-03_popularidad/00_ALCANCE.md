# Fase: popularidad y cartera

- **Abierta:** 2026-10-03
- **Estado:** abierta
- **Decidida por:** usuario

Las fases 1 y 2 dejaron el proyecto capaz de **medir**, de **reproducir** lo que mide y de **negarse
a afirmar** lo que no ha pasado el protocolo. Las tres cosas miran hacia dentro: a la urna y a los
datos oficiales.

Esta fase mira por primera vez hacia **la otra mitad del problema**. El valor esperado de un boleto no
depende solo de la urna: depende de **con cuánta gente compartirías la bolsa si acertaras**. Y eso no
está en ningún CSV oficial — hay que estimarlo de las tablas de ganadores por categoría.

Es también la primera fase que **toca un sitio de terceros**. El proyecto ya tiene una cicatriz de
confiar en un tercero (`Fases/2026-10-02_arranque/Bugs/2026-10-02_23-29_s1-porton-linea-base.md`: un
número mal transcrito en el espejo de GitHub infló el resultado más llamativo del proyecto). Esta vez
el tercero no es solo una fuente: es un servidor ajeno al que vamos a pedirle páginas.

## Qué entra

1. **El dictamen de términos del sitio**, escrito **antes** que el código que depende de él. No es
   burocracia: es lo único que separa una herramienta personal de un raspador. Va en
   `Decisiones/` de este dossier y fija el límite de tráfico, la identificación y qué NO se hace.
2. **`src/melate/popularity.py`** — descarga y parsea las tablas de ganadores por categoría con
   Scrapling (`Fetcher`/`FetcherSession`, caché en disco, 1 solicitud por segundo), y de ellas
   estima:
   - las **ventas** (combinaciones jugadas) de cada sorteo,
   - el **`menores_brutos`** real, que hoy está escrito a mano en `baseline_auditoria.py:252` con
     los valores de las tablas 4271/4272 y **caduca**,
   - la **popularidad relativa de cada número**, que es lo que `portfolio.py` necesita.
3. **`src/melate/portfolio.py`** — carteras de boletos con presupuesto fijo, usando la popularidad
   para evitar combinaciones compartidas.
4. **Tests** de todo lo anterior, incluida la propiedad que de verdad importa: que **la cartera no
   mejora el valor esperado**, y que ninguna salida pueda sugerir lo contrario.

## Qué NO entra

- **`baseline_auditoria.py` no se toca.** Sigue siendo el oráculo y `tests/test_paridad.py` sigue
  siendo bloqueante con tolerancia cero. En concreto: **el valor por defecto de `menores_brutos` en
  `src/melate/ev.py` no cambia**, porque el oráculo llama a `valor_esperado(juegos)` sin argumento y
  cualquier cambio del defecto rompería la paridad. Lo medido entra por una **clave nueva declarada**,
  igual que hizo la Fase 2 con `q_BH_global`.
- **No se añaden estrategias de predicción.** La popularidad **no predice la urna**: dice qué juega
  la gente. No es una hipótesis sobre el sorteo y **no entra en la familia de Benjamini-Hochberg**.
  Si alguna vez se usara para predecir números, eso sería otra decisión y llevaría su documento.
- **No se declara ninguna ventaja.** El veredicto sigue siendo `sin ventaja demostrada`, y la cartera
  no lo cambia: el EV de un boleto sigue siendo negativo y la cartera no lo mejora.
- **No se raspa el histórico completo** sin una decisión explícita del usuario. Ver el dictamen.
- **La app** es de la Fase 4.

## Criterio de terminado

1. El dictamen de términos escrito y fechado **antes** que `popularity.py`, con hechos verificados,
   no promesas.
2. `popularity.py` descarga, cachea y parsea las tablas de los tres juegos, y respeta el límite de
   tráfico de forma **comprobable con un test**, no de palabra.
3. El `menores_brutos` medido se publica con su procedencia (regla 6: sorteos usados y fecha de
   descarga), y la diferencia contra el valor escrito a mano queda explicada.
4. `portfolio.py` arma una cartera con presupuesto fijo, y **cada salida dice que el EV es negativo**.
5. `pytest tests` en verde con la paridad intacta.
6. Cada número publicado, vuelto a medir; cada parámetro del que se diga que gobierna algo, probado
   con dos valores distintos
   (`Protocolo_Estadistico/Bugs/2026-10-03_01-59_auditoria-retrospectiva-fases-1-y-2.md`).
7. Bitácora íntegra, colador limpio y la hoja de ruta del `_MAPA.md` actualizada.

## Estado de partida

El `Fases/2026-10-03_protocolo/99_CIERRE.md` de la Fase 2 y sus cinco pendientes heredados, de los
cuales esta fase recoge los que son suyos:

| Pendiente heredado | Qué hace esta fase |
|---|---|
| El `SystemExit` de `ingest._leer_bytes` sin ejercitar | Lo mira: la fase añade un segundo camino de red y el criterio debe ser el mismo |
| Nada probado fuera de Windows salvo finales de línea | Sigue pendiente; se declara, no se finge |
| Descripción del repositorio y correo privado en GitHub | **No son míos.** Son de la cuenta del usuario |

## Qué emitirá a las áreas base al cerrar

| Área | Por qué |
|---|---|
| `Conexiones/Añadir/` | Una fuente HTTP nueva y de terceros: el contrato, el límite y el dictamen |
| `Seguridad/Añadir/` | Primera vez que el proyecto hace tráfico saliente identificándose ante un tercero |
| `Almacenamiento/Añadir/` | La caché en disco de las páginas descargadas |
| `Estructura_Datos/Añadir/` | La forma de una tabla de ganadores y de la cartera |
| `Mapa/Modificar/` | `popularity.py` y `portfolio.py` entran en el mapa |
| `Protocolo_Estadistico/Añadir/` | Por qué la popularidad **no** entra en la familia de BH |
| `Despliegue/Añadir/` | La subida |

## Riesgos declarados

| Riesgo | Mitigación |
|---|---|
| Que la cartera se lea como "una forma de ganar" | Toda salida lleva el EV negativo y la frase de que no mejora. Hay test |
| Que el raspado moleste al sitio | Dictamen previo: 1 solicitud/segundo, caché en disco, identificación honesta, ventana acotada. Test del límite |
| Que Scrapling se use en modo evasión | `impersonate=None` y `stealthy_headers=False` explícitos. `StealthyFetcher` y `DynamicFetcher` prohibidos y **innecesarios**: la página es HTML estático |
| Que la popularidad se confunda con predicción | No entra en la familia de BH, y el documento de `Protocolo_Estadistico/` dice por qué |
| Que el `menores_brutos` medido rompa la paridad | El defecto de `ev.py` no se toca. Lo medido entra por clave nueva declarada |
| Que un estimador ruidoso se publique como si fuera estable | Se publica con su dispersión y el número de sorteos que lo sostienen |

## Premisas de las que depende

- `baseline_auditoria.py` es el oráculo y no se modifica.
- El espejo de GitHub es solo validación cruzada, nunca carga.
- Para declarar ventaja manda `q_BH_global`, la familia de 36 pruebas.
- La bitácora se publica; rutas relativas, nada personal.
- `pandas < 3` mientras el oráculo use `df.attrs`.
