"""Fixtures compartidas.

Las corridas completas (2000 simulaciones + 3 backtests) tardan medio minuto o más cada una, así
que se generan **una vez por sesión** y se reparten entre los tests que las necesitan. Los tests
que solo leen los CSV no pasan por aquí y son instantáneos.
"""
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
def copiar_arbol(destino):
    """Una copia de `reportes/` y `prereg/` en `destino`, con la estructura del repositorio.

    Los tests de la base y de la app trabajan siempre sobre una copia: nunca escriben en la
    `melate.duckdb` de la raíz, que es la que está usando la app.
    """
    shutil.copytree(RAIZ / "reportes", destino / "reportes")
    shutil.copytree(RAIZ / "prereg", destino / "prereg")
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
    """`melate.duckdb` construida con los reportes y el preregistro del repositorio, tal cual."""
    return construir_arbol(copiar_arbol(tmp_path_factory.mktemp("base_real")))


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
    escribir_json(arbol / "reportes" / nombre, v)
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
