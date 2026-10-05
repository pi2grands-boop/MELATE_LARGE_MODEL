# Cada cifra nueva dice de qué snapshot sale, y la base lo comprueba por el hash

- **Fecha/hora:** 2026-10-05 10:09
- **Área:** Reproducibilidad · **Acción:** Modificar
- **Chat / página:** cierre de la Fase 5 · `Fases/2026-10-04_ciclo-vivo/`
- **Archivos afectados:** `src/melate/ciclo.py`, `src/melate/almacen.py`, `app/streamlit_app.py`

## Qué cambia

Hasta la Fase 4 había un solo snapshot, `data/raw/2026-10-02/`, y reproducir una cifra era correr su
orden con `--datos data/raw/2026-10-02`. Desde el veredicto que registra sus datos
(`Reproducibilidad/Arreglos_Bugs/2026-10-04_16-35_s4-el-veredicto-registra-sus-datos.md`) se sabía
**sobre qué bytes** juzgó cada veredicto; no se comprobaba que esos bytes estuvieran guardados.

Ahora:

1. **Cada sorteo nuevo entra en un snapshot nuevo**, congelado por el ciclo, con su `SHA256.txt` y su
   procedencia. Los CSV crecen con cada sorteo; los snapshots no cambian nunca.
2. **Cada cifra nueva sale de un snapshot con nombre**: `reportes/<snapshot>_popularidad.json`,
   `<snapshot>_informe.json` y `<snapshot>_veredicto-<preregistro>.json`. El nombre es una pista;
   lo que cuenta es el SHA-256 de los datos que lleva dentro cada reporte.
3. **La base enlaza cada veredicto e informe con su snapshot por ese hash**, no por la ruta, y **un
   veredicto cuyos datos no son un snapshot congelado no vale**: no puede ser el vigente. Lo que era
   costumbre —*nunca sobre una descarga en vivo que no quede guardada*— es regla con test.
4. **La app dice de qué snapshot sale** el veredicto de la cabecera y cada informe, y la orden para
   reproducir el veredicto lleva `--datos` con ese snapshot.

**Las cifras de la línea base del `CLAUDE.md` no cambian**: siguen siendo las del snapshot del
2026-10-02, y la paridad con el oráculo, con tolerancia cero, también.

## Reproducir lo que deriva el ciclo

Con el snapshot del 4274, por ejemplo. La salida, fuera de `reportes/`: `--salida` escribe encima sin
avisar (H6 del inventario de la Fase 5; el ciclo nunca lo hace, una orden a mano sí).

```powershell
# El veredicto: tiene que dar «sin ventaja demostrada», 2 de 5
.venv\Scripts\python.exe -m melate.lab --prereg prereg/2026-10-03_logistica-revancha.json `
    --datos data\raw\2026-10-04_4274 --salida $env:TEMP\veredicto.json

# El informe, con los premios menores medidos: el valor esperado del 4275
.venv\Scripts\python.exe -m melate.informe --datos data\raw\2026-10-04_4274 `
    --popularidad reportes\2026-10-04_4274_popularidad.json --salida $env:TEMP\informe.json

# La popularidad: lee la caché, que no se publica; en otra máquina pediría las 200 páginas
.venv\Scripts\python.exe -m melate.popularity --desde 4175 --hasta 4274 `
    --datos data\raw\2026-10-04_4274 --salida $env:TEMP\popularidad.json
```

**Comprobado:** el informe que deriva el ciclo da, sobre los mismos bytes que el snapshot del
2026-10-02, el valor esperado del 4273 que publicó la Fase 1, cifra por cifra
(`test_el_informe_del_ciclo_reproduce_el_valor_esperado_publicado`, lento). Y el snapshot que congela
el ciclo es, byte a byte, el que se congeló a mano, `SHA256.txt` incluido
(`test_congela_lo_que_sirve_el_oficial_byte_a_byte`).

## Lo que no se puede reproducir en otra máquina sin pedirlo otra vez

Las páginas de melate-e.com no se publican: son de un tercero. La popularidad de una ventana se
reproduce con la caché de esta máquina; en otra, pidiendo las páginas con el ritmo del dictamen. Es
lo mismo que en la Fase 3.

## Cómo verificar / revertir

```powershell
.venv\Scripts\python.exe -m pytest tests\test_almacen.py -k "snapshot or congelad" -q
.venv\Scripts\python.exe -m pytest tests\test_ciclo.py -k "byte_a_byte or reproduce" -q   # el segundo es lento
```

**Revertir** el enlace por hash está descrito en
`Fases/2026-10-04_ciclo-vivo/Cambios/2026-10-05_10-00_s5-c3-la-app-y-el-almacen-con-sus-snapshots.md`.
No se recomienda: un veredicto sobre bytes que no se guardaron volvería a contar.

Relacionado: `Reproducibilidad/Añadir/2026-10-03_00-13_s1-linea-base-reproducida.md`,
`Reproducibilidad/Arreglos_Bugs/2026-10-04_16-35_s4-el-veredicto-registra-sus-datos.md`,
`Almacenamiento/Modificar/2026-10-05_10-05_s5-los-snapshots-los-congela-el-ciclo.md`,
`Fases/2026-10-04_ciclo-vivo/Cambios/2026-10-05_10-03_s5-el-ciclo-vivo.md`.
