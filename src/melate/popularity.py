"""Qué combinaciones juega la gente, estimado de las tablas de ganadores por categoría.

Este módulo existe para sustituir una constante que caduca. `baseline_auditoria.py:252` lleva
escrito a mano `{"Melate": 4.38, "Revancha": 2.10, "Revanchita": 0.0}`: el premio bruto esperado
por las categorías menores, sacado de las tablas de los sorteos 4271 y 4272. Es correcto para esos
dos sorteos y deja de serlo con cada sorteo nuevo.

**Lo que este módulo NO es.** No predice la urna. La popularidad dice qué juega *la gente*, no qué
va a salir, y las dos cosas son independientes: el sorteo no sabe qué apostó nadie. Por eso nada de
aquí entra en la familia de Benjamini-Hochberg del protocolo — no hay ninguna hipótesis sobre el
sorteo que corregir. El porqué está en `Documentos_Contexto/Protocolo_Estadistico/`.

**Para qué sirve entonces.** Para dos cosas, las dos sobre el dinero y ninguna sobre los números:

1. El valor esperado real de un boleto, con las categorías menores medidas en vez de supuestas.
2. Con cuánta gente compartirías la bolsa si acertaras, que es lo que `portfolio.py` usa. La bolsa
   es a repartir: elegir una combinación impopular no sube la probabilidad de ganar —nada la sube—
   pero sí sube cuánto te tocaría si ganaras.

**El trato con el sitio del que se descarga** está en
`Documentos_Contexto/Fases/2026-10-03_popularidad/Decisiones/2026-10-03_02-40_s3-dictamen-terminos-melate-e.md`,
escrito antes que este fichero. En corto: 1 solicitud por segundo, caché permanente en disco,
`User-Agent` honesto, sin suplantación de navegador, y Revanchita no se pide porque no tiene tabla.
Si el sitio bloquea, se para y se pregunta. No se escala.
"""
import argparse
import datetime
import json
import pathlib
import re
import statistics
import time
from math import comb

from .constantes import C, JUEGOS, K, N

# ---------------------------------------------------------------- el trato con el sitio
#
# Estas constantes SON el dictamen, en código. Cambiar cualquiera es cambiar el trato, y eso
# necesita su documento en Documentos_Contexto/.

URL = "https://resultados.melate-e.com/{juego}/sorteo/{sorteo}"

# Honesto a propósito, sin el "Mozilla/5.0" de adorno que lleva ingest.py para las fuentes
# oficiales. Si al dueño del sitio le molesta este tráfico, con esto puede vernos en sus logs y
# bloquearnos de una línea. Quien no quiere ser bloqueable está admitiendo que no debería estar ahí.
UA = "MaquinaMelate/0.1 (analisis personal; github.com/pi2grands-boop/MELATE_LARGE_MODEL)"

PAUSA_SEGUNDOS = 1.0
CACHE = pathlib.Path("data/cache/melate-e")

# Las páginas reales pesan entre 5 y 8 KB. El tope es holgado a propósito: no está para ajustar,
# está para que algo claramente distinto no entre en la caché como si fuera bueno.
MAXIMO_BYTES = 1_000_000

# Revanchita solo paga 6 aciertos (CLAUDE.md, Constantes), así que su página no trae `<table>`:
# comprobado sobre el sorteo 4272. Pedirla sería gastar peticiones ajenas para no obtener nada.
SIN_TABLA = ("Revanchita",)


class SitioBloqueado(RuntimeError):
    """El sitio dejó de responder como se espera.

    Es su propia excepción y no un `OSError` cualquiera porque la instrucción del usuario para este
    caso es concreta: **parar y preguntar**, nunca reintentar con otra identidad ni escalar a un
    navegador. Que el tipo de la excepción lo diga evita que alguien la capture por accidente dentro
    de un `except Exception` y siga descargando.
    """


