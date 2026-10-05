"""El ciclo vivo: `python -m melate.ciclo`. La única orden que incorpora sorteos.

    .venv\\Scripts\\python.exe -m melate.ciclo                        # todo
    .venv\\Scripts\\python.exe -m melate.ciclo --comprobar            # descarga y valida; no escribe
    .venv\\Scripts\\python.exe -m melate.ciclo --sin-testigo espejo   # sigue sin un testigo que FALTA

Descarga los tres CSV del oficial, comprueba que el pasado no cambió, valida cada sorteo nuevo con
sus testigos —el espejo de GitHub y melate-e.com— y solo entonces congela un snapshot nuevo, entero y
de una vez, en `data/raw/<fecha del último sorteo>_<último concurso>/`. Después deriva sobre él la
popularidad, el informe con el valor esperado del sorteo siguiente, el veredicto de cada preregistro y
la base de la app. **Nunca escribe encima de nada, nunca deja nada a medias, y no comitea ni sube
nada.**

La decisión que fija todo esto se escribió antes que este fichero:
`Documentos_Contexto/Almacenamiento/Decisiones/2026-10-04_20-10_s5-el-ciclo-vivo.md`. La regla de los
testigos es la C2.2 del usuario: **uno que discrepa para el ciclo; uno que falta hace esperar**, y
seguir sin él se pide con `--sin-testigo` y queda escrito. Esa opción nunca salta un desacuerdo: el
espejo se consulta igual, y de melate-e.com se comparan las páginas que ya estén en caché; lo único
que deja de hacer es pedir páginas nuevas al sitio, que es lo que hace falta si el sitio bloquea.
"""
import argparse
import datetime
import hashlib
import json
import os
import pathlib
import re
import shutil
import sys
import time

from . import ingest
from .constantes import BOLSA_MINIMA, JUEGOS, OFICIAL

RAIZ = pathlib.Path(__file__).resolve().parents[2]

# Los códigos de salida, los de la decisión.
OK, HALLAZGO, ESPERAR, FUENTE_CAIDA, BLOQUEO = 0, 1, 2, 3, 4

RAW = pathlib.Path("data", "raw")
CACHE = pathlib.Path("data", "cache", "melate-e")
INCOMPLETAS = pathlib.Path("data", "cache", "melate-e-incompletas")
CUARENTENA = pathlib.Path("data", "cuarentena")
REPORTES = pathlib.Path("reportes")

# El nombre de un snapshot del ciclo: la fecha del último sorteo y su concurso.
NOMBRE = re.compile(r"^(\d{4}-\d{2}-\d{2})_(\d+)$")
TESTIGOS = ("espejo", "melate-e")
CON_TABLA = ("Melate", "Revancha")       # Revanchita no se pide a melate-e.com (dictamen, C2.1)
VENTANA = 100                            # la de la popularidad: comparable con la publicada
SIMULACIONES = 2000                      # las de los informes publicados

# La BOLSA inválida que ya se conoce del oficial (regla 4 de los datos). Una nueva es un hallazgo.
BOLSA_CONOCIDA = {"Melate": [2120, 2142, 2234], "Revancha": [2120, 2142, 2234], "Revanchita": []}


class Parada(Exception):
    """El ciclo se para sin congelar nada. `codigo` es el de salida; `descargas`, la evidencia de un
    hallazgo, que va a la cuarentena."""

    def __init__(self, codigo, mensaje, descargas=None):
        super().__init__(mensaje)
        self.codigo, self.descargas = codigo, descargas


class NoSePide(LookupError):
    """La página no está en caché y no se pide: `--comprobar` no escribe, y `--sin-testigo melate-e`
    no vuelve a llamar a un sitio que puede estar bloqueando."""


def _ahora():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def _sha(crudo):
    return hashlib.sha256(crudo).hexdigest()


# ---------------------------------------------------------------- las fuentes
def descargar_oficial(juego, plantilla=OFICIAL):
    """GET al oficial con la identificación y la comprobación de `ingest._descargar`, pero con la
    respuesta entera: la procedencia apunta el HTTP, los bytes y el `Last-Modified`."""
    import requests

    url = plantilla.format(juego)
    r = requests.get(url, timeout=30, headers=ingest._UA)
    if not r.ok:
        raise OSError(f"{url} respondió HTTP {r.status_code}")
    if "CONCURSO" not in r.content[:200].decode("utf-8-sig", errors="replace"):
        raise OSError(f"{url} respondió algo que no es el CSV esperado")
    return {"url": url, "crudo": r.content, "http": r.status_code,
            "last_modified": r.headers.get("Last-Modified"), "utc": _ahora()}


