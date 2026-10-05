# La forma de un snapshot del ciclo, del veredicto nuevo y de la base, versión 2

- **Fecha/hora:** 2026-10-05 10:31
- **Área:** Estructura_Datos · **Acción:** Modificar
- **Chat / página:** cierre de la Fase 5 · `Fases/2026-10-04_ciclo-vivo/`
- **Archivos afectados:** `src/melate/ciclo.py`, `src/melate/lab.py`, `src/melate/almacen.py`

## 1 · Un snapshot del ciclo

`data/raw/<fecha>_<sorteo>/`, con cinco ficheros:

| Fichero | Forma |
|---|---|
| `Melate.csv`, `Revancha.csv`, `Revanchita.csv` | Los bytes que sirvió el oficial, sin tocar: CRLF, orden descendente, sus errores conocidos incluidos |
| `SHA256.txt` | Tres líneas `<sha256 en minúsculas>  <Juego>.csv`, con dos espacios y LF. La misma forma que el de la Fase 1: el test de punta a punta exige que, con los mismos datos, salga idéntico byte a byte. La base exige dos campos por línea, un hash de 64 caracteres y un fichero de un juego; si no, el snapshot no congela nada |
| `data/raw/<carpeta>/PROCEDENCIA.md` | **Descarga**: la URL real, la hora de cada descarga y la de congelar, y por fichero el HTTP, los bytes, el `Last-Modified` limpio y el SHA-256. **Sobre el snapshot anterior**: cuál, que el pasado no cambió y qué sorteos son nuevos. **Testigos**: por sorteo nuevo y juego, los números, el adicional y la BOLSA del oficial, y lo que dijo cada testigo (`confirma`, `discrepa en …`, `falta: …` o `no se pide (dictamen)`). Y **los testigos sin los que se siguió**, por `--sin-testigo`, o «ninguno» |

Sin rutas de la máquina en ninguno: se publican (test).

## 2 · Los reportes que deriva el ciclo

`reportes/<snapshot>_popularidad.json`, `<snapshot>_informe.json` y
`<snapshot>_veredicto-<id del preregistro>.json`. Respecto a
`Estructura_Datos/Modificar/2026-10-04_16-35_s4-veredicto-popularidad-y-cartera.md`:

- **El veredicto** gana `resultados.holdout_necesario`: los sorteos de holdout que necesita la
  condición 5 con el efecto que declaró el sello (1 778 con el sellado), o `null` si no declara
  ninguno. Su clave `datos` lleva rutas relativas al snapshot.
- **La popularidad del ciclo** gana `snapshot`, y su `procedencia.peticiones_de_red` cuenta las
  páginas que pidió la corrida al validar los sorteos nuevos; la ventana se analiza desde la caché,
  sin red, y lo dice en `procedencia.nota`.
- **El informe** no cambia de forma.

## 3 · `melate.duckdb`, esquema 2

Respecto a `Estructura_Datos/Añadir/2026-10-04_16-35_s4-esquema-de-melate-duckdb.md`, **17 tablas**:

| Tabla | Qué cambia |
|---|---|
| `snapshots` | **Nueva**, procedencia: una fila por línea de cada `data/raw/*/SHA256.txt` —carpeta, fichero, juego, SHA-256— |
| `construccion` | `dir_raw`: de qué carpeta se leyeron los snapshots |
| `veredictos` | `snapshot`, `holdout_necesario`, `efecto_minimo_detectable` y los aciertos por boleto de cada juego (`media_melate`, `media_revancha`, `media_revanchita`) |
| `informes` y `datos_informe` | `snapshot` |
| `fuentes` | cada `SHA256.txt`, con su tipo `snapshot`, su hash y si vale |

**La regla nueva, escrita en los datos:** `veredictos.valido` es falso si los datos no son un snapshot
congelado —los tres hashes en el `SHA256.txt` de una misma carpeta—, y `motivo` dice cuál de las tres
cosas falló. `construccion.version_esquema` vale **2**: la app rechaza una base de otra versión, y el
lanzador la reconstruye.

## Cómo verificar

```powershell
.venv\Scripts\python.exe -m pytest tests\test_almacen.py -k "esquema or snapshot or congelad" -q
.venv\Scripts\python.exe -m pytest tests\test_ciclo.py -k "byte_a_byte or ruta_de_la_maquina" -q
```

## Cómo revertir

Descrito en
`Fases/2026-10-04_ciclo-vivo/Cambios/2026-10-05_10-00_s5-c3-la-app-y-el-almacen-con-sus-snapshots.md`
y `Fases/2026-10-04_ciclo-vivo/Cambios/2026-10-05_10-03_s5-el-ciclo-vivo.md`.

Relacionado: `Estructura_Datos/Añadir/2026-10-04_16-35_s4-esquema-de-melate-duckdb.md`,
`Estructura_Datos/Modificar/2026-10-04_16-35_s4-veredicto-popularidad-y-cartera.md`,
`Almacenamiento/Modificar/2026-10-05_10-05_s5-los-snapshots-los-congela-el-ciclo.md`.