class SorteoNoPublicado(LookupError):
    """Ese sorteo no está en el sitio (404). No es un bloqueo: es una página que no existe.

    Tiene su propio tipo porque confundirlo con `SitioBloqueado` es peligroso en la dirección mala:
    pedir un sorteo futuro es normal y no debe parar nada, pero si ese caso se trata como bloqueo,
    quien lo capture acabará capturando también los bloqueos de verdad. La primera versión de este
    módulo los mezclaba y el guion de cosecha tuvo que mirar si la cadena contenía "404", que es
    exactamente la clase de apaño que esconde un fallo real.
    """


# ---------------------------------------------------------------- combinatoria de las categorías
#
# Las fórmulas son las del CLAUDE.md, sección Constantes:
#   Melate:   C(6,k) * C(1,a) * C(49, 6-k-a)   con a = 1 si la categoría incluye el adicional
#   Revancha: C(6,k) * C(50, 6-k)
#   Revanchita: solo paga 6 aciertos
#
# El 49 de Melate no es arbitrario: 56 esferas - 6 naturales - 1 adicional. Y el 50 de Revancha es
# 56 - 6, porque Revancha no tiene adicional.


def favorables(juego, aciertos, con_adicional=False):
    """Combinaciones de 6 números que caen en esa categoría. Devuelve 0 si la categoría no existe."""
    if juego == "Revanchita":
        return 1 if (aciertos == K and not con_adicional) else 0
    if not 0 <= aciertos <= K:
        return 0
    if juego == "Revancha":
        return 0 if con_adicional else comb(K, aciertos) * comb(N - K, K - aciertos)
    if juego != "Melate":
        raise ValueError(f"juego desconocido: {juego}")
    a = 1 if con_adicional else 0
    restantes = K - aciertos - a          # números del boleto que no son premiados ni el adicional
    if restantes < 0:
        return 0
    return comb(K, aciertos) * comb(1, a) * comb(N - K - 1, restantes)


def probabilidad(juego, aciertos, con_adicional=False):
    """Probabilidad de que un boleto cualquiera caiga en esa categoría."""
    return favorables(juego, aciertos, con_adicional) / C


# ---------------------------------------------------------------- parseo de la tabla
#
# El texto de la columna "Aciertos" NO es consistente en el sitio. En la misma página del sorteo
# 4272 de Melate conviven:
#
#     "5 números naturales + adicional"      (categoría 2)
#     "3 números naturales y el adicional"   (categoría 6)
#
# Un parser que busque "+ adicional" se come la mitad de las categorías en silencio, y en silencio
# es la palabra importante: daría una tabla con menos filas y un `menores_brutos` más bajo, sin
# error. Por eso se busca la palabra "adicional" en cualquier posición, y el número con un regex
# anclado al principio.

_ACIERTOS = re.compile(r"^\s*(\d+)\s+n[úu]mer", re.IGNORECASE)
_ADICIONAL = re.compile(r"adicional", re.IGNORECASE)


def _entero(txt):
    """'115,808' -> 115808. Los miles van con coma en el sitio."""
    limpio = re.sub(r"[^\d]", "", txt or "")
    if not limpio:
        raise ValueError(f"no es un entero: {txt!r}")
    return int(limpio)


def _importe(txt):
    """'$44,898.68' -> 44898.68."""
    limpio = re.sub(r"[^\d.]", "", txt or "")
    if not limpio:
        raise ValueError(f"no es un importe: {txt!r}")
    return float(limpio)


