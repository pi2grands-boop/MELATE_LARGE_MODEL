"""Mutación de tests: rompe una cosa a la vez y exige que algún test se entere.

    .venv\\Scripts\\python.exe scripts\\mutar.py              # todas
    .venv\\Scripts\\python.exe scripts\\mutar.py --solo F4    # las que contienen "F4"

Un test que no falla cuando rompes lo que dice vigilar no vigila nada. Este guion convierte esa
comprobación —que la auditoría de la Fase 3 hizo a mano, con un guion que no quedó en el
repositorio— en una herramienta: cada mutación es una sustitución de texto exacta en un fichero, y
la lista de tests que tiene que cazarla.

**Nunca toca el árbol de trabajo.** Copia lo necesario a una carpeta temporal y corre pytest allí,
con `PYTHONPATH` apuntando a la copia. Así una interrupción a medias no deja un fichero mutado, ni
finales de línea cambiados, que es lo que le pasó a aquella auditoría al restaurar los ficheros.

Salida: una línea por mutación. Código 0 si todas se detectan; 1 si alguna no; 2 si los tests
elegidos no pasan sin mutar, porque entonces que fallen con la mutación no prueba nada.
"""
import argparse
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time

RAIZ = pathlib.Path(__file__).resolve().parent.parent
COPIAR = ["src", "app", "tests", ".streamlit", "data/raw", "reportes", "prereg",
          "baseline_auditoria.py", "pyproject.toml", ".gitignore"]

