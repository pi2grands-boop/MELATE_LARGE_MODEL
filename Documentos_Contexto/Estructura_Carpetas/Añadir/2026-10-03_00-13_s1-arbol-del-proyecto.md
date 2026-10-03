# El árbol del proyecto, y los dos módulos que no estaban en el plano

- **Fecha/hora:** 2026-10-03 00:13
- **Área:** Estructura_Carpetas · **Acción:** Añadir
- **Chat / página:** sesión de arranque · emitido al cerrar la Fase 1
- **Archivos afectados:** todo el árbol; `pyproject.toml`, `.gitignore`, `.gitattributes`

## Qué se hizo

De dos ficheros a 40 blobs. Este es el árbol y el porqué de cada carpeta.

```
baseline_auditoria.py         el oráculo heredado. NO se modifica.
CLAUDE.md                     el contrato
README.md                     la puerta de entrada del repositorio público
REGLAS-DOCUMENTACION.md       cómo se documenta, y la Regla 0 invertida
requirements.txt              restricciones de versión
pyproject.toml                empaquetado (src-layout) y markers de pytest
.gitignore  .gitattributes    qué no se sube, y qué bytes no se tocan

src/melate/                   el paquete: 9 módulos
tests/                        5 ficheros, 52 pruebas
data/raw/<fecha>/             snapshots congelados, inmutables
reportes/                     el JSON de cada corrida, con su procedencia
entorno/                      el pip freeze que reproduce la línea base
scripts/colador.ps1           el control previo a cada push
Documentos_Contexto/          la bitácora (se publica, ver REGLAS §0)
.venv/                        local, no se sube
```

### `src/` y no `melate/` en la raíz

La disposición `src/` es la que describe el `CLAUDE.md`, y tiene una ventaja concreta: con el
paquete fuera de la raíz, un `import melate` que funcione **solo** porque estás en el directorio
correcto falla pronto en vez de engañarte. El coste es un paso de instalación:

```
.venv\Scripts\python.exe -m pip install -e .
```

Después, `python -m melate.informe` y los imports de los tests funcionan desde cualquier sitio, sin
tocar `sys.path`. `pyproject.toml` usa `setuptools` con `packages.find where = ["src"]`.

La única excepción es `tests/conftest.py`, que mete la raíz del repositorio en `sys.path`: lo necesita
porque `baseline_auditoria.py` vive ahí y **no forma parte del paquete**, a propósito.

### Dos módulos que no están en la estructura sugerida del `CLAUDE.md`

El plano del contrato lista `ingest`, `validate`, `audit`, `backtest`, `ev`, `popularity`,
`portfolio` y `lab`. Se añadieron dos, y cada uno tiene su razón:

- **`constantes.py`** — los mismos valores (`N`, `K`, `C`, precios, bolsas mínimas, la línea base del
  azar) los usan cinco módulos. Repartirlos "por el que más los use" es la forma más fiable de que un
  día dejen de coincidir, y aquí una constante que se desincroniza no da error: da una cifra
  equivocada. Guarda también las tres semillas con nombre, que antes eran literales sueltos en tres
  sitios y son lo que hace reproducibles las cifras publicadas.
- **`protocolo.py`** — `benjamini_hochberg` la usan `audit` y `backtest`, y la familia global
  necesita un dueño único que vea las dos familias a la vez. Es además donde vivirá
  `declara_ventaja()` en la Fase 2: el módulo tiene futuro, no es un cajón de sastre.

### Lo que NO se creó

`popularity.py`, `portfolio.py`, `lab.py`, `prereg/`, `app/` y `melate.duckdb`. Están en el plano del
`CLAUDE.md` pero pertenecen a las fases 2, 3 y 4. **Crear ficheros vacíos para parecerse a un
diagrama es ruido**: quien abra el proyecto en seis meses no sabrá si están vacíos porque no toca
todavía o porque alguien se dejó el trabajo a medias.

### Carpetas que se suben y suele sorprender

| Carpeta | Por qué se sube |
|---|---|
| `data/raw/` | 438 KB. Es lo que hace que el hash del protocolo signifique algo y que alguien de fuera pueda recomprobar las cifras |
| `reportes/` | La evidencia de cada corrida, con su hash, semillas y versiones dentro |
| `Documentos_Contexto/` | Decisión explícita del usuario, que invierte la Regla 0. Ver `Seguridad/Decisiones/` |
| `entorno/` | Las versiones exactas. Sin ellas, "reproducible" es una palabra vacía |

El `.gitignore` solo esconde `.venv/`, caché de Python y artefactos de empaquetado — y dice en un
comentario qué **no** ignora y por qué.

## Por qué

Un fichero de 322 líneas que hace seis cosas no se puede extender sin miedo, y quedan tres fases por
delante. La estructura la fija el `CLAUDE.md`; lo que esta fase aporta es respetarla, documentar las
dos desviaciones, y no inventar carpetas vacías.

## Impacto en seguridad / conexiones / datos

- **Seguridad:** `.gitignore` y `.gitattributes` son parte del perímetro. El segundo, además,
  protege la integridad de los datos: ver `Almacenamiento/Añadir/`.
- **Conexiones:** sin impacto estructural.
- **Datos:** aparece `data/raw/<fecha>/` como almacén fechado.

## Cómo verificar / revertir

```powershell
.venv\Scripts\python.exe -m pip install -e .
.venv\Scripts\python.exe -c "import melate; print(melate.__version__)"      # 0.1.0
.venv\Scripts\python.exe -m pytest tests -m "not lento and not red" -q      # 31 en verde
```

**Revertir:** borrar `src/`, `tests/`, `pyproject.toml` y `scripts/`, y `pip uninstall melate`.
`baseline_auditoria.py` sigue funcionando por sí solo: nunca dependió de nada de esto.

Relacionado: `Mapa/Añadir/2026-10-03_00-13_s1-mapa-del-sistema.md`,
`Almacenamiento/Añadir/2026-10-03_00-13_s1-snapshots-congelados.md`,
`Fases/2026-10-02_arranque/Cambios/2026-10-03_00-03_s1-paquete-src-melate.md`
