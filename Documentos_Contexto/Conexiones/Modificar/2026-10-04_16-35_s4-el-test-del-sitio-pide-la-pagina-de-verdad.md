# La suite completa pide una página real a melate-e.com, y la app no llama a nadie

- **Fecha/hora:** 2026-10-04 16:35
- **Área:** Conexiones · **Acción:** Modificar
- **Chat / página:** cierre de la Fase 4 · `Fases/2026-10-04_app-local/`
- **Archivos afectados:** `tests/test_popularidad.py`, `src/melate/app.py`, `app/streamlit_app.py`

## Qué cambia

Dos cosas en quién llama a quién, las dos de la Fase 4.

**1 · El test que vigila el contrato con melate-e.com va de verdad al sitio.**
`Conexiones/Añadir/2026-10-03_05-15_s3-tablas-de-ganadores-melate-e.md` dice que
`pytest -m red` va «contra el sitio real». **No era verdad hasta hoy:** el test leía el sorteo 4272
de la caché permanente, que lo guarda desde la Fase 3, y hacía 0 peticiones. Ahora usa una caché de
usar y tirar y exige `peticiones == 1`. Es una excepción, **decidida por el usuario**, a la regla
«una página descargada no se vuelve a pedir nunca»: vale solo para ese test y solo para esa página.
El proceso, con el hallazgo y las dos opciones que se le presentaron, está en
`Fases/2026-10-04_app-local/Cambios/2026-10-04_16-35_s4-el-test-del-sitio-pide-la-pagina-de-verdad.md`.

**2 · La app y su lanzador no llaman a nadie.** La app lee `melate.duckdb` y nada más, y Streamlit
sale de la máquina en dos sitios que el proyecto cierra: la telemetría del *frontend*, apagada, y
la búsqueda de la IP pública ante una conexión de otro origen, que el lanzador anula. El detalle, en
`Red/Añadir/2026-10-04_16-35_s4-que-sirve-la-app-y-a-quien.md`.

## Quién sale de la máquina hoy, y cuándo

| Quién | A dónde | Cuándo |
|---|---|---|
| `melate.ingest.cargar` | `loterianacional.gob.mx` | solo sin `--datos`: el laboratorio o el informe con datos de hoy |
| `melate.popularity` | `resultados.melate-e.com` | solo las páginas que no están en la caché, a 1 por segundo |
| `tests/test_reglas_datos.py`, los dos marcados `red` (cuatro casos) | `raw.githubusercontent.com` | en cada `pytest tests`: el espejo no tiene caché (`ingest.cargar_espejo`) |
| `tests/test_popularidad.py`, el marcado `red` | `resultados.melate-e.com` | **nuevo:** una página, el 4272 de Melate, en cada `pytest tests` |
| La app y `python -m melate.app` | nadie | — |

El bucle rápido (`-m "not lento and not red"`) y `scripts/mutar.py` no salen nunca a la red.

## Qué NO cambia

- El contrato con melate-e.com para todo lo que no es ese test: ritmo, caché permanente,
  identificación, sin evasión, Revanchita no se pide, ventana declarada, y si bloquean, se para y
  se pregunta. El test también para con `SitioBloqueado` si el sitio bloquea.
- El oficial sigue siendo la única carga, y el espejo, solo validación cruzada.

## Cómo verificar / revertir

```powershell
.venv\Scripts\python.exe -m pytest tests\test_popularidad.py -k sitio_sigue -q   # 1 petición real, 1 passed
.venv\Scripts\python.exe -m pytest tests\test_app.py -k recorrido -q            # la app, con los sockets fuera de esta máquina prohibidos
```

**Revertir** el punto 1 es devolverle al test la caché por defecto y quitar su aserción de
`peticiones`: vuelve a leer una copia y a no vigilar nada. El punto 2 no tiene revertir que
recomendar: es la ausencia de llamadas.

Relacionado: `Conexiones/Añadir/2026-10-03_05-15_s3-tablas-de-ganadores-melate-e.md`,
`Conexiones/Añadir/2026-10-03_00-13_s1-fuentes-de-datos.md`,
`Fases/2026-10-04_app-local/Cambios/2026-10-04_16-35_s4-el-test-del-sitio-pide-la-pagina-de-verdad.md`,
`Red/Añadir/2026-10-04_16-35_s4-que-sirve-la-app-y-a-quien.md`.
