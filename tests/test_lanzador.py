"""El lanzador, `python -m melate.app`: la base al día, la red forzada y sin preguntar la IP pública.

Lo que se prueba es lo que el lanzador promete **aunque el entorno diga otra cosa**: un `config.toml`
hostil en la carpeta desde la que se lanza, variables `STREAMLIT_*` hostiles, y una base que falta,
que está rota, que es de otro esquema o que se quedó vieja. Ningún test arranca un servidor: se
sustituye `bootstrap.run`, que es lo último que hace `streamlit run`, y se mira la configuración con
la que habría arrancado.

Lo que esto NO prueba, y se declara: el proceso real escuchando. Eso se comprobó en vivo, con la
tabla de conexiones del sistema y un proxy que apunta lo que le llega (bitácora de la Fase 4).
"""
import pathlib
import re
import shutil
import tomllib

import pytest

from melate import almacen
from melate import app as lanzador


@pytest.fixture
def streamlit_intacto(monkeypatch):
    """Lo que el lanzador cambia en Streamlit —su configuración global, la ruta del script y la
    búsqueda de la IP— vuelve a estar como estaba al acabar el test."""
    from streamlit import config, net_util

    monkeypatch.setattr(config, "_config_options", config._config_options)
    monkeypatch.setattr(config, "_main_script_path", config._main_script_path)
    monkeypatch.setattr(net_util, "get_external_ip", net_util.get_external_ip)


# ---------------------------------------------------------------- 1. la base
@pytest.fixture(scope="module")
def arbol_al_dia(base_real):
    """El árbol de `base_real`, que la sesión ya construyó. Nunca se toca: cada test trabaja sobre
    una copia, porque construir cuesta y copiar no."""
    return base_real.parent


def _actualizar(sql):
    """Un estado estropeado de la base, escrito con una sentencia: más barato que construir otra."""
    def estropear(ruta):
        import duckdb

        con = duckdb.connect(str(ruta))
        try:
            con.execute(sql)
        finally:
            con.close()
    return estropear


ESTADOS = {
    "falta": (lambda ruta: ruta.unlink(), "no existe"),
    "rota": (lambda ruta: ruta.write_bytes(b"esto no es una base"), "no se puede leer"),
    "de otro esquema": (_actualizar("UPDATE construccion SET version_esquema = 0"),
                        "no se puede usar: es del esquema 0"),
    # Lo que guarda una base construida con carpetas de fuera de su árbol: no sabe dónde están.
    "de otro árbol": (_actualizar("UPDATE construccion SET dir_reportes = NULL"),
                      "no se puede comprobar si está al día"),
    "desactualizada": (lambda ruta: (ruta.parent / "reportes" / "2026-10-09_nuevo.json")
                       .write_text("{}", encoding="utf-8"), "está desactualizada (1 nuevos)"),
}


def _estropeada(arbol_al_dia, tmp_path, estado):
    arbol = shutil.copytree(arbol_al_dia, tmp_path / "arbol")
    ruta = arbol / almacen.SALIDA
    estropear, motivo = ESTADOS[estado]
    estropear(ruta)
    return ruta, motivo


@pytest.mark.parametrize("estado", list(ESTADOS))
def test_el_lanzador_sabe_por_que_hay_que_construir(arbol_al_dia, tmp_path, estado):
    """Saber por qué cuesta leer la base; construirla, seis veces más. Los cinco estados se prueban
    aquí sin construir, y todos llevan después al mismo camino, que se prueba una vez abajo."""
    ruta, motivo = _estropeada(arbol_al_dia, tmp_path, estado)
    assert lanzador.por_que_construir(ruta).startswith(motivo)


def test_construye_con_las_carpetas_de_su_propio_arbol(arbol_al_dia, tmp_path):
    """Un clon recién hecho, que no trae base: al acabar, la base está al día con el árbol en el
    que vive, que es contra lo que la app comprueba su frescura."""
    ruta, motivo = _estropeada(arbol_al_dia, tmp_path, "falta")
    assert lanzador.poner_al_dia(ruta) == motivo
    assert lanzador.por_que_construir(ruta) is None, "y a la segunda ya no hay nada que hacer"


