# Lo que entra de fuera con el ciclo, y por dónde podría colarse

- **Fecha/hora:** 2026-10-05 10:07
- **Área:** Seguridad · **Acción:** Modificar
- **Chat / página:** cierre de la Fase 5 · `Fases/2026-10-04_ciclo-vivo/`
- **Archivos afectados:** `src/melate/ciclo.py`, `app/streamlit_app.py`, `.gitignore`

## Qué cambia

`Seguridad/Modificar/2026-10-04_16-35_s4-un-servidor-local-y-su-superficie.md` describe la superficie
de la app; sigue igual, y con el veredicto del 4274 en pantalla la app no abrió ni una conexión hacia
fuera. **Lo nuevo es el ciclo**: una orden que sale a la red cada vez que se lanza y escribe en el
repositorio lo que le sirve un tercero. Lo que eso abre, y cómo se cierra:

| Por dónde | El riesgo | Cómo se cierra |
|---|---|---|
| Las URL | Que un dato de fuera elija a quién se llama | Tres sitios fijos: el oficial y el espejo por sus constantes, melate-e.com por `popularity.Descargador`, que valida juego y sorteo. Ninguna URL lleva un dato leído |
| Lo que dice un servidor y se publica | La cabecera `Last-Modified` acaba en `data/raw/<carpeta>/PROCEDENCIA.md`: una barra partiría la tabla y una etiqueta o una imagen entrarían en un Markdown público | `_de_fuera()` deja letras, cifras y la puntuación de una fecha, con un tope de 64 (B2). Los números de la procedencia son enteros ya leídos |
| Un nombre de fichero hecho con un dato | El id de un preregistro acaba en `reportes/<snapshot>_veredicto-<id>.json`: un `../` escribiría fuera | Un id que no sean letras, cifras, puntos, guiones o guiones bajos, o que lleve `..`, no se evalúa, y se dice (B6). El nombre de un snapshot es una fecha y un entero ya leídos |
| Dónde escribe | Que pise algo publicado | Solo en `data/raw/<nombre>/` —por una carpeta temporal que se renombra—, en las dos cachés de `data/cache/`, en `data/cuarentena/`, en `reportes/` y en la base. **Nunca escribe encima** de un snapshot ni de un reporte |
| Una descarga rara | Que un fichero ilegible o una página a medias pasen por buenos, o que el ciclo se caiga sin dejar rastro | Un CSV que no se deja leer es un hallazgo y su descarga queda en la cuarentena (B12); una página sin sus seis números es un testigo que falta (B13) |
| Las celdas de la app | `st.table` pasa cada celda por Markdown: un motivo con `![x](http://…)` haría que el navegador pidiera una imagen fuera | Las celdas pasan por `escapar()` (B8 de la review de C3) |

**Lo que no se publica**, en `.gitignore` y comprobado con `git check-ignore`: la carpeta a medio
escribir (`data/raw/.*`), la cuarentena, las páginas incompletas —como toda `data/cache/`— y los
`*.escribiendo`. El colador sigue buscando rutas y correos en todo lo que sí se publica, los
snapshots y reportes nuevos incluidos.

## Lo que queda abierto, a propósito

- **Sin tope de tamaño en la descarga del oficial**, igual que `ingest._descargar` desde la Fase 1. Es
  la fuente de carga y pesa ~200 KB; un tope arbitrario podría cortar un fichero bueno. Queda dicho.
- **El ciclo confía en el oficial** para lo que ningún testigo puede ver; eso lo cubren las
  comprobaciones que no dependen de nadie —el pasado byte a byte, `validar_era`, la BOLSA— y la regla
  7 del `CLAUDE.md` para lo demás.

## Cómo verificar

```powershell
.venv\Scripts\python.exe -m pytest tests\test_ciclo.py -k "servidor or fuera_de_reportes or ruta_de_la_maquina or no_se_deja_leer or seis_numeros" -q
git check-ignore -v data/raw/.x.construyendo data/cuarentena/x data/cache/melate-e-incompletas/x x.escribiendo
.\scripts\colador.ps1 -Autoprueba
```

## Cómo revertir

Ninguna de estas medidas se recomienda quitar: cada una tiene su test y su mutación en
`scripts/mutar.py`, y quitarla reintroduce lo que dice su fila.

Relacionado: `Seguridad/Modificar/2026-10-04_16-35_s4-un-servidor-local-y-su-superficie.md`,
`Seguridad/Añadir/2026-10-03_05-15_s3-trafico-saliente-a-un-tercero.md`,
`Conexiones/Modificar/2026-10-05_10-06_s5-el-ciclo-sale-a-tres-sitios.md`,
`Fases/2026-10-04_ciclo-vivo/Bugs/2026-10-04_20-51_s5-review-ciclo.md`.
