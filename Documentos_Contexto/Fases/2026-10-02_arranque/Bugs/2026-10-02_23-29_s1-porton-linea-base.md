# Review s1 — el portón: reproducir la línea base del CLAUDE.md

- **Fecha/hora:** 2026-10-02 23:29
- **Área:** Fases/2026-10-02_arranque · **Acción:** Bugs
- **Chat / página:** sesión de arranque · etapa 4 del alcance
- **Archivos afectados:** `baseline_auditoria.py` (solo ejecutado, no modificado), `CLAUDE.md` (bajo
  sospecha), `data/raw/2026-10-02/*`, `reportes/2026-10-02_oraculo.json`

## Qué se hizo

Correr `baseline_auditoria.py` contra el snapshot congelado y comparar **cifra por cifra** contra la
sección "Línea base verificada" del `CLAUDE.md`. Es el portón del
`Fases/2026-10-02_arranque/00_ALCANCE.md`: si la línea base no reproduce, la fase se detiene.

```
.venv\Scripts\python.exe .\baseline_auditoria.py --datos .\data\raw\2026-10-02 --salida .\reportes\2026-10-02_oraculo.json
```

Duración 84.5 s. Versiones: Python 3.13.9, numpy 2.5.3, pandas 2.3.3, scipy 1.18.1,
scikit-learn 1.9.1. Semillas del script: 20261001 (auditoría), 7 (backtest), `random_state=0` (HGB).

**Limitaciones del entorno, por delante:** no hay forma de saber con qué versiones de librería se
produjeron las cifras del `CLAUDE.md` — el documento no las registra, y ese hueco es precisamente lo
que la regla 6 del protocolo pide cerrar. Tampoco existe el fichero de datos original con el que se
calcularon. El diagnóstico de abajo tuvo que reconstruirlo por deducción, y lo consiguió.

## Review de fallas #1

- ✅ **Sorteos de la era 6/56:** Melate 2 184 · Revancha 2 184 · Revanchita 1 902. Coincide.
- ✅ **Chi-cuadrada Melate:** 52.1889 contra 52.19 del contrato.
- ✅ **Chi-cuadrada Revanchita:** 54.8280 contra 54.83.
- ✅ **Inicio del backtest:** concurso 2489 en Melate y Revancha, 2771 en Revanchita. Coincide.
- ✅ **Gradient boosting en Melate:** 0.6160. Exacto.
- ✅ **Aleatorio en Melate:** 0.6328. Exacto.
- ✅ **Premios mayores por bajas de `BOLSA`:** 69 · 61 · 35. Exacto.
- ✅ **Valor esperado del 4273:** −59 % · −49 % · −12 %, con λ = 0.037. Exacto.
- ✅ **Constantes del azar:** media 0.6429, log-loss 0.34050, efecto mínimo detectable 0.0477 con
  1 784 sorteos de prueba. Coincide con 0.642857, 0.340500 y 0.048.
- ❌ **Chi-cuadrada Revancha:** obtenido **42.2889**, el contrato dice **42.03**.
- ❌ **Regresión logística en Revancha:** obtenido **0.6839 (p = 0.017, q = 0.3465)**, el contrato
  dice **0.6861 (p = 0.011, q = 0.24)**.

Diez de doce exactas, y las dos fallas las dos en Revancha.

### El diagnóstico: una causa raíz, no dos

La escalera de diagnóstico del plan dice que, si fallan la regresión logística o el gradient
boosting, el sospechoso es la versión de scikit-learn. **Aquí no era eso**, y la chi-cuadrada lo
demostró: `estadisticas()` (`baseline_auditoria.py:99-108`) no tiene nada aleatorio ni nada de
scikit-learn, es aritmética determinista sobre los conteos de las 56 esferas. Si da otro número con
el mismo código, es que **los datos son otros**.

Comparación del snapshot oficial contra el espejo de GitHub, sorteo por sorteo, en la era 6/56:

| Juego | Sorteos comparados | Diferencias en R1–R6 |
|---|---|---|
| Melate | 2 184 | **0** |
| Revancha | 2 184 | **1** |
| Revanchita | 1 902 | **0** |

La única diferencia, en **Revancha concurso 3827 (26/11/2023)**:

```
oficial:  15  16  38  40  41  50
espejo:   15  16  38  40  41  54
```

Sustituyendo ese único valor por el del espejo, el script produce:

