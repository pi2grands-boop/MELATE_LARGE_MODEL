# Procedencia del snapshot 2026-10-04_4274

Snapshot **inmutable**, congelado por `python -m melate.ciclo` (Fase 5). Estos ficheros no se vuelven a descargar ni se tocan. Un sorteo nuevo no se añade aquí: va en otra carpeta.

## Descarga

- **Fuente:** `https://www.loterianacional.gob.mx/Documentos/Historicos/{Melate,Revancha,Revanchita}.csv`
- **Descargado:** 2026-10-05T14:22:00+00:00 · **congelado:** 2026-10-05T14:22:07+00:00
- **Método:** `melate.ciclo.descargar_oficial`: `requests.get` con `timeout=30` y el `User-Agent` de `src/melate/ingest.py`; bytes guardados tal cual, sin recodificar

| Fichero | HTTP | Bytes | Descargado (UTC) | Last-Modified | SHA-256 |
|---|---|---|---|---|---|
| `Melate.csv` | 200 | 206774 | 2026-10-05T14:22:00+00:00 | Mon, 05 Oct 2026 12:00:05 GMT | `c8495fa2fcb166cf2bcbb104d5d2b3ecb3f2fcf6290a2d664333588596d301c3` |
| `Revancha.csv` | 200 | 150376 | 2026-10-05T14:22:01+00:00 | Mon, 05 Oct 2026 12:00:05 GMT | `3bbb79119df6472d4c746d800b6efcc985d494fd070863d5146837024b07c6b1` |
| `Revanchita.csv` | 200 | 88330 | 2026-10-05T14:22:02+00:00 | Mon, 05 Oct 2026 12:00:06 GMT | `3fee8866b9e20eb56a4143fc300ad98d76032bde70e9f506cea009369615b1b6` |

## Sobre el snapshot anterior

- **Anterior:** `data/raw/2026-10-02_4273`, hasta el sorteo 4273.
- **El pasado no cambió:** en los tres juegos, la cabecera es la misma y el fichero anterior es un sufijo exacto, byte a byte, del nuevo.
- **Sorteos nuevos:** 4274.
- **Validados** con `validar_era`: concursos consecutivos, sin duplicados, números en rango y ordenados, el adicional fuera de los naturales, la BOLSA inválida solo donde ya se conocía, y la de cada sorteo nuevo por encima de la bolsa mínima.

## Testigos de cada sorteo nuevo (regla 7, C2.2)

| Sorteo | Juego | Números del oficial | Adicional | BOLSA | Espejo | melate-e.com |
|---|---|---|---|---|---|---|
| 4274 | Melate | 20 27 32 38 43 54 | 26 | 84100000 | confirma | confirma |
| 4274 | Revancha | 3 6 17 20 30 52 | — | 118300000 | confirma | confirma |
| 4274 | Revanchita | 6 13 17 26 39 49 | — | 160600000 | confirma | no se pide (dictamen) |

**Testigos sin los que se siguió, por decisión explícita:** ninguno.

## SHA-256

```
c8495fa2fcb166cf2bcbb104d5d2b3ecb3f2fcf6290a2d664333588596d301c3  Melate.csv
3bbb79119df6472d4c746d800b6efcc985d494fd070863d5146837024b07c6b1  Revancha.csv
3fee8866b9e20eb56a4143fc300ad98d76032bde70e9f506cea009369615b1b6  Revanchita.csv
```

Los mismos valores, legibles por máquina, en `SHA256.txt`.

## Cómo verificar

```powershell
Get-FileHash .\Melate.csv, .\Revancha.csv, .\Revanchita.csv -Algorithm SHA256 |
  ForEach-Object { "$($_.Hash.ToLower())  $(Split-Path $_.Path -Leaf)" }
```

Debe coincidir, línea por línea, con `SHA256.txt`. Si no coincide, el snapshot está corrupto o alguien lo modificó: no se arregla, se descarta.
