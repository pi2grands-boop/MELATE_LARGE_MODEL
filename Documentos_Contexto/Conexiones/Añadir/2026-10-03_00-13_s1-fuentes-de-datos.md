# Las fuentes de datos: una carga, una validación, y por qué no se mezclan

- **Fecha/hora:** 2026-10-03 00:13
- **Área:** Conexiones · **Acción:** Añadir
- **Chat / página:** sesión de arranque · emitido al cerrar la Fase 1
- **Archivos afectados:** `src/melate/ingest.py`, `src/melate/constantes.py`,
  `tests/test_reglas_datos.py`

## Qué se hizo

Tres fuentes, con papeles **distintos y no intercambiables**. Esto es lo que cambia respecto al
código heredado, y es la conexión más importante del proyecto.

| Fuente | URL | Papel | Quién la llama |
|---|---|---|---|
| Oficial | `loterianacional.gob.mx/Documentos/Historicos/{juego}.csv` | **La única fuente de carga** | `ingest._leer_bytes` |
| Espejo | `raw.githubusercontent.com/pakinja/pakin/master/{juego}.csv` | **Solo validación cruzada** | `ingest.cargar_espejo`, llamada únicamente por el test de la regla 7 |
| melate-e.com | `resultados.melate-e.com/{juego}/sorteo/{n}` | Árbitro ante un conflicto, y tablas de ganadores (Fase 3) | Nadie todavía: una consulta manual en esta fase |

### El contrato de `cargar()`

```python
cargar(juego, carpeta=None)   # carpeta -> lee del disco, SIN red
                              # sin carpeta -> GET al oficial, y solo al oficial
```

- `timeout=30`, cabecera `User-Agent` propia.
- Acepta la respuesta solo si es HTTP correcto **y** contiene `CONCURSO` en los primeros 200 bytes.
- Devuelve los **bytes**, no el texto: el SHA-256 que se publica es el del fichero tal cual.
- Si el oficial falla, levanta `SystemExit` con un mensaje que explica por qué no hay respaldo
  automático y qué hacer en su lugar.
- Deja en `df.attrs` la `fuente`, el `sha256` y los `bytes` de **lo que realmente leyó**.

**El parseo indexa por nombre de columna, nunca por posición.** No es una preferencia de estilo: el
espejo trae tres columnas extra (`PRIMOS`, `REPETIDOS`, `MEDIA`), así que la `BOLSA` no está en el
mismo sitio que en el oficial. Durante la auditoría de esta fase, un parseo posicional hecho a mano
leyó `REPETIDOS` como `BOLSA` y dio resultados sin sentido. El código heredado ya lo hacía bien y se
conservó.

También: **el oficial llega en orden descendente** —la primera fila de datos es el sorteo más
reciente—, y `cargar` lo ordena por `CONCURSO`.

### Lo que cambió: el espejo ya no es respaldo de carga

`baseline_auditoria.py:44-53` intenta el oficial y, si falla, carga del espejo **en silencio**. En
el paquete eso desapareció, por decisión del usuario, con tres razones que son hechos medidos y no
precauciones:

1. **El espejo tiene mal el sexto número de Revancha 3827.** Dice 54 donde el oficial y melate-e.com
   dan 50. Dos de las cifras publicadas del proyecto se habían calculado con ese dato.
2. **El espejo puede ir desalineado entre juegos.** El 2026-10-02 traía Revancha y Revanchita en el
   sorteo 4273 mientras Melate seguía en el 4272. Cargar así daría los tres juegos terminando en
   sorteos distintos, lo que rompe la comparación pareada entre juegos de la regla 5 del protocolo y
   descoloca el valor esperado, que lee la bolsa de la última fila.
3. **Un respaldo silencioso convierte una caída del sitio oficial en datos malos sin aviso.**

Esto no afecta a la reproducción de cifras publicadas: con `--datos` no se toca la red.

### La validación cruzada, que es lo único que pilla un número mal transcrito

`tests/test_reglas_datos.py::test_regla7_oficial_contra_espejo`, marcado `red`. Compara los tres
juegos sorteo a sorteo y lleva su excepción conocida escrita **como dato**, no como tolerancia:

```python
EXCEPCIONES = {"Revancha": {3827: ([15, 16, 38, 40, 41, 50], [15, 16, 38, 40, 41, 54])}}
```

Si aparece una diferencia nueva, el test falla a propósito y su mensaje dice qué hacer: investigarla
con una tercera fuente antes de elegir un valor. Ampliar esa lista sin investigar convertiría el
único control que funciona en un sello de goma.

**Por qué hace falta cruzar fuentes:** la fila errónea del espejo es formalmente válida —seis
números distintos, en rango, ordenados— y pasa las nueve comprobaciones de `validar()` sin levantar
una sola bandera. Ninguna validación de una sola fuente podía encontrarla.

### Estado comprobado del espejo, en todo el fichero

| Juego | Filas comunes | Diferencias en números | Diferencias en `BOLSA` |
|---|---|---|---|
| Melate | 2 187 | 0 | 0 |
| Revancha | 2 187 | **1** (3827) | 0 |
| Revanchita | 1 902 | 0 | **1** (3380: 54.7 M contra 57.4 M) |

La de `BOLSA` es la que el `CLAUDE.md` ya documentaba.

## Por qué

La regla 7 del `CLAUDE.md` pide validar que el oficial es igual al espejo, y eso no existía en
ninguna parte del código heredado. Implementarlo no fue un trámite: es lo que encontró el error que
inflaba la cifra más llamativa del proyecto.

Separar carga de validación es la consecuencia lógica. Una fuente que sirve para **detectar**
discrepancias no sirve para **resolverlas** siendo ella misma el dato.

## Impacto en seguridad / conexiones / datos

- **Seguridad:** mejora. Se eliminó la vía por la que entraban datos de un tercero con un error
  conocido, sin aviso. Las tres fuentes son GET público sin autenticación: no hay credenciales que
  proteger, y conviene que siga siendo así.
- **Conexiones:** este documento **es** el contrato. Con `--datos` no hay ninguna.
- **Datos:** sin cambios en los ficheros. Cambia de dónde se permite que vengan.

## Cómo verificar / revertir

```powershell
.venv\Scripts\python.exe -m pytest tests -m red -q       # los 4 tests de red, con el espejo

# que _leer_bytes no conoce el espejo
.venv\Scripts\python.exe -c "import inspect, melate.ingest as i; print('ESPEJO' in inspect.getsource(i._leer_bytes))"
# -> False
```

**Revertir** al respaldo silencioso: en `ingest._leer_bytes`, sustituir el `raise SystemExit` por un
intento contra `ESPEJO.format(juego)`. **No se recomienda:** se reintroduce la carga silenciosa de
datos con un error conocido y la posibilidad de analizar los tres juegos terminando en sorteos
distintos.

Relacionado: `Fases/2026-10-02_arranque/Bugs/2026-10-02_23-29_s1-porton-linea-base.md`,
`Fases/2026-10-02_arranque/Cambios/2026-10-03_00-03_s1-paquete-src-melate.md`,
`Almacenamiento/Añadir/2026-10-03_00-13_s1-snapshots-congelados.md`