def parsear(html, juego, sorteo=None):
    """HTML de una página de resultado -> lista de categorías.

    Cada categoría es un dict con `aciertos`, `adicional`, `ganadores`, `premio`, y la combinatoria
    ya resuelta (`favorables`, `probabilidad`). Se valida que la tabla tenga el número de categorías
    que el juego debe tener: si el sitio cambia de forma, esto tiene que fallar ruidosamente y no
    devolver media tabla.
    """
    from scrapling.parser import Selector

    filas = Selector(html).css("table tr")
    cats = []
    for tr in filas:
        celdas = [c.text.strip() for c in tr.css("td")]
        if len(celdas) != 4:
            continue                      # la fila de cabecera trae <th>, no <td>
        _lugar, aciertos_txt, ganadores_txt, premio_txt = celdas
        m = _ACIERTOS.match(aciertos_txt)
        if not m:
            raise ValueError(f"{juego} {sorteo}: no entiendo la categoría {aciertos_txt!r}")
        k = int(m.group(1))
        a = bool(_ADICIONAL.search(aciertos_txt))
        f = favorables(juego, k, a)
        if not f:
            raise ValueError(f"{juego} {sorteo}: categoría imposible {k} aciertos, adicional={a}")
        cats.append({"aciertos": k, "adicional": a, "ganadores": _entero(ganadores_txt),
                     "premio": _importe(premio_txt), "favorables": f, "probabilidad": f / C})

    esperadas = {"Melate": 9, "Revancha": 5, "Revanchita": 0}[juego]
    if len(cats) != esperadas:
        raise ValueError(f"{juego} {sorteo}: {len(cats)} categorías, esperaba {esperadas}. "
                         "¿Cambió la forma de la página? No sigo adivinando.")
    return cats


# ---------------------------------------------------------------- descarga, con caché y ritmo


class Descargador:
    """Pide páginas al sitio respetando el dictamen: caché permanente y 1 solicitud por segundo.

    La caché es **permanente a propósito**, no un TTL. Una tabla de ganadores de un sorteo pasado no
    cambia nunca: es un hecho histórico. Un TTL solo serviría para volver a molestar al servidor por
    el mismo dato. El efecto buscado es que una segunda corrida sobre la misma ventana haga **cero**
    peticiones.

    El ritmo se mide entre el *inicio* de una petición y el inicio de la siguiente, no entre el
    final y el inicio. Si la red tarda 3 s, la siguiente sale inmediatamente: ya ha pasado más de un
    segundo desde que empezó la anterior. Medirlo desde el final sería más lento sin ser más amable.
    """

    def __init__(self, cache=CACHE, pausa=PAUSA_SEGUNDOS, sesion=None):
        self.cache = pathlib.Path(cache)
        self.pausa = pausa
        self._sesion = sesion
        self._cm = None                   # el gestor de contexto, para poder cerrarlo
        self._ultima = None
        self.peticiones = 0               # cuántas salieron de verdad a la red; los tests lo miran

    def _crear_sesion(self):
        """La sesión de Scrapling, configurada para NO esconderse.

        `impersonate=None` y `stealthy_headers=False` apagan lo que Scrapling trae encendido por
        defecto: suplantar el saludo TLS de Chrome y añadir cabeceras de navegador. Comprobado que
        con esto la única cabecera que sale es nuestro `User-Agent`.

        `retries=0` porque el reintento lo lleva quien llama, que es el único que sabe si merece la
        pena insistir. Tres reintentos automáticos convierten un ritmo de 1/s en uno de 3/s contra
        un servidor que ya está teniendo problemas.

        `FetcherSession` solo expone `.get` dentro de su gestor de contexto, así que se entra aquí
        y se sale en `cerrar()`. Mantener una sola sesión abierta reutiliza la conexión TCP, que
        para el servidor es más barato que abrir una por página.
        """
        from scrapling.fetchers import FetcherSession

        self._cm = FetcherSession(impersonate=None, stealthy_headers=False,
                                  headers={"User-Agent": UA}, timeout=30, retries=0)
        return self._cm.__enter__()

    def cerrar(self):
        if self._cm is not None:
            self._cm.__exit__(None, None, None)
            self._cm, self._sesion = None, None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.cerrar()
        return False

    def _ruta(self, juego, sorteo):
        """La ruta en la caché, con los dos componentes validados.

        `juego` y `sorteo` se interpolan en una ruta de fichero **y** en una URL. Hoy los dos
        llegan de un `range()` y de una lista cerrada, así que no hay por dónde colarse; validarlos
        aquí cuesta dos líneas y cierra la puerta antes de que alguien llame a `html()` desde un
        sitio nuevo con un valor que venga de fuera. Un `sorteo` con `../` escribiría fuera de la
        caché, y un `juego` arbitrario pediría una URL que no es la nuestra.
        """
        if juego not in JUEGOS:
            raise ValueError(f"juego desconocido: {juego!r}")
        if not isinstance(sorteo, int) or isinstance(sorteo, bool) or sorteo <= 0:
            raise ValueError(f"el sorteo tiene que ser un entero positivo, no {sorteo!r}")
        return self.cache / juego.lower() / f"{sorteo}.html"

    def _esperar(self):
        if self._ultima is not None:
            resto = self.pausa - (time.monotonic() - self._ultima)
            if resto > 0:
                time.sleep(resto)
        self._ultima = time.monotonic()

    def html(self, juego, sorteo):
        """El HTML de esa página, de la caché si está y de la red si no."""
        if juego in SIN_TABLA:
            raise ValueError(f"{juego} no tiene tabla de ganadores: no se pide. Ver el dictamen.")
        ruta = self._ruta(juego, sorteo)
        if ruta.is_file():
            return ruta.read_text(encoding="utf-8")

        if self._sesion is None:
            self._sesion = self._crear_sesion()
        self._esperar()
        self.peticiones += 1
        url = URL.format(juego=juego.lower(), sorteo=sorteo)
        r = self._sesion.get(url)
        if r.status == 404:
            raise SorteoNoPublicado(f"{url} responde 404: ese sorteo no está en el sitio")
        if r.status != 200:
            raise SitioBloqueado(
                f"{url} respondió HTTP {r.status}.\n"
                "PARA AQUÍ. El dictamen dice que ante un bloqueo se pregunta al usuario, no se\n"
                "reintenta con otra identidad ni se escala a un navegador. Ver\n"
                "Documentos_Contexto/Fases/2026-10-03_popularidad/Decisiones/"
                "2026-10-03_02-40_s3-dictamen-terminos-melate-e.md")
        crudo = r.body if isinstance(r.body, bytes) else str(r.body).encode("utf-8")
        # Las páginas reales pesan entre 5 y 8 KB. Un megabyte no es una tabla de ganadores: es
        # otra cosa, y lo que no se quiere es escribirla en la caché y tratarla como buena.
        if len(crudo) > MAXIMO_BYTES:
            raise SitioBloqueado(f"{url} devolvió {len(crudo)} bytes, más del tope "
                                 f"{MAXIMO_BYTES}: eso no es una página de resultado")
        texto = crudo.decode("utf-8", errors="replace")
        if "<table" not in texto:
            raise SitioBloqueado(f"{url} respondió 200 pero sin tabla: ¿página de bloqueo o cambio de forma?")
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(texto, encoding="utf-8")
        return texto

    def tabla(self, juego, sorteo):
        return parsear(self.html(juego, sorteo), juego, sorteo)