class Paginas:
    """Las páginas de melate-e.com de los sorteos nuevos, con el dictamen y sin pedir dos veces.

    Una página nueva se pide a la caché de las incompletas; si su tabla está entera y con premios,
    pasa a la permanente, la que lee la popularidad. Si no, se queda donde está: sus números sirven
    igual como testigo, pero no entra en la popularidad (H5 del inventario de la Fase 5). Antes de pedir
    se miran las dos cachés, así que ninguna página se pide dos veces.
    """

    def __init__(self, raiz, descargador=None):
        self.cache, self.incompletas = raiz / CACHE, raiz / INCOMPLETAS
        self._d, self._propio = descargador, descargador is None

    @property
    def peticiones(self):
        return self._d.peticiones if self._d is not None else 0

    def _ruta(self, cache, juego, sorteo):
        return cache / juego.lower() / f"{sorteo}.html"

    def html(self, juego, sorteo, pedir=True):
        from . import popularity

        if juego not in CON_TABLA:
            raise ValueError(f"{juego} no se pide a melate-e.com: ver el dictamen")
        for cache in (self.cache, self.incompletas):
            ruta = self._ruta(cache, juego, sorteo)
            if ruta.is_file():
                return ruta.read_text(encoding="utf-8")
        if not pedir:
            raise NoSePide(f"{juego} {sorteo}: su página no está en caché y no se pide")
        if self._d is None:
            self._d = popularity.Descargador(cache=self.incompletas)
        html = self._d.html(juego, sorteo)
        destino = self.cache if completa(html, juego, sorteo) else self.incompletas
        ruta = self._ruta(destino, juego, sorteo)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(html, encoding="utf-8")
        if destino == self.cache:
            self._ruta(self.incompletas, juego, sorteo).unlink(missing_ok=True)
        return html

    def cerrar(self):
        if self._propio and self._d is not None:
            self._d.cerrar()


def completa(html, juego, sorteo):
    """¿Trae la página su tabla entera y con los premios publicados?"""
    from . import popularity

    try:
        return popularity.premios_publicados(popularity.parsear(html, juego, sorteo))
    except ValueError:
        return False


class Fuentes:
    """De dónde saca el ciclo cada cosa. Los tests le pasan unas falsas: la suite no sale a la red."""

    def __init__(self, raiz, oficial=None, espejo=None, descargador=None):
        self._oficial = oficial or descargar_oficial
        self._espejo = espejo or ingest.cargar_espejo
        self.paginas = Paginas(raiz, descargador)
        self.peticiones = {"oficial": 0, "espejo": 0}

    def oficial(self, juego):
        self.peticiones["oficial"] += 1
        return self._oficial(juego)

    def espejo(self, juego):
        self.peticiones["espejo"] += 1
        return self._espejo(juego)


# ---------------------------------------------------------------- los snapshots que hay
def snapshots(raiz):
    """Los snapshots de `data/raw/`, como `(último concurso, carpeta)`, del más viejo al más nuevo.

    El de un snapshot del ciclo lo dice su nombre. El de la Fase 1, que se nombró con la fecha de
    descarga, se lee de su fichero. Las carpetas que empiezan por punto están a medio escribir.
    """
    out = []
    for c in sorted((raiz / RAW).iterdir()):
        if not c.is_dir() or c.name.startswith(".") or not (c / "SHA256.txt").is_file():
            continue
        m = NOMBRE.match(c.name)
        ultimo = int(m.group(2)) if m else int(ingest.cargar("Melate", str(c)).CONCURSO.max())
        out.append((ultimo, c.name))
    if not out:
        raise SystemExit(f"No hay ningún snapshot en {RAW}: el ciclo necesita uno contra el que comparar.")
    return sorted(out)


def _partir(crudo):
    """La cabecera de un CSV del oficial, con su salto de línea, y el resto."""
    i = crudo.find(b"\n")
    if i < 0:
        raise ValueError("no tiene ni una línea entera")
    return crudo[:i + 1], crudo[i + 1:]


