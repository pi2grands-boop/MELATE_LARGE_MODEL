# Review s1 — el refactor a `src/melate/` y sus tests

- **Fecha/hora:** 2026-10-03 00:03
- **Área:** Fases/2026-10-02_arranque · **Acción:** Bugs
- **Chat / página:** sesión de arranque · etapas 5 a 7 del alcance
- **Archivos afectados:** `src/melate/*.py`, `tests/*.py`, `pyproject.toml`, `scripts/colador.ps1`

## Qué se hizo

Review del código escrito en esta fase: el paquete `src/melate/`, los cuatro ficheros de test y el
colador. `baseline_auditoria.py` no entra en esta review: no se tocó, y su reproducción ya está
cerrada en el `Bugs/` del portón.

**Limitaciones del entorno, por delante:** no hay linter ni analizador estático instalado —el
proyecto solo trae lo que el `CLAUDE.md` pide—, así que la revisión fue lectura línea a línea más
los tests. No hay cobertura medida. Nada de esto se ha probado en Linux ni macOS: los comandos del
repositorio son de PowerShell en Windows, y el colador es un `.ps1`.

## Review de fallas #1

- ❌ **El hash del dataset podía no ser el de los datos analizados.** `sha256_datos(carpeta)` volvía
  a leer la fuente para hashearla, en una segunda pasada independiente de la carga. Con `--datos` el
  riesgo es bajo, pero **sin** `--datos` son dos descargas distintas, y hoy mismo quedó demostrado
  que eso no es teórico: el oficial está a punto de publicar el sorteo 4273, y una publicación a
  media corrida habría registrado el hash de unos datos distintos de los que se acababan de
  analizar. Eso es exactamente lo contrario de lo que pide la regla 6 del protocolo.
  → **Corregido.** `cargar()` deja ahora `sha256`, `bytes` y `fuente` en `df.attrs` de **lo que
  realmente leyó**, y `procedencia(crudos)` los recoge. `sha256_datos` desapareció. Se hashean los
  bytes crudos, no el texto decodificado, para que el valor coincida con el `SHA256.txt` publicado
  junto al snapshot.
  → Lo vigila `tests/test_paridad.py::test_el_hash_registrado_es_el_de_los_datos_analizados`, que
  compara contra los bytes del fichero **y** contra el `SHA256.txt`.

- ❌ **`python -m melate.informe` moría en un clon nuevo.** El `--salida` por defecto es
  `reportes/informe.json` y esa carpeta no existe recién clonado el repositorio: `open()` lanzaba
  `FileNotFoundError` después de haber corrido los dos minutos de cómputo. El oráculo no tenía el
  problema porque escribía en el directorio actual.
  → **Corregido.** `main()` hace `mkdir(parents=True, exist_ok=True)` sobre el padre de la salida.
  → Lo vigila `tests/test_paridad.py::test_la_salida_se_crea_aunque_no_exista_la_carpeta`, que pide
  una ruta de tres niveles inexistentes y corre con `--sims 2` para no tardar.

- ❌ **El colador se encontraba a sí mismo.** Primera ejecución: 5 coincidencias, las cinco dentro
  de `scripts/colador.ps1` —sus propios patrones literales y el cebo de la autoprueba—. Un colador
  que siempre grita es un colador que se acaba ignorando, que es peor que no tenerlo.
  → **Corregido.** Se excluye por nombre de fichero, y es la **única** exclusión por nombre que
  tiene. Está comentada a la vista en el propio script, precisamente para que nadie use ese hueco
  para esconder algo, y la autoprueba demuestra que los patrones siguen teniendo dientes.

- ❌ **Un test comparaba contra un número que yo mismo había redondeado.**
  `test_regresion_logistica_en_revancha` afirmaba `p == approx(0.017, abs=5e-4)` porque 0.017 es lo
  que imprime la consola; el reporte guarda 0.0165, y el test falló justo en el borde de la
  tolerancia. El error de fondo era el enfoque: duplicar la cifra con una tolerancia inventada.
  → **Corregido.** Los tests de la línea base comprueban ahora que el valor almacenado **redondea**
  a lo que publica el `CLAUDE.md` (`round(p, 3) == 0.017`). Así el test detecta de verdad una
  discrepancia entre documento y código, que es justo lo que falló en el portón, en vez de tolerar
  cualquier cosa dentro de un margen.

- ✅ **No hay fuga temporal.** Siete tests en `tests/test_sin_fuga.py`, y los que importan permutan
  las filas ≥ t y exigen que `F[:t]` y `atraso[:t]` sean idénticos bit a bit. Además se recalculan a
  mano la ventana de 10, la frecuencia histórica, el atraso y la matriz de Markov, de forma
  independiente de la implementación.
- ✅ **Paridad con el oráculo.** `tests/test_paridad.py` corre los dos programas como subprocesos
  sobre el mismo snapshot y compara el JSON recursivamente, con tolerancia cero. Las únicas claves
  exentas son las que el paquete declara en `melate.informe.NUEVAS_CLAVES`, y un test aparte exige
  que esas claves existan — si desaparecieran, la comparación las ignoraría en silencio.