# ---------------------------------------------------------------- validación cruzada de regalo
#
# La página trae también los números sorteados. No los usamos para analizar —para eso manda el CSV
# oficial, regla 7 del CLAUDE.md— pero compararlos sale gratis y es justo la comprobación que al
# proyecto le habría ahorrado el bug de Revancha 3827: un error de un tercero que era invisible a
# cualquier validación de una sola fuente, porque la fila estaba formalmente bien.
#
# Aquí melate-e.com hace de TERCERA fuente, independiente del oficial y del espejo de GitHub.


def numeros_de_la_pagina(html):
    """Los 6 naturales y el adicional tal como los publica el sitio. Solo para validación cruzada."""
    from scrapling.parser import Selector

    # El número va en un <b> dentro del <span>, así que hay que bajar al hijo: el `.text` del
    # span devuelve cadena vacía. Un `int('')` aquí fue el primer fallo de este parser.
    s = Selector(html)
    nat = [int(e.text.strip()) for e in s.css("span.numnatural b")]
    adi = [int(e.text.strip()) for e in s.css("span.numadicional b")]
    return nat, (adi[0] if adi else None)


def discrepancias(juego, sorteos, df_oficial, descargador=None):
    """Compara los números del sitio contra el CSV oficial. Lista vacía = los dos coinciden.

    `df_oficial` es lo que devuelve `ingest.cargar`, indexado por CONCURSO.
    """
    d = descargador or Descargador()
    oficial = df_oficial.set_index("CONCURSO")
    fuera = []
    for s in sorteos:
        if s not in oficial.index:
            continue
        nat, adi = numeros_de_la_pagina(d.html(juego, s))
        esperados = sorted(oficial.loc[s, "nums"])
        if sorted(nat) != esperados:
            fuera.append({"sorteo": int(s), "campo": "naturales",
                          "oficial": esperados, "sitio": sorted(nat)})
        if juego == "Melate":
            r7 = oficial.loc[s, "R7"]
            if adi is not None and r7 == r7 and int(r7) != adi:   # r7 != r7 descarta NaN
                fuera.append({"sorteo": int(s), "campo": "adicional",
                              "oficial": int(r7), "sitio": adi})
    return fuera


