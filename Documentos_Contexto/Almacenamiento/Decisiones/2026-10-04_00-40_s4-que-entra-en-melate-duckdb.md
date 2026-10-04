# Decisión: `melate.duckdb` es un índice local de lo ya publicado, y no se publica

- **Fecha/hora:** 2026-10-04 00:40
- **Área:** Almacenamiento · **Acción:** Decisiones
- **Decidido por:** proyecto, dentro del criterio que fijó el usuario para la Fase 4 —la app no
  recalcula y consume `reportes/*.json` y el preregistro—. **Estado:** cerrada
- **Alcance:** `melate.duckdb`, `src/melate/almacen.py`, `app/streamlit_app.py`, `.gitignore`
- **Escrita ANTES** de que exista el código que depende de ella, por instrucción del usuario.

## La decisión

`melate.duckdb` contiene **solo lo que ya está en `reportes/*.json` y `prereg/*.json`**, reordenado
en tablas y con la integridad comprobada; lo genera **una orden aparte**,
`python -m melate.almacen`, nunca la app; y **no se publica**: va en `.gitignore`.

## Qué entra

Cada tabla declara su **naturaleza**, y esa columna es la frontera del proyecto escrita en los
datos y no solo en la documentación:

| Naturaleza | Tablas | De dónde sale |
|---|---|---|
| **juzga** | `preregistros`, `veredictos`, `condiciones` | `prereg/*.json` y las salidas de `melate.lab` |
| **explora** | `informes`, `auditoria`, `backtest`, `exploracion_juego` | las salidas de `melate.informe` y del oráculo |
| **mide** | `valor_esperado`, `premios_mayores`, `popularidad`, `carteras`, `cartera_boletos` | informe, `melate.popularity`, `melate.portfolio` |
| **procedencia** | `construccion`, `fuentes`, `datos_informe`, `catalogo` | la propia construcción y los bloques de reproducibilidad |

Y una segunda columna, `mira_a` —`urna`, `dinero`, `jugadores`, `datos`—, que es la otra frontera,
la de la Fase 3: lo que habla de la urna puede entrar en la familia de Benjamini-Hochberg; lo que
habla de los jugadores, no.

Tres reglas sobre el contenido, y son contrato:

1. **Ningún número que no esté ya en un fichero publicado.** El constructor copia y reordena; no
   calcula estadísticos. Lo único que calcula son comprobaciones de integridad: el SHA-256 de cada
   fichero que lee, el sello de cada preregistro (con `lab.hash_preregistro`, la misma función que
   usa el laboratorio) y el enlace entre cada veredicto y su preregistro.
2. **Un veredicto solo cuenta si su `sello_sha256` es el de un preregistro que verifica.** Si el
   preregistro se alteró, o el veredicto apunta a uno que no está, el veredicto entra en la base
   **marcado como no válido, con su motivo**, y la app no lo usa. No se esconde: se ve que está y
   por qué no vale.
3. **El resumen del informe no se llama veredicto.** `protocolo_global.veredicto` del informe
   —que hoy dice "sin ventaja demostrada", y diría "revisar: hay pruebas con q <= 0.05" si alguna
   cayera bajo el umbral— entra como `resumen_exploratorio`. Una columna llamada `veredicto` solo
   existe en la tabla de lo que juzga.

## Qué NO entra, y por qué

| Fuera | Por qué |
|---|---|
| **Los sorteos crudos** | La app no los necesita: los informes ya los resumen con su procedencia. Meterlos invitaría a pantallas de frecuencias por número —los "números calientes" que el proyecto existe para desmentir— y la base dejaría de ser derivable solo de `reportes/` y `prereg/`. Además ya están publicados, en `data/raw/<fecha>/` |
| **Las páginas de melate-e.com** | Son contenido de un tercero (`Almacenamiento/Añadir/2026-10-03_05-15_s3-cache-de-paginas.md`). Ni se republican ni se sirven, tampoco en local |
| **Las muestras sorteo a sorteo de la popularidad** | La app enseña los resúmenes de cada ventana, que es lo que se publica. Si algún día hicieran falta, entran con otro documento |
| **Cifras derivadas nuevas** | "1 premio mayor cada 32 sorteos", un intervalo de confianza calculado en la pantalla… Si una cifra no está en un reporte, no está en la base ni en la app. La app formatea; no calcula |

## Qué la genera

`python -m melate.almacen`, en `src/melate/almacen.py`:

- Lee `reportes/*.json` y `prereg/*.json`, **clasifica** cada fichero por su forma y deja en
  `fuentes` lo que no reconozca, como `desconocido` y con su motivo, en vez de romper la
  construcción.
- Escribe en un fichero temporal y lo **sustituye de una vez**: una app abierta nunca ve una base a
  medio escribir.
- Guarda **rutas relativas a la raíz del repositorio**, nunca absolutas.
- Es determinista: dos construcciones sobre los mismos ficheros dan el mismo contenido, salvo la
  hora de construcción.
- No sale a la red y no recalcula nada: tarda lo que tarda leer unos cientos de KB de JSON.

