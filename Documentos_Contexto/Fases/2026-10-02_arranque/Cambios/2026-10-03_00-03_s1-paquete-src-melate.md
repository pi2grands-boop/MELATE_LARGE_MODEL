# El paquete `src/melate/`: traslado literal del oráculo, con tres añadidos declarados

- **Fecha/hora:** 2026-10-03 00:03
- **Área:** Fases/2026-10-02_arranque · **Acción:** Cambios
- **Chat / página:** sesión de arranque · etapas 5 y 6 del alcance
- **Archivos afectados:** `src/melate/{__init__,constantes,ingest,validate,audit,protocolo,backtest,ev,informe}.py`,
  `pyproject.toml`

## Qué se hizo

Las 322 líneas de `baseline_auditoria.py` pasan a ocho módulos. **El fichero original no se toca**:
queda como oráculo, y `tests/test_paridad.py` exige que el paquete produzca su mismo reporte.

| Destino | Qué se movió, y de dónde |
|---|---|
| `constantes.py` | `N`, `K`, `C`, `OFICIAL`, `ESPEJO`, `JUEGOS`, `PRIMER_SORTEO_56`, `PRECIO`, `BOLSA_MINIMA` (líneas 29-36) y `MEDIA_AZAR`, `VAR_AZAR`, `P_3_O_MAS` (160-162) |
| `ingest.py` | `_leer_texto` → `_leer_bytes`, `cargar` (39-69), `matriz` (92-96) |
| `validate.py` | `validar`, `era_56` (72-90) |
| `audit.py` | `estadisticas`, `simular`, `auditar`, `n_necesario`, `sesgo_minimo` (99-157) |
| `protocolo.py` | `benjamini_hochberg` (140-144) |
| `backtest.py` | `variables`, `top6`, `backtest` (164-237) |
| `ev.py` | `premios_mayores`, `valor_esperado` (240-262) |
| `informe.py` | `main` (265-319), como `python -m melate.informe` |

**La aritmética está copiada literalmente**, incluidas las líneas con varias sentencias separadas
por `;`. Reformatear habría parecido gratis y no lo es: la paridad al cuarto decimal es el único
control de que el traslado no cambió nada, y cualquier "mejora de paso" lo habría contaminado.

### Dos módulos que no están en la estructura sugerida del CLAUDE.md

- **`constantes.py`** — los mismos valores los usan `ingest`, `validate`, `audit`, `backtest` y
  `ev`. Repartirlos por el módulo que "más los use" garantiza que un día dejen de coincidir.
  Además guarda las tres semillas con nombre (`SEMILLA_AUDITORIA`, `SEMILLA_BACKTEST`,
  `SEMILLA_HGB`): antes eran literales sueltos en tres sitios, y son lo que hace reproducibles las
  cifras publicadas.
- **`protocolo.py`** — `benjamini_hochberg` la usan auditoría y backtest, y la familia global
  necesita un dueño único que conozca las dos familias a la vez. Es también donde vivirá
  `declara_ventaja()` en la Fase 2, así que el módulo tiene futuro, no es un cajón.

`popularity.py`, `portfolio.py` y `lab.py` **no se crearon**: no tienen contenido todavía, y
ficheros vacíos para parecerse a un diagrama son ruido.

### Un cambio de comportamiento, deliberado: el espejo deja de ser respaldo de carga

Decisión del usuario, tomada con la evidencia del portón delante. `baseline_auditoria.py` intenta
el oficial y, si falla, carga del espejo **en silencio** (líneas 44-53). En el paquete:

- `cargar()` lee solo del oficial. Si falla, levanta `SystemExit` con un mensaje que dice por qué no
  hay respaldo automático y qué hacer en su lugar.
- `cargar_espejo()` existe aparte, explícita, y su único consumidor es el test de la regla 7.

Tres razones, y las tres son hechos medidos hoy, no precauciones:

1. El espejo tiene **mal el sexto número de Revancha 3827** (dice 54 donde el oficial y
   melate-e.com dan 50). Es un error invisible a toda validación de una sola fuente, porque la fila
   es formalmente válida.
2. El espejo puede estar **parcialmente actualizado**: se observó con Revancha y Revanchita en el
   sorteo 4273 mientras Melate seguía en el 4272. Cargar así daría los tres juegos terminando en
   sorteos distintos, lo que rompe la comparación pareada entre juegos que exige la regla 5 del
   protocolo y descoloca el valor esperado, que lee la bolsa de la última fila.
3. Un respaldo silencioso convierte una caída del sitio oficial en datos malos **sin que nada
   avise**, que es la peor forma posible de fallar en un proyecto cuyo propósito es medir con
   cuidado.

Esto no rompe la paridad: con `--datos` ninguno de los dos programas toca la red.

### Lo que el paquete añade al reporte, y nada más