def test_una_base_al_dia_no_se_toca(arbol_al_dia, monkeypatch):
    """Sobre el árbol compartido, sin copiarlo: con `construir` prohibido, nada puede escribir."""
    ruta = arbol_al_dia / almacen.SALIDA
    antes = ruta.read_bytes()

    def prohibido(*a, **k):
        raise AssertionError("una base al día no se reconstruye")

    monkeypatch.setattr(almacen, "construir", prohibido)
    assert lanzador.poner_al_dia(ruta) is None
    assert ruta.read_bytes() == antes


def test_la_app_y_el_lanzador_buscan_la_base_en_el_mismo_sitio(raiz, tmp_path, monkeypatch):
    """Una sola regla, en `almacen`: con dos, el lanzador podría poner al día una base y la app
    enseñar otra."""
    monkeypatch.delenv("MELATE_DUCKDB", raising=False)
    assert almacen.ruta_de_la_base(tmp_path) == tmp_path / almacen.SALIDA
    monkeypatch.setenv("MELATE_DUCKDB", str(tmp_path / "otra.duckdb"))
    assert almacen.ruta_de_la_base(tmp_path) == tmp_path / "otra.duckdb"
    assert "almacen.ruta_de_la_base(RAIZ)" in (raiz / "app" / "streamlit_app.py").read_text(
        encoding="utf-8")


# ---------------------------------------------------------------- 2. la IP pública
def test_el_lanzador_no_deja_que_streamlit_pregunte_su_ip(monkeypatch, streamlit_intacto):
    """Una conexión de otro origen, sin el lanzador y con él. Sin él, Streamlit pregunta a
    checkip.amazonaws.com; con él no pregunta a nadie, y la conexión se rechaza igual."""
    import requests
    from streamlit.web.server import server_util

    pedidas = []

    def espia(url, *a, **k):
        pedidas.append(url)
        raise requests.ConnectionError("el test no deja salir a la red")

    monkeypatch.setattr(requests, "get", espia)
    assert server_util.is_url_from_allowed_origins("https://evil.example") is False
    assert any("checkip.amazonaws.com" in u for u in pedidas), "sin el lanzador, pregunta"

    pedidas.clear()
    lanzador.sin_ip_publica()
    assert server_util.is_url_from_allowed_origins("https://evil.example") is False
    assert pedidas == [], "con el lanzador, no pregunta a nadie"


def test_streamlit_solo_busca_su_ip_a_traves_del_modulo():
    """El lanzador sustituye `net_util.get_external_ip` en el módulo, y eso solo sirve si nadie se
    guardó una referencia propia (`from streamlit.net_util import get_external_ip`). Se comprueba en
    todo el Streamlit instalado: si una versión nueva lo hace, este test lo dice."""
    import streamlit

    raiz = pathlib.Path(streamlit.__file__).parent
    usos = {}
    for f in raiz.rglob("*.py"):
        texto = f.read_text(encoding="utf-8", errors="replace")
        if "get_external_ip" in texto:
            for m in re.finditer(r"(?:\w+\.)?get_external_ip\b", texto):
                usos.setdefault(m.group(0), set()).add(f.relative_to(raiz).as_posix())
    assert set(usos) == {"get_external_ip", "net_util.get_external_ip"}, usos
    assert usos["get_external_ip"] == {"net_util.py"}, "el nombre a secas, solo donde se define"


def test_sin_la_funcion_que_sustituye_el_lanzador_no_arranca(monkeypatch, streamlit_intacto):
    """Si Streamlit la renombra, el lanzador se niega: no deja la búsqueda viva en silencio."""
    from streamlit import net_util

    monkeypatch.delattr(net_util, "get_external_ip")
    with pytest.raises(SystemExit, match="get_external_ip"):
        lanzador.sin_ip_publica()
    assert not hasattr(net_util, "get_external_ip"), "y no deja nada a medias"