# ---------------------------------------------------------------- estimadores sobre UNA tabla
#
# Todo lo de aquí abajo parte de una identidad simple: si se vendieron N combinaciones y la gente
# eligiera al azar, la categoría c tendría E[ganadores] = N * p_c. Dar la vuelta a eso da una
# estimación de las ventas, y la gracia está en que **la gente no elige al azar**, así que las
# distintas categorías dan números distintos. Esa discrepancia no es ruido: es la señal.


def ventas_implicitas(juego, cats):
    """Ventas que haría falta suponer para explicar los ganadores de cada categoría, una a una.

    `N_c = ganadores_c / p_c`. Si la gente eligiera al azar, las categorías darían todas lo mismo
    salvo ruido de muestreo. Lo que se observa es que **no**, y en una dirección concreta: ver
    `razon_adicional`.

    El error estándar es el de Poisson, `sqrt(ganadores)/p`. Conviene mirarlo con desconfianza: con
    115.808 ganadores el error de muestreo es del 0,3 %, así que **lo que domina no es el ruido
    sino el sesgo** de suponer que la gente elige al azar. Más datos no lo arreglan.
    """
    out = []
    for c in cats:
        if not c["ganadores"]:
            continue                      # 0 ganadores no estima ventas: solo dice "pocas"
        p = c["probabilidad"]
        out.append({"aciertos": c["aciertos"], "adicional": c["adicional"],
                    "ganadores": c["ganadores"], "ventas": c["ganadores"] / p,
                    "error_poisson": c["ganadores"] ** 0.5 / p})
    return out


def _combinar(estimaciones):
    """Combina estimaciones de ventas ponderando por ganadores (precisión de Poisson)."""
    if not estimaciones:
        return None
    peso = sum(e["ganadores"] for e in estimaciones)
    return sum(e["ventas"] * e["ganadores"] for e in estimaciones) / peso


def ventas(juego, cats):
    """Combinaciones vendidas, estimadas de la tabla.

    Se estima **solo con las categorías sin adicional**. No es un detalle: las categorías que
    exigen el adicional obligan al boleto a contener ese número concreto, así que su estimación
    arrastra lo popular que sea ese número. Mezclarlas contaminaría las ventas con la popularidad,
    que es justo lo que queremos medir aparte.

    Devuelve también `con_adicional`, para que `razon_adicional` compare las dos.
    """
    imp = ventas_implicitas(juego, cats)
    puras = [e for e in imp if not e["adicional"]]
    con_a = [e for e in imp if e["adicional"]]
    est = _combinar(puras)
    return {
        "ventas": est,
        "con_adicional": _combinar(con_a),
        "categorias_usadas": len(puras),
        "dispersion": (statistics.pstdev([e["ventas"] for e in puras]) / est
                       if est and len(puras) > 1 else None),
        "por_categoria": imp,
    }


def bolsa_repartida(cats):
    """Lo que de verdad se pagó en las categorías menores: suma de ganadores x premio."""
    return sum(c["ganadores"] * c["premio"] for c in cats if c["aciertos"] < K)