# ---------------------------------------------------------------- comprobar, sin terceros
def comprobar(raiz, fuentes, decir=print):
    """Descarga el oficial y comprueba lo que no depende de nadie. Devuelve qué hay de nuevo.

    No escribe nada. Las comprobaciones, en este orden: que el oficial responda con los tres CSV; que
    el pasado no haya cambiado (el snapshot anterior, sufijo exacto del nuevo); que los tres juegos
    acaben en el mismo sorteo; y que el fichero entero y cada fila nueva sean válidos.
    """
    from .validate import era_56, validar_era

    ultimo_previo, previo = snapshots(raiz)[-1]
    carpeta_previa = raiz / RAW / previo
    decir(f"== El oficial: tres peticiones. Último snapshot: {RAW.as_posix()}/{previo} "
          f"(hasta el {ultimo_previo})")
    descargas = {}
    for juego in JUEGOS:
        try:
            descargas[juego] = fuentes.oficial(juego)
        except Exception as e:  # noqa: BLE001 - cualquier fallo del oficial para todo, igual
            raise Parada(FUENTE_CAIDA, f"El oficial falló en {juego}: {e}\nNo se ha escrito nada. "
                                       "Vuelve a correrlo más tarde.") from e
        d = descargas[juego]
        decir(f"   {juego:11s} HTTP {d['http']}  {len(d['crudo']):7d} bytes  "
              f"Last-Modified {_de_fuera(d['last_modified'])}")

    # 1 · El pasado no cambió.
    nuevas = {}
    for juego in JUEGOS:
        cab_v, cuerpo_v = _partir((carpeta_previa / f"{juego}.csv").read_bytes())
        cab_n, cuerpo_n = _partir(descargas[juego]["crudo"])
        if cab_n != cab_v or not cuerpo_n.endswith(cuerpo_v):
            raise Parada(HALLAZGO, f"El pasado cambió en {juego}: el fichero del snapshot {previo} "
                                   "ya no es el final del que sirve el oficial. Es un hallazgo: se "
                                   "investiga, no se congela.", descargas)
        nuevas[juego] = cuerpo_n[:len(cuerpo_n) - len(cuerpo_v)]
    if not any(nuevas.values()):
        decir(f"   nada nuevo: los tres ficheros son, byte a byte, los de {previo}")
        return {"previo": previo, "ultimo_previo": ultimo_previo, "nuevos": [], "descargas": descargas}

    # 2 · Lo nuevo se lee como lo leería cualquier programa del proyecto. Un CSV que no se deja leer
    # trae una fila nueva que no es válida: es un hallazgo con su evidencia, no una traza.
    completos, era, ultimos = {}, {}, {}
    for juego in JUEGOS:
        try:
            completos[juego] = ingest._normalizar(descargas[juego]["crudo"], descargas[juego]["url"])
            era[juego] = era_56(juego, completos[juego])
            ultimos[juego] = int(era[juego].CONCURSO.max())
        except (ValueError, KeyError, TypeError, AssertionError) as e:
            # El AssertionError es de `validate.era_56`, traslado literal de la línea base que no se
            # toca: afirma que ningún número pasa de 56.
            raise Parada(HALLAZGO, f"El {juego}.csv del oficial no se deja leer ({type(e).__name__}"
                                   f"{': ' + str(e)[:200] if str(e) else ''}).\nEs un hallazgo: se "
                                   "investiga, no se congela.", descargas) from e
    if len(set(ultimos.values())) > 1:
        raise Parada(ESPERAR, "El oficial está a medio actualizar: "
                              + ", ".join(f"{j} hasta el {u}" for j, u in ultimos.items())
                              + ". No se congela nada: vuelve a correrlo más tarde.")
    nuevos = sorted(int(c) for c in era["Melate"].CONCURSO if c > ultimo_previo)

    # 3 · Las filas nuevas son sorteos nuevos, y el fichero entero sigue siendo válido.
    problemas = []
    for juego in JUEGOS:
        lineas = [l for l in nuevas[juego].decode("utf-8", errors="replace").splitlines() if l.strip()]
        suyos = sorted(int(c) for c in era[juego].CONCURSO if c > ultimo_previo)
        if suyos != nuevos or len(lineas) != len(nuevos):
            problemas.append(f"{juego}: {len(lineas)} líneas nuevas para los sorteos {suyos}")
            continue
        v = validar_era(juego, completos[juego])
        for clave in ("concursos_faltantes", "duplicados", "fuera_de_rango",
                      "filas_no_ordenadas_o_repetidas", "adicional_repetido_en_naturales"):
            if v.get(clave):
                problemas.append(f"{juego}: {clave} = {v[clave]}")
        if v["bolsa_cero_o_invalida"] != BOLSA_CONOCIDA[juego]:
            problemas.append(f"{juego}: BOLSA inválida en {v['bolsa_cero_o_invalida']}")
        filas = era[juego][era[juego].CONCURSO > ultimo_previo]
        bajas = filas[filas.BOLSA < BOLSA_MINIMA[juego]]
        if len(bajas):
            problemas.append(f"{juego}: BOLSA por debajo de la mínima ({BOLSA_MINIMA[juego] / 1e6:.0f} "
                             f"millones) en {[int(c) for c in bajas.CONCURSO]}")
        anterior = era[juego][era[juego].CONCURSO <= ultimo_previo].FECHA.max()
        if not (filas.FECHA > anterior).all() or not filas.FECHA.is_monotonic_increasing:
            problemas.append(f"{juego}: fechas nuevas que no van después de {anterior.date()}")
    fechas = {j: tuple(era[j][era[j].CONCURSO > ultimo_previo].FECHA) for j in JUEGOS}
    if len(set(fechas.values())) > 1:
        problemas.append("los tres juegos no dan las mismas fechas a los mismos sorteos")
    if problemas:
        raise Parada(HALLAZGO, "Sorteos nuevos que no son válidos:\n  " + "\n  ".join(problemas)
                     + "\nEs un hallazgo: se investiga, no se congela.", descargas)
    decir(f"   el pasado no cambió; sorteos nuevos: {', '.join(map(str, nuevos))}; válidos")
    return {"previo": previo, "ultimo_previo": ultimo_previo, "nuevos": nuevos,
            "descargas": descargas, "era": era}


