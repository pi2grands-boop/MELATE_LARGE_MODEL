"""El ciclo vivo: que congele solo lo que debe, entero y de una vez, y que se pare cuando debe.

Ningún test de este fichero sale a la red. El oficial, el espejo y melate-e.com son falsos, y el único
servidor que se levanta escucha en 127.0.0.1: hace de oficial que falla a mitad, para que el camino
de `requests` también se pruebe. La decisión que esto vigila:
`Documentos_Contexto/Almacenamiento/Decisiones/2026-10-04_20-10_s5-el-ciclo-vivo.md`.

El escenario de casi todos: el snapshot del 2026-10-02 **sin su último sorteo** hace de «snapshot
anterior» (hasta el 4271), y el de verdad hace de «el oficial de hoy» (hasta el 4272). Así el sorteo
nuevo es real, y lo que congele el ciclo tiene que ser, byte a byte, lo que se congeló a mano en la
Fase 1.
"""
import functools
import http.server
import re
import shutil
import threading

import pytest

from melate import ciclo, ingest, popularity
from melate.ciclo import CON_TABLA
from melate.constantes import JUEGOS

from conftest import PREREG_REAL, RAIZ, SNAPSHOT

NUEVO = 4272
NOMBRE_NUEVO = "2026-09-30_4272"


def quitar_primera_fila(crudo):
    cabecera, cuerpo = ciclo._partir(crudo)
    return cabecera + cuerpo[cuerpo.find(b"\n") + 1:]


def editar(crudo, concurso, cambio):
    """Cambia los campos de la línea de un concurso, sin tocar nada más del fichero."""
    lineas = crudo.split(b"\r\n")
    for i, linea in enumerate(lineas):
        campos = linea.split(b",")
        if len(campos) > 1 and campos[1] == str(concurso).encode():
            lineas[i] = b",".join(cambio(campos))
    return b"\r\n".join(lineas)


def de_hoy():
    return {j: (SNAPSHOT / f"{j}.csv").read_bytes() for j in JUEGOS}


@functools.lru_cache(maxsize=None)
def leido(crudo):
    """Los falsos parsean los mismos ficheros en cada test: una vez basta. Quien lo use, que copie."""
    return ingest._normalizar(crudo, "falso")


class Oficial:
    """Un oficial falso: sirve unos bytes por juego, y apunta lo que le piden."""

    def __init__(self, ficheros, last_modified="Sun, 04 Oct 2026 12:00:04 GMT"):
        self.ficheros, self.pedidos, self.last_modified = dict(ficheros), [], last_modified

    def __call__(self, juego):
        self.pedidos.append(juego)
        return {"url": f"https://oficial.test/{juego}.csv", "crudo": self.ficheros[juego],
                "http": 200, "last_modified": self.last_modified,
                "utc": "2026-10-04T12:00:05+00:00"}


class Espejo:
    """Un espejo falso que, por defecto, dice lo mismo que el oficial."""

    def __init__(self, ficheros, sin=(), cambio=None, cae=False):
        self.ficheros, self.sin, self.cambio, self.cae = ficheros, set(sin), cambio, cae

    def __call__(self, juego):
        if self.cae:
            raise OSError("el espejo no responde")
        df = leido(self.ficheros[juego])
        df = df[~df.CONCURSO.isin(self.sin)].reset_index(drop=True).copy()
        if self.cambio:
            df = self.cambio(juego, df)
        return df


def pagina(juego, nums, adicional=None, con_premios=True):
    """Una página de resultado como las de melate-e.com, con su tabla entera."""
    nat = "".join(f'<span class="numnatural"><b>{n}</b></span>' for n in nums)
    adi = f'<span class="numadicional"><b>{adicional}</b></span>' if adicional else ""
    if juego == "Melate":
        cats = ["6 números naturales", "5 números naturales + adicional", "5 números naturales",
                "4 números naturales + adicional", "4 números naturales",
                "3 números naturales y el adicional", "3 números naturales",
                "2 números naturales + adicional", "2 números naturales"]
    else:
        cats = [f"{k} números naturales" for k in (6, 5, 4, 3, 2)]
    filas = "".join(
        f"<tr><td>{i}</td><td>{c}</td><td>{0 if i < 2 else 10 * i}</td>"
        f"<td>{'$0.00' if i < 2 or not con_premios else f'${100 * i}.00'}</td></tr>"
        for i, c in enumerate(cats))
    return (f'<html><body><div id="resultados">{nat}{adi}</div><table><tr><th>Lugar</th>'
            f"<th>Aciertos</th><th>Ganadores</th><th>Premio</th></tr>{filas}</table></body></html>")