- ✅ **El orden de consumo del RNG se conservó.** `auditar()` sigue compartiendo un `rng` entre los
  tres juegos en el orden de `JUEGOS`, y el diccionario `elec` de `backtest()` mantiene sus 8
  asignaciones en el mismo orden. Ambos puntos llevan comentario explícito en el código, y el test
  de paridad es lo que los vigila.
- ✅ **Las claves del oráculo no se renombraron.** `q_BH` se mantiene y la familia global se añade
  como `q_BH_global`. Renombrar habría roto la paridad y, peor, habría hecho irreproducibles los
  `q` publicados.

## Optimización

- `benjamini_hochberg` estaba duplicada de hecho entre auditoría y backtest (dos bloques de
  llamadas con la misma forma). Ahora vive una sola vez en `protocolo.py`, con las familias como
  funciones nombradas (`claves_auditoria`, `claves_backtest`). El reporte no cambia.
- `cargar` y `cargar_espejo` comparten `_normalizar`, que antes era el cuerpo de `cargar`. Era eso
  o copiar el parseo entero para el espejo, con la garantía de que un día divergirían.
- `validar_era` reutiliza `validar` en vez de duplicar las nueve comprobaciones.

**Lo que se decidió NO tocar, y vale tanto como lo anterior:**

- **La aritmética de `estadisticas`, `variables`, `backtest` y `valor_esperado` está copiada
  literalmente**, incluidas las líneas con varias sentencias separadas por `;` y los nombres cortos.
  Reformatear habría sido gratis en apariencia y carísimo en realidad: la paridad al cuarto decimal
  es el único control que tenemos de que el refactor no cambió nada.
- **`baseline_auditoria.py` no se toca nunca.** Es el oráculo. Los dos fallos de arriba están en el
  código nuevo, no en él.
- **No se arregló el orden aparente de `_normalizar`** (mirar `FECHA.iloc[0]` antes de ordenar). Está
  registrado como observación aceptada en el `Bugs/` del portón y lleva comentario en el código.

## Review de fallas #2 + review de seguridad

- ✅ **Imports sin usar:** se quitaron `pandas` y `PRIMER_SORTEO_56` de `tests/test_reglas_datos.py`
  y `JUEGOS` de `ingest.py`, que quedó huérfano al desaparecer `sha256_datos`.
- ✅ **Superficie de red del paquete.** Tres sitios hacen peticiones, y ninguno más:
  `_leer_bytes` (solo al oficial), `cargar_espejo` (solo al espejo, y solo si alguien lo llama a
  mano) y los tests marcados `red`. Con `--datos` no se toca la red en absoluto, lo que importa
  porque es el modo en el que se reproducen las cifras publicadas.
- ✅ **El espejo ya no puede entrar por la puerta de atrás.** `_leer_bytes` levanta `SystemExit` con
  un mensaje que explica por qué no hay respaldo automático y qué hacer en su lugar. Antes, una
  caída del oficial cargaba datos con un error conocido sin decir nada.
- ✅ **Nada se ejecuta al importar.** Ningún módulo hace peticiones, lee ficheros ni imprime en
  tiempo de import. `informe.py` solo actúa bajo `if __name__ == "__main__"` o cuando se le llama.
- ✅ **Sin credenciales, sin `.env`, sin secretos.** Confirmado leyendo los seis módulos: no hay
  ninguna lectura de variables de entorno ni de ficheros de configuración.
- ✅ **Nada personal en lo que se sube.** `scripts/colador.ps1` sobre 38 ficheros: 0 coincidencias,
  exit 0, con la autoprueba en verde. La identidad de git de este repositorio es
  `pi2grands-boop@users.noreply.github.com`, puesta **antes** del primer commit; la global, con el
  correo personal, no se tocó.
- ✅ **El `.gitignore` no esconde nada que haga falta.** Solo `.venv/`, caché de Python y artefactos
  de empaquetado. El snapshot de datos, los reportes y la bitácora se suben a propósito, y el
  fichero dice por qué.
- ✅ **Rutas relativas.** Los `--datos` de los comandos documentados son relativos, así que el campo
  `fuente` de los reportes que se suben también lo es. Comprobado en
  `reportes/2026-10-02_paquete.json`.

## Observación aceptada (no es bug)

**El informe del paquete tardó 30.7 s y el del oráculo 84.5 s**, haciendo el mismo trabajo. No es
una optimización: el del oráculo fue la primera ejecución de pandas y scikit-learn en un entorno
recién instalado, con los `.pyd` todavía fuera de la caché de ficheros del sistema. Corridas
posteriores de los dos programas quedan en el mismo orden de magnitud —la suite completa, que corre
los dos, tarda 105 s—. Queda anotado para que nadie lo lea como una mejora de rendimiento que no
existe, y la medición formal va al documento de `Rendimiento/`.

