# Procedencia del snapshot 2026-10-02

Snapshot **inmutable**. Estos ficheros no se vuelven a descargar ni se tocan: son la copia fechada
contra la que se reproduce la línea base del `CLAUDE.md`. Un sorteo nuevo no se añade aquí; se crea
otra carpeta con su fecha.

## Por qué existe

Las cifras de la sección "Línea base verificada" del `CLAUDE.md` son al sorteo 4272. Los CSV
oficiales crecen con cada sorteo, así que una descarga en vivo deja de reproducirlas en cuanto se
celebra el siguiente. Sin este snapshot no habría forma de distinguir "el refactor rompió algo" de
"llegaron datos nuevos".

## Descarga

- **Fuente:** `https://www.loterianacional.gob.mx/Documentos/Historicos/{Melate,Revancha,Revanchita}.csv`
- **Hora:** 2026-10-03T03:19:27Z (2026-10-02 22:19 hora local)
- **Método:** `requests.get` con `timeout=60` y el mismo `User-Agent` que usa
  `baseline_auditoria.py`; bytes guardados tal cual, sin recodificar
- **Comprobación de integridad en la descarga:** HTTP 200 y la cadena `CONCURSO` presente en los
  primeros 200 caracteres de cada fichero

| Fichero | HTTP | Bytes | Primera fila de datos |
|---|---|---|---|
| `Melate.csv` | 200 | 206 675 | concurso 4272 del 30/09/2026 |
| `Revancha.csv` | 200 | 150 284 | concurso 4272 del 30/09/2026 |
| `Revanchita.csv` | 200 | 88 235 | concurso 4272 del 30/09/2026 |

El oficial llega **en orden descendente**: la primera fila de datos es el sorteo más reciente, no el
más antiguo. De ahí que la columna de arriba sea 4272 en los tres.

## SHA-256

```
51de5afd3b7d348bff2b3032c1d125fa6870d7176f8006a1dd9baf12ae1891cc  Melate.csv
5d1b191e3c8bc52de154124b3b0d6d5f730ebd0a1f6006f9d48f2776bf811581  Revancha.csv
06beda9ab84cf015951756ade4c8df4d894ebdf5e7dda64ef20f21e81e913b5a  Revanchita.csv
```

Los mismos valores, en formato legible por máquina, están en `SHA256.txt` junto a este documento.

## Cómo verificar

```powershell
Get-FileHash .\Melate.csv, .\Revancha.csv, .\Revanchita.csv -Algorithm SHA256 |
  ForEach-Object { "$($_.Hash.ToLower())  $(Split-Path $_.Path -Leaf)" }
```

Debe coincidir, línea por línea, con `SHA256.txt`. Si no coincide, el snapshot está corrupto o
alguien lo modificó: no se arregla, se descarta y se crea otro con su fecha.

## Cómo volver a crearlo

No se recrea: un snapshot fechado es inmutable por definición. Para hacer uno **nuevo**, con los
datos del día, se descargan los tres CSV a `data/raw/<AAAA-MM-DD>/` conservando los nombres
`Melate.csv`, `Revancha.csv` y `Revanchita.csv` —`cargar(juego, carpeta)` abre exactamente
`{juego}.csv`—, se calculan los SHA-256 y se escribe un `PROCEDENCIA.md` como este.

## Qué se puede y qué no se puede concluir de aquí

- **Sí:** que la línea base reproducida con `--datos data/raw/2026-10-02` es comparable con la del
  `CLAUDE.md`, porque los datos son los mismos bytes.
- **No:** que estos ficheros estén libres de errores. El propio `CLAUDE.md` documenta tres
  (`BOLSA = 0` en 2120, 2142 y 2234) y uno fuera de secuencia (Revancha 3221 = 238.6 M). El snapshot
  congela los datos **con sus errores incluidos**, que es lo correcto: el código los trata, no los
  esconde.
