"""Fixtures compartidas.

Las corridas completas (2000 simulaciones + 3 backtests) tardan medio minuto o más cada una, así
que se generan **una vez por sesión** y se reparten entre los tests que las necesitan. Los tests
que solo leen los CSV no pasan por aquí y son instantáneos.
"""
import json
import os
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
