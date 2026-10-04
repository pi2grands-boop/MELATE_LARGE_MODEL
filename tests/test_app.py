"""La app: que enseñe lo que hay, que diga siempre el veredicto, y que no pueda mentir.

`streamlit.testing.v1.AppTest` ejecuta `app/streamlit_app.py` sin servidor ni navegador y deja ver
qué elementos pintó. Lo que de verdad se prueba aquí es lo que la app **no** puede hacer: enseñar una
pantalla sin "sin ventaja demostrada", presentar una q exploratoria como veredicto, aceptar un sello
roto, recalcular, salir a la red o arrancar escuchando fuera de esta máquina.

Lo que esto NO prueba, y se declara: cómo se ve. `AppTest` da el árbol de elementos, no píxeles.
"""
import ast
import importlib.util
import socket
import tomllib

import pytest

from conftest import FECHA_MALICIOSA
from melate.protocolo import SIN_VENTAJA

APP = "app/streamlit_app.py"
PANTALLAS = ["veredicto", "exploracion", "valor-esperado", "jugadores", "procedencia"]


@pytest.fixture(scope="module", autouse=True)
def sin_buscar_componentes():
    """Cada `AppTest` nueva recorre los metadatos de los 69 paquetes instalados buscando
    componentes personalizados de Streamlit: ~0,3 s por instancia, la mayor parte de su coste, y la
    app no usa ninguno. Se les ahorra a los tests; la app real no se toca. Si un día usara uno, estos
    tests no lo encontrarían y fallarían a la vista."""
    from streamlit.components.v2 import manifest_scanner

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(manifest_scanner, "scan_component_manifests", lambda: [])
        yield


@pytest.fixture(scope="module")
def modulo(raiz):
    """El fichero de la app como módulo, sin ejecutar `main()`: para sus funciones puras."""
    spec = importlib.util.spec_from_file_location("streamlit_app", raiz / APP)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture
def red():
    """La configuración de red que la app exige, puesta a mano: así el test no depende de la
    carpeta desde la que se lance pytest. Devuelve cómo cambiarla."""
    from streamlit import config

    previas = {k: config.get_option(k) for k in ("server.address", "browser.gatherUsageStats")}

    def poner(direccion="127.0.0.1", telemetria=False):
        config.set_option("server.address", direccion)
        config.set_option("browser.gatherUsageStats", telemetria)

    poner()
    yield poner
    for k, v in previas.items():
        config.set_option(k, v)


def correr(raiz, base, monkeypatch, pantalla=None, url=None):
    from streamlit.testing.v1 import AppTest

    monkeypatch.setenv("MELATE_DUCKDB", str(base))
    at = AppTest.from_file(str(raiz / APP), default_timeout=30)
    if url:
        at.query_params["pantalla"] = url
    at.run()
    if pantalla:
        ir(at, pantalla)
    assert not at.exception, [e.value for e in at.exception]
    return at


def ir(at, pantalla):
    at.sidebar.radio[0].set_value(pantalla).run()
    assert not at.exception, (pantalla, [e.value for e in at.exception])
    assert at.sidebar.radio[0].value == pantalla
    return at


def textos(at):
    """Todo el texto que la app pintó, incluidas las celdas de las tablas."""
    partes = []
    for tipo in ("title", "header", "subheader", "markdown", "caption", "info", "warning", "error",
                 "code", "text"):
        partes += [str(e.value) for e in getattr(at, tipo)]
    partes += [str(m.label) + " " + str(m.value) for m in at.metric]
    partes += [df.value.to_string() for df in at.dataframe]
    return "\n".join(partes)


