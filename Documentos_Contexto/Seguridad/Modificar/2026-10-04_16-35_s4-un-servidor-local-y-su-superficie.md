# Un servidor local, y lo que eso cambia en la superficie

- **Fecha/hora:** 2026-10-04 16:35
- **Área:** Seguridad · **Acción:** Modificar
- **Chat / página:** cierre de la Fase 4 · `Fases/2026-10-04_app-local/`
- **Archivos afectados:** `src/melate/app.py`, `app/streamlit_app.py`, `.streamlit/config.toml`,
  `src/melate/almacen.py`, `.gitignore`, `scripts/colador.ps1`, `requirements.txt`,
  `tests/test_popularidad.py`

## Qué cambia

`Seguridad/Añadir/2026-10-03_05-15_s3-trafico-saliente-a-un-tercero.md` decía, al cerrar la Fase 3:
«seguimos sin servir nada, sin credenciales y sin `.env`». **Lo primero deja de ser verdad**: la Fase
4 levanta un servidor. Lo demás sigue igual: ni credenciales, ni `.env`, ni secretos.

## La superficie nueva, y cómo se cierra

**Un servidor, solo para esta máquina.** Streamlit en `127.0.0.1:8501`, con la red forzada por el
lanzador, dicha en `.streamlit/config.toml` y vigilada por una guarda dentro de la app. Qué se sirve,
a quién, y la comprobación en vivo en un entorno hostil: `Red/Añadir/2026-10-04_16-35_s4-que-sirve-la-app-y-a-quien.md`.

**Nada sale de la máquina por la app.** La telemetría de Streamlit, encendida por defecto, está
apagada; la búsqueda de la IP pública ante una conexión de otro origen, que no es configurable, la
anula el lanzador sustituyendo `streamlit.net_util.get_external_ip` en su propio proceso. Con el
proxy chivato puesto: 0 peticiones.

**Lo que viene de un fichero no se interpreta.** Todo texto de `reportes/` o `prereg/` pasa por
`escapar()` antes de llegar a Markdown —un `![x](url)` sería una imagen que el navegador iría a
buscar fuera, y un `$` abriría una fórmula—, o por `codigo()` dentro de comillas invertidas. Nunca
`unsafe_allow_html` ni HTML crudo (`grep`, vacío). **Test:** un veredicto válido con una fecha que es
una imagen en Markdown llega a la cabecera escapado.

**La app no escribe, no recalcula y no sale a la red**, con un test cada cosa: lee su propio código
buscando escrituras, abre la base en solo lectura (un espía sobre `duckdb.connect`), solo importa lo
que lee (su árbol sintáctico), y recorre las cinco pantallas con el cómputo y los sockets fuera de
esta máquina convertidos en excepciones.

**Lo que no se publica, blindado.** `melate.duckdb` está en `.gitignore`, no guarda ninguna ruta
absoluta (test), y el colador busca además en el índice de git cualquier `*.duckdb` metida a la
fuerza, porque es un binario que no sabe leer (autoprueba 4/4). Los `secrets.toml` que lee
Streamlit —el de la carpeta de arranque y el de `app/`— quedan excluidos a cualquier profundidad,
con test y mutación. El proyecto no tiene secretos: eso es para que uno creado por accidente no se
publique.

## Las dependencias

**23 paquetes nuevos** (de 43 a 66, más la instalación editable; `entorno/pip-freeze-2026-10-04.txt`),
todos con *wheel*. `streamlit==1.65.0` y `duckdb==1.5.6` van fijadas exactas, y ninguna versión que
reproduce la línea base se movió: pandas sigue en 2.3.3. **Actualizar Streamlit obliga a revisar su
red**: el lanzador sustituye una función interna suya, y su dirección de escucha, su telemetría y su
comprobación de origen se revisaron leyendo el código de esta versión. Lo dice `requirements.txt`, y
un test falla a la vista si una versión nueva renombra la función o la importa de otra forma.

## Hacia un tercero: una petición más, decidida por el usuario

El test que vigila la tabla de melate-e.com pide ahora la página de verdad: **una petición por cada
pasada de la suite completa**, con el mismo `User-Agent` que nos identifica y nos hace bloqueables.
Es una excepción a la caché permanente del dictamen, limitada a ese test y decidida por el usuario
(`Conexiones/Modificar/2026-10-04_16-35_s4-el-test-del-sitio-pide-la-pagina-de-verdad.md`).

## Lo que queda abierto, a propósito

Cuatro configuraciones que el lanzador no fuerza —`corsAllowedOrigins`, un tema remoto, el modo de
desarrollo y la IP de la red local como origen aceptado—, todas porque exigen que alguien escriba a
propósito una configuración. El porqué de cada una está en `Red/Añadir/`.

**La regla 0 invertida no cambia** (`Seguridad/Decisiones/2026-10-03_00-13_s1-bitacora-publica.md`):
la bitácora se sigue publicando, sin nada personal, y su premisa de que la app es local se mantiene.

## Cómo verificar / revertir

```powershell
.\scripts\colador.ps1 -Autoprueba                          # autoprueba 4/4, 0 coincidencias
.venv\Scripts\python.exe -m pytest tests\test_app.py tests\test_lanzador.py tests\test_almacen.py -q
.venv\Scripts\python.exe scripts\mutar.py --solo F4       # las protecciones de la Fase 4, rotas una a una
```

**Revertir:** ninguna de estas medidas se recomienda quitar; cada una tiene su test y su mutación, y
quitarla reintroduce lo que dice su párrafo. Quitar el lanzador entero está descrito en
`Fases/2026-10-04_app-local/Cambios/2026-10-04_16-08_s4-lanzador-propio.md`.

Relacionado: `Seguridad/Añadir/2026-10-03_05-15_s3-trafico-saliente-a-un-tercero.md`,
`Seguridad/Decisiones/2026-10-03_00-13_s1-bitacora-publica.md`,
`Red/Añadir/2026-10-04_16-35_s4-que-sirve-la-app-y-a-quien.md`,
`Fases/2026-10-04_app-local/Bugs/2026-10-04_10-05_s4-review-base-app-y-red.md`,
`Fases/2026-10-04_app-local/Bugs/2026-10-04_11-39_s4-review-lanzador.md`.
