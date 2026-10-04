"""Las herramientas de verificación, verificadas.

El colador y el verificador de la bitácora traen su autoprueba. `scripts/mutar.py` no la tenía, y
su primera versión fallaba en silencio: comprobaba el texto a mutar con los saltos de línea
normalizados y lo sustituía en los bytes, así que en un fichero con CRLF una mutación con salto de
línea no se aplicaba. Lo destapó la propia herramienta, con una mutación «no detectada» que en
realidad no había mutado nada.
"""
import importlib.util

import pytest


@pytest.fixture(scope="module")
def mutar(raiz):
    spec = importlib.util.spec_from_file_location("mutar", raiz / "scripts" / "mutar.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.mark.parametrize("fin", ["\n", "\r\n"])
def test_la_mutacion_se_aplica_con_cualquier_final_de_linea(mutar, tmp_path, fin):
    f = tmp_path / "x.py"
    antes = f"a = 1{fin}b = 2{fin}c = 3{fin}".encode()
    f.write_bytes(antes)
    original = mutar.mutar(f, "a = 1\nb = 2\n", "a = 0\n")
    assert original == antes, "devuelve los bytes de antes, para restaurarlos"
    assert f.read_bytes() == f"a = 0{fin}c = 3{fin}".encode(), "y respeta el final de línea"


def test_una_mutacion_que_no_muta_nada_no_se_cuenta(mutar, tmp_path):
    f = tmp_path / "x.py"
    f.write_bytes(b"a = 1\na = 1\n")
    with pytest.raises(ValueError, match="0 veces"):
        mutar.mutar(f, "no está", "x")
    with pytest.raises(ValueError, match="2 veces"):
        mutar.mutar(f, "a = 1", "a = 2")
    f.write_bytes(b"a = 1\n")
    with pytest.raises(ValueError, match="ningún byte"):
        mutar.mutar(f, "a = 1", "a = 1")
    assert f.read_bytes() == b"a = 1\n", "si se niega, el fichero queda como estaba"


def test_las_mutaciones_del_proyecto_estan_bien_definidas(mutar, raiz):
    """Cada mutación de la lista se aplica sobre el fichero real: texto una vez, y algún cambio.

    Se comprueba sobre una copia en memoria: el árbol de trabajo no se toca.
    """
    for nombre, fichero, buscar, poner, ficheros, expresion in mutar.MUTACIONES:
        texto = (raiz / fichero).read_bytes().decode("utf-8").replace("\r\n", "\n")
        assert texto.count(buscar) == 1, f"{nombre}: el texto aparece {texto.count(buscar)} veces"
        assert buscar != poner, nombre
        for f in ficheros.split():
            assert (raiz / f).is_file(), f"{nombre}: no existe {f}"