# ---------------------------------------------------------------- 3. la red
def test_lo_que_fuerza_el_lanzador_ata_la_app_a_esta_maquina():
    red = lanzador.RED
    assert red["server.address"] == "127.0.0.1"
    assert set(red["server.allowedHosts"]) == {"127.0.0.1", "localhost"}
    assert red["browser.gatherUsageStats"] is False
    assert red["server.enableCORS"] is True and red["server.enableXsrfProtection"] is True
    assert red["server.headless"] is True, "sin la pregunta del correo la primera vez"
    assert red["client.toolbarMode"] == "viewer", "sin el botón de desplegar en la nube"


def test_el_lanzador_y_la_configuracion_dicen_lo_mismo(raiz):
    """Dos formas de arrancar y una sola postura de red: si una cambia, la otra también."""
    c = tomllib.loads((raiz / ".streamlit" / "config.toml").read_text(encoding="utf-8"))
    plano = {f"{s}.{k}": v for s, opciones in c.items() for k, v in opciones.items()}
    assert {k: plano.get(k) for k in lanzador.RED} == lanzador.RED
    assert set(plano) - set(lanzador.RED) == {"server.port", "server.runOnSave"}, "y nada más"


HOSTIL_TOML = """
[server]
address = "0.0.0.0"
headless = false
allowedHosts = ["*"]
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = true
serverAddress = "evil.example"

[client]
toolbarMode = "developer"
"""
HOSTIL_ENV = {"STREAMLIT_SERVER_ADDRESS": "0.0.0.0", "STREAMLIT_BROWSER_GATHER_USAGE_STATS": "true",
              "STREAMLIT_SERVER_ENABLE_CORS": "false"}


def test_la_red_queda_forzada_aunque_el_entorno_diga_otra_cosa(base_real, tmp_path, monkeypatch,
                                                               streamlit_intacto):
    """Lanzado desde una carpeta con un `config.toml` hostil y con variables `STREAMLIT_*` hostiles.

    Primero `streamlit run` a secas, en el mismo entorno: tiene que quedar hostil, o el test no
    probaría nada. Después el lanzador: cada opción, la de `RED`.
    """
    from streamlit import config, net_util
    from streamlit.web import bootstrap, cli

    (tmp_path / ".streamlit").mkdir()
    (tmp_path / ".streamlit" / "config.toml").write_text(HOSTIL_TOML, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    for k, v in HOSTIL_ENV.items():
        monkeypatch.setenv(k, v)
    # Una base al día que no es la de la raíz: ningún test toca la `melate.duckdb` de verdad.
    monkeypatch.setenv("MELATE_DUCKDB", str(base_real))
    monkeypatch.setattr(cli, "check_credentials", lambda: None)
    arrancado = []
    monkeypatch.setattr(bootstrap, "run", lambda script, *a: arrancado.append(script))

    def opciones():
        valores = {k: config.get_option(k) for k in lanzador.RED}
        return {k: list(v) if isinstance(v, tuple) else v for k, v in valores.items()}

    with pytest.raises(SystemExit) as fin:
        cli.main(["run", str(lanzador.APP)], prog_name="streamlit")
    assert fin.value.code == 0
    sin = opciones()
    assert sin["server.address"] == "0.0.0.0" and sin["browser.gatherUsageStats"] is True
    assert sin["server.enableCORS"] is False and sin["browser.serverAddress"] == "evil.example"

    with pytest.raises(SystemExit) as fin:
        lanzador.main(["--puerto", "8765"])
    assert fin.value.code == 0
    assert opciones() == lanzador.RED
    assert config.get_option("server.port") == 8765
    assert arrancado == [str(lanzador.APP)] * 2
    assert net_util.get_external_ip is lanzador.ninguna_ip_publica


def test_sin_la_app_el_lanzador_lo_dice(tmp_path, monkeypatch):
    monkeypatch.setattr(lanzador, "APP", tmp_path / "no-existe.py")
    with pytest.raises(SystemExit, match="No encuentro la app"):
        lanzador.main([])