class Sitio:
    """melate-e.com falso: páginas hechas con los números del oficial, o con el fallo que se pida."""

    def __init__(self, ficheros, modo=None):
        self.oficial = {j: leido(c).set_index("CONCURSO") for j, c in ficheros.items()}
        self.modo, self.peticiones, self.pedidas = modo, 0, []

    def html(self, juego, sorteo):
        self.peticiones += 1
        self.pedidas.append((juego, sorteo))
        if self.modo == "404":
            raise popularity.SorteoNoPublicado(f"{juego} {sorteo}: 404")
        if self.modo == "bloqueo":
            raise popularity.SitioBloqueado("HTTP 403")
        fila = self.oficial[juego].loc[sorteo]
        nums = list(fila["nums"])
        if self.modo == "discrepa":
            nums[-1] = next(n for n in range(1, 57) if n not in nums)
        adicional = int(fila["R7"]) if fila["R7"] == fila["R7"] else None
        return pagina(juego, nums, adicional, con_premios=self.modo != "incompleta")

    def cerrar(self):
        pass


def fuentes(repo, oficial=None, espejo=None, sitio=None):
    ficheros = de_hoy()
    oficial = oficial or Oficial(ficheros)
    f = ciclo.Fuentes(repo, oficial=oficial, espejo=espejo or Espejo(oficial.ficheros),
                      descargador=sitio or Sitio(oficial.ficheros))
    return f


def preparar(raiz, monkeypatch, quitar=1):
    """Un repositorio de usar y tirar: el snapshot real sin sus `quitar` últimos sorteos como
    snapshot anterior, y la raíz como carpeta de trabajo, que es donde corre el ciclo."""
    ultimo = NUEVO - quitar
    fecha = ingest.cargar("Melate", str(SNAPSHOT)).set_index("CONCURSO").loc[ultimo, "FECHA"]
    previo = raiz / "data" / "raw" / f"{fecha.date().isoformat()}_{ultimo}"
    previo.mkdir(parents=True)
    lineas = []
    for j, crudo in de_hoy().items():
        for _ in range(quitar):
            crudo = quitar_primera_fila(crudo)
        (previo / f"{j}.csv").write_bytes(crudo)
        lineas.append(f"{ciclo._sha(crudo)}  {j}.csv\n")
    (previo / "SHA256.txt").write_text("".join(lineas), encoding="utf-8")
    (raiz / "reportes").mkdir()
    (raiz / "prereg").mkdir()
    shutil.copy2(RAIZ / "prereg" / PREREG_REAL, raiz / "prereg" / PREREG_REAL)
    monkeypatch.chdir(raiz)
    return raiz


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """El escenario de casi todos: el snapshot anterior llega hasta el 4271."""
    return preparar(tmp_path / "repo", monkeypatch)


def carpetas(repo):
    return sorted(p.name for p in (repo / "data" / "raw").iterdir())


def correr(repo, f, **k):
    return ciclo.ejecutar(repo, fuentes=f, derivar_=False, decir=lambda *a: None, **k)


def parada(repo, f, **k):
    with pytest.raises(ciclo.Parada) as e:
        correr(repo, f, **k)
    return e.value


# ---------------------------------------------------------------- el camino bueno
def test_congela_lo_que_sirve_el_oficial_byte_a_byte(repo):
    """El snapshot que congela el ciclo es, byte a byte, el que se congeló a mano en la Fase 1: los
    mismos SHA-256 publicados, y hasta el mismo `SHA256.txt`."""
    sitio = Sitio(de_hoy())
    f = fuentes(repo, sitio=sitio)
    r = correr(repo, f)
    assert r["congelado"] == NOMBRE_NUEVO
    nuevo = repo / "data" / "raw" / NOMBRE_NUEVO
    for j in JUEGOS:
        assert (nuevo / f"{j}.csv").read_bytes() == (SNAPSHOT / f"{j}.csv").read_bytes()
    assert (nuevo / "SHA256.txt").read_bytes() == (SNAPSHOT / "SHA256.txt").read_bytes()
    procedencia = (nuevo / "PROCEDENCIA.md").read_text(encoding="utf-8")
    assert "Sorteos nuevos:** 4272" in procedencia and "2026-09-27_4271" in procedencia
    assert procedencia.count("confirma") == 5, "espejo en tres juegos y melate-e.com en dos"
    assert "no se pide (dictamen)" in procedencia, "Revanchita no se le pide a melate-e.com"
    # Lo que pasó de verdad: de dónde salió y cuándo se descargó, que no es cuándo se congeló.
    assert "`https://oficial.test/{Melate,Revancha,Revanchita}.csv`" in procedencia
    assert "**Descargado:** 2026-10-04T12:00:05+00:00 · **congelado:**" in procedencia
    assert r["peticiones"] == {"oficial": 3, "espejo": 3, "melate-e": 2}
    assert sitio.pedidas == [("Melate", NUEVO), ("Revancha", NUEVO)]
    assert carpetas(repo) == ["2026-09-27_4271", NOMBRE_NUEVO], "y nada a medias"


