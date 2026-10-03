# Review s2 — los pendientes que la Fase 1 dejó sin verificar

- **Fecha/hora:** 2026-10-03 01:05
- **Área:** Fases/2026-10-03_protocolo · **Acción:** Bugs
- **Chat / página:** sesión de arranque · apertura de la Fase 2
- **Archivos afectados:** `src/melate/informe.py`, `tests/conftest.py`, `tests/test_paridad.py`

## Qué se hizo

Ejecutar la lista de "pendiente de verificar en vivo" del `Fases/2026-10-02_arranque/99_CIERRE.md`.
La Fase 1 se cerró con siete puntos que su entorno no permitía comprobar, y un ciclo no está cerrado
de verdad mientras esa lista no se corre.

**Limitaciones del entorno, por delante:** no hay una máquina Linux ni macOS disponible, así que el
punto sobre otros sistemas operativos no se puede ejecutar literalmente. Se ejecutó **lo que de
verdad importaba de él** —la conversión de finales de línea— emulando el checkout de Linux desde
Windows, que es un sustituto fiel para ese riesgo concreto pero no para el resto.

## Review de fallas #1

### ✅ 1 · Clon limpio y hashes, emulando Linux

```
git -c core.autocrlf=false -c core.eol=lf clone <url> clon-lf
cd clon-lf/data/raw/2026-10-02 && sha256sum -c SHA256.txt
```

```
Melate.csv: OK
Revancha.csv: OK
Revanchita.csv: OK
```

Los tres CSV conservan sus 4273 / 3265 / 1903 terminaciones CRLF intactas tras el clon. **El
`.gitattributes` de la Fase 1 funciona**: el riesgo era que un checkout con finales de línea LF
—lo que haría Linux o macOS— cambiara los bytes y con ellos el SHA-256, dejando inservible el hash
publicado justo para quien lo necesita. No ocurre.

Forzar `core.eol=lf` es lo que hace válida la prueba desde Windows: un clon normal en Windows
devolvería CRLF por el camino equivocado (normalizar a LF y volver a convertir) y no distinguiría
los dos casos.

### ❌ 2 · Entorno nuevo y suite completa en el clon limpio — **17 de 53 tests fallaban**

Este es el hallazgo de la fase.

```
python -m venv .venv && pip install -r requirements.txt && pip install -e . && pytest tests
-> 1 failed, 35 passed, 16 errors
```

La instalación fue limpia y las versiones las correctas (numpy 2.5.3, pandas 2.3.3, scipy 1.18.1,
scikit-learn 1.9.1). Lo que falló fueron **todos los tests que lanzan un subproceso**, con una sola
causa raíz:

```
UnicodeEncodeError: 'charmap' codec can't encode character 'Δ'
stdout encoding: cp1252 | isatty: False
```

El resumen del informe imprime `Δ`, `≈` y `–`. **Ninguno existe en cp1252**, la página de códigos
ANSI de este Windows. Cuando la salida va a una tubería o a un fichero, Python usa la codificación
local y esos caracteres lanzan `UnicodeEncodeError` **a mitad del informe**, después de haber gastado
el minuto de cómputo. En una consola de verdad no pasa, porque Windows usa un escritor UTF-16 aparte.

Y lo peor del fallo no es el fallo: **dependía del shell desde el que se lanzara pytest.** La misma
suite, el mismo commit, el mismo repositorio — pasaba desde PowerShell y fallaba desde Bash. Así
había pasado toda la Fase 1 inadvertido, con 52 tests en verde. *Un test que pasa o falla según
quién lo corra no protege nada.*

→ **Corregido, con dos arreglos porque hay dos públicos:**

- **`melate.informe._salida_robusta()`** — si la salida está redirigida, pasa a UTF-8, que es lo que
  espera quien la consume; si es una consola, respeta su codificación y solo añade
  `errors="replace"`, para degradar a `?` en vez de reventar. Se llama al principio de `construir()`,
  no al importar: ningún módulo tiene efectos al importarse.
