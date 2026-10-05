# Los snapshots los congela el ciclo, y la base sabe cuáles hay

- **Fecha/hora:** 2026-10-05 10:05
- **Área:** Almacenamiento · **Acción:** Modificar
- **Chat / página:** cierre de la Fase 5 · `Fases/2026-10-04_ciclo-vivo/`
- **Archivos afectados:** `src/melate/ciclo.py`, `src/melate/almacen.py`, `.gitignore`, `data/raw/`,
  `data/cache/`, `reportes/`

## Qué cambia

`Almacenamiento/Añadir/2026-10-03_00-13_s1-snapshots-congelados.md` describe un snapshot hecho a mano
y nombrado con la fecha de la descarga. **Sus reglas siguen**: los ficheros con su nombre, los bytes
tal cual llegaron, inmutables, publicados, y `data/raw/** -text` en `.gitattributes`. Lo que cambia es
quién los hace, cómo se llaman, y que ahora hay más sitios donde el proyecto guarda cosas.

| Dónde | Qué | ¿Se publica? |
|---|---|---|
| `data/raw/2026-10-02/` | El snapshot de la Fase 1, hecho a mano. No se toca nunca | sí |
| `data/raw/<fecha>_<sorteo>/` | **Nuevo.** Los que congela `python -m melate.ciclo`: los tres CSV como los sirvió el oficial, su `SHA256.txt` y su procedencia (`data/raw/2026-10-04_4274/PROCEDENCIA.md`, por ejemplo). El nombre es la fecha del último sorteo y su concurso: lo decide el contenido, así que los mismos datos bajados dos días tienen un solo nombre | sí |
| `data/raw/.<nombre>.construyendo/` | **Nuevo.** Donde el ciclo escribe un snapshot antes de renombrarlo: o está entero, o no está. La corrida siguiente borra uno que haya quedado | no |
| `data/cache/melate-e/` | La caché permanente de la Fase 3; ahora recibe también las páginas de los sorteos nuevos, **si traen la tabla entera con premios** | no |
| `data/cache/melate-e-incompletas/` | **Nueva.** Las páginas nuevas que llegaron sin la tabla entera: sirven de testigo, no entran en la popularidad, y no se vuelven a pedir | no |
| `data/cuarentena/<hora UTC>/` | **Nueva.** Ante un hallazgo, la descarga tal cual y un `HALLAZGO.txt` con lo que se vio. Sin esos bytes, investigar sería fiarse de la memoria | no |
| `reportes/<snapshot>_{popularidad,informe,veredicto-<id>}.json` | **Nuevos.** Lo que el ciclo deriva de cada snapshot. Se escriben una vez, en un `*.escribiendo` que se renombra, y nunca encima de otro | sí |

**Hoy hay tres snapshots:** `2026-10-02` (hasta el 4272, a mano), `2026-10-02_4273` y
`2026-10-04_4274`, los dos del ciclo.

## La base sabe qué está congelado

`Almacenamiento/Decisiones/2026-10-04_00-40_s4-que-entra-en-melate-duckdb.md` decía que la base es un
índice de `reportes/` y `prereg/`. **Ahora lee también los `data/raw/*/SHA256.txt`** —salvo las
carpetas que empiezan por punto, que están a medio escribir— y por eso:

- enlaza cada veredicto e informe con su snapshot **por SHA-256**, no por la ruta;
- **un veredicto cuyos datos no son un snapshot congelado no vale**, y no puede llegar a la cabecera de
  la app (C3, aprobada por el usuario);
- un snapshot nuevo deja la base desactualizada, y el lanzador la reconstruye
  (`Almacenamiento/Modificar/2026-10-04_16-35_s4-la-base-la-pone-al-dia-el-lanzador.md`, que sigue
  valiendo con esa fuente más);
- su esquema pasa a la versión 2, con una tabla nueva, `snapshots`. Una base del esquema 1 se
  reconstruye; la app no la usa.

## Cuánto crece

Medido con los snapshots reales, y corregido al cerrar la fase (la decisión del ciclo publicó una
medida que solo contaba los CSV: B14 de la review del ciclo). Cada snapshot pesa **448 KB** el primero
y **143 B más** cada siguiente, porque arrastra los sorteos de los anteriores. Con uno por sorteo:
**71,7 MB el primer año** y **~1,02 GB** al llegar a los 1 778 sorteos de holdout. En el paquete de git,
~1,5 KiB por snapshot: guarda solo lo que cambia. `data/raw/` pasa de **100 MB a los 216 snapshots,
unos 1,4 años**, y ahí la decisión del ciclo se reabre para estudiar guardar solo las filas nuevas.

## Cómo verificar

```powershell
Get-Content .\data\raw\2026-10-04_4274\SHA256.txt
Get-FileHash .\data\raw\2026-10-04_4274\*.csv -Algorithm SHA256 |
  ForEach-Object { "$($_.Hash.ToLower())  $(Split-Path $_.Path -Leaf)" }
git check-attr text -- data/raw/2026-10-04_4274/Melate.csv     # text: unset
git check-ignore -v data/raw/.x.construyendo data/cuarentena/x data/cache/melate-e-incompletas/x
.venv\Scripts\python.exe -m melate.almacen        # «snapshots congelados: 2026-10-02, 2026-10-02_4273, 2026-10-04_4274»
```

## Cómo revertir

Los snapshots no se revierten: son datos publicados, y los veredictos que juzgaron sobre ellos dejarían
de valer. Quitar el ciclo y la lectura de los `SHA256.txt` está descrito en
`Fases/2026-10-04_ciclo-vivo/Cambios/2026-10-05_10-03_s5-el-ciclo-vivo.md` y
`Fases/2026-10-04_ciclo-vivo/Cambios/2026-10-05_10-00_s5-c3-la-app-y-el-almacen-con-sus-snapshots.md`.

Relacionado: `Almacenamiento/Decisiones/2026-10-04_20-10_s5-el-ciclo-vivo.md`,
`Almacenamiento/Añadir/2026-10-03_00-13_s1-snapshots-congelados.md`,
`Almacenamiento/Añadir/2026-10-03_05-15_s3-cache-de-paginas.md`,
`Almacenamiento/Decisiones/2026-10-04_00-40_s4-que-entra-en-melate-duckdb.md`,
`Mapa/Modificar/2026-10-05_10-04_s5-entra-el-ciclo-vivo.md`.