def menores_brutos_directo(cats):
    """Premio esperado de las categorías menores, por la vía directa: suma de p_c x premio_c.

    Es la definición literal de "lo que esperaría cobrar un boleto cualquiera en ESTE sorteo", y por
    eso parece la buena. Tiene un problema grave de varianza: el premio de cada categoría es a
    repartir, `premio_c = bolsa_c / ganadores_c`, y cuando una categoría alta tiene 3 ganadores el
    premio individual se dispara y arrastra toda la suma. Ver `menores_brutos_por_bolsa`.
    """
    return sum(c["probabilidad"] * c["premio"] for c in cats if c["aciertos"] < K)


def menores_brutos_por_bolsa(cats, ventas_estimadas):
    """El mismo premio esperado, pero por la bolsa: lo pagado dividido entre las ventas.

    Algebraicamente es el anterior con `ganadores_c / N` en lugar de `p_c`. La diferencia práctica
    es toda: la bolsa de cada categoría es un porcentaje de las ventas fijado por reglamento, así
    que `bolsa_c / N` es casi constante entre sorteos, mientras que `p_c * bolsa_c / ganadores_c`
    estalla cuando hay pocos ganadores.

    Para estimar lo que pagará el PRÓXIMO sorteo —que es para lo que sirve esto— se quiere la media
    de largo plazo, y este estimador la alcanza con muchísimos menos sorteos.
    """
    if not ventas_estimadas:
        return None
    return bolsa_repartida(cats) / ventas_estimadas


def razon_adicional(juego, cats):
    """Cuánto menos (o más) jugado está el número adicional de este sorteo. Solo Melate.

    Las categorías "k naturales + adicional" exigen que el boleto **contenga** el número adicional;
    las "k naturales" a secas exigen que **no** lo contenga. Si la gente eligiera al azar, las dos
    familias estimarían las mismas ventas y la razón sería 1.

    Una razón de 0,8 quiere decir que el adicional de ese sorteo aparece en un 20 % menos de boletos
    de lo que daría el azar: está infrajugado. Es la única medida de popularidad que estos datos
    sostienen de verdad, porque cada sorteo aísla **un** número.

    Es aproximada: supone que contener el adicional es independiente de cuántos naturales aciertas,
    y no lo es del todo (quien juega solo números bajos falla las dos cosas a la vez). Sirve para
    el efecto agregado, no para afinar un número concreto.
    """
    if juego != "Melate":
        return None
    v = ventas(juego, cats)
    if not v["ventas"] or not v["con_adicional"]:
        return None
    return v["con_adicional"] / v["ventas"]


# ---------------------------------------------------------------- agregado sobre una ventana
#
# Un sorteo suelto no sostiene nada. Lo que se publica sale de una ventana declarada, y la ventana
# va en la procedencia junto con la fecha de descarga: las tablas de sorteos pasados no cambian,
# pero la ventana sí, y una cifra sin su ventana no se puede reproducir (regla 6 del protocolo).


def adicionales_oficiales(df):
    """{concurso: R7} del CSV oficial de Melate. El adicional sale del oficial, no del sitio.

    Regla 7 del CLAUDE.md: para los números sorteados manda el oficial. Lo que el sitio aporta son
    los **ganadores**, que el oficial no publica en formato legible.
    """
    return {int(c): int(r) for c, r in zip(df.CONCURSO, df.R7) if r == r}


