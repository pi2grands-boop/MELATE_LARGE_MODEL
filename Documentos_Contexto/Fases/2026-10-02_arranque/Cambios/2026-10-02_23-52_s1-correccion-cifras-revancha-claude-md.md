# Corregidas dos cifras de Revancha en el CLAUDE.md, y añadida su procedencia

- **Fecha/hora:** 2026-10-02 23:52
- **Área:** Fases/2026-10-02_arranque · **Acción:** Cambios
- **Chat / página:** sesión de arranque · etapa 4 del alcance, cierre del portón
- **Archivos afectados:** `CLAUDE.md`, `entorno/pip-freeze-2026-10-02.txt`

## Qué se hizo

Cuatro cambios en `CLAUDE.md`, el contrato del proyecto. Decisión del usuario, consultada con la
evidencia del `Bugs/` delante.

**1 · Las dos cifras erróneas de la sección "Línea base verificada":**

| Cifra | Antes | Ahora |
|---|---|---|
| Chi-cuadrada corregida, Revancha | 42.03 (p = 0.21) | **42.29 (p = 0.22)** |
| Regresión logística, Revancha | 0.6861 aciertos (p = 0.011, q = 0.24) | **0.6839 aciertos (p = 0.017, q = 0.35)** |

Valores exactos del reporte, para quien necesite más decimales: chi-cuadrada 42.2889 con p de dos
colas 0.2239; regresión logística 0.6839 aciertos, Δ = +0.0410 sobre el azar, p = 0.017,
q de Benjamini-Hochberg 0.3465.

**2 · Añadido un apartado "Procedencia de estas cifras (regla 6 del protocolo)"** con los tres
SHA-256 del snapshot, las tres semillas y las versiones de Python, numpy, pandas, scipy y
scikit-learn. Y una cita en bloque que deja constancia de cuáles eran los valores anteriores y por
qué estaban mal, para que nadie que haya leído la versión vieja crea que se le escondió el cambio.

**3 · Añadida una frase de veredicto** al final de la lista de cifras: ninguna estrategia bate al
azar, el mejor caso está en q = 0.35 contra el 0.05 que pide el protocolo, y el resultado es "sin
ventaja demostrada". Antes había que deducirlo de los números.

**4 · Advertido que la línea base se corre contra el snapshot**, no contra la descarga en vivo, con
el comando `--datos data/raw/2026-10-02` en el propio texto.

Dos cambios más, en otras secciones, que salen del mismo hallazgo:

**5 · La fila del espejo en la tabla de fuentes** pasa de "respaldo y validación" a **"solo
validación cruzada, nunca carga"**, y suma dos defectos documentados: el error en los números de
Revancha 3827, y que puede estar parcialmente actualizado —se observó con Revancha y Revanchita en
el sorteo 4273 mientras Melate seguía en el 4272.

**6 · La regla 7 de datos** ("oficial igual al espejo") gana su excepción conocida, con los dos
valores enfrentados, con quién manda, y con la advertencia de que este error es invisible a
cualquier validación de una sola fuente porque la fila del espejo es formalmente válida.

Y en la línea del stack: `pandas` queda anotado como **`<3`**, con el motivo, y se apunta a
`requirements.txt` y `entorno/` para las versiones exactas. `entorno/pip-freeze-2026-10-02.txt` es
nuevo: 23 paquetes y la versión de Python.

## Por qué

El portón de la fase comparó las 12 cifras del contrato contra una corrida real y 10 salieron
exactas. Las dos que no, las dos de Revancha, resultaron tener una sola causa raíz: el espejo de
GitHub tiene `54` donde el oficial y melate-e.com dan `50` en el sexto número del sorteo 3827, y la
línea base del contrato se había calculado con el espejo. Sustituyendo ese único número, el script
reproduce 42.03 y 0.6861 al cuarto decimal — es decir, el código nunca estuvo mal.

Dejar el contrato como estaba tenía un coste concreto e inmediato: los tests de línea base de la
etapa 7 del alcance no podrían usarlo como expectativa, porque dos de sus cifras son irreproducibles
con los datos correctos. Y quien llegara nuevo al proyecto leería primero dos números que su propio
código no produce.

La procedencia se añadió porque el hueco que permitió que esto pasara inadvertido era precisamente
ese: el contrato declaraba cifras **sin decir con qué datos ni con qué versiones** se obtuvieron. La
regla 6 del protocolo lo pedía para cada corrida; ahora también lo cumple el documento que las
publica.

El cambio de papel del espejo es la otra decisión del usuario del mismo ciclo, y se escribe aquí
porque el contrato lo describía como fuente de carga. Su implementación en el paquete —y el porqué
largo— van en sus propios documentos.

## Impacto en seguridad / conexiones / datos

- **Seguridad:** sin impacto. `CLAUDE.md` no contiene rutas de la máquina ni datos personales; se
  revisó al editarlo. Los tres SHA-256 añadidos son hashes de ficheros públicos.
- **Conexiones:** cambia el **contrato** de una: el espejo deja de estar declarado como fuente de
  carga y queda como fuente de validación. El código todavía no lo refleja —`baseline_auditoria.py`
  no se toca nunca— y el cambio efectivo llega con `src/melate/ingest.py`.
- **Datos:** ninguno se modificó. El snapshot sigue con sus hashes intactos; lo que cambió es lo que
  el contrato dice **sobre** ellos.

## Cómo verificar / revertir

**Verificar que las cifras nuevas son las que produce el código:**

```powershell
.venv\Scripts\python.exe .\baseline_auditoria.py --datos .\data\raw\2026-10-02 --salida .\reportes\comprobacion.json
# chi2 Revancha -> 42.2889   |   Regresión logística Revancha -> 0.6839 (p = 0.017)
```

**Verificar que el dato de origen es el correcto**, con las dos fuentes que mandan:

```powershell
Select-String .\data\raw\2026-10-02\Revancha.csv -Pattern '^41,3827,'
# -> 41,3827,15,16,38,40,41,50,234700000,26/11/2023
```

y `resultados.melate-e.com/revancha/sorteo/3827`, que da `15 16 38 40 41 50` el domingo 26 de
noviembre de 2023.

**Verificar que no quedan números viejos citados como vigentes** en ningún sitio:

```powershell
Select-String -Path .\*.md,.\Documentos_Contexto\*\*\*.md -Pattern '42\.03','0\.6861','q = 0\.24'
```

Debe aparecer **solo** dentro de contextos que los citan como el valor erróneo: este documento, el
`Bugs/` del portón, la cita en bloque del `CLAUDE.md` y el inventario `s0`. Que el `s0` los conserve
es correcto y deliberado: es el inventario del estado heredado, su trabajo es decir qué decía el
contrato cuando se abrió la fase, y los documentos de inventario no se reescriben.

**Revertir:** en `CLAUDE.md`, volver a poner `42.29 (p = 0.22)` como `42.03 (p = 0.21)` y
`0.6839 aciertos (p = 0.017, q = 0.35)` como `0.6861 aciertos (p = 0.011, q = 0.24)`, borrar el
apartado "Procedencia de estas cifras", la frase del veredicto, la excepción de la regla 7 y los dos
defectos añadidos a la fila del espejo. Y borrar `entorno/pip-freeze-2026-10-02.txt`.

**No se recomienda**: se reintroducirían dos cifras que el código no puede reproducir con los datos
correctos, y se perdería la única constancia de con qué versiones de librería se obtuvieron.

Relacionado: `Fases/2026-10-02_arranque/Bugs/2026-10-02_23-29_s1-porton-linea-base.md`,
`Fases/2026-10-02_arranque/00_ALCANCE.md`
