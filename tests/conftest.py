"""Fixtures compartidas.

Las corridas completas (2000 simulaciones + 3 backtests) tardan medio minuto o más cada una, así
que se generan **una vez por sesión** y se reparten entre los tests que las necesitan. Los tests
que solo leen los CSV no pasan por aquí y son instantáneos.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
SNAPSHOT = RAIZ / "data" / "raw" / "2026-10-02"

# La raíz del repositorio en sys.path: baseline_auditoria.py vive ahí y no es parte del paquete.
sys.path.insert(0, str(RAIZ))


@pytest.fixture(scope="session")
def raiz():
    return RAIZ


@pytest.fixture(scope="session")
def snapshot():
    """La carpeta del snapshot congelado del sorteo 4272, que es contra lo que se compara todo."""
    if not SNAPSHOT.is_dir():
        pytest.skip(f"no existe el snapshot {SNAPSHOT.relative_to(RAIZ)}")
    return SNAPSHOT


@pytest.fixture(scope="session")
def datos(snapshot):
    """Los tres juegos de la era 6/56, cargados del snapshot."""
    from melate.constantes import JUEGOS
    from melate.ingest import cargar
    from melate.validate import era_56

    crudos = {j: cargar(j, str(snapshot)) for j in JUEGOS}
    return {"crudos": crudos, "era": {j: era_56(j, d) for j, d in crudos.items()}}


def entorno_utf8():
    """El entorno con el que se lanzan los subprocesos del arnés.

    `PYTHONIOENCODING=utf-8` no es un adorno. Cuando la salida de un hijo va a una tubería, Python
    usa la codificación local: en Windows con cp1252, los caracteres 'Δ', '≈' y '–' que imprime el
    resumen lanzan UnicodeEncodeError y el proceso muere a mitad del informe. El fallo depende del
    shell desde el que se lance pytest, así que sin fijarlo la suite pasa o falla según quién la
    corra — que es la peor clase de test.

    `melate.informe` ya se protege por su cuenta (`_salida_robusta`), pero `baseline_auditoria.py`
    es el oráculo y no se modifica nunca, así que para él esta es la única solución posible. Y
    fijarlo para los dos mantiene la comparación simétrica.
    """
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def _correr(cmd, salida, snapshot, raiz):
    r = subprocess.run([sys.executable, *cmd, "--datos", str(snapshot), "--salida", str(salida)],
                       cwd=raiz, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env=entorno_utf8())
    assert r.returncode == 0, f"{cmd} falló:\n{r.stdout[-3000:]}\n{r.stderr[-3000:]}"
    return json.loads(salida.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def oraculo(tmp_path_factory, snapshot, raiz):
    """El reporte de baseline_auditoria.py: la referencia que no se discute."""
    salida = tmp_path_factory.mktemp("paridad") / "oraculo.json"
    return _correr(["baseline_auditoria.py"], salida, snapshot, raiz)


@pytest.fixture(scope="session")
def paquete(tmp_path_factory, snapshot, raiz):
    """El reporte de src/melate/, que debe coincidir con el oráculo."""
    salida = tmp_path_factory.mktemp("paridad") / "paquete.json"
    return _correr(["-m", "melate.informe"], salida, snapshot, raiz)


# ---------------------------------------------------------------- la base de la app (Fase 4)
# Lo que había al cerrar la Fase 4, todo sobre el snapshot del 2026-10-02. Las bases de los tests se
# construyen con esto y no con `reportes/` entero: el ciclo de la Fase 5 añade reportes y snapshots con
# cada sorteo, y un test que dijera «el vigente es tal» sobre `reportes/` entero dejaría de ser verdad
# con el primer sorteo nuevo, sin que nada estuviera roto. Lo que hay en el repositorio hoy, sea lo que
# sea, lo vigila `test_almacen.py::test_todo_lo_que_hay_en_el_repositorio_se_reconoce`.
REPORTES_FASE_4 = ("2026-10-02_oraculo.json", "2026-10-02_paquete.json", "2026-10-03_cartera.json",
                   "2026-10-03_informe-con-popularidad.json", "2026-10-03_popularidad.json",
                   "2026-10-03_veredicto.json", "2026-10-03_vivo.json",
                   "2026-10-04_popularidad-melate-300-sorteos.json", "2026-10-04_veredicto.json")
SNAPSHOTS_FASE_4 = ("2026-10-02",)


def copiar_arbol(destino, todo=False):
    """Una copia de los reportes, `prereg/` y los `SHA256.txt` de los snapshots en `destino`, con la
    estructura del repositorio: los de la Fase 4, o con `todo`, lo que haya hoy.

    Los tests de la base y de la app trabajan siempre sobre una copia: nunca escriben en la
    `melate.duckdb` de la raíz, que es la que está usando la app. De los snapshots basta el
    `SHA256.txt`: es lo único que lee la base para saber qué está congelado (C3 de la Fase 5).
    """
    reportes = (sorted(p.name for p in (RAIZ / "reportes").glob("*.json")) if todo
                else REPORTES_FASE_4)
    snapshots = (sorted(p.parent.name for p in (RAIZ / "data" / "raw").glob("*/SHA256.txt")
                        if not p.parent.name.startswith(".")) if todo else SNAPSHOTS_FASE_4)
    (destino / "reportes").mkdir(parents=True)
    for nombre in reportes:
        shutil.copy2(RAIZ / "reportes" / nombre, destino / "reportes" / nombre)
    shutil.copytree(RAIZ / "prereg", destino / "prereg")
    for carpeta in snapshots:
        (destino / "data" / "raw" / carpeta).mkdir(parents=True)
        shutil.copy2(RAIZ / "data" / "raw" / carpeta / "SHA256.txt",
                     destino / "data" / "raw" / carpeta / "SHA256.txt")
    return destino


def construir_arbol(arbol):
    from melate import almacen

    almacen.construir(arbol / "reportes", arbol / "prereg", arbol / "melate.duckdb")
    return arbol / "melate.duckdb"


VEREDICTO_REAL = "2026-10-04_veredicto.json"
PREREG_REAL = "2026-10-03_logistica-revancha.json"
INFORME_REAL = "2026-10-03_informe-con-popularidad.json"


def leer_json(ruta):
    return json.loads(ruta.read_text(encoding="utf-8"))


def escribir_json(ruta, doc):
    ruta.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")


def forjar_veredicto(arbol, *, coherente=True, nombre="2026-10-05_veredicto.json"):
    """Un veredicto hecho a mano que dice VENTAJA DEMOSTRADA, posterior a los reales.

    Sirve para dos pruebas opuestas: que la cabecera de la app **sí** cambia cuando el veredicto
    apunta a un sello que verifica y es coherente —si no pudiera cambiar nunca, no se distinguiría
    de una cabecera escrita a mano—, y que **no** cambia cuando el veredicto es incoherente.
    Incoherente quiere decir: proclama la ventaja con las cinco condiciones reales, que no se cumplen.
    """
    v = leer_json(arbol / "reportes" / VEREDICTO_REAL)
    v["corrida_utc"] = "2026-10-05T00:00:00+00:00"
    if coherente:
        for c in v["veredicto"]["condiciones"]:
            c["cumple"], c["motivo"] = True, "forjado a mano por un test"
    v["veredicto"].update({"veredicto": "VENTAJA DEMOSTRADA", "ventaja": True, "cumplidas": 5})
    escribir_json(arbol / "reportes" / nombre, v)
    return nombre


def informe_con_q_bajo(arbol, nombre="2026-10-05_informe-q-bajo.json"):
    """Un informe exploratorio en el que una prueba queda con q <= 0.05. Lo que la app no puede
    convertir en un veredicto."""
    d = leer_json(arbol / "reportes" / INFORME_REAL)
    d["reproducibilidad"]["corrida_utc"] = "2026-10-05T00:00:00+00:00"
    d["backtest"]["Revancha"]["estrategias"]["Regresión logística"]["q_BH_global"] = 0.01
    d["protocolo_global"].update({"q_minima": 0.01,
                                  "sobreviven_a_q_0.05": ["backtest/Revancha/Regresión logística"],
                                  "veredicto": "revisar: hay pruebas con q <= 0.05"})
    escribir_json(arbol / "reportes" / nombre, d)
    return nombre


@pytest.fixture(scope="session")
def base_real(tmp_path_factory):
    """`melate.duckdb` construida con los reportes y el preregistro del repositorio tal como estaban
    al cerrar la Fase 4: reales, y fijos."""
    return construir_arbol(copiar_arbol(tmp_path_factory.mktemp("base_real")))


@pytest.fixture(scope="session")
def base_del_repositorio(tmp_path_factory):
    """`melate.duckdb` construida con todo lo que hay hoy en el repositorio, crezca lo que crezca."""
    return construir_arbol(copiar_arbol(tmp_path_factory.mktemp("base_del_repositorio"), todo=True))


# Las bases adversarias se construyen una vez por sesión y las comparten los tests de la base y de
# la app: construir cuesta ~0,16 s y el bucle rápido no puede pagar una por test
# (Rendimiento/Arreglos_Bugs/2026-10-03_01-59_la-suite-rapida-no-era-rapida.md).

MENOS_DATOS = "2026-10-06_veredicto-menos-datos.json"


@pytest.fixture(scope="session")
def base_forjada(tmp_path_factory):
    """Lo que no debe llegar a la cabecera, todo junto en una sola base:

    * un veredicto incoherente que proclama la ventaja;
    * un veredicto válido, **el más reciente**, pero con menos datos que el real: el vigente tiene
      que seguir siendo el real, que juzgó con más;
    * un veredicto sin fecha de corrida;
    * un informe con una q exploratoria de 0.01;
    * un informe con la forma rota, un preregistro fuera de `prereg/`, y dos ficheros que no son
      reportes. Ninguno puede tumbar la construcción.
    """
    arbol = copiar_arbol(tmp_path_factory.mktemp("base_forjada"))
    rep = arbol / "reportes"
    forjar_veredicto(arbol, coherente=False)
    informe_con_q_bajo(arbol)
    viejo = leer_json(rep / VEREDICTO_REAL)
    viejo["corrida_utc"] = "2026-10-06T00:00:00Z"
    for d in viejo["datos"].values():
        d.update({"ultimo_concurso": 4200, "ultima_fecha": "2026-03-01"})
    escribir_json(rep / MENOS_DATOS, viejo)
    sin_fecha = leer_json(rep / VEREDICTO_REAL)
    del sin_fecha["corrida_utc"]
    escribir_json(rep / "x-veredicto-sin-fecha.json", sin_fecha)
    escribir_json(rep / "x-informe-roto.json", {"auditoria": {"Melate": 5}, "backtest": {},
                                                "valor_esperado_proximo": {},
                                                "reproducibilidad": {}})
    escribir_json(rep / "x-prereg-fuera.json", leer_json(arbol / "prereg" / PREREG_REAL))
    (rep / "x-lista.json").write_text("[1, 2]", encoding="utf-8")
    (rep / "x-roto.json").write_text("{esto no es json", encoding="utf-8")
    return construir_arbol(arbol)


FECHA_MALICIOSA = "![x](http://x.test/rastreo.png)"


@pytest.fixture(scope="session")
def base_con_ventaja(tmp_path_factory):
    """Un veredicto coherente que dice VENTAJA DEMOSTRADA sobre el preregistro real. Su fecha de
    datos es una imagen en Markdown: si llegara sin escapar, el navegador iría a buscarla fuera."""
    arbol = copiar_arbol(tmp_path_factory.mktemp("base_con_ventaja"))
    nombre = forjar_veredicto(arbol, coherente=True)
    v = leer_json(arbol / "reportes" / nombre)
    for d in v["datos"].values():
        d["ultima_fecha"] = FECHA_MALICIOSA
    # Y en un motivo: la tabla de condiciones pasa cada celda por Markdown (Fase 5).
    v["veredicto"]["condiciones"][4]["motivo"] = FECHA_MALICIOSA
    escribir_json(arbol / "reportes" / nombre, v)
    return construir_arbol(arbol)


UN_SORTEO = "2026-10-05_veredicto-un-sorteo.json"
NO_CONGELADO = "2026-10-05_veredicto-no-congelado.json"
SNAPSHOT_FALSO = "2026-10-04_4274"


def veredicto_de_un_sorteo(arbol):
    """El primer veredicto con holdout tal como lo escribiría `melate.lab`, sin esperar al 4274.

    Un sorteo de holdout en cada juego —2 aciertos en Revancha, 1 en Melate, 0 en Revanchita—, las
    condiciones calculadas con el `declara_ventaja` real, y los datos de un snapshot que no existe en
    el repositorio pero sí en el árbol del test: `data/raw/2026-10-04_4274/` con su `SHA256.txt`.
    """
    from melate import lab, protocolo
    from melate.constantes import JUEGOS, MEDIA_AZAR

    v = leer_json(arbol / "reportes" / VEREDICTO_REAL)
    aciertos = {"Melate": 1, "Revancha": 2, "Revanchita": 0}
    hashes = {j: hashlib.sha256(f"{SNAPSHOT_FALSO}/{j}".encode()).hexdigest() for j in JUEGOS}
    emd = lab.detectable(1)
    por_juego = {j: {"sorteos_holdout": 1, "media": float(a), "delta": round(a - MEDIA_AZAR, 6),
                     "z": round((a - MEDIA_AZAR) / (emd / lab.Z_DETECTABLE), 4), "p": 0.5,
                     "efecto_minimo_detectable": emd, "q_BH_global": 1.0}
                 for j, a in aciertos.items()}
    res = dict(por_juego["Revancha"], variantes=[{"hiperparametros": {}, "delta": por_juego["Revancha"]["delta"]}] * 4,
               reentrenar_cada=100, semilla=7, familia_declarada=36, pruebas_corridas=3,
               holdout_necesario=lab.holdout_necesario(0.048))
    v["holdout"] = {j: {"sorteos": 1, "primer_concurso": 4274, "ultimo_concurso": 4274} for j in JUEGOS}
    v["por_juego"], v["resultados"] = por_juego, res
    v["veredicto"] = protocolo.declara_ventaja(res, por_juego, efecto_minimo_declarado=0.048)
    v["datos"] = {j: {"sha256": hashes[j], "origen": f"data\\raw\\{SNAPSHOT_FALSO}\\{j}.csv",
                      "bytes": 1, "ultimo_concurso": 4274, "ultima_fecha": "2026-10-04"} for j in JUEGOS}
    v["corrida_utc"] = "2026-10-05T13:00:00+00:00"
    carpeta = arbol / "data" / "raw" / SNAPSHOT_FALSO
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / "SHA256.txt").write_text("".join(f"{hashes[j]}  {j}.csv\n" for j in JUEGOS),
                                        encoding="utf-8")
    escribir_json(arbol / "reportes" / UN_SORTEO, v)
    return v


@pytest.fixture(scope="session")
def base_un_sorteo(tmp_path_factory):
    """Lo que la app enseñará con el 4274: un holdout de un sorteo, sobre un snapshot del ciclo. Y
    al lado, el mismo veredicto con unos datos que no están congelados en ninguna parte."""
    arbol = copiar_arbol(tmp_path_factory.mktemp("base_un_sorteo"))
    v = veredicto_de_un_sorteo(arbol)
    v["datos"] = {j: dict(d, sha256="f" * 64) for j, d in v["datos"].items()}
    v["corrida_utc"] = "2026-10-05T14:00:00+00:00"
    escribir_json(arbol / "reportes" / NO_CONGELADO, v)
    return construir_arbol(arbol)


HUERFANO = "2026-10-05_huerfano.json"


@pytest.fixture(scope="session")
def base_sello_roto(tmp_path_factory):
    """El preregistro real con el umbral aflojado después de sellar —el sello ya no cuadra—, y un
    veredicto huérfano: apunta a un sello que no es de ningún preregistro de `prereg/`."""
    arbol = copiar_arbol(tmp_path_factory.mktemp("base_sello_roto"))
    ruta = arbol / "prereg" / PREREG_REAL
    doc = leer_json(ruta)
    doc["umbral_q"] = 0.5
    escribir_json(ruta, doc)
    huerfano = leer_json(arbol / "reportes" / VEREDICTO_REAL)
    huerfano["preregistro"].update({"id": "otra-hipotesis", "sello_sha256": "0" * 64})
    escribir_json(arbol / "reportes" / HUERFANO, huerfano)
    return construir_arbol(arbol)