def analizar(juego, sorteos, descargador=None, adicionales=None):
    """Recorre una ventana de sorteos y resume lo que las tablas dicen.

    `adicionales` es {concurso: R7} y solo hace falta en Melate, para el efecto calendario. Si no se
    pasa, las muestras no llevan `adicional` y `efecto_calendario` no tendrá nada que agrupar.

    `sorteos` se materializa a lista antes de recorrerlo. No es un detalle de estilo: la versión
    anterior lo recorría y después hacía `len(list(sorteos))` para el recuento, y con un generador
    eso devolvía **0 pedidos** junto a 3 usados — un reporte absurdo, y silencioso. Con un `range`
    no pasaba, que es justo por qué no se vio.
    """
    d = descargador or Descargador()
    adicionales = adicionales or {}
    sorteos = list(sorteos)
    muestras, fallos = [], []
    for s in sorteos:
        try:
            cats = d.tabla(juego, s)
        except SorteoNoPublicado as e:
            # Pedir un sorteo que el sitio no tiene es normal (uno futuro, por ejemplo) y se
            # anota. Un bloqueo NO se captura aquí a propósito: sube y para la corrida, que es
            # lo que manda el dictamen.
            fallos.append({"sorteo": int(s), "error": f"{type(e).__name__}: {e}"})
            continue
        except ValueError as e:
            fallos.append({"sorteo": int(s), "error": f"{type(e).__name__}: {e}"})
            continue
        v = ventas(juego, cats)
        muestras.append({
            "sorteo": int(s),
            "ventas": v["ventas"],
            "ventas_con_adicional": v["con_adicional"],
            "razon_adicional": razon_adicional(juego, cats),
            "bolsa_repartida": bolsa_repartida(cats),
            "menores_directo": menores_brutos_directo(cats),
            "menores_por_bolsa": menores_brutos_por_bolsa(cats, v["ventas"]),
            "adicional": adicionales.get(int(s)),
        })

    return {
        "juego": juego,
        "sorteos_pedidos": len(sorteos),
        "sorteos_usados": len(muestras),
        "ventana": [muestras[0]["sorteo"], muestras[-1]["sorteo"]] if muestras else None,
        "fallos": fallos,
        "ventas": _resumir([m["ventas"] for m in muestras]),
        "menores_brutos_directo": _resumir([m["menores_directo"] for m in muestras]),
        "menores_brutos_por_bolsa": _resumir([m["menores_por_bolsa"] for m in muestras]),
        "efecto_calendario": efecto_calendario(muestras),
        "muestras": muestras,
    }


def _resumir(valores):
    """Media, mediana, dispersión y rango. La dispersión es lo que decide si una cifra es publicable."""
    v = [x for x in valores if x is not None]
    if not v:
        return None
    media = statistics.fmean(v)
    return {
        "n": len(v),
        "media": media,
        "mediana": statistics.median(v),
        "desviacion": statistics.stdev(v) if len(v) > 1 else 0.0,
        "cv": (statistics.stdev(v) / media if len(v) > 1 and media else None),
        "min": min(v),
        "max": max(v),
    }


# El corte en 31 no es arbitrario: es el último día que cabe en un mes. Es el efecto de popularidad
# mejor documentado de las loterías de números — la gente juega cumpleaños — y el único que estos
# datos pueden medir, porque cada sorteo de Melate aísla exactamente un número: el adicional.
CORTE_CALENDARIO = 31


def efecto_calendario(muestras, corte=CORTE_CALENDARIO):
    """¿Están los números > 31 menos jugados que los <= 31? Medido, no supuesto.

    Agrupa las `razon_adicional` de la ventana según el adicional de cada sorteo caiga dentro o
    fuera del calendario, y compara las medias. Si la gente eligiera al azar, las dos medias serían
    1 y la razón entre ellas también.

    Devuelve `None` si no hay datos de los dos lados: media de un grupo vacío no es 0, es nada.
    """
    dentro = [m["razon_adicional"] for m in muestras
              if m.get("adicional") and m["razon_adicional"] and m["adicional"] <= corte]
    fuera = [m["razon_adicional"] for m in muestras
             if m.get("adicional") and m["razon_adicional"] and m["adicional"] > corte]
    if not dentro or not fuera:
        return None
    md, mf = statistics.fmean(dentro), statistics.fmean(fuera)
    out = {
        "corte": corte,
        "dentro_del_calendario": {"n": len(dentro), "razon_media": md,
                                  "desviacion": statistics.stdev(dentro) if len(dentro) > 1 else 0.0},
        "fuera_del_calendario": {"n": len(fuera), "razon_media": mf,
                                 "desviacion": statistics.stdev(fuera) if len(fuera) > 1 else 0.0},
        "cociente_fuera_entre_dentro": mf / md if md else None,
    }
    # Prueba de Welch a mano: scipy ya es dependencia, pero esto son dos medias y no merece el
    # import. La p es informativa y NO entra en la familia de Benjamini-Hochberg: no es una
    # hipótesis sobre la urna, es una medición de la conducta de los jugadores. Ver el documento
    # de Protocolo_Estadistico de esta fase.
    if len(dentro) > 1 and len(fuera) > 1:
        vd = statistics.variance(dentro) / len(dentro)
        vf = statistics.variance(fuera) / len(fuera)
        if vd + vf > 0:
            out["t_welch"] = (mf - md) / (vd + vf) ** 0.5
    return out