- **`tests/conftest.py`** — fija `PYTHONIOENCODING=utf-8` en los subprocesos. Es la **única** solución
  posible para `baseline_auditoria.py`, que tiene el mismo fallo latente y **no se modifica nunca**,
  y mantiene la comparación de paridad simétrica entre los dos programas.

→ **Y un test que lo fija:** `test_el_informe_sobrevive_a_una_codificacion_hostil` fuerza
`PYTHONIOENCODING=cp1252` y exige que el informe acabe y escriba el JSON. **Verificado que tiene
dientes:** desactivando `_salida_robusta()` a mano, el test falla; restaurándolo, pasa.

Después del arreglo, en el clon limpio desde cero: **53 tests en verde**, y los hashes cuadran.

### ✅ 3 · El informe sin `--datos`, contra la descarga en vivo

El camino de red no se había ejercitado desde que se le quitó el respaldo al espejo. Funciona, y de
paso da una verificación que no estaba prevista: **los hashes que registra la corrida en vivo son
idénticos a los del snapshot congelado**, en los tres juegos. Eso valida a la vez el camino de
descarga, el hash tomado desde `df.attrs` y que el snapshot es copia fiel del oficial.

El oficial, a esta hora, sigue publicando hasta el 4272 aunque el espejo ya tenga el 4273 de Revancha
y Revanchita. Otra confirmación del desalineamiento que motivó quitarlo como fuente de carga.

### ❌ 4 · El `SystemExit` de `_leer_bytes` — **sigue sin ejercitarse**

El sitio oficial no ha fallado en ninguna de las corridas de esta sesión, así que ese camino de error
nunca se ha ejecutado. No se fuerza artificialmente: inyectar un fallo de red requeriría un *mock*
que probaría el *mock*, no el código. Pasa a los pendientes de esta fase.

### ⚠️ 5 · Nada probado en Linux ni macOS

Sigue siendo verdad para todo lo que no sea la conversión de finales de línea. Los comandos
documentados usan `.venv\Scripts\` y los dos scripts de verificación son PowerShell. No es un bug —
el proyecto es local y de este equipo— pero el README no lo dice, y debería.

### ⚠️ 6 y 7 · Descripción del repositorio y correo privado en GitHub

Las dos necesitan la cuenta del usuario. Siguen pendientes, y son de él, no mías.

## Optimización

Nada que optimizar: los dos arreglos suman 25 líneas y un `env` en el arnés.

**Lo que se decidió NO hacer:** no se tocó `baseline_auditoria.py`, aunque tiene el mismo fallo
latente de codificación. Es el oráculo y no se modifica, y para él la solución del arnés es
suficiente: lo único que lo ejecuta de forma automática son los tests. Un usuario que lo corra a mano
redirigiendo la salida se encontrará el fallo; queda registrado aquí como limitación conocida del
fichero heredado, no como bug pendiente.

## Review de fallas #2 + review de seguridad

- ✅ **La paridad de la Fase 1 sigue intacta** tras los dos arreglos: `test_paridad.py` en verde. Los
  cambios tocan la salida por pantalla, no el JSON.
- ✅ **`_salida_robusta` no puede tumbar el informe.** El `try/except` cubre el caso de un flujo sin
  `reconfigure`, y el fallo de reconfigurar no es motivo para abortar una corrida de dos minutos.
- ✅ **Nada se ejecuta al importar.** `_salida_robusta()` se llama dentro de `construir()`.
- ✅ **Colador limpio** sobre 56 ficheros, autoprueba 3/3.
- ✅ **Sin cambios en la superficie de red** ni en los datos.

## Observación aceptada (no es bug)

El clon limpio tardó 155 s en la suite contra 93 s en el repositorio de trabajo. Es el mismo efecto
de caché en frío que la Fase 1 ya registró con el oráculo: wheels recién instalados, `.pyd` fuera de
la caché de ficheros del sistema. No se compara una medida en frío con una en caliente.

## Resultado

**Bugs abiertos: ninguno.** El de codificación se corrigió en este mismo ciclo, con su test.

De los siete pendientes heredados: **tres ejecutados y en verde** (1, 2, 3), **uno sigue sin
ejercitarse** (4, el camino de error de red), **uno parcialmente cubierto** (5, solo la parte de
finales de línea) y **dos son del usuario** (6 y 7).

El hallazgo que justifica la práctica: la Fase 1 cerró con 52 tests en verde y, en otro shell, 17 de
ellos no pasaban. **Declarar algo verificado sin haberlo ejecutado en las condiciones reales es la
forma más rápida de que la bitácora deje de merecer confianza**, y aquí la lista de pendientes es lo
único que lo impidió.

## Cómo verificar / revertir

```powershell
# el arreglo, con la codificacion que lo rompia
.venv\Scripts\python.exe -m pytest tests\test_paridad.py -k hostil -v

