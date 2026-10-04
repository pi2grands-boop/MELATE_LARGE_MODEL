# Dictamen: en qué condiciones este proyecto pide páginas a resultados.melate-e.com

- **Fecha/hora:** 2026-10-03 02-40
- **Área:** Fases/2026-10-03_popularidad · **Acción:** Decisiones
- **Estado:** cerrada
- **Escrito ANTES** de que exista código que dependa de él. Ese es el punto.

## Por qué este documento va primero

Es la primera vez que este proyecto le pide algo a un servidor que no es una fuente oficial de datos
abiertos. Hasta hoy todo el tráfico saliente iba a `loterianacional.gob.mx` (CSV públicos, una
descarga por juego) y a `raw.githubusercontent.com` (validación cruzada). Ahora vamos a pedir
**páginas HTML, una por sorteo**, a un sitio pequeño y privado.

La diferencia entre una herramienta personal y un raspador no está en la tecnología —es el mismo GET—
sino en **el límite que se pone antes de empezar**. Un límite decidido después de ver cuánto tarda la
descarga no es un límite: es una excusa. Por eso este documento se escribe antes, y por eso fija
números, no intenciones.

## Hechos comprobados (no supuestos)

Todo lo de abajo lo comprobé el **2026-10-03 entre las 02:10 y las 02:35** hora local (UTC-5), con
`curl` y con Scrapling. Son hechos verificables, no lectura de la documentación de nadie.

### 1 · No hay `robots.txt`, ni en un dominio ni en el otro

| URL | Respuesta |
|---|---|
| `resultados.melate-e.com/robots.txt` | **HTTP 404** |
| `resultados.melate-e.com/sitemap.xml` | **HTTP 404** |
| `www.melate-e.com/robots.txt` | **HTTP 404** |

Ningún parser de robots encontrará reglas en ninguno de los dos. Esto **no es permiso**: es ausencia
de instrucciones. La lectura correcta de un 404 en `robots.txt` es "el sitio no ha dicho nada", no
"el sitio ha dicho que sí". **El límite lo ponemos nosotros**, y es el de la sección siguiente.

Nota operativa: Scrapling arrastra `protego` (un parser de robots) como dependencia. Dado el 404, no
encontrará reglas que aplicar. No delegamos el criterio en esa librería.

### 2 · No hay términos de uso, ni aviso legal, ni nota de copyright

`grep -i -E "aviso|legal|termino|privacidad|copyright|derechos"` sobre la portada de
`resultados.melate-e.com` y sobre tres páginas de resultado (Melate, Revancha y Revanchita del sorteo
4272): **0 coincidencias**. La portada del sitio comercial `www.melate-e.com` tiene siete enlaces
(`detalles.php`, `donde_comprar.php`, `preguntas_frecuentes.php`, `zona_clientes.php`, el blog y una
tienda de MercadoLibre) y **ninguno es un aviso legal**.

Otra vez: ausencia de términos no es consentimiento. Es un sitio pequeño que no se ha planteado la
pregunta. La respuesta decente ante eso es comportarse como el visitante más barato que puedan tener.

### 3 · Es un sitio pequeño y comercial, monetizado con publicidad

`nginx` + `PHP/7.3.33` (cabecera `X-Powered-By`), con Google AdSense (`ca-pub-4318537970390227`),
Google Analytics (`UA-30005195-2`) y StatCounter (`sc_project=11970187`). Vende software de lotería
por MercadoLibre y tiene zona de clientes.

Esto **sube el listón, no lo baja**: cada petición nuestra le cuesta ancho de banda y no le genera
ingreso publicitario, porque no ejecutamos su JavaScript ni vemos sus anuncios. No es un servicio
público financiado con impuestos como `loterianacional.gob.mx`. Es el servidor de alguien.

### 4 · Las páginas son HTML estático: no hace falta navegador

Respuesta de 7.924 bytes para el sorteo 4272 de Melate, `Content-Type: text/html; charset=UTF-8`,
`Cache-Control: max-age=60, public`. La tabla de ganadores viene **en el HTML servido**, en un
`<table>` plano. Comprobado: un `GET` sin JavaScript devuelve las 10 filas (cabecera + 9 categorías).

Consecuencia directa y la razón por la que la prohibición del `CLAUDE.md` es fácil de cumplir:
**`StealthyFetcher` y `DynamicFetcher` no están prohibidos solo por política — es que no sirven para
nada aquí.** Levantar un navegador headless para leer 8 KB de HTML estático sería gastar los recursos
del sitio y los nuestros a cambio de cero información adicional.

### 5 · El sitio es, estructuralmente, una capa de conveniencia sobre una fuente oficial

Cada página de resultado enlaza la **mascarilla oficial** de Pronósticos:

```
https://www.pronosticos.gob.mx/Documentos/juegos/Concursosysorteos/Mascarillas/RESULTADOS 2026-09-30.pdf
```