**La app no la construye.** Si falta, o si su esquema es de otra versión, lo dice y enseña la orden.
Si los ficheros de `reportes/` o `prereg/` cambiaron desde la construcción —lo sabe comparando los
SHA-256 de `fuentes` con los de disco—, avisa de que está desactualizada. La app abre la base **en
solo lectura**, lee lo que necesita y la cierra.

## Si se publica: no

Por cuatro razones, cada una suficiente:

1. **No añade información.** Es derivable entera de ficheros que ya están en el repositorio, en
   menos de un segundo y con una orden.
2. **Un binario se salta el colador.** `scripts/colador.ps1` lee texto (`*.md`, `*.py`, `*.json`…);
   una ruta absoluta o un correo dentro de un `.duckdb` pasaría sin que nadie lo viera. La bitácora
   es pública por decisión del usuario y el colador es la única barrera: no se le pone delante algo
   que no puede leer.
3. **Cada reconstrucción cambia los bytes.** Un binario versionado es un diff ilegible en cada
   commit y un repositorio que engorda sin que nadie pueda revisar qué cambió.
4. **Dos fuentes de verdad acaban discrepando.** Los JSON de `reportes/` llevan su propia
   procedencia y son lo que se revisa. La base es una vista, y una vista publicada se confunde con
   el original.

Va en `.gitignore` con el porqué al lado, como `data/cache/`.

## Dónde vive

`melate.duckdb`, en la raíz del repositorio: es el nombre y el sitio que usan el `CLAUDE.md` y la
hoja de ruta. `--salida` permite construirla en otro sitio, y la app lee la que diga la variable de
entorno `MELATE_DUCKDB` o, si no está, la de la raíz.

## Alternativas descartadas

| Opción | Por qué no |
|---|---|
| Que la app lea los JSON directamente | La clasificación de cada fichero, la verificación de los sellos y el enlace veredicto-preregistro vivirían en la interfaz, que es lo más difícil de probar. Con la base, esa lógica está en un módulo con sus tests y la app solo hace `SELECT` |
| Que la base sea la fuente de verdad y los programas escriban en ella | Los JSON publicados son la evidencia reproducible: el colador los lee, `git diff` los enseña y `tests/test_paridad.py` compara contra ellos. Moverla a un binario rompería las tres cosas |
| Guardar cada JSON entero como un texto en una tabla | Es la primera alternativa disfrazada: la app tendría que volver a interpretar cada forma de reporte |
| Que la app construya la base si falta | La app escribiría en disco. "La app no escribe nada" es una propiedad simple y comprobable con un test; perderla cuesta más que la orden que ahorra |
| Publicarla | Ver arriba |

## Consecuencias

- **Un tipo de reporte nuevo obliga a tocar `almacen.py`.** Mientras no se haga, el fichero aparece
  en `fuentes` como `desconocido` y la app lo enseña como tal: no se pierde en silencio.
- **La base se puede borrar en cualquier momento** sin perder nada.
- **`reportes/` sigue siendo la fuente de verdad** y el colador la sigue leyendo entera.
- La app depende de `duckdb`, una dependencia nueva fijada exacta en `requirements.txt`.

## Premisas que esta decisión invalida

**Ninguna.** Se revisaron las tres decisiones de almacenamiento anteriores:

| Documento | ¿Sigue válido? |
|---|---|
| `Almacenamiento/Añadir/2026-10-03_00-13_s1-snapshots-congelados.md` | Sí: `data/raw/` sigue siendo la entrada; la base no la toca |
| `Almacenamiento/Añadir/2026-10-03_01-30_s2-prereg-sellado.md` | Sí: la base **verifica** los sellos, no los escribe ni los corrige |
| `Almacenamiento/Añadir/2026-10-03_05-15_s3-cache-de-paginas.md` | Sí: la caché sigue fuera, de la base y del repositorio |

Y la premisa de `Seguridad/Decisiones/2026-10-03_00-13_s1-bitacora-publica.md` —"la app corre en
local"— se refuerza: la base es local por la misma razón.

## Cuándo reabrirla

- Si alguna pantalla necesitara datos sorteo a sorteo: entrarían los sorteos crudos, con su
  documento.
- Si algún programa empezara a **leer** de la base para calcular: dejaría de ser una vista y habría
  que replantear que no se publique.
- Si se quisiera compartir la app o sus datos con alguien: eso es dejar de ser local, y reabre
  también la decisión de Seguridad.

## Cómo verificar

```powershell
git check-ignore -v melate.duckdb                         # la regla de .gitignore que la excluye
.venv\Scripts\python.exe -m melate.almacen                # construye y dice qué leyó
.venv\Scripts\python.exe -m pytest tests\test_almacen.py -q
```

Relacionado: `Fases/2026-10-04_app-local/00_ALCANCE.md`,
`Almacenamiento/Añadir/2026-10-03_05-15_s3-cache-de-paginas.md`,
`Almacenamiento/Añadir/2026-10-03_01-30_s2-prereg-sellado.md`,
`Seguridad/Decisiones/2026-10-03_00-13_s1-bitacora-publica.md`.
