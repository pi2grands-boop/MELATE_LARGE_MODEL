# El árbol tras la Fase 3

- **Fecha/hora:** 2026-10-03 05-15
- **Área:** Estructura_Carpetas · **Acción:** Modificar

## Qué apareció

```
src/melate/
  popularity.py          NUEVO   las tablas de ganadores: red, parseo y estimadores
  portfolio.py           NUEVO   carteras con presupuesto fijo
  informe.py             +       clave `valor_esperado_medido` y opción --popularidad

tests/
  test_popularidad.py    NUEVO   36 pruebas (1 marcada `red`)
  test_cartera.py        NUEVO   26 pruebas

data/cache/melate-e/     NUEVO   caché de páginas. EN .gitignore: contenido de terceros
  melate/<n>.html
  revancha/<n>.html

entorno/
  pip-freeze-2026-10-03.txt  NUEVO   45 paquetes (eran 24)

reportes/
  2026-10-03_popularidad.json           NUEVO
  2026-10-03_cartera.json               NUEVO
  2026-10-03_informe-con-popularidad.json  NUEVO
```

Con esto, `src/melate/` tiene los nueve módulos que la «Estructura sugerida» del `CLAUDE.md`
preveía, menos `app/streamlit_app.py` y `melate.duckdb`, que son de la Fase 4.

## La única carpeta que NO se publica

`data/cache/` es la primera carpeta de datos que entra en `.gitignore`, y conviene ver por qué es
lo contrario de `data/raw/`:

| | ¿Se publica? | Por qué |
|---|---|---|
| `data/raw/<fecha>/` | **Sí** | 435 KB que hacen que el hash del protocolo signifique algo |
| `data/cache/melate-e/` | **No** | Páginas de un tercero, 2,9 MB, y reconstruibles |

La entrada del `.gitignore` lleva el porqué escrito al lado, para que nadie la quite por
descuido pensando que es un olvido.

## Dónde NO se tocó nada

- **`baseline_auditoria.py`**, en la raíz. Sigue siendo el oráculo y no se modifica.
- **`prereg/`**. Ningún preregistro se tocó, y el sellado declara una familia de 36 que sigue
  siendo 36.
- **`entorno/pip-freeze-2026-10-02.txt`**. Es el que reproduce la línea base y se conserva tal
  cual; el nuevo se añade al lado, no lo sustituye.

## Cómo verificar

```powershell
Get-ChildItem src\melate\*.py | Select-Object Name
git status --short        # data/cache/ no debe aparecer
```

## Cómo revertir

Borrar los cinco ficheros nuevos de `src/` y `tests/`, la carpeta `data/cache/`, los tres
reportes y `entorno/pip-freeze-2026-10-03.txt`; y en `informe.py`, la clave
`"valor_esperado_medido"` de `NUEVAS_CLAVES`, la función `_valor_esperado_medido` y sus tres usos.

Relacionado: `Estructura_Carpetas/Añadir/2026-10-03_00-13_s1-arbol-del-proyecto.md`,
`Estructura_Carpetas/Modificar/2026-10-03_01-59_arbol-tras-el-laboratorio.md`,
`Almacenamiento/Añadir/2026-10-03_05-15_s3-cache-de-paginas.md`.
