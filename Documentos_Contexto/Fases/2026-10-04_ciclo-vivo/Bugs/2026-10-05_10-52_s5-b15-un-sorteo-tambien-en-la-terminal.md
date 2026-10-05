# B15 · El laboratorio escribía «1 sorteos» en la terminal

- **Fecha/hora:** 2026-10-05 10:52
- **Área:** Fases/2026-10-04_ciclo-vivo · **Acción:** Bugs
- **Chat / página:** sesión de la Fase 5 · al preparar la guía para que el usuario pruebe la fase
- **Archivos afectados:** `src/melate/lab.py`, `tests/test_protocolo.py`, `scripts/mutar.py`
- **Estado:** CERRADO el 2026-10-05 a las 11:29 (bloque al final)

## Limitaciones del entorno, por delante

- **Windows 11, PowerShell 5.1 y Git Bash.** Nada probado en Linux ni macOS.
- Las tres reviews de la fase ya estaban cerradas. Este fallo apareció después, al reproducir a mano el
  veredicto del 4274 para escribir la guía de pruebas del usuario, y por eso tiene su propio documento.

## Lo que se vio

Reproduciendo el veredicto del 4274 con su orden:

```
.venv\Scripts\python.exe -m melate.lab --prereg prereg/2026-10-03_logistica-revancha.json --datos data\raw\2026-10-04_4274
== Holdout (sorteos posteriores al sello)
   Melate         1 sorteos  4274-4274
```

C3 había pasado al singular el motivo de la condición 1 (`protocolo._sorteos`) y la app (`sorteos()`),
pero no la línea del holdout de la salida de terminal del laboratorio,
`lab._imprimir` (`src/melate/lab.py:366`), que escribía siempre `{n} sorteos`. El JSON del veredicto y
la cabecera de la app estaban bien: es solo la terminal, y es lo primero que lee quien reproduce el
veredicto a mano.

**Se consultó al usuario**, con la recomendación de arreglarlo antes de cerrar la fase. Respuesta,
antes de las 10:52: *«Arregla eso que me dijiste primero»*.

## Evidencia antes del arreglo

`test_el_laboratorio_dice_un_sorteo_tambien_en_la_terminal`, escrito antes de tocar el código, falla con
el código de entonces:

```
AssertionError: == Preregistro x
     Melate         1 sorteos  4274-4274
```

## El arreglo

`lab._imprimir` usa la misma regla de plural que el motivo de la condición 1, `protocolo._sorteos`, en
vez de una segunda copia: una sola regla para «sorteo» y «sorteos» en todo lo que escribe el
laboratorio. La línea queda alineada a la derecha, con el mismo ancho que antes.

- **Test:** `test_el_laboratorio_dice_un_sorteo_tambien_en_la_terminal`, en `tests/test_protocolo.py`:
  1 sorteo en singular, y 2 y 0 en plural, con su rango.
- **Mutación:** «F5 cierre: el laboratorio vuelve a escribir «1 sorteos» en la terminal (B15)»
  devuelve la línea de antes; detectada por ese test, en 3,0 s.
- **En la salida real**, reproduciendo el veredicto del 4274:

```
== Holdout (sorteos posteriores al sello)
   Melate          1 sorteo  4274-4274
   Revancha        1 sorteo  4274-4274
   Revanchita      1 sorteo  4274-4274
```

- **El bucle rápido**: 287 en verde, 35,1 s, con el portátil a batería.

## Pendiente de verificar en vivo

Nada propio: la salida real del laboratorio ya se miró, arriba. Fuera de Windows, heredado.

## Resultado — CERRADO el 2026-10-05 a las 11:29

| # | Hallazgo | Arreglo | Lo fija |
|---|---|---|---|
| B15 | `melate.lab` escribía «1 sorteos» en la terminal | la regla de `protocolo._sorteos`, la misma del motivo | `test_el_laboratorio_dice_un_sorteo_tambien_en_la_terminal` y su mutación |

**Medido después del arreglo**, con el código final de la fase:

- `pytest tests`: **321 en verde**, 234 s; por el proxy, **7 conexiones**, las mismas de siempre.
- El bucle rápido: **287 en verde**, 35 s.
- `scripts/mutar.py`: **97 de 97**, 450 s con el portátil a batería.

Los recuentos que lo citaban como estado actual —el README, `_MAPA.md`, el cierre de la fase, el árbol
y `Rendimiento/`— dicen ya 287, 321 y 97. Las cifras de las reviews y de los `Cambios/` son medidas de
su hora, y se quedan como fueron.

Relacionado: `Fases/2026-10-04_ciclo-vivo/Bugs/2026-10-04_20-37_s5-review-c3-app-y-almacen.md`,
`Fases/2026-10-04_ciclo-vivo/99_CIERRE.md`.

## Cómo verificar

```powershell
.venv\Scripts\python.exe -m pytest tests\test_protocolo.py -k tambien_en_la_terminal -q
.venv\Scripts\python.exe scripts\mutar.py --solo B15
```