# (nombre, fichero, texto exacto, sustitución, ficheros de test, expresión -k)
MUTACIONES = [
    # -- Fase 3: el trato con melate-e.com y la cartera (las nueve de la auditoría posterior)
    ("F3 sin el límite de 1 solicitud/segundo", "src/melate/popularity.py",
     "PAUSA_SEGUNDOS = 1.0", "PAUSA_SEGUNDOS = 0.0",
     "tests/test_popularidad.py", "ritmo_por_defecto"),
    ("F3 sin caché", "src/melate/popularity.py",
     "        if ruta.is_file():", "        if False:",
     "tests/test_popularidad.py", "cache"),
    ("F3 combinatoria de Melate con 50 donde va 49", "src/melate/popularity.py",
     "comb(N - K - 1, restantes)", "comb(N - K, restantes)",
     "tests/test_popularidad.py", "favorables or universo"),
    ("F3 Revanchita se pide", "src/melate/popularity.py",
     'SIN_TABLA = ("Revanchita",)', "SIN_TABLA = ()",
     "tests/test_popularidad.py", "revanchita"),
    ("F3 el User-Agent finge ser un navegador", "src/melate/popularity.py",
     'UA = "MaquinaMelate/0.1 (', 'UA = "Mozilla/5.0 MaquinaMelate/0.1 (',
     "tests/test_popularidad.py", "user_agent"),
    ("F3 se acepta una tabla con menos categorías", "src/melate/popularity.py",
     "    if len(cats) != esperadas:", "    if len(cats) > esperadas:",
     "tests/test_popularidad.py", "incompleta"),
    ("F3 sin tope de popularidad", "src/melate/portfolio.py",
     "aptas = [c for c in pool if pops[c] <= tope_popularidad]", "aptas = list(pool)",
     "tests/test_cartera.py", "minuscula or tope"),
    ("F3 nunca se comparte la bolsa", "src/melate/portfolio.py",
     "    return (1 - math.exp(-lam)) / lam, lam", "    return 1.0, lam",
     "tests/test_cartera.py", "compartir or reparto"),
    ("F3 la valoración sin su aviso", "src/melate/portfolio.py",
     '"aviso": ("El valor esperado es NEGATIVO y esta cartera no lo arregla. ',
     '"aviso": ("', "tests/test_cartera.py", "aviso"),

    # -- Fase 4: la base y la app
    ("F4 la guarda acepta cualquier dirección", "app/streamlit_app.py",
     "    if direccion not in LOOPBACK:", "    if False:",
     "tests/test_app.py", "loopback"),
    ("F4 la guarda ignora la telemetría", "app/streamlit_app.py",
     "    if telemetria:", "    if False:",
     "tests/test_app.py", "se_niega"),
    ("F4 la configuración escucha en 0.0.0.0", ".streamlit/config.toml",
     'address = "127.0.0.1"', 'address = "0.0.0.0"',
     "tests/test_app.py", "configuracion"),
    ("F4 la configuración envía telemetría", ".streamlit/config.toml",
     "gatherUsageStats = false", "gatherUsageStats = true",
     "tests/test_app.py", "configuracion"),
    ("F4 una pantalla sin la cabecera", "app/streamlit_app.py",
     "    cabecera(vigente)\n", "",
     "tests/test_app.py", "recorrido"),
    ("F4 la exploración sin su aviso", "app/streamlit_app.py",
     "    st.warning(AVISO_EXPLORA)", "    pass",
     "tests/test_app.py", "recorrido"),
    ("F4 una q exploratoria baja sin el aviso de candidata", "app/streamlit_app.py",
     '        if inf["pruebas_bajo_umbral"]:', "        if False:",
     "tests/test_app.py", "candidata"),
    ("F4 la cabecera usa veredictos no válidos", "src/melate/almacen.py",
     'validos = v[v["valido"]].assign(', "validos = v.assign(",
     "tests/test_almacen.py tests/test_app.py", "incoherente or alterado or sello_roto"),
    ("F4 el sello no se verifica", "src/melate/almacen.py",
     "        cargar_preregistro(ruta_disco)\n", "        pass\n",
     "tests/test_almacen.py", "alterado"),
    ("F4 el vigente es el último que se corrió", "src/melate/almacen.py",
     'validos.sort_values(["_datos", "corrida_utc", "ruta"])',
     'validos.sort_values(["corrida_utc", "ruta"])',
     "tests/test_almacen.py", "vigente"),
    ("F4 la base se abre en escritura", "src/melate/almacen.py",
     "duckdb.connect(str(ruta), read_only=True)", "duckdb.connect(str(ruta))",
     "tests/test_almacen.py", "solo_lectura"),
    ("F4 rutas absolutas en la base", "src/melate/almacen.py",
     "return pathlib.Path(ruta).resolve().relative_to(base).as_posix()",
     "return pathlib.Path(ruta).resolve().as_posix()",
     "tests/test_almacen.py", "absoluta"),
    ("F4 un fichero roto deja filas a medias", "src/melate/almacen.py",
     "                lote = {t: [] for t in ESQUEMA}\n                valido, motivo = False, f\"forma",
     "                valido, motivo = False, f\"forma",
     "tests/test_almacen.py", "no_se_reconoce"),
    ("F4 base vacía en silencio desde otra carpeta", "src/melate/almacen.py",
     "        if not carpeta.is_dir():", "        if False:",
     "tests/test_almacen.py", "sin_carpetas"),
    ("F4 la frescura nunca avisa", "src/melate/almacen.py",
     '"al_dia": not (nuevos or borrados or cambiados)', '"al_dia": True',
     "tests/test_almacen.py tests/test_app.py", "frescura or desactualizada"),
    ("F4 una base vieja pasa por buena", "src/melate/almacen.py",
     "        if ausentes:", "        if False:",
     "tests/test_almacen.py", "otro_esquema"),
    ("F4 sin escapar el Markdown", "app/streamlit_app.py",
     'return "" if nulo(texto) else str(texto).translate(_MARKDOWN)',
     'return "" if nulo(texto) else str(texto)',
     "tests/test_app.py", "escapar"),
    ("F4 la URL no elige la pantalla", "app/streamlit_app.py",
     "index=list(PANTALLAS).index(pedida) if pedida in PANTALLAS else 0)", "index=0)",
     "tests/test_app.py", "url"),
    ("F4 el veredicto no registra sus datos (H1)", "src/melate/lab.py",
     '"datos": _datos(juegos, crudos),', '"datos": {},',
     "tests/test_almacen.py", "registra_los_datos"),
    ("F4 la caché ignora la reconstrucción de la base", "app/streamlit_app.py",
     "t = cargar(str(ruta), (info.st_mtime_ns, info.st_size))", "t = cargar(str(ruta), (0, 0))",
     "tests/test_app.py", "reconstruir"),
    ("F4 la fecha de un veredicto llega sin escapar", "app/streamlit_app.py",
     "({escapar(r['ultima_fecha_datos'])})", "({r['ultima_fecha_datos']})",
     "tests/test_app.py", "afirmativo"),
    ("F4 una tabla sin premios cuenta como premios a cero (C1)", "src/melate/popularity.py",
     'return all(c["premio"] > 0 for c in cats if c["aciertos"] < K and c["ganadores"] > 0)',
     "return True", "tests/test_popularidad.py", "sin_premios"),
    ("F4 la base no cuenta los sorteos sin premios (C1)", "src/melate/almacen.py",
     "None if sin_premios is None else len(sin_premios),", "None,",
     "tests/test_almacen.py", "contenido"),
    ("F4 la valoración no dice con qué bolsa se hizo (C4)", "src/melate/portfolio.py",
     '        "bolsa": bolsa,\n', "", "tests/test_cartera.py", "con_que_se_hizo"),

    # -- Fase 4: el lanzador (C3)
    ("F4 el lanzador escucha en 0.0.0.0 (C3)", "src/melate/app.py",
     '    "server.address": "127.0.0.1",', '    "server.address": "0.0.0.0",',
     "tests/test_lanzador.py", "ata_la_app or dicen_lo_mismo"),
    ("F4 el lanzador envía telemetría (C3)", "src/melate/app.py",
     '    "browser.gatherUsageStats": False,', '    "browser.gatherUsageStats": True,',
     "tests/test_lanzador.py", "ata_la_app or dicen_lo_mismo"),
    ("F4 el lanzador apaga la protección de origen (C3)", "src/melate/app.py",
     '    "server.enableCORS": True,', '    "server.enableCORS": False,',
     "tests/test_lanzador.py", "ata_la_app or dicen_lo_mismo"),
    ("F4 la configuración apaga la protección de origen (C3)", ".streamlit/config.toml",
     "enableCORS = true", "enableCORS = false",
     "tests/test_app.py tests/test_lanzador.py", "configuracion or dicen_lo_mismo"),
    ("F4 el lanzador no fuerza nada por línea de órdenes (C3)", "src/melate/app.py",
     '    return args + ["--server.port", str(puerto)]',
     '    return ["run", str(APP), "--server.port", str(puerto)]',
     "tests/test_lanzador.py", "forzada"),
    ("F4 el lanzador deja que Streamlit pregunte su IP (C3)", "src/melate/app.py",
     "    net_util.get_external_ip = ninguna_ip_publica\n", "    pass\n",
     "tests/test_lanzador.py", "pregunte_su_ip or forzada"),
    ("F4 el lanzador arranca sin poder sustituir la búsqueda (C3)", "src/melate/app.py",
     '    if not callable(getattr(net_util, "get_external_ip", None)):', "    if False:",
     "tests/test_lanzador.py", "no_arranca"),
    ("F4 el lanzador no ve una base vieja (C3)", "src/melate/app.py",
     '    if not fres["al_dia"]:', "    if False:",
     "tests/test_lanzador.py", "por_que_hay_que_construir or carpetas"),
    ("F4 una base rota tumba el lanzador (C3)", "src/melate/app.py",
     "    except duckdb.Error as e:", "    except KeyError as e:",
     "tests/test_lanzador.py", "por_que_hay_que_construir"),
    ("F4 el lanzador reconstruye una base al día (C3)", "src/melate/app.py",
     "    return None\n\n\ndef poner_al_dia(ruta):",
     '    return "siempre"\n\n\ndef poner_al_dia(ruta):',
     "tests/test_lanzador.py", "al_dia_no_se_toca"),
    ("F4 el lanzador construye con las carpetas de otro árbol (C3)", "src/melate/app.py",
     'str(ruta.parent / "reportes")', 'str(RAIZ / "reportes")',
     "tests/test_lanzador.py", "carpetas"),
    ("F4 el secrets.toml junto al script se publicaría (C3)", ".gitignore",
     "**/.streamlit/secrets.toml", ".streamlit/secrets.toml",
     "tests/test_app.py", "secreto"),
    ("F4 la app y el lanzador miran bases distintas (C3)", "src/melate/almacen.py",
     '    return pathlib.Path(os.environ.get("MELATE_DUCKDB") or pathlib.Path(raiz) / SALIDA)',
     "    return pathlib.Path(raiz) / SALIDA",
     "tests/test_lanzador.py", "mismo_sitio"),
]


