# El árbol después del ciclo vivo

- **Fecha/hora:** 2026-10-05 10:29
- **Área:** Estructura_Carpetas · **Acción:** Modificar
- **Chat / página:** cierre de la Fase 5 · `Fases/2026-10-04_ciclo-vivo/`
- **Archivos afectados:** los de la tabla

## Qué aparece y qué cambia

Respecto a `Estructura_Carpetas/Modificar/2026-10-04_16-35_s4-arbol-tras-la-app.md`:

```
src/melate/
  ciclo.py                     NUEVO   python -m melate.ciclo: incorpora los sorteos nuevos (703 líneas)
  almacen.py                   CAMBIA  lee los SHA256.txt de data/raw/; esquema 2 (766 líneas)
  lab.py                       CAMBIA  publica holdout_necesario; detectable(), una sola vez; «1 sorteo» (B15)
  protocolo.py                 CAMBIA  la condición 5 exige un holdout capaz (C1); «1 sorteo»
app/
  streamlit_app.py             CAMBIA  el holdout como lo que es, y de qué snapshot sale cada cosa
tests/
  test_ciclo.py                NUEVO   50 pruebas, una lenta
  test_almacen.py              CAMBIA  41 pruebas (eran 31)
  test_app.py                  CAMBIA  30 pruebas (eran 26)
  test_protocolo.py            CAMBIA  61 pruebas (eran 46)
  conftest.py                  CAMBIA  el corpus de la Fase 4, fijo, y el veredicto de un sorteo
scripts/
  mutar.py                     CAMBIA  97 mutaciones (eran 46)
data/raw/
  2026-10-02/                  sin tocar: el de la Fase 1, hecho a mano
  2026-10-02_4273/             NUEVO   el primer snapshot del ciclo
  2026-10-04_4274/             NUEVO   el del primer sorteo del holdout
  .<nombre>.construyendo/      NO SE PUBLICA   un snapshot a medio escribir
data/cache/
  melate-e-incompletas/        NO SE PUBLICA   las páginas nuevas que llegan sin la tabla entera
data/cuarentena/               NO SE PUBLICA   la evidencia de cada hallazgo
reportes/
  2026-10-02_4273_*.json       NUEVOS  popularidad, informe y veredicto del snapshot del 4273
  2026-10-04_4274_*.json       NUEVOS  los mismos tres, del 4274
.gitignore                     CAMBIA  data/raw/.*, data/cuarentena/ y *.escribiendo
```

Y en la bitácora, el dossier `Documentos_Contexto/Fases/2026-10-04_ciclo-vivo/`, y los documentos que
emitió a las áreas base al cerrar.

## Los nombres, que ahora son contrato

- **Un snapshot del ciclo se llama `<fecha del último sorteo>_<su concurso>`**, con la fecha en
  `AAAA-MM-DD`. El ciclo lee el último concurso del nombre; el de `2026-10-02`, el único sin concurso,
  lo lee del fichero. Una carpeta que empieza por punto no es un snapshot.
- **Un reporte del ciclo se llama `<snapshot>_<qué>.json`**, y el veredicto lleva además el id del
  preregistro, que tiene que servir de nombre de fichero.

## Cómo verificar / revertir

```powershell
git status --short --ignored -- data/                       # !! data/cache/; la cuarentena, si hubo un hallazgo
.venv\Scripts\python.exe -m pytest tests --collect-only -q   # 321 pruebas
```

**Revertir** la fase entera es quitar lo marcado NUEVO salvo los snapshots y reportes —son datos
publicados—, deshacer lo marcado CAMBIA según su documento y quitar las tres líneas de la Fase 5 de
`.gitignore`.

Relacionado: `Estructura_Carpetas/Modificar/2026-10-04_16-35_s4-arbol-tras-la-app.md`,
`Mapa/Modificar/2026-10-05_10-04_s5-entra-el-ciclo-vivo.md`,
`Almacenamiento/Modificar/2026-10-05_10-05_s5-los-snapshots-los-congela-el-ciclo.md`.
