# Subida de la Fase 3: popularidad y cartera

- **Fecha/hora:** 2026-10-03 05-50
- **Área:** Despliegue · **Acción:** Añadir

## Qué se subió

- **Commit:** `e7d8c50` — *feat: popularidad y cartera, con el dictamen escrito antes del codigo*
- **Rama:** `main` → `673fcb5..e7d8c50`
- **Repositorio:** `pi2grands-boop/MELATE_LARGE_MODEL` (público)
- **Volumen:** 27 ficheros, 7.123 inserciones, 23 borrados

| Qué | Ficheros |
|---|---|
| Código | `src/melate/popularity.py`, `src/melate/portfolio.py`, `src/melate/informe.py` (modificado) |
| Tests | `tests/test_popularidad.py` (38), `tests/test_cartera.py` (26) |
| Bitácora | 10 documentos: el dossier de la fase y 6 emitidos a las áreas base |
| Contrato | `CLAUDE.md` (nota de EV + ventas corregidas), `README.md`, `_MAPA.md` |
| Entorno | `requirements.txt`, `entorno/pip-freeze-2026-10-03.txt` |
| Reportes | los tres de esta fase |

## Qué NO se subió, y es deliberado

**`data/cache/melate-e/`** — 400 páginas, 2,9 MB. Entrada nueva en `.gitignore` con su porqué
escrito al lado. Son páginas de un tercero y republicarlas no es nuestro papel; lo que el
repositorio publica son las cifras derivadas. Es reconstruible a 1 solicitud por segundo.

Es la primera carpeta de datos del proyecto que no se publica, al contrario de
`data/raw/<fecha>/`, que sí se publica porque es lo que hace que el hash del protocolo signifique
algo.

## Las dos puertas, antes de subir

```
colador.ps1 -Autoprueba   ->  0 coincidencias sobre 95 ficheros; autoprueba 3/3
verificar-bitacora.ps1    ->  0 hallazgos en las 5 comprobaciones; 48 documentos
pytest tests              ->  161 en verde, 131 s, test_paridad.py intacto
```

El colador pasó de revisar 83 ficheros a 95 y siguió en 0. Importaba comprobarlo en esta fase más
que en ninguna: es la primera que mete rutas de caché, un `User-Agent` y URLs de un tercero en el
código, y cualquiera de las tres era un sitio plausible donde colar una ruta absoluta.

## Lo que ahora es público y antes no

- El `User-Agent` con el que este proyecto se presenta ante `resultados.melate-e.com`, **a
  propósito**: está en el código y en el dictamen, y enlaza este repositorio para que el dueño del
  sitio pueda identificarnos y bloquearnos si quiere.
- El dictamen de términos completo, con los hechos comprobados y el límite que nos ponemos.
- Que el EV real de Revancha es −44,4 % y no −49,1 %.

Nada personal. El proyecto sigue sin secretos: las tres fuentes son HTTP GET público sin
autenticación, no hay `.env` ni credenciales.

## Cómo verificar

```powershell
git log --oneline -1          # e7d8c50
git status -sb                # ## main...origin/main  (sin divergencia)
git ls-files data/cache       # vacío: la caché no está en el repositorio
```

## Cómo revertir

```powershell
git revert e7d8c50
```

Revierte la fase entera. Deja la caché en disco (no está versionada) y no desinstala Scrapling;
para eso, ver `Seguridad/Añadir/2026-10-03_05-15_s3-trafico-saliente-a-un-tercero.md`.

Relacionado: `Despliegue/Añadir/2026-10-03_01-45_s2-push-del-laboratorio.md`,
`Fases/2026-10-03_popularidad/99_CIERRE.md`,
`Seguridad/Añadir/2026-10-03_05-15_s3-trafico-saliente-a-un-tercero.md`.