Tres claves, declaradas en `melate.informe.NUEVAS_CLAVES` para que el test de paridad sepa qué puede
ignorar. Ninguna cifra del oráculo cambia.

1. **`reproducibilidad`** — regla 6 del protocolo. SHA-256, origen y tamaño de cada CSV cargado, las
   tres semillas, el número de simulaciones, la hora UTC y las versiones de Python, numpy, pandas,
   scipy y scikit-learn. El hash sale de `df.attrs`, es decir de **los bytes que se analizaron**:
   la primera versión volvía a leer la fuente para hashear, y con el oficial a punto de publicar el
   sorteo 4273 eso podía registrar el hash de otros datos (ver el `Bugs/` de esta misma fase).
2. **`validacion_era_56`** — las nueve comprobaciones de `validar()`, pero sobre la era que se
   analiza. `validar()` corre sobre el fichero crudo, y en Melate eso incluye 1984-2007: reporta 174
   filas con `BOLSA` < 1 M de las que **solo 3 son errores reales**. El dato útil quedaba sepultado.
   La clave original no se toca.
3. **`q_BH_global`** y **`protocolo_global`** — la familia única de 36 pruebas que pide la regla 3
   (15 de auditoría + 21 de backtest; la estrategia aleatoria es la referencia, no una hipótesis).
   `q_BH` se conserva con las dos familias del oráculo porque es lo que produce los `q` publicados;
   para declarar ventaja manda la global. Con los datos del 4272, la q global mínima es **0.306** y
   el veredicto es *sin ventaja demostrada*.

### Empaquetado

`pyproject.toml` con `setuptools`, disposición `src/`, y `pip install -e .`. Así
`python -m melate.informe` y los imports de los tests funcionan sin tocar `sys.path`. También
declara los *markers* `lento` y `red` de pytest y las mismas restricciones de versión que
`requirements.txt`.

## Por qué

El `CLAUDE.md` describe esta estructura y el alcance de la fase la aprueba. El motivo de fondo es
que un fichero de 322 líneas que hace seis cosas no se puede extender sin miedo: la Fase 2 añade
preregistro, la 3 popularidad y cartera, la 4 una app. Sin separar las piezas, cada añadido toca el
mismo fichero y cualquier cambio puede mover una cifra publicada sin que nadie se entere.

El oráculo existe precisamente para eliminar ese miedo. Mientras `baseline_auditoria.py` esté
intacto y el test de paridad en verde, cualquier refactor es demostrable.

## Impacto en seguridad / conexiones / datos

- **Seguridad:** mejora, y es la parte menos obvia del cambio. El respaldo silencioso al espejo era
  una vía por la que entraban datos de un tercero con un error conocido, sin aviso. Ya no existe.
  Nada se ejecuta en tiempo de import; no se leen variables de entorno ni ficheros de
  configuración; no hay credenciales porque las fuentes son GET público.
- **Conexiones:** cambia el contrato. Antes: oficial con respaldo automático al espejo. Ahora:
  oficial, y punto; el espejo solo bajo llamada explícita y solo para validar. Con `--datos` no hay
  ninguna conexión.
- **Datos:** ningún fichero de datos se modificó. El reporte gana tres claves y no pierde ninguna.

## Cómo verificar / revertir

```powershell
.venv\Scripts\python.exe -m pip install -e .
.venv\Scripts\python.exe -m melate.informe --datos .\data\raw\2026-10-02 --salida .\reportes\paquete.json
.venv\Scripts\python.exe -m pytest tests\test_paridad.py -v     # el que de verdad lo prueba
```

Que el espejo ya no es respaldo de carga, sin esperar a que el oficial se caiga:

```powershell
.venv\Scripts\python.exe -c "import inspect, melate.ingest as i; print('ESPEJO' in inspect.getsource(i._leer_bytes))"
# -> False: _leer_bytes no menciona el espejo salvo en el texto del error
```

**Revertir:** borrar `src/` y `pyproject.toml`, y `pip uninstall melate`. `baseline_auditoria.py`
sigue funcionando por sí solo. **Lo que se reintroduce al revertir:** el respaldo silencioso al
espejo, la ausencia de hash y semillas en el reporte, la validación ahogada en 174 falsos positivos,
y la familia de Benjamini-Hochberg sin la corrección global que pide la regla 3.

Relacionado: `Fases/2026-10-02_arranque/Bugs/2026-10-03_00-03_s1-review-refactor-y-tests.md`,
`Fases/2026-10-02_arranque/Bugs/2026-10-02_23-29_s1-porton-linea-base.md`,
`Fases/2026-10-02_arranque/Cambios/2026-10-03_00-03_s1-tests.md`,
`Fases/2026-10-02_arranque/Cambios/2026-10-02_23-52_s1-correccion-cifras-revancha-claude-md.md`
