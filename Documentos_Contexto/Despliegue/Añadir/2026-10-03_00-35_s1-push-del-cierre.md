# Segunda subida: el cierre de la Fase 1, y la convención que evita el espejo infinito

- **Fecha/hora:** 2026-10-03 00:35
- **Área:** Despliegue · **Acción:** Añadir
- **Chat / página:** sesión de arranque · cierre de la Fase 1
- **Archivos afectados:** 16 ficheros de `Documentos_Contexto/` y `scripts/verificar-bitacora.ps1`

## Qué se hizo

```
3c2ed35..5e79986  main -> main
```

Un commit, `5e79986` — *docs: cierra la fase de arranque y emite a las áreas base*. Contenido:

- Los **diez documentos emitidos** a las áreas base: `Mapa`, `Estructura_Carpetas`,
  `Estructura_Datos`, `Almacenamiento`, `Conexiones`, `Reproducibilidad`,
  `Protocolo_Estadistico`, `Seguridad`, `Rendimiento` y `Despliegue`.
- El `99_CIERRE.md` de la fase y el `00_ALCANCE.md` marcado como cerrado.
- El `_MAPA.md` reescrito con las rutas de lectura reales.
- El bloque de cierre del `Bugs/` del refactor.
- `scripts/verificar-bitacora.ps1`, nuevo.

El árbol remoto queda en **56 blobs**.

### Estado comprobado justo antes de subir

| Control | Resultado |
|---|---|
| `pytest tests` | **52 en verde**, 93 s |
| `scripts/verificar-bitacora.ps1` | **19 documentos, 0 hallazgos** en las 5 comprobaciones, exit 0 |
| `scripts/colador.ps1 -Autoprueba` | **53 ficheros, 0 coincidencias**, exit 0, autoprueba 3/3 |
| Identidad de los commits | todos `users.noreply.github.com` |

## La convención: una subida de solo-documentación no genera su propio documento

Este documento registra la subida `5e79986`. Pero el documento que estás leyendo también hay que
subirlo, y esa subida tendría que registrarse en otro documento, que a su vez… El área `Despliegue`
se convertiría en un espejo infinito y dejaría de servir para lo único que sirve: saber qué hay
público y desde cuándo.

**La regla, a partir de aquí:** se escribe un documento de `Despliegue/` por cada subida que cambia
**el código, los datos o lo que el proyecto afirma**. Una subida que solo transporta documentos de la
bitácora de un cambio ya documentado se menciona dentro del documento de ese cambio, o en el cierre
de su fase, y no genera uno nuevo.

Por eso la subida de este fichero —que será la tercera de la noche— no tendrá documento propio. Para
reconstruirla basta `git log`, que es exactamente para lo que está.

## Por qué

El área `Despliegue` existe porque "qué se subió y cuándo" es lo que no se puede reconstruir después
con comodidad. Pero la rejilla sirve a un lector, no al revés: un área que se llena de registros de
registros ahoga el dato útil, que es justo el anti-patrón que el `REGLAS-DOCUMENTACION.md` llama
"volcar un bloque de trabajo entero en las áreas base".

## Impacto en seguridad / conexiones / datos

- **Seguridad:** el colador atrapó, en la ejecución previa a esta subida, una dirección de correo
  personal escrita literalmente en el documento del primer push — un documento sobre fugas de datos
  personales a punto de filtrar una. Corregido antes de subir, y convertido en la regla 6 de
  `Seguridad/Decisiones/2026-10-03_00-13_s1-bitacora-publica.md`.
- **Conexiones:** sin cambios.
- **Datos:** sin cambios. Esta subida no toca ni `data/` ni `src/`.

## Cómo verificar / revertir

```powershell
git fetch origin
git diff --stat origin/main        # sin salida
git log --oneline origin/main | Select-Object -First 3
```

**Revertir:** `git revert 5e79986` y volver a empujar. Se perderían los diez documentos emitidos y el
cierre de la fase, dejando el dossier abierto y las áreas base vacías. No hay razón para hacerlo.

Relacionado: `Despliegue/Añadir/2026-10-03_00-13_s1-primer-push.md`,
`Fases/2026-10-02_arranque/99_CIERRE.md`,
`Seguridad/Decisiones/2026-10-03_00-13_s1-bitacora-publica.md`