def test_dos_sorteos_nuevos_de_una_vez(tmp_path, monkeypatch):
    """Si el ciclo no se corre en cada sorteo, el snapshot nuevo trae varios: todos validados, y el
    nombre, el del último."""
    raiz = preparar(tmp_path / "repo", monkeypatch, quitar=2)
    sitio = Sitio(de_hoy())
    r = correr(raiz, fuentes(raiz, sitio=sitio))
    assert r["congelado"] == NOMBRE_NUEVO
    procedencia = (raiz / "data" / "raw" / NOMBRE_NUEVO / "PROCEDENCIA.md").read_text(encoding="utf-8")
    assert "Sorteos nuevos:** 4271, 4272" in procedencia and procedencia.count("confirma") == 10
    assert sorted(sitio.pedidas) == [(j, c) for j in CON_TABLA for c in (NUEVO - 1, NUEVO)]


def test_lo_que_dice_el_servidor_no_rompe_la_procedencia(repo):
    """La cabecera `Last-Modified` viene de fuera y acaba en un fichero que se publica: ni una barra
    que parta la tabla, ni una comilla invertida, ni una etiqueta."""
    oficial = Oficial(de_hoy(), last_modified="Sun | `x` <script>alert(1)</script>")
    r = correr(repo, fuentes(repo, oficial=oficial))
    procedencia = (repo / "data" / "raw" / r["congelado"] / "PROCEDENCIA.md").read_text(encoding="utf-8")
    assert "<script>" not in procedencia and "`x`" not in procedencia
    filas = [l for l in procedencia.splitlines() if l.startswith("| `") and ".csv` |" in l]
    assert len(filas) == 3 and all(f.count("|") == 7 for f in filas), filas


def test_nada_nuevo_no_escribe_nada_ni_pregunta_a_los_testigos(repo):
    anterior = repo / "data" / "raw" / "2026-09-27_4271"
    f = fuentes(repo, oficial=Oficial({j: (anterior / f"{j}.csv").read_bytes() for j in JUEGOS}))
    r = correr(repo, f)
    assert r["congelado"] is None and carpetas(repo) == ["2026-09-27_4271"]
    assert r["peticiones"] == {"oficial": 3, "espejo": 0, "melate-e": 0}


# ---------------------------------------------------------------- el oficial
@pytest.fixture
def servidor(tmp_path, monkeypatch):
    """Un oficial de verdad, HTTP, en 127.0.0.1: sirve los ficheros de hoy, y falla donde se le pida."""
    www, fallos = tmp_path / "www", {}
    www.mkdir()
    for j, crudo in de_hoy().items():
        (www / f"{j}.csv").write_bytes(crudo)

    class Manejador(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=str(www), **k)

        def do_GET(self):
            nombre = self.path.lstrip("/")
            if nombre in fallos:
                codigo, cuerpo = fallos[nombre]
                self.send_response(codigo)
                self.end_headers()
                self.wfile.write(cuerpo)
                return
            super().do_GET()

        def log_message(self, *a):
            pass

    for variable in ("NO_PROXY", "no_proxy"):
        monkeypatch.setenv(variable, "127.0.0.1,localhost")
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Manejador)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield fallos, f"http://127.0.0.1:{srv.server_address[1]}/{{}}.csv"
    srv.shutdown()
    srv.server_close()


@pytest.mark.parametrize("codigo,cuerpo", [(500, b"Internal Server Error"),
                                           (200, b"<html>Mantenimiento</html>")])
def test_si_el_oficial_falla_a_mitad_no_queda_nada(repo, servidor, codigo, cuerpo):
    """El pendiente heredado nº 3, contestado: Melate llega, Revancha no —un 500, o una página de
    mantenimiento con un 200—, y no se ha escrito nada, porque nada se escribe antes de tener los tres."""
    fallos, plantilla = servidor
    fallos["Revancha.csv"] = (codigo, cuerpo)
    f = ciclo.Fuentes(repo, oficial=lambda j: ciclo.descargar_oficial(j, plantilla),
                      espejo=Espejo(de_hoy()), descargador=Sitio(de_hoy()))
    p = parada(repo, f)
    assert p.codigo == ciclo.FUENTE_CAIDA and "Revancha" in str(p)
    assert carpetas(repo) == ["2026-09-27_4271"]
    assert not (repo / "data" / "cuarentena").exists()
    assert f.peticiones["oficial"] == 2, "se para en el que falla"


def test_por_el_servidor_de_verdad_tambien_congela(repo, servidor):
    """El camino de `requests`, entero, contra un servidor que responde bien."""
    _, plantilla = servidor
    f = ciclo.Fuentes(repo, oficial=lambda j: ciclo.descargar_oficial(j, plantilla),
                      espejo=Espejo(de_hoy()), descargador=Sitio(de_hoy()))
    assert correr(repo, f)["congelado"] == NOMBRE_NUEVO


