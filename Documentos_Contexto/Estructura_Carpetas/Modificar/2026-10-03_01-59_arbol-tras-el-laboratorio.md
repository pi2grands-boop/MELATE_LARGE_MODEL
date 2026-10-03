# El árbol tras el laboratorio, y por qué el documento anterior quedó mintiendo

- **Fecha/hora:** 2026-10-03 01:59
- **Área:** Estructura_Carpetas · **Acción:** Modificar
- **Chat / página:** sesión de arranque · auditoría retrospectiva
- **Archivos afectados:** `src/melate/lab.py`, `prereg/`, `tests/test_protocolo.py`,
  `scripts/verificar-bitacora.ps1`

## Qué se hizo

`Estructura_Carpetas/Añadir/2026-10-03_00-13_s1-arbol-del-proyecto.md` es un documento del índice
permanente que afirma sobre el presente, y había dejado de ser cierto en cuatro puntos:

| Decía | Hay |
|---|---|
| `tests/` 5 ficheros, 52 pruebas | **6 ficheros, 100 pruebas** |
| `src/melate/` con 9 módulos, sin `lab.py` | **10 módulos**, `lab.py` incluido |
| `scripts/colador.ps1` | también **`scripts/verificar-bitacora.ps1`** |
| (no mencionaba `prereg/`) | **`prereg/`** existe |

### El árbol de ahora

```
baseline_auditoria.py         el oráculo heredado. NO se modifica.
CLAUDE.md  README.md  REGLAS-DOCUMENTACION.md
requirements.txt  pyproject.toml  .gitignore  .gitattributes

src/melate/                   10 módulos
  constantes.py  ingest.py  validate.py  audit.py  protocolo.py
  backtest.py  ev.py  informe.py  lab.py  __init__.py
tests/                        6 ficheros, 100 pruebas
  conftest.py  test_reglas_datos.py  test_linea_base.py
  test_paridad.py  test_sin_fuga.py  test_protocolo.py
data/raw/<fecha>/             snapshots congelados, inmutables
prereg/                       hipótesis preregistradas, selladas
reportes/                     el JSON de cada corrida y de cada veredicto
entorno/                      el pip freeze que reproduce la línea base
scripts/                      colador.ps1  verificar-bitacora.ps1
Documentos_Contexto/          la bitácora (se publica, ver REGLAS §0)
.venv/                        local, no se sube
```

### Las dos piezas nuevas, y por qué están donde están

- **`src/melate/lab.py`** — el laboratorio. Va en el paquete y no en `scripts/` porque es parte del
  sistema, no una herramienta de mantenimiento: lo importan los tests y tiene su propio CLI
  (`python -m melate.lab`). La frontera que marca —el informe explora, el laboratorio juzga— está en
  `Mapa/Modificar/2026-10-03_01-30_s2-entra-el-laboratorio.md`.
- **`prereg/`** — en la raíz y no dentro de `data/`, porque no son datos: son compromisos. Su
  integridad es de contenido y no de bytes, al contrario que los snapshots, y eso hace que necesiten
  mecanismos distintos (ver `Almacenamiento/Añadir/…prereg-sellado.md`).

Y la que faltaba desde la Fase 1:

- **`scripts/verificar-bitacora.ps1`** — se creó durante el cierre de la Fase 1, **después** de haber
  escrito el documento del árbol. Nunca llegó a figurar en ninguna parte del índice permanente.

## Por qué

Esto no es un cambio de árbol: es la corrección de un documento que describía uno que ya no existía.

La causa concreta: **la tabla de emisión de la Fase 2 no incluía `Estructura_Carpetas`.** Añadió un
módulo, una carpeta y un fichero de tests, y emitió a `Protocolo_Estadistico`, `Almacenamiento`,
`Estructura_Datos`, `Mapa` y `Reproducibilidad` — pero no a la única área cuya pregunta es "¿dónde
vive este fichero?".

La lección, para la Fase 3: **al cerrar una fase, la pregunta no es "¿qué áreas toqué?" sino "¿qué
documento del índice permanente acabo de dejar desactualizado?"**. Son conjuntos distintos, y el
segundo es el que importa, porque un documento del índice que miente es peor que uno que falta: el
que falta se busca en otro sitio, y el que miente se cree.

## Impacto en seguridad / conexiones / datos

- **Seguridad:** `scripts/verificar-bitacora.ps1` entra en el índice. Es parte del perímetro junto
  con el colador: uno comprueba que no se publica nada personal, el otro que la bitácora es
  consistente.
- **Conexiones:** sin cambios.
- **Datos:** `prereg/` queda registrado como carpeta del árbol; su contenido y su formato ya estaban
  documentados en `Almacenamiento/` y `Estructura_Datos/`.

## Cómo verificar / revertir

```powershell
ls src\melate\*.py | Measure-Object        # 10
ls tests\*.py | Measure-Object             # 6
ls scripts\                                # colador.ps1, verificar-bitacora.ps1
.venv\Scripts\python.exe -m pytest tests --collect-only -q | Select-Object -Last 1   # 100
```

**Revertir:** no aplica. Este documento no cambia nada; corrige lo que el índice permanente dice del
árbol. El documento anterior se queda como constancia de lo que era cierto al cerrar la Fase 1.

Relacionado: `Estructura_Carpetas/Añadir/2026-10-03_00-13_s1-arbol-del-proyecto.md`,
`Protocolo_Estadistico/Bugs/2026-10-03_01-59_auditoria-retrospectiva-fases-1-y-2.md`,
`Mapa/Modificar/2026-10-03_01-30_s2-entra-el-laboratorio.md`
