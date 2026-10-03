# Tercera subida: el laboratorio y el preregistro

- **Fecha/hora:** 2026-10-03 01:45
- **Área:** Despliegue · **Acción:** Añadir
- **Chat / página:** sesión de arranque · cierre de la Fase 2
- **Archivos afectados:** `src/melate/{lab,protocolo,informe}.py`, `prereg/`, `tests/`, `README.md`,
  `Documentos_Contexto/` (12 documentos), `reportes/2026-10-03_veredicto.json`

## Qué se hizo

Dos commits, y esta vez sí cambian código y datos, así que llevan documento propio
(la convención está en `Despliegue/Añadir/2026-10-03_00-35_s1-push-del-cierre.md`).

```
c5ae4b2..ae5e79f   fix: el informe ya no muere por la codificacion de la consola
ae5e79f..639088b   feat: el laboratorio, con preregistro sellado y las 5 condiciones
```

El árbol remoto queda en **14 commits y 68 ficheros**.

| Novedad pública | Qué es |
|---|---|
| `src/melate/lab.py` | El laboratorio: sella, verifica, calcula el holdout y evalúa |
| `prereg/2026-10-03_logistica-revancha.json` | La primera hipótesis preregistrada, sellada |
| `tests/test_protocolo.py` | 41 pruebas |
| `reportes/2026-10-03_veredicto.json` | El veredicto de hoy: 0 de 5 condiciones |

## Verificación desde un clon limpio

Lo importante de esta subida no es que llegara, es que **el sello sobrevive al viaje.** Clonado
emulando un checkout de Linux (`core.autocrlf=false core.eol=lf`), con entorno nuevo desde
`requirements.txt`:

| Comprobación | Resultado |
|---|---|
| Finales de línea del preregistro tras el clon | **70 de 70 líneas con CR** |
| SHA-256 **del fichero** | `4858a015…` — distinto del que tiene en disco aquí |
| **El sello verifica** | ✅ `36edc964461c0152…`, `tamano_familia = 36` |
| Hashes del snapshot | ✅ `sha256sum -c SHA256.txt` → OK en los tres |
| Suite completa | ✅ **92 en verde** |
| El veredicto | ✅ `sin ventaja demostrada`, 0 de 5, holdout vacío |

Las dos primeras filas con la tercera son el punto: **los bytes del preregistro cambian al clonar y
el sello sigue valiendo.** Es exactamente lo que se diseñó — el hash cubre el JSON canónico del
contenido parseado, no los bytes del fichero — pero era de las cosas que había que comprobar y no
suponer, porque el fallo habría sido indistinguible de una manipulación.

Y es la contrapartida de lo que la Fase 1 tuvo que arreglar con `.gitattributes`: los CSV **sí**
necesitan protección byte a byte, porque su hash es de bytes; el preregistro no, porque el suyo es
de contenido. Dos ficheros versionados con dos clases de integridad distintas, y cada uno con el
mecanismo que le corresponde.

## Por qué

El área registra qué quedó público y cuándo. Esta subida añade al dominio público el mecanismo que
impide que el proyecto afirme algo sin haberlo preregistrado, y el propio preregistro: un documento
que a partir de ahora cualquiera puede verificar que no se ha tocado.

Que el preregistro sea público importa. Uno que solo existiera en la máquina de quien lo escribió no
preregistraría gran cosa.

## Impacto en seguridad / conexiones / datos

- **Seguridad:** colador limpio sobre 69 ficheros, autoprueba 3/3. Los dos commits firmados con
  `users.noreply.github.com`. El preregistro no contiene nada sensible: es metodología.
- **Conexiones:** ninguna nueva. `lab.py` solo llega a la red si se le llama sin `--datos`, y
  entonces pasa por `ingest.cargar`.
- **Datos:** `prereg/` (4 KB) y un reporte de veredicto nuevo. El snapshot no se tocó.

## Cómo verificar / revertir

```powershell
git fetch origin; git diff --stat origin/main      # sin salida
git log --format='%h %ae %s' origin/main | Select-Object -First 3
```

Y la verificación que de verdad cuenta, desde un clon:

```
git -c core.autocrlf=false -c core.eol=lf clone <url> /tmp/clon && cd /tmp/clon
( cd data/raw/2026-10-02 && sha256sum -c SHA256.txt )
python -m venv .venv && .venv/Scripts/python -m pip install -q -r requirements.txt -e .
.venv/Scripts/python -c "from melate import lab; print(lab.cargar_preregistro('prereg/2026-10-03_logistica-revancha.json')['id'])"
.venv/Scripts/python -m pytest tests -q
```

**Revertir:** `git revert 639088b ae5e79f` y empujar. Se perdería el laboratorio y el arreglo de
codificación — con lo segundo, la suite volvería a pasar o fallar según el shell.

**Pendiente de verificar en vivo:** los cinco puntos de
`Fases/2026-10-03_protocolo/99_CIERRE.md`. Siguen sin resolver la descripción del repositorio y el
ajuste de correo privado en GitHub, los dos de la cuenta del usuario.

Relacionado: `Despliegue/Añadir/2026-10-03_00-35_s1-push-del-cierre.md`,
`Fases/2026-10-03_protocolo/99_CIERRE.md`,
`Almacenamiento/Añadir/2026-10-03_01-30_s2-prereg-sellado.md`