# ---------------------------------------------------------------- los testigos (C2.2)
def _igual(a, b):
    return a == b or (a != a and b != b)          # NaN, el adicional que no tienen dos juegos


def _lo_que_dice_la_pagina(html, juego, fila):
    """Lo que testifica una página de melate-e.com sobre una fila del oficial.

    Solo una lectura entera puede contradecirlo (C2.2): una página sin sus seis números, o con algo
    que no es un número donde va uno, no dice nada. Ese testigo falta, no discrepa; y como la página
    ya está en caché y ninguna se pide dos veces, volver a correr el ciclo no lo arregla.
    """
    from . import popularity

    try:
        nat, adi = popularity.numeros_de_la_pagina(html)
    except ValueError:
        return "falta: la página no se deja leer (ya pedida: no se vuelve a pedir)"
    if len(nat) != 6:
        return f"falta: la página trae {len(nat)} números, no 6 (ya pedida: no se vuelve a pedir)"
    difs = []
    if sorted(nat) != sorted(fila["nums"]):
        difs.append("números")
    if juego == "Melate" and adi is not None and int(fila["R7"]) != adi:
        difs.append("adicional")
    return "confirma" if not difs else "discrepa en " + ", ".join(difs)


def testigos(r, fuentes, sin_testigo=frozenset(), pedir=True, decir=print):
    """Lo que dice cada testigo de cada sorteo nuevo. Un desacuerdo para; una ausencia hace esperar,
    salvo que se haya pedido `--sin-testigo`. Devuelve la tabla, que va a la procedencia."""
    from . import popularity

    nuevos, era = r["nuevos"], r["era"]
    tabla = {(c, j): {} for c in nuevos for j in JUEGOS}
    decir("== Testigos")
    for juego in JUEGOS:
        oficial = era[juego].set_index("CONCURSO")
        try:
            espejo, motivo = fuentes.espejo(juego).set_index("CONCURSO"), None
        except Exception as e:  # noqa: BLE001 - un testigo que no responde falta, no para
            espejo, motivo = None, f"falta: no se pudo descargar ({type(e).__name__})"
        for c in nuevos:
            if espejo is None:
                estado = motivo
            elif c not in espejo.index:
                estado = "falta: no trae el sorteo"
            else:
                of, es = oficial.loc[c], espejo.loc[c]
                difs = [campo for campo, a, b in (
                    ("números", sorted(of["nums"]), sorted(es["nums"])),
                    ("adicional", of["R7"], es["R7"]),
                    ("BOLSA", float(of["BOLSA"]), float(es["BOLSA"]))) if not _igual(a, b)]
                estado = "confirma" if not difs else "discrepa en " + ", ".join(difs)
            tabla[(c, juego)]["espejo"] = estado

    pedir_paginas = pedir and "melate-e" not in sin_testigo
    for juego in JUEGOS:
        oficial = era[juego].set_index("CONCURSO")
        for c in nuevos:
            if juego not in CON_TABLA:
                tabla[(c, juego)]["melate-e"] = "no se pide (dictamen)"
                continue
            try:
                html = fuentes.paginas.html(juego, c, pedir=pedir_paginas)
            except popularity.SorteoNoPublicado:
                estado = "falta: el sitio no tiene la página"
            except NoSePide:
                estado = ("no se pide con --comprobar" if not pedir
                          else "falta: no se pide con --sin-testigo melate-e")
            except popularity.SitioBloqueado as e:
                raise Parada(BLOQUEO, f"melate-e.com dejó de responder como se espera: {e}\nSe para y "
                                      "se pregunta, como dice el dictamen. Si se decide seguir sin "
                                      "él: --sin-testigo melate-e.") from e
            else:
                estado = _lo_que_dice_la_pagina(html, juego, oficial.loc[c])
            tabla[(c, juego)]["melate-e"] = estado

    for (c, juego), t in sorted(tabla.items()):
        nums = " ".join(f"{n:2d}" for n in era[juego].set_index("CONCURSO").loc[c, "nums"])
        decir(f"   {c} {juego:11s} {nums}   espejo: {t['espejo']} · melate-e.com: {t['melate-e']}")
    discrepan = [f"{c} {j}, {t}: {e}" for (c, j), d in sorted(tabla.items()) for t, e in d.items()
                 if e.startswith("discrepa")]
    if discrepan:
        raise Parada(HALLAZGO, "Un testigo discrepa del oficial:\n  " + "\n  ".join(discrepan)
                     + "\nEs un hallazgo: se investiga con una tercera fuente antes de elegir un "
                       "valor (regla 7). Ninguna opción lo salta.", r["descargas"])
    faltan = sorted({t for d in tabla.values() for t, e in d.items()
                     if e.startswith("falta") and t not in sin_testigo})
    if faltan:
        raise Parada(ESPERAR, f"Falta{'n' if len(faltan) > 1 else ''} {' y '.join(faltan)} para algún "
                              "sorteo nuevo. No se congela nada: vuelve a correrlo más tarde, o sigue "
                              "sin él con --sin-testigo " + " --sin-testigo ".join(faltan)
                              + " (quedará escrito en la procedencia).")
    return tabla