# ---------------------------------------------------------------- la app real, entera
def test_el_recorrido_completo_de_la_app_real(raiz, base_real, monkeypatch, red, modulo):
    """Las cinco pantallas, una tras otra, con el cómputo y la red convertidos en excepciones.

    Tres propiedades en un solo recorrido, porque las tres se miran en las mismas pantallas:

    1. **Cada pantalla dice "sin ventaja demostrada"**, de dónde sale y sobre qué datos.
    2. **La frontera:** la pantalla que juzga no tiene al lado ninguna cifra de la exploración; la
       exploración lleva su aviso delante y no dice nunca VENTAJA DEMOSTRADA.
    3. **No recalcula ni sale a la red.** La red se corta a nivel de socket dejando pasar loopback:
       el bucle de asyncio de Windows se conecta consigo mismo por 127.0.0.1 para despertarse, y eso
       no es salir de la máquina.
    """
    import requests

    from melate import audit, backtest, informe, ingest, lab, popularity, portfolio

    def prohibido(*a, **k):
        raise AssertionError("la app no recalcula ni sale a la red")

    for mod, nombre in ((backtest, "backtest"), (audit, "auditar"), (lab, "evaluar"),
                        (informe, "construir"), (ingest, "cargar"), (portfolio, "cartera"),
                        (popularity.Descargador, "html"), (requests, "get")):
        monkeypatch.setattr(mod, nombre, prohibido)
    fuera = []
    original = socket.socket.connect

    def solo_esta_maquina(self, direccion, *a, **k):
        if direccion[0] not in ("127.0.0.1", "::1", "localhost"):
            fuera.append(direccion)
            raise AssertionError(f"la app intentó conectar con {direccion}")
        return original(self, direccion, *a, **k)

    monkeypatch.setattr(socket.socket, "connect", solo_esta_maquina)

    at = correr(raiz, base_real, monkeypatch)
    assert list(at.sidebar.radio[0].options) == [modulo.PANTALLAS[p] for p in PANTALLAS]
    for p in PANTALLAS:
        ir(at, p)
        cabecera = at.info[0].value
        assert SIN_VENTAJA in cabecera, (p, cabecera)
        assert "melate.lab" in cabecera, (p, "la cabecera dice de dónde sale el veredicto")
        assert "4272" in cabecera, (p, "y sobre qué datos se emitió")
        texto = textos(at)
        if p == "veredicto":
            for exploratoria in ("0.0165", "0.306", "0.6839", "0.3465"):
                assert exploratoria not in texto, ("la pantalla que juzga", exploratoria)
        if p == "exploracion":
            assert at.warning[0].value == modulo.AVISO_EXPLORA
            assert "0.0165" in texto, "la exploración sí enseña sus p"
        assert "VENTAJA DEMOSTRADA" not in texto, p
    assert fuera == []


# ---------------------------------------------------------------- la frontera, forzada
def test_una_q_exploratoria_bajo_el_umbral_es_una_candidata_y_no_una_ventaja(
        raiz, base_forjada, monkeypatch, red):
    """El informe forjado, con q = 0.01, es el más reciente y sale por defecto. Y la base trae
    además un veredicto incoherente que proclama la ventaja: tampoco llega a la cabecera."""
    at = correr(raiz, base_forjada, monkeypatch, "exploracion")
    assert SIN_VENTAJA in at.info[0].value, "la cabecera no se mueve"
    avisos = " ".join(w.value for w in at.warning)
    assert "no es una ventaja" in avisos and "candidata a preregistrar" in avisos
    assert "VENTAJA DEMOSTRADA" not in textos(at)
    ir(at, "veredicto")
    texto = textos(at)
    assert "incoherente" in texto, "el veredicto que no vale se ve, con su motivo"
    # La base trae también un veredicto más reciente con menos datos. La cabecera y la pantalla
    # tienen que enseñar el mismo, el que juzgó con más: con dos reglas, podían discrepar.
    assert "sorteo 4272" in at.info[0].value
    assert "`reportes/2026-10-04_veredicto.json`" in texto


def test_un_sello_roto_no_llega_a_la_cabecera(raiz, base_sello_roto, monkeypatch, red):
    """Y el veredicto huérfano de esa base tampoco: se enseña aparte, como lo que es."""
    at = correr(raiz, base_sello_roto, monkeypatch, "veredicto")
    assert "por defecto" in at.info[0].value and SIN_VENTAJA in at.info[0].value
    errores = " ".join(e.value for e in at.error)
    assert "no verifica" in errores
    assert "no está en `prereg/`" in errores and "otra-hipotesis" in textos(at)


def test_el_camino_afirmativo_llega_a_la_cabecera(raiz, base_con_ventaja, monkeypatch, red):
    """Si el laboratorio dijera que sí con un sello que verifica, la cabecera lo diría. Una
    cabecera incapaz de cambiar no se distinguiría de una escrita a mano.

    Y lo que viene del fichero llega escapado: la fecha de datos de ese veredicto es una imagen en
    Markdown, que sin escapar haría al navegador pedir una URL de fuera."""
    at = correr(raiz, base_con_ventaja, monkeypatch, "jugadores")
    cabecera = at.info[0].value
    assert "VENTAJA DEMOSTRADA" in cabecera
    assert FECHA_MALICIOSA not in cabecera and r"\!\[x\]\(http" in cabecera


