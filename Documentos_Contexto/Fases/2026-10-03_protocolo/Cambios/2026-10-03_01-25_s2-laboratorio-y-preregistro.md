# El laboratorio: `lab.py`, `prereg/` y las 5 condiciones

- **Fecha/hora:** 2026-10-03 01:25
- **Área:** Fases/2026-10-03_protocolo · **Acción:** Cambios
- **Chat / página:** sesión de arranque · etapas 2 a 5 del alcance
- **Archivos afectados:** `src/melate/lab.py`, `src/melate/protocolo.py`,
  `prereg/2026-10-03_logistica-revancha.json`, `tests/test_protocolo.py`,
  `reportes/2026-10-03_veredicto.json`

## Qué se hizo

### `prereg/*.json` — el preregistro sellado

Un fichero JSON que declara, **antes de que existan los datos que lo juzgarán**: la hipótesis, los
juegos, la estrategia, la métrica, la línea base, la prueba estadística, el umbral de `q`, el tamaño
de la familia de corrección, la rejilla de hiperparámetros alternativos, el criterio de declaración,
y el hash del snapshot vigente al sellar.

Y dos campos que son el mecanismo:

- **`sello_utc`** — la frontera. El holdout son los sorteos con `FECHA` posterior a esta fecha.
- **`sello_sha256`** — SHA-256 del JSON canónico de todo lo demás (claves ordenadas, sin espacios,
  excluyendo el propio hash). Cambiar un byte lo invalida.

El preregistro escrito es la única hipótesis que la fase exploratoria dejó sobre la mesa: la
regresión logística en Revancha, que en la Fase 1 fue la única de las 8 estrategias con p < 0.05 sin
corregir. Su campo `advertencia` dice en voz alta lo que un preregistro **no** hace: no valida
retroactivamente la medición de la Fase 1, que fue exploratoria y lo seguirá siendo.

### `src/melate/lab.py`

| Función | Qué hace |
|---|---|
| `sellar(spec, ruta)` | Escribe el preregistro con su hash. **No sobrescribe** y **no sella en el pasado** |
| `hash_preregistro(spec)` | El SHA-256 del contenido canónico, sin el campo del hash |
| `cargar_preregistro(ruta)` | Carga **y verifica**. Si el sello no cuadra, se niega |
| `holdout(spec, juegos)` | Los sorteos posteriores al sello, por juego |
| `evaluar(spec, juegos)` | Corre **solo** lo declarado, sobre **solo** su holdout |

Más el CLI: `python -m melate.lab --prereg <fichero>` para evaluar y
`python -m melate.lab --sellar <borrador> --salida <destino>` para sellar.

**Las tres negativas son el módulo.** Si se puede evaluar sin preregistro, si se puede reescribir un
sello, o si se puede fecharlo antes de mirar los datos, el preregistro no prueba nada: se convierte
en un trámite que se rellena después.

### `protocolo.declara_ventaja()` — las 5 condiciones de la regla 5

Cada una es una función pública con su propio veredicto y su motivo en texto, y **se evalúan todas**
aunque la primera falle:

| # | Condición | Qué mata |
|---|---|---|
| 1 | Holdout futuro positivo | Mirar el pasado y llamarlo predicción |
| 2 | `q_BH_global` ≤ 0.05 | Pescar entre muchas pruebas y reportar la mejor |
| 3 | Estable al mover hiperparámetros | Un efecto que solo existe con una configuración concreta |
| 4 | Mismo signo en los tres juegos | Ruido de un juego disfrazado de patrón de la urna |
| 5 | Efecto ≥ mínimo detectable | Medir algo más pequeño que el error de medición |

La 4 es la más dura y la que más hallazgos falsos mata: los tres juegos comparten mecánica, así que
un patrón real tendría que aparecer en los tres.

