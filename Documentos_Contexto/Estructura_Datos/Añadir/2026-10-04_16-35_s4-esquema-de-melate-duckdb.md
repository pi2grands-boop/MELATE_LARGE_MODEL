# El esquema de `melate.duckdb`

- **Fecha/hora:** 2026-10-04 16:35
- **Área:** Estructura_Datos · **Acción:** Añadir
- **Chat / página:** cierre de la Fase 4 · `src/melate/almacen.py`
- **Archivos afectados:** `src/melate/almacen.py`

Qué entra en la base y por qué no se publica lo decidió
`Almacenamiento/Decisiones/2026-10-04_00-40_s4-que-entra-en-melate-duckdb.md`, antes del código.
Este documento es la forma que tomó.

## Las 16 tablas, y la frontera escrita en los datos

Cada tabla declara su **naturaleza** —juzga, explora, mide o procedencia— y a qué **mira**: la urna,
el dinero, los jugadores o los datos. Son las dos fronteras del proyecto, «el informe explora, el
laboratorio juzga» y «la urna dentro de la familia, los jugadores fuera», escritas en la propia base
para que la app no tenga que adivinarlas. La tabla `catalogo` las guarda.

| Tabla | Naturaleza | Mira a | Qué es |
|---|---|---|---|
| `construccion` | procedencia | datos | Cuándo, con qué versión del esquema, de `melate` y de `duckdb`, y desde qué carpetas se construyó |
| `fuentes` | procedencia | datos | Cada fichero leído: ruta relativa, tipo, SHA-256, bytes, fecha que declara, si vale y por qué no |
| `datos_informe` | procedencia | datos | Sobre qué datos se corrió cada informe: hash, origen, último sorteo, defectos de la validación |
| `catalogo` | procedencia | datos | Esta tabla de tablas |
| `preregistros` | juzga | urna | Las hipótesis selladas, y si su sello verifica (con la función del propio laboratorio) |
| `veredictos` | juzga | urna | Las salidas de `melate.lab`, cada una con su preregistro, si vale y por qué, y sobre qué datos juzgó |
| `condiciones` | juzga | urna | Las cinco condiciones de cada veredicto, con su motivo |
| `informes` | explora | urna | Cada salida de `melate.informe` o del oráculo, con su **resumen exploratorio** |
| `auditoria` | explora | urna | Los estadísticos de la urna por juego, con su p y sus dos q |
| `backtest` | explora | urna | Las estrategias por juego con su p y sus q, y el log-loss donde lo hay |
| `exploracion_juego` | explora | urna | Por juego: tramo de prueba, mínimo detectable y poder de la auditoría |
| `valor_esperado` | mide | dinero | El EV del sorteo siguiente, con la constante del oráculo y con los premios menores medidos |
| `premios_mayores` | mide | dinero | Premios mayores detectados por bajas de BOLSA |
| `popularidad` | mide | jugadores | Cada ventana: ventas, premios menores, sorteos sin premios publicados y efecto calendario |
| `carteras` | mide | jugadores | Cada cartera, con su valoración, con qué bolsa se hizo y su aviso |
| `cartera_boletos` | mide | jugadores | Los boletos de cada cartera |

## Las reglas de la forma, cada una con su test

- **Ningún número que no esté en un fichero publicado.** Se copia y se reordena. Lo único que se
  calcula son comprobaciones de integridad: el SHA-256 de cada fichero, el sello de cada
  preregistro y el enlace de cada veredicto con el suyo.
- **Una columna llamada `veredicto` solo existe en las tablas que juzgan.** El resumen del informe
  se llama `resumen_exploratorio`, nunca veredicto.
- **Un veredicto vale** si su sello es el de un preregistro que verifica, tiene fecha de corrida, y
  su texto, su marca de ventaja y sus cinco condiciones dicen lo mismo. Si no, entra igual, con
  `valido = false` y su `motivo`: se ve que está y por qué no cuenta.
- **El vigente de cada preregistro** es el que juzgó con más datos (`ultimo_concurso_datos`); a
  igualdad, el más reciente. Volver a correr el laboratorio sobre el snapshot viejo no desplaza a
  uno con holdout.
- **Rutas relativas a la carpeta de la base**, nunca absolutas. Lo que está fuera se guarda solo por
  su nombre.
- **Cada fichero entra entero o no entra:** uno malformado queda en `fuentes` como no válido, sin
  filas a medias y sin tumbar la construcción.
- **Las fechas se normalizan a UTC y segundos** antes de guardarse: se ordena por ellas.

## Versión del esquema y frescura

`construccion.version_esquema` vale **1** (`almacen.VERSION_ESQUEMA`). La app comprueba la versión,
las tablas **y las columnas** (`almacen.problema_de_esquema`): una base de una versión anterior del
código tenía todas las tablas y le faltaba una columna. Cualquier cambio de columnas obliga a subir
la versión.

`fuentes` guarda el SHA-256 de cada fichero leído, y `almacen.frescura` lo compara con lo que hay en
disco: ficheros nuevos, cambiados o borrados. Por eso la base sabe si está al día, y el lanzador la
reconstruye cuando no.

## El fichero

4 993 024 bytes para unos 250 KB de JSON: son los bloques de 256 KB de DuckDB, uno por tabla como
mínimo. Se construye en una transacción en 0,16-0,31 s en caliente, en un temporal `.construyendo`
que sustituye al anterior de una vez, para que una app abierta nunca vea una base a medias.

## Cómo verificar

```powershell
.venv\Scripts\python.exe -m melate.almacen                # qué leyó, qué vale y qué enseñará la app
.venv\Scripts\python.exe -m pytest tests\test_almacen.py -q
```

## Cómo revertir

La base se puede borrar en cualquier momento sin perder nada: el lanzador la vuelve a construir.
Cambiar su forma es cambiar `ESQUEMA` y `CATALOGO` en `src/melate/almacen.py`, subir
`VERSION_ESQUEMA` y reconstruir.

Relacionado: `Almacenamiento/Decisiones/2026-10-04_00-40_s4-que-entra-en-melate-duckdb.md`,
`Almacenamiento/Modificar/2026-10-04_16-35_s4-la-base-la-pone-al-dia-el-lanzador.md`,
`Interconexion/Añadir/2026-10-04_16-35_s4-las-pantallas-de-la-app.md`,
`Estructura_Datos/Modificar/2026-10-04_16-35_s4-veredicto-popularidad-y-cartera.md`.