def test_reconstruir_la_base_cambia_lo_que_ensena(raiz, base_real, base_con_ventaja, tmp_path,
                                                 monkeypatch, red):
    """La caché de la app está atada a la fecha y el tamaño del fichero. Si no lo estuviera, la app
    seguiría enseñando la base vieja después de reconstruirla. Dos bases en la misma ruta, dos
    cabeceras."""
    import shutil

    ruta = tmp_path / "melate.duckdb"
    shutil.copy2(base_real, ruta)
    at = correr(raiz, ruta, monkeypatch)
    assert "VENTAJA DEMOSTRADA" not in at.info[0].value
    shutil.copyfile(base_con_ventaja, ruta)
    at.run()
    assert "VENTAJA DEMOSTRADA" in at.info[0].value


@pytest.mark.parametrize("pedida,esperada", [("jugadores", "jugadores"),
                                              ("no-existe", "veredicto")])
def test_la_url_elige_la_pantalla(raiz, base_real, monkeypatch, red, pedida, esperada):
    """`?pantalla=<slug>` abre esa pantalla, y una que no existe cae en el veredicto.

    La primera versión ligaba la radio con `bind="query-params"`, que exige la etiqueta y no el
    slug: descartaba `?pantalla=jugadores` en silencio. Lo vio una captura del navegador, no un test.
    """
    at = correr(raiz, base_real, monkeypatch, url=pedida)
    assert at.sidebar.radio[0].value == esperada
    assert at.query_params["pantalla"] == esperada, "la URL queda con la pantalla que se ve"


def test_el_selector_de_informe_gobierna_la_pantalla(raiz, base_real, monkeypatch, red):
    """Dos informes de los mismos datos con 2000 y 200 simulaciones: dos q mínimas distintas, y la
    pantalla dice con cuántas simulaciones se hizo cada uno."""
    at = correr(raiz, base_real, monkeypatch, "exploracion")
    assert "**q mínima: 0.3060**" in textos(at)
    at.selectbox(key="informe_exploracion").set_value("reportes/2026-10-03_vivo.json").run()
    texto = textos(at)
    assert "**q mínima: 0.5940**" in texto and "200 simulaciones" in texto


# ---------------------------------------------------------------- lo que la app no hace
def test_la_app_solo_importa_lo_que_lee(raiz):
    arbol = ast.parse((raiz / APP).read_text(encoding="utf-8"))
    nombres = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            nombres |= {a.name for a in nodo.names}
        elif isinstance(nodo, ast.ImportFrom):
            nombres.add(nodo.module)
    assert nombres == {"datetime", "pathlib", "pandas", "streamlit", "melate",
                       "melate.protocolo"}, nombres


def test_la_app_no_escribe(raiz):
    """Ni un `open` en escritura, ni `to_csv`, ni una conexión propia a la base, ni construirla."""
    fuente = (raiz / APP).read_text(encoding="utf-8")
    for prohibido in ("open(", "write_", ".to_csv", ".to_json", "duckdb.connect", "construir("):
        assert prohibido not in fuente, prohibido


# ---------------------------------------------------------------- la base, ausente o vieja
def test_sin_base_la_app_lo_dice(raiz, tmp_path, monkeypatch, red):
    at = correr(raiz, tmp_path / "no-existe.duckdb", monkeypatch)
    assert SIN_VENTAJA in at.info[0].value
    assert "No encuentro la base" in at.error[0].value
    assert "melate.almacen" in at.code[0].value
    assert not at.dataframe, "sin base no se enseña ninguna cifra"


def test_la_app_avisa_si_la_base_esta_desactualizada(raiz, base_real, monkeypatch, red):
    """Un veredicto nuevo en `reportes/` después de construir: la app lo dice. Se hace sobre el
    árbol compartido y se deja como estaba, pase lo que pase."""
    nuevo = base_real.parent / "reportes" / "2026-10-09_veredicto.json"
    try:
        nuevo.write_text("{}", encoding="utf-8")
        at = correr(raiz, base_real, monkeypatch)
        assert any("no está al día" in w.value and "1 nuevos" in w.value for w in at.warning)
    finally:
        nuevo.unlink(missing_ok=True)