# y que el test tiene dientes: quitar la llamada a _salida_robusta() de construir()
# y volver a correrlo. Tiene que fallar. Deshacer despues.
```

El clon limpio, de punta a punta:

```
git -c core.autocrlf=false -c core.eol=lf clone <url> /tmp/clon
cd /tmp/clon/data/raw/2026-10-02 && sha256sum -c SHA256.txt
cd /tmp/clon && python -m venv .venv && .venv/Scripts/python -m pip install -r requirements.txt -e .
.venv/Scripts/python -m pytest tests -q
```

**Revertir:** quitar `_salida_robusta` y su llamada de `informe.py`, el `env=entorno_utf8()` de
`conftest.py` y el test `hostil`. **No se recomienda:** la suite volvería a pasar o fallar según el
shell desde el que se lance.

**Pendiente de verificar** — hereda `Fases/2026-10-03_protocolo/99_CIERRE.md`:

1. El `SystemExit` de `_leer_bytes`, cuando el oficial falle de verdad.
2. Cualquier cosa fuera de Windows que no sean finales de línea.
3. Los dos puntos de la cuenta de GitHub, que son del usuario.

Relacionado: `Fases/2026-10-02_arranque/99_CIERRE.md`,
`Fases/2026-10-03_protocolo/00_ALCANCE.md`

---

## Resultado — CERRADO el 2026-10-03 a las 01:30

Lo ejecutado, con su evidencia:

| Pendiente heredado | Resultado |
|---|---|
| 1 · Clon limpio y hashes, en Linux o macOS | ✅ **Ejecutado** emulando el checkout de Linux (`core.eol=lf`). `sha256sum -c SHA256.txt` → OK en los tres |
| 2 · Entorno nuevo y suite en el clon | ❌ **17 de 53 fallaban** → causa raíz única encontrada y corregida, con test. Reejecutado: **53 en verde** |
| 3 · Informe sin `--datos` | ✅ **Ejecutado.** Funciona, y los hashes en vivo coinciden con el snapshot |
| 4 · El `SystemExit` de `_leer_bytes` | ⬜ **Sigue sin ejercitarse.** El oficial no ha fallado. Pasa a `Fases/2026-10-03_protocolo/99_CIERRE.md` |
| 5 · Fuera de Windows | ⚠️ **Parcial.** Cubierta la conversión de finales de línea; el resto, no |
| 6 · Descripción del repositorio | ⬜ Del usuario |
| 7 · Correo privado en GitHub | ⬜ Del usuario |

**El bug encontrado se corrigió en este mismo ciclo** y está fijado por
`test_el_informe_sobrevive_a_una_codificacion_hostil`, verificado con dientes: desactivando el
arreglo, el test falla.

Y la conclusión que vale más que el arreglo: la Fase 1 se cerró con 52 tests en verde, y 17 de ellos
no pasaban en otro shell. **La lista de pendientes es lo único que lo impidió.** Si se hubiera
cerrado declarando "verificado" sin ejecutarla, el proyecto habría arrastrado un fallo que solo
aparecía en casa de otro.