# ---------------------------------------------------------------- congelar
def nombre_del_snapshot(r):
    ultimo = r["nuevos"][-1]
    fecha = r["era"]["Melate"].set_index("CONCURSO").loc[ultimo, "FECHA"].date().isoformat()
    return f"{fecha}_{ultimo}"


def _de_fuera(texto):
    """Un texto que viene de un servidor —la cabecera `Last-Modified`— va a un fichero que se publica:
    sin nada que pueda romper la tabla ni el Markdown, y con un tope."""
    return re.sub(r"[^\w ,:+./-]", "", str(texto))[:64] if texto else "—"


def procedencia(nombre, r, tabla, sin_testigo, hashes, ahora):
    """El `PROCEDENCIA.md` de un snapshot del ciclo. Sin rutas de la máquina: esto se publica.

    Dice lo que pasó de verdad: la URL de la que salió cada fichero y la hora de su descarga, que no es
    la de congelar —entre una y otra se pregunta a los testigos—.
    """
    d = r["descargas"]
    fuente = d["Melate"]["url"].replace("Melate", "{Melate,Revancha,Revanchita}")
    lineas = [
        f"# Procedencia del snapshot {nombre}",
        "",
        "Snapshot **inmutable**, congelado por `python -m melate.ciclo` (Fase 5). Estos ficheros no se "
        "vuelven a descargar ni se tocan. Un sorteo nuevo no se añade aquí: va en otra carpeta.",
        "",
        "## Descarga",
        "",
        f"- **Fuente:** `{fuente}`",
        f"- **Descargado:** {d['Melate']['utc']} · **congelado:** {ahora}",
        "- **Método:** `melate.ciclo.descargar_oficial`: `requests.get` con `timeout=30` y el "
        "`User-Agent` de `src/melate/ingest.py`; bytes guardados tal cual, sin recodificar",
        "",
        "| Fichero | HTTP | Bytes | Descargado (UTC) | Last-Modified | SHA-256 |",
        "|---|---|---|---|---|---|",
    ]
    lineas += [f"| `{j}.csv` | {d[j]['http']} | {len(d[j]['crudo'])} | {d[j]['utc']} | "
               f"{_de_fuera(d[j]['last_modified'])} | `{hashes[j]}` |" for j in JUEGOS]
    lineas += [
        "",
        "## Sobre el snapshot anterior",
        "",
        f"- **Anterior:** `{RAW.as_posix()}/{r['previo']}`, hasta el sorteo {r['ultimo_previo']}.",
        "- **El pasado no cambió:** en los tres juegos, la cabecera es la misma y el fichero anterior es "
        "un sufijo exacto, byte a byte, del nuevo.",
        f"- **Sorteos nuevos:** {', '.join(map(str, r['nuevos']))}.",
        "- **Validados** con `validar_era`: concursos consecutivos, sin duplicados, números en rango y "
        "ordenados, el adicional fuera de los naturales, la BOLSA inválida solo donde ya se conocía, y la "
        "de cada sorteo nuevo por encima de la bolsa mínima.",
        "",
        "## Testigos de cada sorteo nuevo (regla 7, C2.2)",
        "",
        "| Sorteo | Juego | Números del oficial | Adicional | BOLSA | Espejo | melate-e.com |",
        "|---|---|---|---|---|---|---|",
    ]
    for (c, j), t in sorted(tabla.items()):
        fila = r["era"][j].set_index("CONCURSO").loc[c]
        adicional = "—" if fila["R7"] != fila["R7"] else str(int(fila["R7"]))
        lineas.append(f"| {c} | {j} | {' '.join(str(n) for n in fila['nums'])} | {adicional} | "
                      f"{int(fila['BOLSA'])} | {t['espejo']} | {t['melate-e']} |")
    lineas += [
        "",
        "**Testigos sin los que se siguió, por decisión explícita:** "
        + (", ".join(f"`--sin-testigo {t}`" for t in sorted(sin_testigo)) or "ninguno") + ".",
        "",
        "## SHA-256",
        "",
        "```",
        *[f"{hashes[j]}  {j}.csv" for j in JUEGOS],
        "```",
        "",
        "Los mismos valores, legibles por máquina, en `SHA256.txt`.",
        "",
        "## Cómo verificar",
        "",
        "```powershell",
        "Get-FileHash .\\Melate.csv, .\\Revancha.csv, .\\Revanchita.csv -Algorithm SHA256 |",
        "  ForEach-Object { \"$($_.Hash.ToLower())  $(Split-Path $_.Path -Leaf)\" }",
        "```",
        "",
        "Debe coincidir, línea por línea, con `SHA256.txt`. Si no coincide, el snapshot está corrupto o "
        "alguien lo modificó: no se arregla, se descarta.",
        "",
    ]
    return "\n".join(lineas)


