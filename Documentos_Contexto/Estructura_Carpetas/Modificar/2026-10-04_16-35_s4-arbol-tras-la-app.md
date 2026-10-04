# El árbol después de la app local

- **Fecha/hora:** 2026-10-04 16:35
- **Área:** Estructura_Carpetas · **Acción:** Modificar
- **Chat / página:** cierre de la Fase 4 · `Fases/2026-10-04_app-local/`
- **Archivos afectados:** los de la tabla

## Qué aparece y qué cambia

Respecto a `Estructura_Carpetas/Modificar/2026-10-03_05-15_s3-arbol-tras-la-popularidad.md`, que
dejaba fuera `app/streamlit_app.py` y `melate.duckdb` por ser de esta fase:

```
app/
  streamlit_app.py             NUEVO   la app: cinco pantallas, solo lectura (625 líneas)
.streamlit/
  config.toml                  NUEVO   lo que fuerza el lanzador, para streamlit run desde la raíz
src/melate/
  almacen.py                   NUEVO   construye y lee melate.duckdb (674 líneas)
  app.py                       NUEVO   el lanzador, python -m melate.app (140 líneas)
  lab.py                       CAMBIA  el veredicto registra sus datos
  popularity.py                CAMBIA  los sorteos sin premios publicados
  portfolio.py                 CAMBIA  la valoración dice con qué se hizo
scripts/
  mutar.py                     NUEVO   mutación de tests sobre una copia: 46 mutaciones
  colador.ps1                  CAMBIA  caza también una base de datos versionada
tests/
  test_almacen.py              NUEVO   31 pruebas
  test_app.py                  NUEVO   26 pruebas
  test_lanzador.py             NUEVO   15 pruebas
  test_herramientas.py         NUEVO   4 pruebas, las de mutar.py
  conftest.py                  CAMBIA  las bases adversarias, construidas una vez por sesión
reportes/
  2026-10-04_veredicto.json    NUEVO   el primer veredicto que registra sus datos
entorno/
  pip-freeze-2026-10-04.txt    NUEVO   66 paquetes (eran 43) más la instalación editable
melate.duckdb                  NO SE PUBLICA   la reconstruye el lanzador
```

Y en la bitácora, el dossier `Documentos_Contexto/Fases/2026-10-04_app-local/` y los primeros
documentos de `Red/` e `Interconexion/`, que existían vacías desde la Fase 1.

## Lo que no se publica, y por qué

| Ruta | Por qué no |
|---|---|
| `melate.duckdb` y sus temporales (`*.duckdb.wal`, `*.duckdb.construyendo`…) | Un índice derivable de `reportes/` y `prereg/`; un binario que el colador no puede leer; cambia de bytes en cada reconstrucción. Ver `Almacenamiento/Decisiones/2026-10-04_00-40_s4-que-entra-en-melate-duckdb.md` |
| Cualquier `.streamlit/secrets.toml`, a cualquier profundidad | El proyecto no tiene secretos; la regla es para que uno creado por accidente no se publique. Streamlit los lee también junto al script, en `app/.streamlit/` |

## Lo que se decidió no crear

**`app/.streamlit/config.toml`.** Streamlit 1.65 también lee la configuración junto al script, se
lance desde donde se lance. No se movió allí la de la raíz: el lanzador ya fuerza las opciones por
línea de órdenes, que además mandan sobre las variables `STREAMLIT_*` —un fichero no puede—, y moverla
cambiaría una ruta citada en el README, el `CLAUDE.md`, la app, los tests y `scripts/mutar.py`.

## Cómo verificar / revertir

```powershell
git status --short --ignored -- melate.duckdb             # !! melate.duckdb: ignorada
.venv\Scripts\python.exe -m pytest tests --collect-only -q   # 242 pruebas
```

**Revertir** la fase entera es quitar lo marcado NUEVO, deshacer lo marcado CAMBIA según su
documento, y quitar las líneas de la Fase 4 de `.gitignore`.

Relacionado: `Estructura_Carpetas/Modificar/2026-10-03_05-15_s3-arbol-tras-la-popularidad.md`,
`Mapa/Modificar/2026-10-04_16-35_s4-entra-la-app-local.md`,
`Almacenamiento/Decisiones/2026-10-04_00-40_s4-que-entra-en-melate-duckdb.md`.