def test_el_pasado_cambiado_es_un_hallazgo_y_va_a_cuarentena(repo):
    hoy = de_hoy()
    hoy["Revancha"] = editar(hoy["Revancha"], 4000, lambda c: c[:-2] + [b"99999999", c[-1]])
    p = parada(repo, fuentes(repo, oficial=Oficial(hoy)))
    assert p.codigo == ciclo.HALLAZGO and "El pasado cambió en Revancha" in str(p)
    assert carpetas(repo) == ["2026-09-27_4271"]
    (cuarentena,) = (repo / "data" / "cuarentena").iterdir()
    assert (cuarentena / "Revancha.csv").read_bytes() == hoy["Revancha"], "la evidencia, tal cual"
    assert "El pasado cambió" in (cuarentena / "HALLAZGO.txt").read_text(encoding="utf-8")


def test_un_oficial_a_medio_actualizar_hace_esperar(repo):
    anterior = repo / "data" / "raw" / "2026-09-27_4271"
    hoy = de_hoy()
    for j in ("Revancha", "Revanchita"):
        hoy[j] = (anterior / f"{j}.csv").read_bytes()
    p = parada(repo, fuentes(repo, oficial=Oficial(hoy)))
    assert p.codigo == ciclo.ESPERAR and "a medio actualizar" in str(p)
    assert carpetas(repo) == ["2026-09-27_4271"]


@pytest.mark.parametrize("cambio,motivo", [
    (lambda c: c[:9] + [b"1000000"] + c[10:], "por debajo de la mínima"),
    (lambda c: c[:2] + [c[2], c[2]] + c[4:], "filas_no_ordenadas_o_repetidas"),
])
def test_un_sorteo_nuevo_que_no_es_valido_es_un_hallazgo(repo, cambio, motivo):
    """Una BOLSA por debajo de la mínima, o un número repetido, en la fila nueva de Melate."""
    hoy = de_hoy()
    hoy["Melate"] = editar(hoy["Melate"], NUEVO, cambio)
    p = parada(repo, fuentes(repo, oficial=Oficial(hoy)))
    assert p.codigo == ciclo.HALLAZGO and motivo in str(p), str(p)
    assert carpetas(repo) == ["2026-09-27_4271"]


def _en(juego, cambio):
    """El cambio, en la fila nueva de un juego."""
    return lambda hoy: {**hoy, juego: editar(hoy[juego], NUEVO, cambio)}


def _en_los_tres(cambio):
    return lambda hoy: {j: editar(c, NUEVO, cambio) for j, c in hoy.items()}


def _otra_linea(juegos, cual):
    """Una línea más justo después de la cabecera: la fila nueva otra vez, o la más vieja del fichero."""
    def cambio(hoy):
        hoy = dict(hoy)
        for j in juegos:
            lineas = hoy[j].split(b"\r\n")
            otra = lineas[1] if cual == "la nueva" else [l for l in lineas if l.strip()][-1]
            hoy[j] = b"\r\n".join([lineas[0], otra, *lineas[1:]])
        return hoy
    return cambio


@pytest.mark.parametrize("cambio,motivo", [
    (_en("Melate", lambda c: c[:9] + [b""] + c[10:]), "Melate: BOLSA inválida en"),
    (_en_los_tres(lambda c: c[:-1] + [b"01/09/2026"]), "no van después de 2026-09-27"),
    (_en("Revancha", lambda c: c[:-1] + [b"01/10/2026"]), "no dan las mismas fechas"),
    (_otra_linea(["Revancha"], "la más vieja"), "Revancha: 2 líneas nuevas"),
    (_en_los_tres(lambda c: c[:1] + [b"4273"] + c[2:]), "concursos_faltantes = [4272]"),
    (_otra_linea(JUEGOS, "la nueva"), "duplicados = 1"),
    (_en("Melate", lambda c: c[:2] + [b"0"] + c[3:]), "fuera_de_rango = 1"),
    (_en("Melate", lambda c: c[:8] + [c[2]] + c[9:]), "adicional_repetido_en_naturales = 1"),
], ids=["bolsa-vacia", "fecha-de-antes", "fechas-distintas", "linea-de-mas", "concurso-que-falta",
        "duplicado", "fuera-de-rango", "adicional-en-los-naturales"])
def test_cada_comprobacion_de_las_filas_nuevas_caza_lo_suyo(repo, cambio, motivo):
    """Un caso por comprobación, que solo ella ve: si se quitara, el ciclo congelaría. Una BOLSA vacía
    no es menor que la mínima —NaN no es menor que nada— y la caza la de las BOLSA inválidas; una
    línea de más que repite una fila de antes de la era 6/56 solo la ve la cuenta de líneas."""
    p = parada(repo, fuentes(repo, oficial=Oficial(cambio(de_hoy()))))
    assert p.codigo == ciclo.HALLAZGO and motivo in str(p), str(p)
    assert carpetas(repo) == ["2026-09-27_4271"]