Esa URL **redirige (301) a `www.loterianacional.gob.mx`**, que es exactamente el dominio del que este
proyecto ya carga los CSV. Es decir: la fuente primaria de las tablas de ganadores es oficial, y el
proyecto ya habla con ese host.

**Entonces, ¿por qué no ir al PDF oficial y saltarse al tercero?** Porque lo intenté y no funciona:

| Comprobación | Resultado |
|---|---|
| `www.pronosticos.gob.mx` con verificación TLS normal | **Falla**: `SEC_E_WRONG_PRINCIPAL`, el certificado no cubre ese nombre |
| Sin `www`, siguiendo la redirección, TLS verificado | **200**, `application/pdf`, 882.608 bytes, 1 página |
| Texto extraíble del PDF | 25.885 caracteres: están las **etiquetas** (`LUGAR`, `ACIERTOS`, `GANADORES`, `PREMIO INDIVIDUAL`, los nombres de categoría) |
| Dígitos en ese texto | **1 dígito en 25.885 caracteres.** Las cifras no están en la capa de texto |

El PDF es una mascarilla gráfica: los números de ganadores y los importes están dibujados, no
escritos. Sacarlos exigiría OCR, que es una fuente de error nueva y silenciosa — exactamente la clase
de cosa que ya mordió a este proyecto una vez.

**Conclusión:** el tercero no se usa por comodidad, se usa porque la fuente oficial de este dato
concreto no es legible por máquina. Eso es un motivo legítimo, y queda escrito para que nadie tenga
que redescubrirlo. Si algún día Lotería Nacional publica las tablas en CSV, esta decisión se reabre.

### 6 · Revanchita no tiene tabla, y eso es correcto

La página de Revanchita del sorteo 4272 **no contiene ningún `<table>`**. Es coherente con el
`CLAUDE.md`: *"Revanchita solo paga 6 aciertos"*. No hay categorías menores que listar.

Consecuencia: el `menores_brutos` de Revanchita es **exactamente 0 por estructura del juego**, no por
estimación. El `0.0` escrito a mano en `baseline_auditoria.py:252` era correcto, y ahora se sabe por
qué. Y pedirle páginas de Revanchita al sitio sería gastar peticiones ajenas para no obtener nada:
**no se piden.**

## El límite que nos ponemos

Esto es el dictamen propiamente dicho. Es vinculante y es comprobable.

| Regla | Valor | Cómo se comprueba |
|---|---|---|
| **Ritmo** | **1 solicitud por segundo**, medida entre el inicio de una y el inicio de la siguiente | Test que mide el reloj con un servidor local |
| **Caché** | En disco, permanente. Una página descargada **no se vuelve a pedir nunca** | Test: dos llamadas seguidas, una sola petición |
| **Identificación** | `User-Agent` honesto, con el nombre del proyecto y la URL del repositorio | Test sobre las cabeceras enviadas |
| **Sin evasión** | `impersonate=None`, `stealthy_headers=False` | Test: la única cabecera que sale es la nuestra |
| **Sin navegador** | Solo `Fetcher`/`FetcherSession`. `StealthyFetcher` y `DynamicFetcher`, prohibidos | Test: no se importan |
| **Revanchita** | No se pide | Test |
| **Ventana** | Acotada y declarada en cada corrida. **El histórico completo no se descarga sin decisión explícita del usuario** | Parámetro obligatorio, sin defecto "todo" |
| **Si bloquean** | **Se para y se pregunta al usuario.** No se escala, no se reintenta con otra identidad | Instrucción del usuario, literal |

### Sobre el `User-Agent`

El resto del proyecto usa `"Mozilla/5.0 (proyecto personal de análisis)"`
(`src/melate/ingest.py:23`). Para las fuentes oficiales lo dejo como está: cambiarlo alteraría el
camino de red que produjo las cifras publicadas, y eso toca la reproducibilidad.

Para este tercero uso uno **distinto y honesto**, sin el `Mozilla/5.0` de adorno:

```
MaquinaMelate/0.1 (analisis personal; github.com/pi2grands-boop/MELATE_LARGE_MODEL)
```

Si al dueño del sitio le molesta nuestro tráfico, con ese `User-Agent` puede ver quiénes somos en sus
logs y bloquearnos de una línea. Esa posibilidad es deliberada: **quien no quiere ser bloqueable está
admitiendo que no debería estar ahí.**

### Sobre el coste del histórico completo, con números

| Juego | Sorteos de la era 6/56 | Páginas |
|---|---|---|
| Melate | 2.184 | 2.184 |
| Revancha | 2.184 | 2.184 |
| Revanchita | 1.902 | **0** (no tiene tabla) |
| **Total** | | **4.368** |

A 1 solicitud por segundo son **1 hora y 13 minutos** de tráfico continuo contra el servidor de otra
persona, y unos 33 MB. **No se hace en esta fase.** Si algún día hace falta, es una decisión del
usuario, va con su documento, y se hace una sola vez porque la caché es permanente.