def mutar(ruta, buscar, poner):
    """Aplica la mutación respetando el final de línea del fichero. Devuelve los bytes originales.

    Se busca y se sustituye sobre el texto con los saltos normalizados a `\\n`, y se escribe con el
    final de línea que tenía el fichero. La primera versión comprobaba sobre el texto y sustituía
    sobre los bytes: en un fichero con CRLF, un texto con salto de línea «aparecía una vez» y la
    sustitución no cambiaba nada. La mutación no se aplicaba y el guion lo contaba igual.
    """
    original = ruta.read_bytes()
    texto = original.decode("utf-8")
    crlf = "\r\n" in texto
    normal = texto.replace("\r\n", "\n")
    if normal.count(buscar) != 1:
        raise ValueError(f"el texto aparece {normal.count(buscar)} veces")
    mutado = normal.replace(buscar, poner, 1)
    if crlf:
        mutado = mutado.replace("\n", "\r\n")
    nuevo = mutado.encode("utf-8")
    if nuevo == original:
        raise ValueError("la mutación no cambió ningún byte")
    ruta.write_bytes(nuevo)
    return original


def preparar(destino):
    for rel in COPIAR:
        origen = RAIZ / rel
        if origen.is_dir():
            shutil.copytree(origen, destino / rel, ignore=shutil.ignore_patterns("__pycache__"))
        else:
            (destino / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(origen, destino / rel)


def pytest(copia, ficheros, expresion):
    entorno = dict(os.environ, PYTHONPATH=str(copia / "src"), PYTHONIOENCODING="utf-8")
    t0 = time.monotonic()
    r = subprocess.run([sys.executable, "-m", "pytest", *ficheros.split(), "-k", expresion,
                        "-q", "-x", "-p", "no:cacheprovider", "-m", "not lento and not red"],
                       cwd=copia, env=entorno, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    fallidos = [l.split(" - ")[0].replace("FAILED ", "") for l in r.stdout.splitlines()
                if l.startswith("FAILED")]
    return r.returncode, fallidos, time.monotonic() - t0, r.stdout[-1500:]


def main(argv=None):
    ap = argparse.ArgumentParser(description="Mutación de tests sobre una copia del repositorio.")
    ap.add_argument("--solo", default="", help="solo las mutaciones cuyo nombre contenga esto")
    a = ap.parse_args(argv)
    elegidas = [m for m in MUTACIONES if a.solo in m[0]]

    with tempfile.TemporaryDirectory(prefix="mutar-") as tmp:
        copia = pathlib.Path(tmp)
        preparar(copia)

        # Cada mutación tiene que aplicarse —el texto, exactamente una vez, y algún byte distinto—
        # antes de empezar: si no, no muta lo que dice, y su resultado no significaría nada.
        for nombre, fichero, buscar, poner, _, _ in elegidas:
            try:
                (copia / fichero).write_bytes(mutar(copia / fichero, buscar, poner))
            except ValueError as e:
                print(f"MAL DEFINIDA  {nombre} en {fichero}: {e}")
                return 2

        # Sin mutar, los tests elegidos tienen que pasar; si no, que fallen después no prueba nada.
        # Una sola pasada sobre todos sus ficheros: si pasa entera, pasa cualquier selección.
        ficheros = " ".join(sorted({f for m in elegidas for f in m[4].split()}))
        codigo, _, dt, salida = pytest(copia, ficheros, "not ninguna_seleccion_excluye_nada")
        if codigo != 0:
            print(f"LÍNEA BASE ROTA: sin mutar, {ficheros} no pasa (código {codigo}):\n{salida}")
            return 2
        print(f"línea base: {ficheros} en verde sin mutar ({dt:.1f} s)")

        no_detectadas = 0
        print(f"{len(elegidas)} mutaciones sobre una copia del repositorio\n")
        for nombre, fichero, buscar, poner, ficheros, expresion in elegidas:
            ruta = copia / fichero
            original = mutar(ruta, buscar, poner)
            try:
                codigo, fallidos, dt, salida = pytest(copia, ficheros, expresion)
            finally:
                ruta.write_bytes(original)
            if codigo == 1:
                print(f"  detectada     {dt:5.1f} s  {nombre}  <- {fallidos[0] if fallidos else '?'}")
            else:
                no_detectadas += 1
                estado = "NO DETECTADA" if codigo == 0 else f"ERROR {codigo}"
                print(f"  {estado:13s} {dt:5.1f} s  {nombre}\n{salida}")
        print(f"\n{len(elegidas) - no_detectadas} de {len(elegidas)} detectadas.")
        return 0 if no_detectadas == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