@pytest.mark.parametrize("cambio", [lambda c: c[:2] + [b"x"] + c[3:], lambda c: c[:-1] + [b"31/02/2026"],
                                    lambda c: c[:7] + [b"57"] + c[8:]],
                         ids=["un-numero-que-no-es-numero", "una-fecha-que-no-existe", "un-57"])
def test_un_csv_que_no_se_deja_leer_es_un_hallazgo_y_no_una_traza(repo, cambio):
    """Una fila nueva ilegible es una fila nueva que no es válida: el ciclo se para como hallazgo y la
    descarga queda en la cuarentena para investigarla. Antes salía con una traza y sin evidencia. El 57
    no llega a la comprobación de rango: lo para antes el `assert` de `validate.era_56`, que viene de
    la línea base y no se toca (un 0 sí llega, y está arriba)."""
    hoy = de_hoy()
    hoy["Melate"] = editar(hoy["Melate"], NUEVO, cambio)
    # El sitio falso lee sus CSV al crearse: con los de hoy, porque al sitio no se llega.
    p = parada(repo, fuentes(repo, oficial=Oficial(hoy), sitio=Sitio(de_hoy())))
    assert p.codigo == ciclo.HALLAZGO and "El Melate.csv del oficial no se deja leer" in str(p), str(p)
    assert carpetas(repo) == ["2026-09-27_4271"]
    (cuarentena,) = (repo / "data" / "cuarentena").iterdir()
    assert (cuarentena / "Melate.csv").read_bytes() == hoy["Melate"], "la evidencia, tal cual"


# ---------------------------------------------------------------- los testigos (C2.2)
def _espejo_que_discrepa(juego, df):
    if juego == "Revanchita":
        df.loc[df.CONCURSO == NUEVO, "BOLSA"] = 1.0
    return df


@pytest.mark.parametrize("sin_testigo", [frozenset(), frozenset({"espejo", "melate-e"})])
def test_un_espejo_que_discrepa_para_el_ciclo_con_o_sin_opciones(repo, sin_testigo):
    """Ninguna opción salta un desacuerdo: con `--sin-testigo espejo` el espejo se consulta igual."""
    f = fuentes(repo, espejo=Espejo(de_hoy(), cambio=_espejo_que_discrepa))
    p = parada(repo, f, sin_testigo=sin_testigo)
    assert p.codigo == ciclo.HALLAZGO and "Revanchita, espejo: discrepa en BOLSA" in str(p)
    assert carpetas(repo) == ["2026-09-27_4271"]


def test_una_pagina_que_discrepa_para_el_ciclo_y_no_se_salta_despues(repo):
    """El sitio da otro número para el 4272. La página queda en caché; una segunda corrida con
    `--sin-testigo melate-e` no la vuelve a pedir, pero la compara, y se para igual."""
    p = parada(repo, fuentes(repo, sitio=Sitio(de_hoy(), "discrepa")))
    assert p.codigo == ciclo.HALLAZGO and "melate-e: discrepa en números" in str(p)
    otra = Sitio(de_hoy())
    p2 = parada(repo, fuentes(repo, sitio=otra), sin_testigo=frozenset({"melate-e"}))
    assert p2.codigo == ciclo.HALLAZGO and otra.peticiones == 0
    assert carpetas(repo) == ["2026-09-27_4271"]


@pytest.mark.parametrize("testigo,f_args", [
    ("espejo", {"espejo": "sin"}),
    ("espejo", {"espejo": "cae"}),
    ("melate-e", {"sitio": "404"}),
])
def test_un_testigo_que_falta_hace_esperar_y_seguir_sin_el_queda_escrito(repo, testigo, f_args):
    hoy = de_hoy()
    espejo = (Espejo(hoy, sin=[NUEVO]) if f_args.get("espejo") == "sin"
              else Espejo(hoy, cae=True) if f_args.get("espejo") == "cae" else Espejo(hoy))
    sitio = Sitio(hoy, f_args.get("sitio"))
    p = parada(repo, fuentes(repo, espejo=espejo, sitio=sitio))
    assert p.codigo == ciclo.ESPERAR and f"--sin-testigo {testigo}" in str(p)
    assert carpetas(repo) == ["2026-09-27_4271"]
    r = correr(repo, fuentes(repo, espejo=espejo, sitio=Sitio(hoy, f_args.get("sitio"))),
               sin_testigo=frozenset({testigo}))
    procedencia = (repo / "data" / "raw" / r["congelado"] / "PROCEDENCIA.md").read_text(encoding="utf-8")
    assert f"`--sin-testigo {testigo}`" in procedencia and "falta" in procedencia