| Cifra | Con el oficial | Con el espejo | `CLAUDE.md` |
|---|---|---|---|
| Chi-cuadrada Revancha | 42.2889 | **42.0256** | **42.03** |
| Regresión logística Revancha | 0.6839 (p = 0.017) | **0.6861 (p = 0.011)** | **0.6861 (p = 0.011)** |

Las dos cifras encajan a la vez. **La línea base del `CLAUDE.md` se calculó con el espejo**, y el
espejo tiene mal el sexto número de ese sorteo.

### Cuál de los dos valores es el correcto

Tercera fuente independiente, consultada con **una sola** petición (no una descarga en masa):
`resultados.melate-e.com/revancha/sorteo/3827` da `15 16 38 40 41 50`, "domingo 26 de noviembre de
2023", y la tabla de ganadores de ese sorteo (0 de 6 aciertos, 4 de 5, 338 de 4, 8 127 de 3,
82 302 de 2).

Dos fuentes independientes contra una: **el oficial tiene razón, el espejo está mal.** El
`CLAUDE.md` ya documentaba que el espejo tiene errores de `BOLSA`; ahora consta que también tiene al
menos un error en los **números sorteados**, que es mucho más grave.

### Por qué ninguna validación de una sola fuente podía detectarlo

`[15, 16, 38, 40, 41, 54]` es una fila perfectamente válida: seis números distintos, en rango 1–56,
estrictamente ascendentes. Pasa las nueve comprobaciones de `validar()`
(`baseline_auditoria.py:72-85`) sin levantar una sola bandera. **Solo la comparación entre fuentes lo
encuentra** — exactamente lo que pide la regla 7 del `CLAUDE.md` ("oficial igual al espejo"), que
hasta ahora no estaba implementada en ninguna parte.

Esto es de la clase de fallos del §6 del `REGLAS-DOCUMENTACION.md`: sintácticamente correcto,
semánticamente equivocado.

### Qué cambia en las conclusiones del proyecto, y qué no

La regresión logística en Revancha era **el resultado más llamativo de toda la línea base**: la única
estrategia que parecía acercarse a batir al azar. El dato erróneo la inflaba.

| | `CLAUDE.md` (espejo) | Correcto (oficial) |
|---|---|---|
| Aciertos por boleto | 0.6861 | 0.6839 |
| Δ sobre el azar | +0.0432 | +0.0410 |
| p | 0.011 | 0.017 |
| q de Benjamini-Hochberg | 0.24 | 0.3465 |

**La conclusión del proyecto no cambia:** con el valor correcto sigue sin pasar el protocolo —q muy
por encima de 0.05—, así que el veredicto continúa siendo "sin ventaja demostrada". Lo que cambia es
que el número que más invitaba a seguir tirando de ese hilo era, en parte, un error de transcripción
de un tercero.

## Optimización

No aplica a este ciclo: no se ha escrito ni tocado código. `baseline_auditoria.py` sigue byte a byte
como estaba, que es su función —ser el oráculo— y está comprobado con su hash en el documento de
reproducibilidad.

**Lo que se decidió NO hacer, y por qué:** no se corrige el espejo ni se abre incidencia en su
repositorio. No es nuestro, y el proyecto no depende de que esté bien: depende de **detectar** cuándo
no lo está.

## Review de fallas #2 + review de seguridad

- ✅ **Determinismo del portón.** Dos corridas del backtest de Revancha, con los dos valores del
  sorteo 3827, dieron en ambos casos `Aleatorio = 0.6469` idéntico: el RNG de numpy consume en el
  mismo orden y no depende de los datos. El cambio se propaga solo por donde debe.
- ✅ **Versiones de librería exoneradas.** Diez cifras exactas al cuarto decimal, incluidas las dos
  que pasan por scikit-learn (gradient boosting en Melate 0.6160 y la propia regresión logística en
  Revancha cuando se le da el dato del espejo). No hay que bisecar las 9 versiones de sklearn: la
  combinación instalada reproduce la línea base.
- ✅ **Integridad del snapshot.** Los tres SHA-256 recalculados después de un reinicio del equipo
  coinciden con `SHA256.txt`.