## Resultado

**Bugs abiertos: ninguno.** Los cuatro encontrados se corrigieron en este mismo ciclo y los tres
primeros tienen test propio. Ningún bug se dejó a propósito, así que no hubo nada que consultar.

Suite completa: **52 tests en verde**, 105 s. Los rápidos —31 de ellos— en 2.4 s con
`-m "not lento and not red"`.

## Cómo verificar / revertir

```powershell
.venv\Scripts\python.exe -m pytest tests -q                           # 52 en verde, ~105 s
.venv\Scripts\python.exe -m pytest tests -m "not lento and not red" -q  # 31 en verde, ~2 s
.\scripts\colador.ps1 -Autoprueba                                     # autoprueba 3/3, 0 coincidencias
```

El test que de verdad cierra esta review es el de paridad:

```powershell
.venv\Scripts\python.exe -m pytest tests\test_paridad.py -v
```

**Revertir:** borrar `src/`, `tests/`, `pyproject.toml` y `scripts/`, y desinstalar el paquete con
`.venv\Scripts\python.exe -m pip uninstall melate`. `baseline_auditoria.py` sigue funcionando solo,
porque nunca dependió de nada de esto.

**Pendiente de verificar** — lo que este entorno no permitió comprobar:

1. **Nada se ha probado fuera de Windows.** Los comandos documentados usan `.venv\Scripts\` y el
   colador es PowerShell. Si alguna vez se usa en Linux o macOS, hay que comprobarlo y documentarlo.
2. **No se ha corrido el informe sin `--datos`** contra la descarga en vivo desde que se cambió
   `_leer_bytes`. El camino de red del paquete está probado solo por los tests marcados `red`, que
   tocan el espejo, no la ruta de carga del oficial. Pendiente para el primer informe de datos
   frescos, que será con el sorteo 4273 ya publicado.
3. **El `SystemExit` de `_leer_bytes` no se ha visto disparar.** El oficial no ha fallado en esta
   sesión. Es un camino de error no ejercitado.

Relacionado: `Fases/2026-10-02_arranque/Bugs/2026-10-02_23-29_s1-porton-linea-base.md`,
`Fases/2026-10-02_arranque/Cambios/2026-10-03_00-03_s1-paquete-src-melate.md`,
`Fases/2026-10-02_arranque/Cambios/2026-10-03_00-03_s1-tests.md`

---

## Resultado — CERRADO el 2026-10-03 a las 00:25

Los cuatro bugs del ciclo quedaron corregidos **dentro del mismo ciclo**, y tres tienen test propio:

| Bug | Test que lo vigila |
|---|---|
| El hash podía no ser el de los datos analizados | `test_paridad.py::test_el_hash_registrado_es_el_de_los_datos_analizados` |
| `informe` moría en un clon nuevo | `test_paridad.py::test_la_salida_se_crea_aunque_no_exista_la_carpeta` |
| Un test comparaba contra un número redondeado a mano | Los tests de línea base comprueban el redondeo, no una tolerancia |
| El colador se encontraba a sí mismo | `colador.ps1 -Autoprueba` |

Suite completa en verde: **52 pruebas, 105 s**. Colador: 41 ficheros, 0 coincidencias, exit 0,
autoprueba 3/3.

### Un quinto hallazgo, encontrado al verificar la propia bitácora

`scripts/verificar-bitacora.ps1` se escribió para comprobar que la bitácora es consistente, y su
primera ejecución encontró dos cosas:

- **Este documento estaba abierto.** Decía "Bugs abiertos: ninguno" pero no tenía bloque de cierre,
  así que para cualquier comprobación automática seguía vivo. Es el bloque que estás leyendo.
- **El verificador tenía un falso positivo masivo**: resolvía las referencias `.md` solo contra la
  raíz de la bitácora, así que marcaba como roto todo enlace a `CLAUDE.md`, `README.md` o
  `REGLAS-DOCUMENTACION.md` —que viven en la raíz del repositorio— y los enlaces relativos dentro del
  dossier. 37 de los 39 hallazgos iniciales eran suyos. Corregido: ahora intenta resolver contra la
  raíz de la bitácora, la raíz del repositorio y la carpeta del propio documento, y omite los
  marcadores de plantilla del tipo `AAAA-MM-DD_HH-MM_slug.md`, que son ejemplos de formato y no
  enlaces.

La lección es la misma que con el colador, y por eso se registra: **una herramienta de verificación
que nadie ha verificado no es una garantía, es una opinión.** Las dos traen ahora su propia
comprobación.

### De los tres pendientes declarados arriba

Siguen pendientes los tres, y pasan al `Fases/2026-10-02_arranque/99_CIERRE.md` de la fase: nada probado fuera de Windows, el
informe sin `--datos` no se ha corrido desde el cambio de `_leer_bytes`, y el `SystemExit` de ese
camino no se ha visto disparar. Ninguno bloquea el cierre y los tres están anotados para la Fase 2.