def congelar(raiz, r, tabla, sin_testigo, decir=print):
    """Escribe el snapshot en una carpeta temporal y la renombra: o está entero, o no está."""
    nombre = nombre_del_snapshot(r)
    raw = raiz / RAW
    final, tmp = raw / nombre, raw / f".{nombre}.construyendo"
    if final.exists():
        raise Parada(HALLAZGO, f"{RAW.as_posix()}/{nombre} ya existe, y no se escribe encima de un "
                               "snapshot. Con los mismos datos no habría nada nuevo: algo no cuadra.",
                     r["descargas"])
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir()
    try:
        hashes = {j: _sha(r["descargas"][j]["crudo"]) for j in JUEGOS}
        for j in JUEGOS:
            (tmp / f"{j}.csv").write_bytes(r["descargas"][j]["crudo"])
        (tmp / "SHA256.txt").write_bytes("".join(f"{hashes[j]}  {j}.csv\n" for j in JUEGOS).encode())
        texto = procedencia(nombre, r, tabla, sin_testigo, hashes, _ahora())
        (tmp / "PROCEDENCIA.md").write_bytes(texto.encode("utf-8"))
        for intento in range(5):
            try:
                os.rename(tmp, final)
                break
            except PermissionError:
                # Un sincronizador o un antivirus pueden tener abierto un fichero un instante.
                if intento == 4:
                    raise
                time.sleep(0.5 * (intento + 1))
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    decir(f"== Congelado: {RAW.as_posix()}/{nombre}/")
    for j in JUEGOS:
        decir(f"   {hashes[j]}  {j}.csv")
    return nombre


def cuarentena(raiz, parada):
    """Guarda la descarga de un hallazgo para poder investigarla. No se publica (`.gitignore`)."""
    marca = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    carpeta = raiz / CUARENTENA / marca
    carpeta.mkdir(parents=True, exist_ok=True)
    for j, d in (parada.descargas or {}).items():
        (carpeta / f"{j}.csv").write_bytes(d["crudo"])
    (carpeta / "HALLAZGO.txt").write_text(f"{_ahora()}\n\n{parada}\n", encoding="utf-8")
    return carpeta