# ---------------------------------------------------------------- línea de órdenes


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Estima ventas y premios menores de las tablas de ganadores por categoría.",
        epilog="Lee el dictamen antes de ampliar la ventana: 1 solicitud/segundo contra el "
               "servidor de otra persona.")
    # Sin defecto "todo el histórico" a propósito: el dictamen exige ventana declarada.
    ap.add_argument("--desde", type=int, required=True, help="primer concurso de la ventana")
    ap.add_argument("--hasta", type=int, required=True, help="último concurso de la ventana")
    ap.add_argument("--juegos", nargs="+", default=[j for j in JUEGOS if j not in SIN_TABLA],
                    help=f"por defecto, los que tienen tabla: {[j for j in JUEGOS if j not in SIN_TABLA]}")
    ap.add_argument("--datos", help="carpeta del snapshot, para el adicional oficial de Melate")
    ap.add_argument("--cache", default=str(CACHE))
    ap.add_argument("--salida", default="reportes/popularidad.json")
    a = ap.parse_args(argv)

    pedidos = [j for j in a.juegos if j not in SIN_TABLA]
    if omitidos := [j for j in a.juegos if j in SIN_TABLA]:
        print(f"Omito {', '.join(omitidos)}: no tiene tabla de ganadores. Ver el dictamen.")

    adicionales = {}
    if "Melate" in pedidos:
        from .ingest import cargar
        from .validate import era_56
        adicionales = adicionales_oficiales(era_56("Melate", cargar("Melate", a.datos)))

    sorteos = range(a.desde, a.hasta + 1)
    paginas = len(sorteos) * len(pedidos)
    print(f"Ventana {a.desde}-{a.hasta} x {len(pedidos)} juegos = {paginas} páginas.")
    print(f"Lo no cacheado sale a 1 solicitud/segundo (como mucho {paginas // 60} min {paginas % 60} s).")

    with Descargador(cache=a.cache) as d:
        reporte = {"ventana": [a.desde, a.hasta], "juegos": {}}
        for j in pedidos:
            r = analizar(j, sorteos, descargador=d, adicionales=adicionales)
            reporte["juegos"][j] = r
            v, mb = r["ventas"], r["menores_brutos_por_bolsa"]
            print(f"\n== {j}: {r['sorteos_usados']} sorteos, {len(r['fallos'])} fallos")
            if v:
                print(f"   ventas          mediana {v['mediana']:>12,.0f}  cv {v['cv']:.3f}")
            if mb:
                print(f"   menores brutos  mediana {mb['mediana']:12.4f}  cv {mb['cv']:.3f}  "
                      f"(estimador por bolsa)")
            if ec := r["efecto_calendario"]:
                print(f"   efecto calendario: los > {ec['corte']} aparecen en un "
                      f"{1 - ec['cociente_fuera_entre_dentro']:.0%} menos de boletos "
                      f"(t = {ec.get('t_welch', float('nan')):.1f})")
        reporte["procedencia"] = {
            "fuente": URL,
            "descargado_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            "peticiones_de_red": d.peticiones,
            "cache": str(d.cache),
            "user_agent": UA,
            "pausa_segundos": d.pausa,
        }

    salida = pathlib.Path(a.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    with open(salida, "w", encoding="utf-8") as f:
        json.dump(reporte, f, ensure_ascii=False, indent=1, default=str)
    print(f"\nReporte en {salida}  ({d.peticiones} peticiones de red esta corrida)")
    print("\nEsto NO predice números. Mide qué juega la gente, que es otra cosa.")
    return reporte


if __name__ == "__main__":
    main()
