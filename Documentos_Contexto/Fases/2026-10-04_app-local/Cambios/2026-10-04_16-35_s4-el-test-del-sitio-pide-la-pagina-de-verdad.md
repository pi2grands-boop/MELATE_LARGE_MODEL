# El test que vigila melate-e.com pide la página de verdad (C8)

- **Fecha/hora:** 2026-10-04 16:35
- **Área:** Fases/2026-10-04_app-local · **Acción:** Cambios
- **Chat / página:** cierre de la Fase 4 · la decisión C8 del usuario
- **Archivos afectados:** `tests/test_popularidad.py`

## Qué se hizo

`test_el_sitio_sigue_teniendo_la_forma_que_esperamos`, el único test marcado `red` de
`tests/test_popularidad.py`, crea su `Descargador` con `cache=tmp_path` —una caché vacía que pytest
borra— y comprueba **`d.peticiones == 1`** antes que la forma de la tabla.

## Por qué

**El hallazgo.** Al preparar la explicación de los pendientes heredados para el usuario
(`Fases/2026-10-04_app-local/Bugs/2026-10-04_11-39_s4-review-lanzador.md`): el test pedía el sorteo
4272 con la caché por defecto, `data/cache/melate-e`, que lo guarda desde la Fase 3, y
`Descargador.html` devuelve la copia si existe (`src/melate/popularity.py:267`). Leía la copia y no
el sitio: con una sesión que falla si se usa, `peticiones = 0`. El pendiente 7 de
`Fases/2026-10-03_popularidad/99_CIERRE.md` —que el sitio conserve la forma de su tabla— no lo
vigilaba nada, y el documento de la conexión decía de ese test «contra el sitio real».

**La decisión fue del usuario.** Se le presentaron dos opciones: (a) una caché temporal, que hace
una petición real al sitio en cada pasada de la suite completa; (b) dejar el test como estaba, una
orden manual para comprobar el sitio y escrito que nada lo vigila. **Eligió (a).**

**Es una excepción intencional** a la regla del dictamen «una página descargada no se vuelve a pedir
nunca» (`Fases/2026-10-03_popularidad/Decisiones/2026-10-03_02-40_s3-dictamen-terminos-melate-e.md`),
y solo para este test: una página, el sorteo 4272 de Melate, en cada `pytest tests`. El bucle rápido
excluye `red` y no la pide. Las demás reglas del dictamen se cumplen igual: el mismo `User-Agent`
que nos identifica, el mismo ritmo, sin evasión, Revanchita no se pide, y si el sitio bloquea,
`SitioBloqueado` para el test con la instrucción de parar y preguntar.

**La aserción `peticiones == 1` es la que impide volver atrás.** Si alguien le devuelve la caché
permanente, el test falla mientras esa caché exista, que es justo cuando el error sería invisible.

## Impacto en seguridad / conexiones / datos

- **Conexiones:** una petición más a `resultados.melate-e.com` por cada pasada de la suite completa,
  que se corre unas pocas veces por fase. Emitido a
  `Conexiones/Modificar/2026-10-04_16-35_s4-el-test-del-sitio-pide-la-pagina-de-verdad.md`.
- **Seguridad:** la misma postura de siempre ante el sitio: nos identificamos y somos bloqueables.
- **Datos:** la caché permanente no se toca. Comprobado: `data/cache/melate-e/melate/4272.html`,
  misma fecha y mismo tamaño (8 185 bytes) antes y después.

## Cómo verificar / revertir

```powershell
.venv\Scripts\python.exe -m pytest tests\test_popularidad.py -k sitio_sigue -q   # 1 passed
```

**Dos valores, medidos:** con la caché permanente, 0 peticiones; con la de usar y tirar, 1, y la
tabla con la forma esperada —9 categorías y los 115 808 ganadores de 2 aciertos— en 1,8 s.

**No entra en `scripts/mutar.py`**, y no por olvido: el guion corre sin red
(`-m "not lento and not red"`), así que nada que solo vigile un test `red` se puede mutar. Lo protege
su propia aserción.

**Revertir:** volver a `pop.Descargador()` sin argumentos y quitar la aserción de `peticiones`. Lo que
se reintroduce: un test que dice ir contra el sitio y lee una copia.

Relacionado: `Fases/2026-10-04_app-local/Bugs/2026-10-04_11-39_s4-review-lanzador.md`,
`Conexiones/Modificar/2026-10-04_16-35_s4-el-test-del-sitio-pide-la-pagina-de-verdad.md`,
`Fases/2026-10-03_popularidad/Decisiones/2026-10-03_02-40_s3-dictamen-terminos-melate-e.md`,
`Fases/2026-10-03_popularidad/99_CIERRE.md`.