# ---------------------------------------------------------------- derivar
def _escribir_json(ruta, doc):
    """Nunca encima de nada, y nunca a medias: a un temporal, y se renombra."""
    if ruta.exists():
        raise FileExistsError(f"{ruta} ya existe")
    tmp = ruta.with_name(ruta.name + ".escribiendo")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1, default=str)
    os.replace(tmp, ruta)


class _SoloCache:
    """La caché permanente de melate-e.com, sin red: un sorteo que no está en ella es un fallo."""

    def __init__(self, cache):
        self.cache = cache

    def tabla(self, juego, sorteo):
        from . import popularity

        ruta = self.cache / juego.lower() / f"{sorteo}.html"
        if not ruta.is_file():
            raise popularity.SorteoNoPublicado(f"{juego} {sorteo}: su página no está en la caché "
                                               "permanente, y al analizar no se pide")
        return popularity.parsear(ruta.read_text(encoding="utf-8"), juego, sorteo)


def derivados(nombre):
    """Lo que el ciclo deriva de un snapshot, con el nombre de su fichero."""
    return {"popularidad": REPORTES / f"{nombre}_popularidad.json",
            "informe": REPORTES / f"{nombre}_informe.json"}


def derivar(raiz, nombre, peticiones=0, decir=print, pasos=("popularidad", "informe", "veredicto",
                                                              "base")):
    """Deriva sobre el snapshot lo que le falte, con rutas relativas a la raíz: estos ficheros se
    publican, y la carpeta de trabajo es la raíz. Devuelve lo que escribió."""
    from . import popularity

    carpeta = str(RAW / nombre)
    rutas, escritos = derivados(nombre), []
    ultimo = int(NOMBRE.match(nombre).group(2))
    decir(f"== Derivados del snapshot {nombre}")

    if "popularidad" in pasos and not (raiz / rutas["popularidad"]).exists():
        from .validate import era_56

        adicionales = popularity.adicionales_oficiales(era_56("Melate", ingest.cargar("Melate", carpeta)))
        ventana = range(ultimo - VENTANA + 1, ultimo + 1)
        lector = _SoloCache(raiz / CACHE)
        reporte = {"ventana": [ventana[0], ventana[-1]], "snapshot": nombre,
                   "juegos": {j: popularity.analizar(j, ventana, descargador=lector,
                                                     adicionales=adicionales) for j in CON_TABLA},
                   "procedencia": {"fuente": popularity.URL, "descargado_utc": _ahora(),
                                   "peticiones_de_red": peticiones, "cache": str(CACHE),
                                   "user_agent": popularity.UA, "pausa_segundos": popularity.PAUSA_SEGUNDOS,
                                   "nota": "Las páginas de los sorteos nuevos se pidieron al validarlos; "
                                           "la ventana se analiza desde la caché, sin red."}}
        _escribir_json(raiz / rutas["popularidad"], reporte)
        escritos.append(rutas["popularidad"])
        for j in CON_TABLA:
            mb = reporte["juegos"][j]["menores_brutos_por_bolsa"] or {}
            decir(f"   {rutas['popularidad'].as_posix()}  {j}: {reporte['juegos'][j]['sorteos_usados']} "
                  f"sorteos, {len(reporte['juegos'][j]['fallos'])} fallos, menores "
                  f"{mb.get('mediana', float('nan')):.4f}")

    if "informe" in pasos and not (raiz / rutas["informe"]).exists():
        from . import informe

        pop = str(rutas["popularidad"]) if (raiz / rutas["popularidad"]).exists() else None
        rep = informe.construir(carpeta, SIMULACIONES, pop)
        _escribir_json(raiz / rutas["informe"], rep)
        escritos.append(rutas["informe"])
        decir(f"   {rutas['informe'].as_posix()}")
        for variante in ("valor_esperado_proximo", "valor_esperado_medido"):
            ev = rep.get(variante) or {}
            if ev.get("Melate"):
                decir(f"     {variante}: " + " · ".join(
                    f"{j} {ev[j]['proximo_sorteo']}: bolsa {ev[j]['bolsa_bruta'] / 1e6:.1f} M, "
                    f"rendimiento {ev[j]['rendimiento']:+.1%}" for j in JUEGOS))

    if "veredicto" in pasos:
        from . import lab

        for p in sorted((raiz / "prereg").glob("*.json")):
            try:
                spec = lab.cargar_preregistro(p)
            except ValueError as e:
                decir(f"   {p.name}: no se evalúa, su sello no verifica ({str(e).splitlines()[0]})")
                continue
            # El id acaba en un nombre de fichero: un `../` escribiría fuera de reportes/.
            if not re.fullmatch(r"[\w.-]+", str(spec["id"])) or ".." in str(spec["id"]):
                decir(f"   {p.name}: no se evalúa, su id {spec['id']!r} no sirve de nombre de fichero")
                continue
            ruta = REPORTES / f"{nombre}_veredicto-{spec['id']}.json"
            if (raiz / ruta).exists():
                continue
            v = lab.evaluar(spec, carpeta=carpeta)
            _escribir_json(raiz / ruta, v)
            escritos.append(ruta)
            ver = v["veredicto"]
            decir(f"   {ruta.as_posix()}  {ver['veredicto']} ({ver['cumplidas']} de {ver['de']}), "
                  f"holdout de {v['resultados']['sorteos_holdout']}, hacen falta "
                  f"{v['resultados'].get('holdout_necesario')}")

    if "base" in pasos:
        from . import almacen

        almacen.construir()
        decir("   melate.duckdb al día")
    return escritos


