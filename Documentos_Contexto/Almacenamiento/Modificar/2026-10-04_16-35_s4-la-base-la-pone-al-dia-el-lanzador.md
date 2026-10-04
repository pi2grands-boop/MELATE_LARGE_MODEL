# `melate.duckdb` la pone al día el lanzador

- **Fecha/hora:** 2026-10-04 16:35
- **Área:** Almacenamiento · **Acción:** Modificar
- **Chat / página:** cierre de la Fase 4 · `src/melate/app.py`, `src/melate/almacen.py`
- **Archivos afectados:** `src/melate/app.py`, `src/melate/almacen.py`, `app/streamlit_app.py`,
  `scripts/colador.ps1`, `.gitignore`

## Qué cambia respecto a la decisión

`Almacenamiento/Decisiones/2026-10-04_00-40_s4-que-entra-en-melate-duckdb.md` decidió qué entra en la
base, que la genera `python -m melate.almacen` y nunca la app, y que no se publica. **Las tres cosas
siguen en pie.** Lo que cambia es **cuándo** se construye.

**Antes**, a mano: si la base faltaba o se quedaba vieja, la app lo decía y enseñaba la orden.

**Ahora**, también la construye el lanzador, `python -m melate.app`, antes de arrancar la app, si:
no existe; no se puede leer; es de otro esquema; no se puede comprobar si está al día; o algún
fichero de `reportes/` o `prereg/` es nuevo, cambió o desapareció desde que se construyó. Si está al
día, **no la toca**. Construye con la misma función que la orden de siempre (`almacen.main`) y con los
`reportes/` y `prereg/` de **la carpeta de la base**, que es contra lo que `almacen.frescura` mide si
está al día.

**La app sigue sin escribir.** La alternativa que la decisión descartó, «que la app construya la
base si falta», sigue descartada: escribe el lanzador, que es una orden de terminal como
`python -m melate.almacen`, antes de que exista ningún servidor.

## Dos detalles que se fijaron

- **Una sola regla para encontrar la base,** `almacen.ruta_de_la_base(raiz)`: la de la variable
  `MELATE_DUCKDB` si está fijada, o `melate.duckdb` en la raíz. La usan la app y el lanzador; con dos
  reglas, uno podría poner al día una base y la otra enseñar otra.
- **No publicarla, blindado.** `.gitignore` se salta con `git add -f`, y el colador no sabe leer un
  binario. Ahora el colador mira también el índice de git y da por coincidencia cualquier
  `*.duckdb` versionada (autoprueba con un repositorio de usar y tirar).

## Comprobado en vivo

Sin base en la raíz: `melate.duckdb no existe: se construye.`, con el resumen de lo leído —10
ficheros, el preregistro verifica, los dos veredictos valen— y lo que la app enseñará: *sin ventaja
demostrada*. Lanzado otra vez: `melate.duckdb está al día.`, con la misma fecha de escritura.

## Cómo verificar / revertir

```powershell
.venv\Scripts\python.exe -m melate.app                    # «melate.duckdb está al día.»
.venv\Scripts\python.exe -m pytest tests\test_lanzador.py -k "construir or al_dia or mismo_sitio" -q
```

**Revertir:** sin el lanzador, la base vuelve a construirse a mano con `python -m melate.almacen`, y
la app sigue avisando si falta o está vieja. Los pasos están en
`Fases/2026-10-04_app-local/Cambios/2026-10-04_16-08_s4-lanzador-propio.md`.

Relacionado: `Almacenamiento/Decisiones/2026-10-04_00-40_s4-que-entra-en-melate-duckdb.md`,
`Estructura_Datos/Añadir/2026-10-04_16-35_s4-esquema-de-melate-duckdb.md`,
`Fases/2026-10-04_app-local/Cambios/2026-10-04_16-08_s4-lanzador-propio.md`.