def test_un_bloqueo_de_melate_e_para_y_pregunta(repo):
    p = parada(repo, fuentes(repo, sitio=Sitio(de_hoy(), "bloqueo")))
    assert p.codigo == ciclo.BLOQUEO and "se pregunta" in str(p)
    assert carpetas(repo) == ["2026-09-27_4271"]


@pytest.mark.parametrize("html,motivo", [
    ("<html><body><table><tr><td>Resultados en proceso</td></tr></table></body></html>",
     "falta: la página trae 0 números, no 6"),
    ('<html><body><span class="numnatural"><b>-</b></span><table></table></body></html>',
     "falta: la página no se deja leer"),
], ids=["sin-numeros", "un-guion-donde-va-un-numero"])
def test_una_pagina_sin_sus_seis_numeros_no_discrepa_falta(repo, html, motivo):
    """C2.2: solo una lectura entera contradice al oficial. Una página que aún no trae los números, o
    que trae un guion donde va uno, no dice nada: el testigo falta y el ciclo espera. Antes una era
    «discrepa» —un hallazgo que ninguna opción salta— y la otra, una traza. Como la página ya está en
    caché y no se vuelve a pedir, seguir sin ella es explícito y queda escrito."""
    class SitioAMedias(Sitio):
        def html(self, juego, sorteo):
            self.peticiones += 1
            return html

    p = parada(repo, fuentes(repo, sitio=SitioAMedias(de_hoy())))
    assert p.codigo == ciclo.ESPERAR and "--sin-testigo melate-e" in str(p), str(p)
    otra = SitioAMedias(de_hoy())
    r = correr(repo, fuentes(repo, sitio=otra), sin_testigo=frozenset({"melate-e"}))
    assert otra.peticiones == 0, "ya está en caché: no se vuelve a pedir"
    procedencia = (repo / "data" / "raw" / r["congelado"] / "PROCEDENCIA.md").read_text(encoding="utf-8")
    assert motivo in procedencia and "`--sin-testigo melate-e`" in procedencia


def test_una_pagina_sin_premios_no_entra_en_la_cache_permanente(repo):
    """H5 del inventario: sus números confirman igual, pero la popularidad no la lee, y nunca se pide
    dos veces."""
    r = correr(repo, fuentes(repo, sitio=Sitio(de_hoy(), "incompleta")))
    assert r["congelado"] == NOMBRE_NUEVO
    assert not (repo / "data" / "cache" / "melate-e" / "melate" / f"{NUEVO}.html").exists()
    assert (repo / "data" / "cache" / "melate-e-incompletas" / "melate" / f"{NUEVO}.html").is_file()
    otra = Sitio(de_hoy())
    pag = ciclo.Paginas(repo, otra)
    pag.html("Melate", NUEVO)
    assert otra.peticiones == 0, "una página incompleta no se vuelve a pedir"


def test_una_pagina_completa_si_entra_en_la_cache_permanente(repo):
    correr(repo, fuentes(repo))
    assert (repo / "data" / "cache" / "melate-e" / "melate" / f"{NUEVO}.html").is_file()
    assert not (repo / "data" / "cache" / "melate-e-incompletas" / "melate" / f"{NUEVO}.html").exists()


# ---------------------------------------------------------------- nunca encima, nunca a medias
def test_nunca_escribe_encima_de_un_snapshot(repo):
    ocupada = repo / "data" / "raw" / NOMBRE_NUEVO
    ocupada.mkdir()
    (ocupada / "nota.txt").write_text("no me toques", encoding="utf-8")
    p = parada(repo, fuentes(repo))
    assert p.codigo == ciclo.HALLAZGO and "ya existe" in str(p)
    assert sorted(x.name for x in ocupada.iterdir()) == ["nota.txt"]


def test_un_renombrado_que_falla_no_deja_nada_a_medias(repo, monkeypatch):
    """Un bloqueo que no se va: cinco intentos, con esperas que crecen, y ni el snapshot ni la carpeta
    temporal. Y lo que dejó una corrida interrumpida, lo limpia la siguiente."""
    resto = repo / "data" / "raw" / ".2026-09-30_4272.construyendo"
    resto.mkdir()
    (resto / "Melate.csv").write_bytes(b"a medias")
    intentos, esperas = [], []

    def falla(*a, **k):
        intentos.append(a)
        raise PermissionError("abierto por otro proceso")

    monkeypatch.setattr(ciclo.time, "sleep", esperas.append)
    monkeypatch.setattr(ciclo.os, "rename", falla)
    with pytest.raises(PermissionError):
        correr(repo, fuentes(repo))
    assert len(intentos) == 5 and esperas == [0.5, 1.0, 1.5, 2.0]
    assert carpetas(repo) == ["2026-09-27_4271"], "ni el snapshot ni la carpeta temporal"


