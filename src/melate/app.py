"""Abre la app local: `python -m melate.app`. Es la forma recomendada, en lugar de `streamlit run`.

Antes de servir hace tres cosas que `streamlit run` no puede hacer. El diseño, su prueba de concepto
y la aprobación del usuario están en la decisión C3 de
`Documentos_Contexto/Fases/2026-10-04_app-local/Decisiones/2026-10-04_11-00_s4-lo-que-decidio-el-usuario.md`.

1. **Pone la base al día.** Si `melate.duckdb` falta, no se puede leer, es de otro esquema o está
   desactualizada, la construye. La app sigue sin escribir nada: escribe este lanzador, que es una
   orden de terminal, como `python -m melate.almacen`.
2. **Anula la búsqueda de la IP pública.** Ante una conexión de otro origen, Streamlit 1.65 le
   pregunta la IP pública de la máquina a `checkip.amazonaws.com` para compararla con el origen.
   Aquí esa función devuelve None: la conexión se rechaza igual, sin preguntarle nada a nadie.
3. **Fuerza la red por línea de órdenes.** Las opciones de `streamlit run` mandan sobre cualquier
   `config.toml` —el global, el de la carpeta desde la que se lanza y el que esté junto al script— y
   sobre las variables `STREAMLIT_*`, así que la app queda atada a esta máquina se lance desde donde
   se lance.

`streamlit run app/streamlit_app.py` desde la raíz sigue funcionando, con `.streamlit/config.toml` y
la guarda de la app, pero sin estas tres cosas.
"""
import argparse
import pathlib

from . import almacen

# El lanzador está en src/melate/ y la app en app/. El paquete se instala en modo editable
# (`pip install -e .`), así que los dos viven en el mismo repositorio.
RAIZ = pathlib.Path(__file__).resolve().parents[2]
APP = RAIZ / "app" / "streamlit_app.py"
PUERTO = 8501

# Lo que se fuerza. Es lo mismo que dice `.streamlit/config.toml` para quien use `streamlit run`, y
# un test exige que no se separen; el porqué de cada línea está en ese fichero.
RED = {
    "server.address": "127.0.0.1",
    "server.headless": True,
    "server.allowedHosts": ["127.0.0.1", "localhost"],
    "server.enableCORS": True,
    "server.enableXsrfProtection": True,
    "browser.serverAddress": "127.0.0.1",
    "browser.gatherUsageStats": False,
    "client.toolbarMode": "viewer",
}


# ---------------------------------------------------------------- 1. la base
def por_que_construir(ruta):
    """Por qué hay que construir la base, o None si está al día."""
    import duckdb

    if not ruta.is_file():
        return "no existe"
    try:
        tablas = almacen.leer(ruta)
    except duckdb.Error as e:
        return f"no se puede leer ({type(e).__name__})"
    problema = almacen.problema_de_esquema(tablas)
    if problema:
        return f"no se puede usar: {problema}"
    fres = almacen.frescura(ruta, tablas)
    if not fres["comprobable"]:
        return "no se puede comprobar si está al día"
    if not fres["al_dia"]:
        cambios = ", ".join(f"{len(fres[k])} {k}" for k in ("nuevos", "cambiados", "borrados")
                            if fres[k])
        return f"está desactualizada ({cambios})"
    return None


def poner_al_dia(ruta):
    """Construye la base si hace falta y devuelve el motivo, o None si ya estaba al día.

    La construye con los `reportes/` y `prereg/` de su misma carpeta, que es lo que `almacen`
    entiende por estar al día: la base indexa el árbol en el que vive.
    """
    motivo = por_que_construir(ruta)
    if motivo is None:
        print(f"{ruta.name} está al día.")
        return None
    print(f"{ruta.name} {motivo}: se construye.")
    almacen.main(["--reportes", str(ruta.parent / "reportes"), "--prereg",
                  str(ruta.parent / "prereg"), "--salida", str(ruta)])
    return motivo


# ---------------------------------------------------------------- 2. la IP pública
def ninguna_ip_publica():
    """Lo que el lanzador pone en lugar de `streamlit.net_util.get_external_ip`."""
    return None


def sin_ip_publica():
    """Que Streamlit no le pregunte su IP pública a nadie.

    `net_util.get_external_ip` hace un GET a checkip.amazonaws.com. Streamlit la llama al pintar la
    URL de arranque (`web/bootstrap.py`) y al comprobar una conexión de otro origen
    (`web/server/server_util.py`), y en los dos sitios la busca en el módulo en cada llamada, así
    que basta con sustituirla aquí. Si una versión nueva la renombra, el lanzador se niega a
    arrancar en vez de dejar la búsqueda viva en silencio.
    """
    from streamlit import net_util

    if not callable(getattr(net_util, "get_external_ip", None)):
        raise SystemExit("Esta versión de Streamlit no tiene net_util.get_external_ip, y el "
                         "lanzador no sabe impedir que pregunte su IP pública. Revisa su red antes "
                         "de actualizarla (requirements.txt).")
    net_util.get_external_ip = ninguna_ip_publica


# ---------------------------------------------------------------- 3. la red
def argumentos(puerto=PUERTO):
    """La orden de `streamlit run`: la app, las opciones de `RED` y el puerto."""
    args = ["run", str(APP)]
    for opcion, valor in RED.items():
        for v in valor if isinstance(valor, list) else [valor]:
            args += [f"--{opcion}", str(v).lower() if isinstance(v, bool) else v]
    return args + ["--server.port", str(puerto)]


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Abre la app local de Máquina Melate: pone su base al día y arranca Streamlit "
                    "solo en 127.0.0.1, sin telemetría y sin preguntar la IP pública.")
    ap.add_argument("--puerto", type=int, default=PUERTO, help=f"por defecto {PUERTO}")
    a = ap.parse_args(argv)
    if not APP.is_file():
        raise SystemExit(f"No encuentro la app en {APP}. El lanzador necesita el repositorio: "
                         "instala el paquete con `pip install -e .` desde su raíz.")

    poner_al_dia(almacen.ruta_de_la_base(RAIZ))
    sin_ip_publica()
    print(f"Solo esta máquina: http://127.0.0.1:{a.puerto} · sin telemetría · sin preguntar la "
          "IP pública. Ctrl+C para cerrarla.")
    from streamlit.web import cli

    cli.main(argumentos(a.puerto), prog_name="streamlit")


if __name__ == "__main__":
    main()