# ---------------------------------------------------------------- la red
@pytest.mark.parametrize("direccion,telemetria", [(None, False), ("127.0.0.1", True)])
def test_la_app_se_niega_fuera_de_loopback_o_con_telemetria(raiz, base_real, monkeypatch, red,
                                                             direccion, telemetria):
    red(direccion, telemetria)
    at = correr(raiz, base_real, monkeypatch)
    assert "se niega a enseñar nada" in at.error[0].value
    assert SIN_VENTAJA in at.info[0].value
    assert not at.dataframe and not at.sidebar.radio, "ni una cifra ni la navegación"


@pytest.mark.parametrize("direccion,aceptada", [
    ("127.0.0.1", True), ("localhost", True), ("::1", True),
    ("0.0.0.0", False), ("::", False), (None, False), ("192.168.1.10", False), ("", False),
])
def test_solo_loopback_se_acepta(modulo, direccion, aceptada):
    assert (modulo.problemas_de_red(direccion, False) == []) is aceptada


def test_la_configuracion_ata_la_app_a_esta_maquina(raiz, modulo):
    c = tomllib.loads((raiz / ".streamlit" / "config.toml").read_text(encoding="utf-8"))
    assert c["server"]["address"] in modulo.LOOPBACK
    assert set(c["server"]["allowedHosts"]) <= set(modulo.LOOPBACK)
    assert c["server"]["headless"] is True, "sin la pregunta del correo la primera vez"
    assert c["browser"]["gatherUsageStats"] is False
    assert c["server"]["enableCORS"] is True, "sin ella, el WebSocket acepta cualquier origen"
    assert c["client"]["toolbarMode"] == "viewer", "sin el botón de desplegar en la nube"


def test_ningun_secreto_de_streamlit_se_publica(raiz, tmp_path):
    """Streamlit lee `secrets.toml` en la carpeta desde la que se lanza y en la del script
    (`app/.streamlit/`), y `.gitignore` tiene que excluir los dos. Se pregunta a git en un
    repositorio de usar y tirar con el mismo `.gitignore`, así que vale también en la copia sin
    repositorio de `scripts/mutar.py`; `-v` dice de qué fichero sale la exclusión, para que no la
    dé por buena un `.gitignore` global de la máquina."""
    import shutil
    import subprocess

    if shutil.which("git") is None:
        pytest.skip("sin git")
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    shutil.copy2(raiz / ".gitignore", tmp_path / ".gitignore")
    for ruta in (".streamlit/secrets.toml", "app/.streamlit/secrets.toml"):
        r = subprocess.run(["git", "-C", str(tmp_path), "check-ignore", "-v", "--no-index", ruta],
                           capture_output=True, text=True)
        assert r.stdout.startswith(".gitignore:"), f".gitignore no excluye {ruta}"


# ---------------------------------------------------------------- utilidades
def test_los_datos_del_veredicto_no_esconden_juegos_desiguales(modulo):
    base = {"datos_registrados": True, "ultima_fecha_datos": "2026-10-04"}
    igual = modulo.datos_del_veredicto(dict(base, ultimo_concurso_datos=4274,
                                            ultimo_concurso_datos_min=4274))
    distinto = modulo.datos_del_veredicto(dict(base, ultimo_concurso_datos=4274,
                                               ultimo_concurso_datos_min=4273))
    assert "el sorteo 4274" in igual
    assert "4273 a 4274" in distinto and "no todos los juegos" in distinto
    assert "no registra" in modulo.datos_del_veredicto({"datos_registrados": False})


def test_escapar_neutraliza_el_markdown(modulo):
    """Un `$` abre una fórmula y `![x](url)` es una imagen que el navegador iría a buscar fuera."""
    malo = "Precio $15 y $10 · [enlace](http://x.test) · ![img](http://x.test/a.png) · :red[x] *y*"
    limpio = modulo.escapar(malo)
    for c in "$[]()!*:":
        assert all(limpio[i - 1] == "\\" for i, ch in enumerate(limpio) if ch == c), c
    assert modulo.escapar(None) == "" and modulo.escapar(float("nan")) == ""
