# Procedencia del snapshot 2026-10-02_4273

Snapshot **inmutable**, congelado por `python -m melate.ciclo` (Fase 5). Estos ficheros no se vuelven a descargar ni se tocan. Un sorteo nuevo no se añade aquí: va en otra carpeta.

## Descarga

- **Fuente:** `https://www.loterianacional.gob.mx/Documentos/Historicos/{Melate,Revancha,Revanchita}.csv`
- **Descargado:** 2026-10-05T02:08:24+00:00 · **congelado:** 2026-10-05T02:08:29+00:00
- **Método:** `melate.ciclo.descargar_oficial`: `requests.get` con `timeout=30` y el `User-Agent` de `src/melate/ingest.py`; bytes guardados tal cual, sin recodificar

| Fichero | HTTP | Bytes | Descargado (UTC) | Last-Modified | SHA-256 |
|---|---|---|---|---|---|
| `Melate.csv` | 200 | 206724 | 2026-10-05T02:08:24+00:00 | Sun, 04 Oct 2026 12:00:04 GMT | `5dbb2ab8838f1a5ec034fbcbbe377ca1674978a4d990012cab264d88b24bc4a5` |
| `Revancha.csv` | 200 | 150330 | 2026-10-05T02:08:25+00:00 | Sun, 04 Oct 2026 12:00:04 GMT | `7f34ff9332524d177792f1f7d2a5af1115756d4a8c1b909fdf7a34c23f0545ab` |
| `Revanchita.csv` | 200 | 88283 | 2026-10-05T02:08:26+00:00 | Sun, 04 Oct 2026 12:00:04 GMT | `fba4afe5f233bd796b1ebae0b0d583d6515cb52a6a37992729668df289050e17` |

## Sobre el snapshot anterior

- **Anterior:** `data/raw/2026-10-02`, hasta el sorteo 4272.
- **El pasado no cambió:** en los tres juegos, la cabecera es la misma y el fichero anterior es un sufijo exacto, byte a byte, del nuevo.
- **Sorteos nuevos:** 4273.
- **Validados** con `validar_era`: concursos consecutivos, sin duplicados, números en rango y ordenados, el adicional fuera de los naturales, la BOLSA inválida solo donde ya se conocía, y la de cada sorteo nuevo por encima de la bolsa mínima.

## Testigos de cada sorteo nuevo (regla 7, C2.2)

| Sorteo | Juego | Números del oficial | Adicional | BOLSA | Espejo | melate-e.com |
|---|---|---|---|---|---|---|
| 4273 | Melate | 6 18 24 44 50 55 | 39 | 80000000 | confirma | confirma |
| 4273 | Revancha | 8 9 32 37 51 55 | — | 115000000 | confirma | confirma |
| 4273 | Revanchita | 16 29 31 42 48 56 | — | 158000000 | confirma | no se pide (dictamen) |

**Testigos sin los que se siguió, por decisión explícita:** ninguno.

## SHA-256

```
5dbb2ab8838f1a5ec034fbcbbe377ca1674978a4d990012cab264d88b24bc4a5  Melate.csv
7f34ff9332524d177792f1f7d2a5af1115756d4a8c1b909fdf7a34c23f0545ab  Revancha.csv
fba4afe5f233bd796b1ebae0b0d583d6515cb52a6a37992729668df289050e17  Revanchita.csv
```

Los mismos valores, legibles por máquina, en `SHA256.txt`.

## Cómo verificar

```powershell
Get-FileHash .\Melate.csv, .\Revancha.csv, .\Revanchita.csv -Algorithm SHA256 |
  ForEach-Object { "$($_.Hash.ToLower())  $(Split-Path $_.Path -Leaf)" }
```

Debe coincidir, línea por línea, con `SHA256.txt`. Si no coincide, el snapshot está corrupto o alguien lo modificó: no se arregla, se descarta.