def test_un_renombrado_bloqueado_un_instante_se_reintenta_y_congela(repo, monkeypatch):
    """La razón del reintento: un sincronizador o un antivirus con un fichero abierto un instante. El
    segundo intento congela, y no queda la carpeta temporal."""
    renombrar, intentos, esperas = ciclo.os.rename, [], []

    def una_vez(*a, **k):
        intentos.append(a)
        if len(intentos) == 1:
            raise PermissionError("abierto un instante")
        return renombrar(*a, **k)

    monkeypatch.setattr(ciclo.time, "sleep", esperas.append)
    monkeypatch.setattr(ciclo.os, "rename", una_vez)
    assert correr(repo, fuentes(repo))["congelado"] == NOMBRE_NUEVO
    assert len(intentos) == 2 and esperas == [0.5]
    assert carpetas(repo) == ["2026-09-27_4271", NOMBRE_NUEVO]


def test_comprobar_no_escribe_nada(repo):
    """Ni el snapshot, ni la caché del sitio, ni la cuarentena: dice qué haría, y nada más."""
    sitio = Sitio(de_hoy())
    r = correr(repo, fuentes(repo, sitio=sitio), comprobar_solo=True)
    assert r["congelado"] is None and carpetas(repo) == ["2026-09-27_4271"]
    assert sitio.peticiones == 0 and not (repo / "data" / "cache").exists()
    hoy = de_hoy()
    hoy["Melate"] = editar(hoy["Melate"], 4000, lambda c: c[:-2] + [b"1", c[-1]])
    p = parada(repo, fuentes(repo, oficial=Oficial(hoy)), comprobar_solo=True)
    assert p.codigo == ciclo.HALLAZGO and not (repo / "data" / "cuarentena").exists()


@pytest.mark.parametrize("codigo", [ciclo.HALLAZGO, ciclo.ESPERAR, ciclo.FUENTE_CAIDA, ciclo.BLOQUEO])
def test_la_orden_sale_con_el_codigo_de_la_parada(repo, monkeypatch, capsys, codigo):
    """Los códigos de salida de la decisión: quien lance el ciclo desde un script tiene que poder
    distinguir esperar de un hallazgo."""
    def para(*a, **k):
        raise ciclo.Parada(codigo, "motivo de la parada")

    monkeypatch.setattr(ciclo, "ejecutar", para)
    monkeypatch.setattr(ciclo, "RAIZ", repo)
    with pytest.raises(SystemExit) as e:
        ciclo.main([])
    assert e.value.code == codigo and "motivo de la parada" in capsys.readouterr().out


def test_el_ciclo_se_corre_desde_la_raiz(repo, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit, match="raíz del repositorio"):
        correr(repo, fuentes(repo))


# ---------------------------------------------------------------- lo derivado
def test_lo_derivado_dice_de_que_snapshot_sale_y_no_se_escribe_dos_veces(repo):
    """La popularidad, el veredicto y la base, sobre el snapshot nuevo. El informe, que tarda dos
    minutos, tiene su propio test lento."""
    correr(repo, fuentes(repo))
    pasos = ("popularidad", "veredicto", "base")
    escritos = ciclo.derivar(repo, NOMBRE_NUEVO, 2, decir=lambda *a: None, pasos=pasos)
    veredicto = f"reportes/{NOMBRE_NUEVO}_veredicto-2026-10-03_logistica-revancha.json"
    assert sorted(p.as_posix() for p in escritos) == sorted(
        [f"reportes/{NOMBRE_NUEVO}_popularidad.json", veredicto])
    import json

    v = json.loads((repo / veredicto).read_text(encoding="utf-8"))
    publicados = dict(reversed(l.split()) for l in (SNAPSHOT / "SHA256.txt").read_text().splitlines())
    assert {j: d["sha256"] for j, d in v["datos"].items()} == {j: publicados[f"{j}.csv"] for j in JUEGOS}
    assert v["datos"]["Melate"]["origen"].replace("\\", "/") == f"data/raw/{NOMBRE_NUEVO}/Melate.csv"
    pop = json.loads((repo / f"reportes/{NOMBRE_NUEVO}_popularidad.json").read_text(encoding="utf-8"))
    assert pop["ventana"] == [NUEVO - 99, NUEVO] and pop["procedencia"]["peticiones_de_red"] == 2
    assert (repo / "melate.duckdb").is_file()
    assert ciclo.derivar(repo, NOMBRE_NUEVO, decir=lambda *a: None, pasos=pasos) == []
    with pytest.raises(FileExistsError):
        ciclo._escribir_json(repo / veredicto, {})