- ✅ **Superficie de red.** Tres peticiones GET a `loterianacional.gob.mx` (la descarga del
  snapshot), tres a `raw.githubusercontent.com` (el espejo, solo en memoria, no se guardó) y **una**
  a `resultados.melate-e.com`. Ninguna autenticada, ninguna con datos enviados, ningún fichero
  descargado fuera de `data/raw/2026-10-02/`.
- ✅ **Nada personal en lo escrito.** Los documentos de esta fase usan rutas relativas a la raíz del
  repositorio. El colador se ejecuta antes del primer push, no ahora.
- ✅ **Sin credenciales.** Confirmado en la práctica: las tres fuentes respondieron 200 sin
  autenticación de ningún tipo.

## Observación aceptada (no es bug)

La detección del formato de fecha en `baseline_auditoria.py:62` mira `df["FECHA"].iloc[0]` **antes**
de ordenar por `CONCURSO`, y el CSV oficial llega en orden descendente. Parece un error de orden de
operaciones, pero no lo es: la comprobación solo busca si hay una `/` para distinguir `dd/mm/aaaa` de
`aaaa-mm-dd`, y eso es una propiedad del fichero entero, no de una fila concreta. Queda registrado
para que nadie lo vuelva a investigar ni lo "arregle" moviendo la línea.

## Resultado

**Bugs abiertos: sí, uno, y no está en el código.** Dos cifras de la sección "Línea base verificada"
del `CLAUDE.md` descansan sobre un dato erróneo de un tercero:

- chi-cuadrada de Revancha: dice 42.03, lo correcto es **42.29**
- regresión logística en Revancha: dice 0.6861 (p = 0.011, q = 0.24), lo correcto es
  **0.6839 (p = 0.017, q = 0.3465)**

El `CLAUDE.md` es el contrato del proyecto y lo escribió el usuario. Corregirlo es decisión suya, no
mía, igual que decidir qué papel juega el espejo de aquí en adelante: hoy
`_leer_texto` (`baseline_auditoria.py:44-53`) lo usa como *fallback* silencioso si el oficial falla,
lo que significa que una caída del sitio oficial haría entrar datos con un error conocido sin que
nada avise. **Ambas decisiones quedan pendientes de consulta y este documento no se cierra hasta
tenerlas.**

**El portón, en cuanto al código: superado.** `baseline_auditoria.py` reproduce las 12 de 12 cifras
del contrato cuando se le dan los mismos datos con los que se calcularon. No hay nada que arreglar en
el script, y el refactor de la etapa 5 del alcance puede proceder en cuanto se resuelva lo de arriba.

## Cómo verificar / revertir

**Verificar el portón:**

```powershell
Get-FileHash .\data\raw\2026-10-02\*.csv -Algorithm SHA256   # debe cuadrar con SHA256.txt
.venv\Scripts\python.exe .\baseline_auditoria.py --datos .\data\raw\2026-10-02 --salida .\reportes\comprobacion.json
```

**Verificar el diagnóstico** (la diferencia del sorteo 3827 y la cifra que produce):

```powershell
Select-String .\data\raw\2026-10-02\Revancha.csv -Pattern '^41,3827,'
# -> 41,3827,15,16,38,40,41,50,234700000,26/11/2023
```

Y contra el espejo, en el navegador o con una petición:
`raw.githubusercontent.com/pakinja/pakin/master/Revancha.csv`, fila del concurso 3827 → termina en
`54`.

**Revertir:** no aplica. Este ciclo no modificó ningún fichero del proyecto; solo creó
`reportes/2026-10-02_oraculo.json`, que se puede borrar y regenerar con el comando de arriba.

**Pendiente de verificar / decidir** — el ciclo NO está cerrado sin esto:

1. **Consultar al usuario** si se corrigen las dos cifras de Revancha en el `CLAUDE.md`. Si se
   corrigen, hay que buscar con `Select-String` todos los documentos que citen `42.03`, `0.6861`,
   `0.011` o `0.24` y corregirlos en el mismo ciclo (§8 del `REGLAS-DOCUMENTACION.md`).
2. **Consultar al usuario** qué papel juega el espejo: *fallback* silencioso como ahora, *fallback*
   que avise, o solo fuente de validación cruzada y nunca de carga.
3. Implementar la regla 7 del `CLAUDE.md` ("oficial igual al espejo") como test, que es lo único que
   detecta esta clase de error. Va en `tests/test_reglas_datos.py` de la etapa 7 del alcance.