## Qué NO hacemos, y por qué está escrito

Lista explícita, porque "no lo hicimos" se demuestra mal y "dijimos que no lo haríamos" se demuestra
bien:

- **No se evade nada.** Ni rotación de IP, ni proxies, ni suplantación de navegador, ni reintentos
  con otra identidad tras un bloqueo.
- **No se descarga en paralelo.** Un hilo, una petición cada segundo.
- **No se piden recursos que no necesitamos**: ni imágenes de volantes, ni CSS, ni los scripts de
  anuncios. Solo el HTML.
- **No se republica el contenido del sitio.** La caché es local y está en `.gitignore`. Lo que el
  repositorio publica son **cifras derivadas** (ventas estimadas, valor esperado), no sus páginas.
- **No se le hace competencia.** Este proyecto no sirve nada por red (`Red/` está vacía por eso) y no
  tiene usuarios.

## La dependencia que esto arrastra, y que no me gusta

`pip install "scrapling[fetchers]==0.4.15"` instala **20 paquetes**, entre ellos
**`playwright 1.63.0` y `patchright 1.63.0`** —dos pilas completas de automatización de navegador—
más `browserforge` y `apify-fingerprint-datapoints`, que existen para **falsificar huellas de
navegador**.

Nada de eso se usa aquí. Están porque el extra `[fetchers]` incluye `StealthyFetcher` y
`DynamicFetcher`, que este proyecto prohíbe. Es decir: **para poder hacer un GET honesto hay que
instalar la maquinaria de la evasión y dejarla sin usar.**

Lo dejo registrado como lo que es, un defecto de la elección de librería, no un accidente:

- Los *navegadores* no se descargan (eso exigiría `playwright install`, que **no se ejecuta**). El
  coste es de disco y de superficie de dependencias, no de ejecución.
- La alternativa —`requests`, que el proyecto ya tiene, más el parser de Scrapling sin el extra— haría
  el mismo trabajo con cero dependencias nuevas de navegador.
- **Se usa `scrapling[fetchers]` porque el usuario lo pidió explícitamente.** Queda anotado para que
  la decisión se pueda revisar con el dato delante, no para discutirla aquí.

## Cómo verificar este dictamen

Cada regla de la tabla de arriba tiene su test en `tests/test_popularidad.py`, y esa es la
diferencia entre un dictamen y una buena intención:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_popularidad.py -q
```

| Qué comprueba | Test |
|---|---|
| La caché evita la segunda petición | `test_la_cache_evita_la_segunda_peticion` |
| La caché sobrevive a un proceso nuevo | `test_la_cache_sobrevive_a_un_descargador_nuevo` |
| El ritmo se respeta, medido con reloj | `test_se_respeta_una_solicitud_por_segundo` |
| El ritmo por defecto es 1,0 s | `test_el_ritmo_por_defecto_es_el_del_dictamen` |
| Revanchita no se pide nunca | `test_revanchita_no_se_pide_nunca` |
| El `User-Agent` nos identifica y no finge | `test_el_user_agent_se_identifica_y_no_finge_ser_un_navegador` |
| No se importa nada de navegador | `test_no_se_importa_nada_de_navegador` |
| Un bloqueo para la descarga | `test_un_bloqueo_para_la_descarga` |
| Un 200 sin tabla también para | `test_un_200_sin_tabla_tambien_es_sospechoso` |

Y el comportamiento real contra el servidor, medido en la cosecha de esta fase: **400 páginas, 398
peticiones de red, 399 segundos** — 1,00 solicitudes por segundo exactas, y las 2 de diferencia son
las que ya estaban en caché de las pruebas previas.

## Cómo revertir

Borrar `src/melate/popularity.py`, su entrada en `requirements.txt` y la carpeta de caché; después
`.venv\Scripts\python.exe -m pip uninstall scrapling playwright patchright browserforge
apify-fingerprint-datapoints curl_cffi msgspec protego tld w3lib orjson cssselect`. Nada del resto del
proyecto depende de este módulo: el oráculo no lo conoce y el defecto de `ev.valor_esperado` no
cambia.

## Pendiente de verificar

1. **Que el sitio siga respondiendo igual dentro de meses.** El parser depende de la forma de su
   `<table>`. Si cambia, hay que verlo fallar ruidosamente, no en silencio.
2. **Que 1 solicitud/segundo le parezca bien al dueño del sitio.** No hay forma de preguntárselo: no
   publica contacto en el sitio de resultados. El límite es el nuestro, no uno acordado.
3. **Un bloqueo real.** No ha ocurrido. Si ocurre: parar y preguntar al usuario, nunca escalar.

Relacionado: `Fases/2026-10-03_popularidad/00_ALCANCE.md`,
`Conexiones/Añadir/2026-10-03_00-13_s1-fuentes-de-datos.md`,
`Seguridad/Decisiones/2026-10-03_00-13_s1-bitacora-publica.md`.
