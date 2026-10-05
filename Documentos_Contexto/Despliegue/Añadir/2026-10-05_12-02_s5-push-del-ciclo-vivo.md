# Subida de la Fase 5: el ciclo vivo

- **Fecha/hora:** 2026-10-05 12:02
- **Área:** Despliegue · **Acción:** Añadir

## Qué se subió

- **Rama:** `main` → `c9b5a47..5674134`, cuatro commits
- **Repositorio:** `pi2grands-boop/MELATE_LARGE_MODEL` (público)
- **Volumen:** 54 ficheros, 31 679 inserciones, 121 borrados; 26 198 de las inserciones son los CSV
  de los dos snapshots
- **Aprobada por el usuario**, junto con el cierre de la fase, después de correr él mismo la guía de
  pruebas y recorrer la app: *«Ya ejecuté todo, me gusta como se ve. Sube todo y la documentación
  también»*.

| Commit | Qué lleva |
|---|---|
| `408f6f0` — *docs: el inventario, el alcance y las decisiones de la fase 5, antes que su codigo* | El inventario, el alcance, las decisiones del usuario, la de C1 (`Protocolo_Estadistico/Decisiones/`) y la del ciclo (`Almacenamiento/Decisiones/`). 5 ficheros |
| `3e3915a` — *feat: el ciclo vivo, la condicion 5 con un holdout capaz y la app con sus snapshots* | `src/melate/ciclo.py` y `tests/test_ciclo.py`, nuevos; `almacen.py`, `lab.py`, `protocolo.py`, la app, los tests de la base, la app y el protocolo, `scripts/mutar.py` y `.gitignore`. 12 ficheros |
| `f7107a0` — *data: los snapshots del 4273 y del 4274, y lo que el ciclo derivo de ellos* | `data/raw/2026-10-02_4273/` y `data/raw/2026-10-04_4274/`, y sus seis reportes en `reportes/`. 16 ficheros |
| `5674134` — *docs: la bitacora de la fase 5 y su cierre, aprobado por el usuario* | El resto del dossier, los once documentos emitidos a las áreas base, el README y `_MAPA.md`. 21 ficheros |

**El orden es a propósito.** El alcance pedía que la decisión del ciclo fuera anterior a su código
«por hora y por `git log`». Nada se comiteó durante la fase, así que git solo puede probar el orden:
las decisiones van en un commit anterior al del código. La hora la prueban los nombres de los
documentos y las reviews: la decisión es de las 20:10 y la review del módulo, de las 20:51.

## Qué NO se subió, y es deliberado

- **`melate.duckdb`**: un índice derivable, un binario que el colador no puede leer. `git ls-files
  "*.duckdb"`, vacío.
- **`data/cache/`**, con las páginas de melate-e.com, como desde la Fase 3: son de un tercero.
- **Lo que el ciclo deja en disco y no se publica**: `data/cache/melate-e-incompletas/` (vacía),
  `data/cuarentena/` (no existe: no hubo ningún hallazgo) y las carpetas temporales `data/raw/.*`.
- **El `CLAUDE.md`, sin cambios**: el cierre propone un texto para el ciclo y la regla 5, y lo decide
  el usuario.

## Las puertas, antes de subir

```
colador.ps1 -Autoprueba   ->  0 coincidencias sobre 173 ficheros; autoprueba 4/4, con el árbol ya comiteado
verificar-bitacora.ps1    ->  0 hallazgos en las 5 comprobaciones; 96 documentos
pytest tests              ->  321 en verde (234 s), test_paridad.py intacto; 7 conexiones por el proxy
scripts/mutar.py          ->  97 de 97 mutaciones detectadas
```

`git show --numstat` no enseña ningún fichero existente reescrito entero por los finales de línea:
el que más líneas pierde es `src/melate/almacen.py`, 34, las que cambiaron. Y **los diez ficheros de
los dos snapshots están en el repositorio byte a byte**: el blob de cada uno es el mismo objeto que
`git hash-object --no-filters` sobre el fichero del disco (`data/raw/** -text`).

## Lo que ahora es público y antes no

- **El ciclo**, con la regla de los testigos y lo que hace ante cada fallo.
- **Dos snapshots nuevos** y su procedencia, con el `Last-Modified` del oficial: se regeneró a las
  12:00 UTC los dos días que se miró, el domingo y el lunes.
- **El primer veredicto con holdout**: *sin ventaja demostrada*, con 1 sorteo de los 1 778.
- **Que el laboratorio podía declarar ventaja con un sorteo hasta el 2026-10-04**, y que se cambió
  antes del sorteo del 4274. Es una debilidad del protocolo publicado, ya cerrada: lo honesto es que
  se vea.

Nada personal. El proyecto sigue sin secretos: ni credenciales, ni `.env`.

## Cómo verificar

```powershell
git log --oneline -6          # el registro de esta subida y, debajo, los cuatro commits de la fase
git status -sb                # ## main...origin/main  (sin divergencia)
git ls-files "*.duckdb"       # vacío: la base no está en el repositorio
git ls-tree HEAD data/raw/2026-10-04_4274/Melate.csv
git hash-object --no-filters data/raw/2026-10-04_4274/Melate.csv   # el mismo objeto
```

## Cómo revertir

```powershell
git revert 5674134 f7107a0 3e3915a 408f6f0
```

Revierte la fase entera, del último commit al primero. **No se recomienda revertir `f7107a0`**: son
datos publicados, y sin ellos el veredicto del 4274 dejaría de valer. Para quitar solo el código, basta
con `git revert 3e3915a`; los snapshots se quedan, y se pueden seguir verificando con su `SHA256.txt`.

Relacionado: `Despliegue/Añadir/2026-10-04_16-53_s4-push-de-la-app-local.md`,
`Fases/2026-10-04_ciclo-vivo/99_CIERRE.md`,
`Seguridad/Modificar/2026-10-05_10-07_s5-lo-que-entra-de-fuera-con-el-ciclo.md`.