# ---------------------------------------------------------------- todo
def ejecutar(raiz, comprobar_solo=False, sin_testigo=frozenset(), fuentes=None, derivar_=True,
             decir=print):
    """El ciclo entero. Devuelve un resumen; ante una parada, la deja subir con su código.

    La carpeta de trabajo tiene que ser `raiz`: las rutas que quedan en los reportes son relativas.
    """
    raiz = pathlib.Path(raiz)
    if pathlib.Path.cwd().resolve() != raiz.resolve():
        raise SystemExit(f"El ciclo se corre desde la raíz del repositorio ({raiz.name}): las rutas "
                         "que quedan en los reportes son relativas a ella.")
    fuentes = fuentes or Fuentes(raiz)
    resumen = {"congelado": None, "derivados": [], "peticiones": {}}
    try:
        if not comprobar_solo:
            for resto in (raiz / RAW).glob(".*.construyendo"):
                shutil.rmtree(resto, ignore_errors=True)
        try:
            r = comprobar(raiz, fuentes, decir)
            if r["nuevos"]:
                tabla = testigos(r, fuentes, sin_testigo, pedir=not comprobar_solo, decir=decir)
                if comprobar_solo:
                    decir(f"== Congelaría {RAW.as_posix()}/{nombre_del_snapshot(r)}/. Con --comprobar "
                          "no se escribe nada.")
                else:
                    resumen["congelado"] = congelar(raiz, r, tabla, sin_testigo, decir)
        except Parada as p:
            if p.codigo == HALLAZGO and p.descargas and not comprobar_solo:
                decir(f"La descarga queda en {cuarentena(raiz, p).relative_to(raiz).as_posix()} "
                      "para investigarla.")
            raise
        ultimo = snapshots(raiz)[-1][1]
        if derivar_ and not comprobar_solo and NOMBRE.match(ultimo):
            resumen["derivados"] = derivar(raiz, ultimo, fuentes.paginas.peticiones, decir)
    finally:
        fuentes.paginas.cerrar()
        resumen["peticiones"] = dict(fuentes.peticiones, **{"melate-e": fuentes.paginas.peticiones})
    decir(f"Peticiones de red de esta corrida: oficial {resumen['peticiones']['oficial']}, espejo "
          f"{resumen['peticiones']['espejo']}, melate-e.com {resumen['peticiones']['melate-e']}.")
    if resumen["congelado"] or resumen["derivados"]:
        decir("Nada se ha comiteado ni subido. Ficheros nuevos: "
              + ", ".join([f"{RAW.as_posix()}/{resumen['congelado']}/"] * bool(resumen["congelado"])
                          + [p.as_posix() for p in resumen["derivados"]]))
    return resumen


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="El ciclo vivo: incorpora los sorteos nuevos en un snapshot congelado y validado, "
                    "y deriva sobre él lo que se publica. No comitea ni sube nada.")
    ap.add_argument("--comprobar", action="store_true",
                    help="descarga y valida, y dice qué haría; no escribe nada")
    ap.add_argument("--sin-testigo", action="append", choices=TESTIGOS, default=[],
                    help="sigue sin un testigo que FALTA, nunca sin uno que discrepa; queda escrito")
    a = ap.parse_args(argv)
    from .informe import _salida_robusta

    _salida_robusta()
    os.chdir(RAIZ)
    try:
        return ejecutar(RAIZ, a.comprobar, frozenset(a.sin_testigo))
    except Parada as p:
        print(f"\n{p}")
        sys.exit(p.codigo)


if __name__ == "__main__":
    main()