4. Comprobar si el espejo tiene más diferencias **fuera** de la era 6/56, que esta comparación no
   cubrió.

Relacionado: `Fases/2026-10-02_arranque/00_ALCANCE.md`,
`Fases/2026-10-02_arranque/Inventario/2026-10-02_22-07_s0-estado-heredado.md`

---

## Resultado — CERRADO el 2026-10-03 a las 00:03

Los cuatro pendientes, ejecutados:

**1 · Las dos cifras del `CLAUDE.md`: corregidas.** El usuario decidió corregirlas **y** añadir su
procedencia. Chi-cuadrada de Revancha pasa de 42.03 a **42.29 (p = 0.22)**; regresión logística en
Revancha, de 0.6861 (p = 0.011, q = 0.24) a **0.6839 (p = 0.017, q = 0.35)**. La sección gana un
apartado con los tres SHA-256, las tres semillas y las versiones de librería, más una cita en bloque
que deja constancia de los valores anteriores y de por qué estaban mal. Detalle en
`Fases/2026-10-02_arranque/Cambios/2026-10-02_23-52_s1-correccion-cifras-revancha-claude-md.md`.

**2 · El papel del espejo: solo validación cruzada, nunca carga.** Decisión del usuario.
`melate.ingest.cargar()` lee solo del oficial y, si falla, levanta `SystemExit` explicando por qué no
hay respaldo automático; `cargar_espejo()` existe aparte y su único consumidor es el test de la
regla 7. Implementación y porqué largo en
`Fases/2026-10-02_arranque/Cambios/2026-10-03_00-03_s1-paquete-src-melate.md`.

**3 · La regla 7, implementada como test.**
`tests/test_reglas_datos.py::test_regla7_oficial_contra_espejo`, marcado `red`, compara los tres
juegos sorteo a sorteo con su excepción conocida escrita como dato. Si aparece una diferencia nueva,
falla a propósito. En verde con la excepción de Revancha 3827.

**4 · El espejo, comparado en TODO el fichero, no solo en la era.** Resultado, con los ficheros
completos:

| Juego | Filas comunes | Diferencias en números | Diferencias en `BOLSA` |
|---|---|---|---|
| Melate | 2 187 | 0 | 0 |
| Revancha | 2 187 | **1** (3827) | 0 |
| Revanchita | 1 902 | 0 | **1** (3380) |

El error de números del espejo es **único en todo el histórico comparable**, y la discrepancia de
`BOLSA` es exactamente la que el `CLAUDE.md` ya documentaba (Revanchita 3380: 54.7 M del espejo
contra 57.4 M del oficial). Ninguna sorpresa adicional.

### Un hallazgo no previsto, y oportuno

Durante esa comparación se descubrió que **el sorteo 4273 ya se había celebrado** (2026-10-02): el
espejo traía Revancha 4273 (`8 9 32 37 51 55`) y Revanchita 4273 (`16 29 31 42 48 56`), pero **no**
Melate 4273, y el oficial todavía no había publicado ninguno de los tres.

Dos consecuencias concretas:

- **Congelar el snapshot antes de la corrida fue lo que salvó la fase.** Si el portón se hubiera
  corrido contra la descarga en vivo unas horas más tarde, no habría habido forma de distinguir
  "el código está mal" de "llegaron datos nuevos", y el error del espejo probablemente no se habría
  encontrado nunca.
- **Es la prueba empírica de la decisión 2.** El espejo estaba, en ese momento, con dos juegos en el
  sorteo N+1 y uno en el N. Un respaldo silencioso habría cargado los tres juegos terminando en
  sorteos distintos, rompiendo la comparación pareada entre juegos de la regla 5 del protocolo y
  descolocando el valor esperado, que lee la bolsa de la última fila.

### El portón, superado

`baseline_auditoria.py` reproduce **las 12 de 12** cifras del contrato cuando se le dan los datos
con los que se calcularon. No hubo que bisecar ninguna versión de scikit-learn: numpy 2.5.3,
pandas 2.3.3, scipy 1.18.1 y scikit-learn 1.9.1 reproducen la línea base. No había nada que arreglar
en el script, y no se tocó.

**Bugs abiertos al cerrar: ninguno.** El ciclo del refactor que vino después tiene su propia review
en `Fases/2026-10-02_arranque/Bugs/2026-10-03_00-03_s1-review-refactor-y-tests.md`.