Y **`benjamini_hochberg` acepta ahora `m`**, el tamaño de una familia declarada por adelantado. El
holdout corre 3 pruebas, una por juego, pero el preregistro declaró pertenecer a una familia de 36:
corregir contra 3 sería aflojar el criterio después de fijarlo. `m < len(ps)` se rechaza, porque
sería exactamente la manera de hacer trampa. Con `m=None` da bit a bit lo de siempre, y hay test.

### El veredicto de hoy

```
== Veredicto: sin ventaja demostrada  (0 de 5 condiciones)
   [NO] holdout futuro positivo    holdout vacío: 0 sorteos posteriores al sello.
                                   Todavía no hay nada que evaluar
```

**Es imposible declarar ventaja hoy, por construcción**, y así debe ser: el holdout de un sello de
hoy está vacío. Un holdout vacío no es un "no sabemos": es la información de que todavía no se ha
jugado nada a esta carta.

## Por qué

La Fase 1 dejó el proyecto capaz de medir y de reproducir lo que mide, y dejó también un resultado
que parecía prometedor y estaba en parte inflado por un error de datos de un tercero. Con el dato
correcto seguía siendo la estrategia que más invitaba a seguir tirando del hilo.

**Esa es la situación en la que un proyecto se autoengaña.** Con 56 números, decenas de estrategias y
miles de sorteos, algo siempre destaca; el problema no es encontrarlo, es distinguirlo de un
hallazgo real. La regla 4 del `CLAUDE.md` responde con preregistro, sello y holdout, y la regla 5 con
cinco condiciones a la vez. Esta fase las convierte en código que no se puede saltar sin que se note.

El coste honesto está en las notas del preregistro: con un efecto mínimo detectable de 0.048
aciertos hacen falta del orden de 1 800 sorteos de holdout, unos 11 años a tres por semana. No es un
defecto del diseño — es la medida de cuánta evidencia haría falta para afirmar algo, y saberla de
antemano es mejor que descubrirla después de haberse convencido.

## Impacto en seguridad / conexiones / datos

- **Seguridad:** sin cambios en la superficie. `lab.py` solo llega a la red si se le llama sin
  `--datos`, y entonces pasa por `ingest.cargar`, que solo habla con el oficial. Sin credenciales ni
  variables de entorno.
- **Conexiones:** ninguna nueva.
- **Datos:** aparece `prereg/` como almacén de documentos sellados e inmutables. El reporte del
  laboratorio es un fichero nuevo en `reportes/`, con su propio bloque de versiones.

## Cómo verificar / revertir

```powershell
.venv\Scripts\python.exe -m melate.lab --prereg .\prereg\2026-10-03_logistica-revancha.json --datos .\data\raw\2026-10-02
.venv\Scripts\python.exe -m pytest tests\test_protocolo.py -q     # 41 pruebas
.venv\Scripts\python.exe -m pytest tests -q                       # 92, con la paridad de la Fase 1
```

Que el sello de verdad protege, sobre el fichero real del repositorio:

```powershell
.venv\Scripts\python.exe -m pytest tests\test_protocolo.py -k manipular -v
```

Cuatro formas de hacer trampa —aflojar `umbral_q`, encoger `tamano_familia`, antedatar `sello_utc`,
cambiar `juego_principal`— y las cuatro tienen que ser rechazadas.

Y que el camino afirmativo existe, que importa tanto como lo demás:

```powershell
.venv\Scripts\python.exe -m pytest tests\test_protocolo.py -k camino_afirmativo -v
```

**Revertir:** borrar `src/melate/lab.py`, `prereg/`, `tests/test_protocolo.py` y el bloque de las 5
condiciones de `protocolo.py`; devolver `benjamini_hochberg` a un solo argumento. **Lo que se
reintroduce:** un proyecto que mide bien y no tiene nada que impida declarar una ventaja que no ha
pasado el protocolo.

Relacionado: `Fases/2026-10-03_protocolo/Bugs/2026-10-03_01-20_s2-review-laboratorio.md`,
`Fases/2026-10-03_protocolo/00_ALCANCE.md`,
`Protocolo_Estadistico/Decisiones/2026-10-03_00-13_s1-familias-benjamini-hochberg.md`