@pytest.mark.parametrize("ventana", [100, 10])
def test_la_ventana_de_la_popularidad_la_gobierna_ventana(repo, monkeypatch, ventana):
    """Dos valores de `VENTANA`: se analiza la ventana que dice, no una escrita a mano. Con 100 es la
    de la popularidad publicada."""
    import json

    correr(repo, fuentes(repo))
    monkeypatch.setattr(ciclo, "VENTANA", ventana)
    ciclo.derivar(repo, NOMBRE_NUEVO, decir=lambda *a: None, pasos=("popularidad",))
    pop = json.loads((repo / f"reportes/{NOMBRE_NUEVO}_popularidad.json").read_text(encoding="utf-8"))
    assert pop["ventana"] == [NUEVO - ventana + 1, NUEVO]
    assert {j: pop["juegos"][j]["sorteos_pedidos"] for j in CON_TABLA} == {j: ventana for j in CON_TABLA}


@pytest.mark.parametrize("simulaciones", [None, 7])
def test_las_simulaciones_del_informe_las_gobierna_simulaciones(repo, monkeypatch, simulaciones):
    """Dos valores de `SIMULACIONES`: sin tocar, las 2 000 de los informes publicados; cambiado, el
    cambiado. El informe de verdad tarda dos minutos, y su valor esperado no depende de esto —por eso
    el test lento no lo vigilaba—: aquí se mira qué se le pide."""
    from melate import informe

    correr(repo, fuentes(repo))
    if simulaciones:
        monkeypatch.setattr(ciclo, "SIMULACIONES", simulaciones)
    pedidos = []
    monkeypatch.setattr(informe, "construir", lambda *a: pedidos.append(a) or {})
    ciclo.derivar(repo, NOMBRE_NUEVO, decir=lambda *a: None, pasos=("informe",))
    assert pedidos == [(str(ciclo.RAW / NOMBRE_NUEVO), simulaciones or 2000, None)]


def test_un_id_de_preregistro_no_escribe_fuera_de_reportes(repo):
    """El id del preregistro acaba en el nombre del fichero del veredicto. Uno con `../` se salta,
    con su motivo, y no escribe nada fuera de `reportes/`."""
    import json

    from melate import lab

    spec = json.loads((repo / "prereg" / PREREG_REAL).read_text(encoding="utf-8"))
    spec = {k: v for k, v in spec.items() if k != lab.CLAVE_HASH}
    spec["id"] = "../fuera"
    spec[lab.CLAVE_HASH] = lab.hash_preregistro(spec)
    (repo / "prereg" / "malo.json").write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
    correr(repo, fuentes(repo))
    dicho = []
    escritos = ciclo.derivar(repo, NOMBRE_NUEVO, decir=dicho.append, pasos=("veredicto",))
    assert [p.name for p in escritos] == [f"{NOMBRE_NUEVO}_veredicto-2026-10-03_logistica-revancha.json"]
    assert not list(repo.glob("*fuera*.json")) and not list(repo.parent.glob("*fuera*.json"))
    assert any("no sirve de nombre de fichero" in d for d in dicho), dicho


def test_ninguna_ruta_de_la_maquina_en_lo_que_escribe_el_ciclo(repo):
    """Lo que escribe el ciclo se publica: ni la carpeta del repositorio ni un directorio de usuario,
    en ningún fichero."""
    correr(repo, fuentes(repo))
    ciclo.derivar(repo, NOMBRE_NUEVO, 2, decir=lambda *a: None, pasos=("popularidad", "veredicto"))
    patron = re.compile(r"(?<![A-Za-z])[A-Za-z]:[\\/]|[\\/]Users[\\/]|/home/")
    escritos = [*(repo / "data" / "raw" / NOMBRE_NUEVO).iterdir(), *(repo / "reportes").iterdir()]
    assert len(escritos) == 7, [f.name for f in escritos]
    absolutas = {str(repo), repo.as_posix(), str(repo).replace("\\", "\\\\")}
    for f in escritos:
        texto = f.read_text(encoding="utf-8", errors="replace")
        assert not patron.search(texto), f.name
        assert not any(a in texto for a in absolutas), f.name


@pytest.mark.lento
def test_el_informe_del_ciclo_reproduce_el_valor_esperado_publicado(repo):
    """Sobre los mismos bytes, el informe que deriva el ciclo da el valor esperado del 4273 que se
    publicó en la Fase 1: la bolsa de la fila del 4272 y el mismo rendimiento."""
    import json

    correr(repo, fuentes(repo))
    ciclo.derivar(repo, NOMBRE_NUEVO, decir=lambda *a: None, pasos=("informe",))
    rep = json.loads((repo / f"reportes/{NOMBRE_NUEVO}_informe.json").read_text(encoding="utf-8"))
    publicado = json.loads((RAIZ / "reportes" / "2026-10-02_paquete.json").read_text(encoding="utf-8"))
    for j in JUEGOS:
        assert rep["valor_esperado_proximo"][j] == publicado["valor_esperado_proximo"][j], j
    assert rep["reproducibilidad"]["datos"]["Melate"]["sha256"] == \
        publicado["reproducibilidad"]["datos"]["Melate"]["sha256"]
