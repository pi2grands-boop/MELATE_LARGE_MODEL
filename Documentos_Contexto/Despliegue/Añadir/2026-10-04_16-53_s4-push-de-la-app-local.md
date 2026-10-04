# Subida de la Fase 4: la app local

- **Fecha/hora:** 2026-10-04 16:53
- **Área:** Despliegue · **Acción:** Añadir

## Qué se subió

- **Commit:** `3c63973` — *feat: la app local, con su base y un lanzador que la ata a esta maquina*
- **Rama:** `main` → `c5eb42f..3c63973`
- **Repositorio:** `pi2grands-boop/MELATE_LARGE_MODEL` (público)
- **Volumen:** 51 ficheros, 6.751 inserciones, 59 borrados
- **Aprobada por el usuario**, junto con el cierre de la fase.

| Qué | Ficheros |
|---|---|
| Código nuevo | `app/streamlit_app.py`, `src/melate/almacen.py`, `src/melate/app.py`, `.streamlit/config.toml`, `scripts/mutar.py` |
| Código modificado | `src/melate/lab.py`, `src/melate/popularity.py`, `src/melate/portfolio.py`, `scripts/colador.ps1` |
| Tests | nuevos `tests/test_almacen.py` (31), `tests/test_app.py` (26), `tests/test_lanzador.py` (15), `tests/test_herramientas.py` (4); modificados `tests/conftest.py`, `tests/test_cartera.py`, `tests/test_popularidad.py` |
| Bitácora | 21 documentos nuevos —los 8 del dossier de la fase y 13 en las áreas base, entre ellos los primeros de `Red/` e `Interconexion/`— y 5 modificados, cada cambio con su marca visible |
| Contrato | `CLAUDE.md`, `README.md`, `_MAPA.md` |
| Entorno | `requirements.txt`, `entorno/pip-freeze-2026-10-04.txt`, `.gitignore` |
| Reportes | `reportes/2026-10-04_veredicto.json`, nuevo; los dos de popularidad y la cartera, regenerados |

## Qué NO se subió, y es deliberado

- **`melate.duckdb`** y sus temporales. Es un índice derivable entero de `reportes/` y `prereg/`, un
  binario que el colador no puede leer, y cambia de bytes en cada reconstrucción
  (`Almacenamiento/Decisiones/2026-10-04_00-40_s4-que-entra-en-melate-duckdb.md`). Además de
  `.gitignore`, el colador mira ahora el índice de git, y no encontró ninguna base versionada.
- **Ningún `secrets.toml`**: no existe ninguno, y `.gitignore` los excluye a cualquier profundidad.
- **`data/cache/`**, como desde la Fase 3: páginas de un tercero.

## Las dos puertas, antes de subir

```
colador.ps1 -Autoprueba   ->  0 coincidencias sobre 130 ficheros; autoprueba 4/4
verificar-bitacora.ps1    ->  0 hallazgos en las 5 comprobaciones; 71 documentos
pytest tests              ->  242 en verde (136,3 y 164,2 s), test_paridad.py intacto
scripts/mutar.py          ->  46 de 46 mutaciones detectadas
```

El colador se pasó dos veces: al cerrar la bitácora y justo antes del `push`, con el árbol limpio.
Y `git show --numstat` no enseña ningún fichero existente reescrito entero por los finales de
línea: el que más líneas pierde es el reporte de popularidad de 300 sorteos, 22, las cifras que
cambiaron.

## Lo que ahora es público y antes no

- **La app y su lanzador**, y con ellos lo que se aprendió de Streamlit 1.65 leyendo su código: que
  sin configurar escucha en todas las interfaces, que envía telemetría, y que ante una conexión de
  otro origen le pregunta a Amazon la IP pública de la máquina. Es comportamiento de una biblioteca
  pública, no del usuario.
- **Que el lanzador sustituye una función interna de Streamlit**, con el porqué y su test.
- **Que el test que vigilaba melate-e.com leía una copia desde la Fase 3**, y que ahora pide una
  página real en cada pasada de la suite completa, por decisión del usuario.

Nada personal. El proyecto sigue sin secretos: ni credenciales, ni `.env`.

## Cómo verificar

```powershell
git log --oneline -2          # el registro de esta subida y, debajo, 3c63973
git status -sb                # ## main...origin/main  (sin divergencia)
git ls-files "*.duckdb"       # vacío: la base no está en el repositorio
```

## Cómo revertir

```powershell
git revert 3c63973
```

Revierte la fase entera. Deja `melate.duckdb` en disco, porque no está versionada, y no desinstala
Streamlit ni DuckDB; para eso, `pip uninstall streamlit duckdb` y sus dependencias, que lista
`entorno/pip-freeze-2026-10-04.txt` frente a `entorno/pip-freeze-2026-10-03.txt`.

Relacionado: `Despliegue/Añadir/2026-10-03_05-50_s3-push-de-la-popularidad.md`,
`Fases/2026-10-04_app-local/99_CIERRE.md`,
`Seguridad/Modificar/2026-10-04_16-35_s4-un-servidor-local-y-su-superficie.md`.
