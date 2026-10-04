# Primera vez que el proyecto hace tráfico saliente a un sitio privado

- **Fecha/hora:** 2026-10-03 05-15
- **Área:** Seguridad · **Acción:** Añadir

## Qué cambia en la superficie

Hasta ahora todo el tráfico saliente iba a dos sitios públicos, una vez por juego:
`loterianacional.gob.mx` (carga) y `raw.githubusercontent.com` (validación cruzada). La Fase 3
añade **peticiones repetidas a un servidor privado y pequeño**, una por sorteo.

Lo que cambia no es la superficie de ataque *contra nosotros* —seguimos sin servir nada, sin
credenciales y sin `.env`— sino **la superficie que nosotros presentamos a otro**. Es una
dirección que el proyecto no había tenido que pensar.

## La postura, y por qué es lo contrario de lo que trae la librería

Scrapling viene configurado **para esconderse**. `FetcherSession` por defecto hace
`impersonate='chrome'` (suplanta el saludo TLS de Chrome con `curl_cffi`) y
`stealthy_headers=True` (añade cabeceras de navegador). Para un proyecto cuya bitácora se publica,
esa es exactamente la postura equivocada.

Se apaga todo:

```python
FetcherSession(impersonate=None, stealthy_headers=False,
               headers={"User-Agent": UA}, timeout=30, retries=0)
```

**Comprobado**: con esa configuración la única cabecera que sale es nuestro `User-Agent`, que dice
quiénes somos y enlaza el repositorio. Si al dueño del sitio le molesta este tráfico, puede vernos
en sus logs y bloquearnos de una línea.

> **Quien no quiere ser bloqueable está admitiendo que no debería estar ahí.**

`retries=0` también es seguridad, aunque no lo parezca: tres reintentos automáticos convierten un
ritmo de 1/s en uno de 3/s **contra un servidor que ya está teniendo problemas**.

## Los dos fallos que encontró la review de seguridad

Ninguno era explotable hoy. Los dos se arreglaron porque costaban dos líneas y porque `html()` es
un método público que mañana puede llamarse desde otro sitio.

### Escritura fuera de la caché

`self.cache / juego.lower() / f"{sorteo}.html"` interpolaba `sorteo` sin validar. Un `../` habría
escrito fuera. Hoy `sorteo` sale de un `range()` y `juego` de una lista cerrada. Ahora se validan
los dos antes de construir la ruta — que además es la misma pareja que se interpola en la **URL**,
así que la validación cierra las dos puertas a la vez.
**Test:** `test_no_se_puede_escribir_fuera_de_la_cache`.

### Respuesta sin tope de tamaño

Se escribía en disco lo que viniera. `MAXIMO_BYTES = 1_000_000`, contra páginas reales de 5-8 KB.
No está para ajustar: está para que algo claramente distinto no entre en la caché como bueno.
**Test:** `test_una_respuesta_enorme_no_entra_en_la_cache`.

## Contenido de terceros en el disco

Las páginas cacheadas traen etiquetas `<script>` de Google Analytics, AdSense y StatCounter. **No
se ejecuta ninguna**: el HTML solo se parsea con lxml, nunca se abre en un navegador y nunca se
sirve. La caché está en `.gitignore`, así que tampoco se republica contenido ajeno.

## Qué se publica y qué no

| | ¿Se publica? |
|---|---|
| Las páginas descargadas | **No.** `data/cache/` en `.gitignore`. Son de un tercero y republicarlas no es nuestro papel |
| Las cifras derivadas (ventas, menores, cociente) | Sí. Son nuestras |
| El `User-Agent` | Sí, y a propósito: está en el código y en el dictamen |
| Credenciales | No hay. La fuente es HTTP GET público sin autenticación |

Esto no cambia la regla 0 invertida de `REGLAS-DOCUMENTACION.md`: la bitácora se sigue publicando
y sigue sin salir nada personal. `colador.ps1 -Autoprueba` da **0 coincidencias** sobre 83 ficheros.

## La dependencia, que es el punto más débil

`scrapling[fetchers]==0.4.15` instala **21 paquetes nuevos**, entre ellos `playwright`,
`patchright`, `browserforge` y `apify-fingerprint-datapoints`. Los dos primeros son pilas completas
de automatización de navegador; los dos últimos existen para **falsificar huellas de navegador**.

Nada de eso se usa, y `StealthyFetcher`/`DynamicFetcher` están prohibidos por el `CLAUDE.md` y
cubiertos por un test que lee el propio fichero. Los navegadores no llegan a descargarse: haría
falta `playwright install`, que no se ejecuta.

Aun así, el entorno pasó de **24 a 45 paquetes** para poder hacer un GET sobre HTML estático. Es un
coste de la librería elegida y queda anotado como tal, no como accidente. La alternativa
—`requests`, que ya estaba, más el parser de Scrapling sin el extra— haría lo mismo sin esas
dependencias. Se usa `[fetchers]` porque el usuario lo pidió explícitamente.

## Cómo verificar

```powershell
.venv\Scripts\python.exe -m pytest tests/test_popularidad.py -q
.\scripts\colador.ps1 -Autoprueba
```

## Cómo revertir

Ver `Conexiones/Añadir/2026-10-03_05-15_s3-tablas-de-ganadores-melate-e.md`. Desinstalar además
las 21 dependencias con `pip uninstall`.

## Pendiente de verificar

**Un bloqueo real.** No ha ocurrido: el camino de `SitioBloqueado` está probado con una sesión
falsa, no contra el servidor. Si ocurre, la instrucción es parar y preguntar al usuario — nunca
reintentar con otra identidad ni escalar a un navegador.

Relacionado: `Seguridad/Decisiones/2026-10-03_00-13_s1-bitacora-publica.md`,
`Fases/2026-10-03_popularidad/Decisiones/2026-10-03_02-40_s3-dictamen-terminos-melate-e.md`,
`Conexiones/Añadir/2026-10-03_05-15_s3-tablas-de-ganadores-melate-e.md`.
