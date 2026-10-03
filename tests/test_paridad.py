"""El paquete tiene que dar exactamente lo mismo que el oráculo.

Es el test bloqueante de la Fase 1. Si falla, el refactor cambió una cifra, y el candidato número
uno es el orden de consumo del RNG: `auditar()` comparte un `rng` entre los tres juegos en el orden
de JUEGOS, y dentro del bucle de `backtest()` el orden de las 8 asignaciones de `elec` determina
qué número saca `trng`.

Tolerancia cero: mismos datos y mismas semillas tienen que dar los mismos bits. Lo único que se
ignora son las claves que el paquete añade a propósito, declaradas en melate.informe.NUEVAS_CLAVES.
"""
import pytest

from melate.informe import NUEVAS_CLAVES

IGNORAR_RAIZ = set(NUEVAS_CLAVES["raiz"])
IGNORAR_HOJA = set(NUEVAS_CLAVES["hoja"])


def diferencias(a, b, ruta="", ignorar_raiz=()):
    """Compara recursivamente y devuelve la lista de rutas que difieren, con sus valores."""
    difs = []
    if isinstance(a, dict) and isinstance(b, dict):
        faltan = set(a) - set(b) - set(ignorar_raiz)
        if faltan:
            difs.append(f"{ruta or '/'}: el paquete no tiene {sorted(faltan)}")
        for k in a:
            if k in ignorar_raiz or k in IGNORAR_HOJA or k not in b:
                continue
            difs += diferencias(a[k], b[k], f"{ruta}/{k}")
        sobran = set(b) - set(a) - IGNORAR_RAIZ - IGNORAR_HOJA
        if sobran:
            difs.append(f"{ruta or '/'}: el paquete añade sin declarar {sorted(sobran)}")
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            difs.append(f"{ruta}: longitudes {len(a)} vs {len(b)}")
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                difs += diferencias(x, y, f"{ruta}[{i}]")
    elif a != b:
        difs.append(f"{ruta}: oráculo {a!r} != paquete {b!r}")
    return difs


@pytest.mark.lento
def test_el_paquete_reproduce_el_oraculo(oraculo, paquete):
    difs = diferencias(oraculo, paquete, ignorar_raiz=IGNORAR_RAIZ)
    assert not difs, "el paquete no reproduce el oráculo:\n  " + "\n  ".join(difs[:25])


@pytest.mark.lento
def test_las_claves_nuevas_estan_todas(paquete):
    """Si una clave nueva desaparece, el test de paridad la ignoraría en silencio."""
    for k in NUEVAS_CLAVES["raiz"]:
        assert k in paquete, f"falta la clave nueva {k}"
    estrategias = paquete["backtest"]["Revancha"]["estrategias"]
    assert "q_BH_global" in estrategias["Regresión logística"]
    assert "q_BH" in estrategias["Regresión logística"], "la clave del oráculo no se renombra"


@pytest.mark.lento
def test_la_familia_global_tiene_36_pruebas(paquete):
    """Regla 3 del protocolo: BH sobre TODAS las pruebas corridas."""
    g = paquete["protocolo_global"]
    assert g["pruebas_auditoria"] == 15, "3 juegos x 5 estadísticos"
    assert g["pruebas_backtest"] == 21, "3 juegos x 7 estrategias (la aleatoria es referencia)"
    assert g["pruebas"] == 36


@pytest.mark.lento
def test_la_familia_global_es_mas_estricta_donde_importa(paquete):
    """La q global de la mejor prueba no puede ser mejor que su q de familia por casualidad.

    No es una desigualdad universal —BH no la garantiza prueba a prueba—, pero sí tiene que
    cumplirse que ninguna prueba pase el umbral solo por haber usado la familia pequeña.
    """
    g = paquete["protocolo_global"]
    assert g["sobreviven_a_q_0.05"] == [], f"algo sobrevive a q<=0.05: {g['sobreviven_a_q_0.05']}"
    assert g["veredicto"] == "sin ventaja demostrada"


@pytest.mark.lento
def test_la_reproducibilidad_queda_registrada(paquete):
    """Regla 6 del protocolo: hash del dataset y semilla en cada corrida."""
    r = paquete["reproducibilidad"]
    assert r["semillas"] == {"auditoria": 20261001, "backtest": 7, "hgb": 0}
    assert r["simulaciones"] == 2000
    for juego in ("Melate", "Revancha", "Revanchita"):
        assert len(r["datos"][juego]["sha256"]) == 64
    for lib in ("python", "numpy", "pandas", "scipy", "scikit-learn"):
        assert r["versiones"][lib], f"falta la versión de {lib}"


@pytest.mark.lento
def test_el_hash_registrado_es_el_de_los_datos_analizados(paquete, snapshot):
    """El hash tiene que salir de los bytes que se cargaron, no de una segunda descarga.

    Si se volviera a leer la fuente para hashear, una publicación a media corrida —el oficial
    sacando el sorteo siguiente— registraría el hash de unos datos distintos de los analizados,
    que es exactamente lo contrario de lo que pide la regla 6.
    """
    import hashlib

    for juego, d in paquete["reproducibilidad"]["datos"].items():
        crudo = (snapshot / f"{juego}.csv").read_bytes()
        assert d["sha256"] == hashlib.sha256(crudo).hexdigest()
        assert d["bytes"] == len(crudo)
    # Y debe cuadrar con el SHA256.txt que se publicó junto al snapshot.
    publicado = dict(l.split()[::-1] for l in (snapshot / "SHA256.txt").read_text().splitlines() if l.strip())
    for juego, d in paquete["reproducibilidad"]["datos"].items():
        assert publicado[f"{juego}.csv"] == d["sha256"]


def test_salida_robusta_no_revienta_con_una_pagina_de_codigos_estrecha():
    """La versión rápida del test de codificación: comprueba el mecanismo, no el programa entero.

    Los dos tests de subproceso de abajo tardan 14 s cada uno porque arrancan un informe completo,
    y eso los saca del bucle del día a día. Este cubre la misma causa raíz en milisegundos: un flujo
    con una codificación que no puede representar 'Δ' no debe hacer estallar una escritura.
    """
    import io
    import sys

    from melate.informe import _salida_robusta

    crudo = io.BytesIO()
    flujo = io.TextIOWrapper(crudo, encoding="cp1252", newline="")
    original = sys.stdout
    try:
        sys.stdout = flujo
        _salida_robusta()
        print("Δ ≈ – delta")          # sin el arreglo, esto lanza UnicodeEncodeError
        sys.stdout.flush()
    finally:
        sys.stdout = original
    assert crudo.getvalue(), "no se escribió nada"


@pytest.mark.lento
def test_la_salida_se_crea_aunque_no_exista_la_carpeta(tmp_path, snapshot, raiz):
    """En un clon nuevo reportes/ no existe, y el informe no puede morir por eso.

    Sin `env=`: hereda el entorno real, así que también comprueba que el informe sobrevive a la
    codificación que le toque. Marcado `lento`: arranca un informe completo, 14 s.
    """
    import subprocess
    import sys

    destino = tmp_path / "sin" / "crear" / "informe.json"
    r = subprocess.run([sys.executable, "-m", "melate.informe", "--datos", str(snapshot),
                        "--sims", "2", "--salida", str(destino)],
                       cwd=raiz, capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 0, r.stderr[-2000:]
    assert destino.is_file()


@pytest.mark.lento
def test_el_informe_sobrevive_a_una_codificacion_hostil(tmp_path, snapshot, raiz):
    """Fija el arreglo de `_salida_robusta`, con la codificación que lo rompía.

    Marcado `lento`: arranca un informe completo, 14 s. La versión rápida del mismo mecanismo está
    en `test_salida_robusta_no_revienta_con_una_pagina_de_codigos_estrecha`.

    El resumen imprime 'Δ', '≈' y '–', que no existen en cp1252. Cuando la salida va a una tubería,
    Python usa la codificación local y el proceso moría con UnicodeEncodeError **a mitad del
    informe**, después de gastar el cómputo. En consola no pasaba, así que el fallo dependía del
    shell desde el que se lanzara: la suite pasaba o fallaba según quién la corriera.

    Aquí se fuerza cp1252 a propósito. Sin el arreglo, este test falla.
    """
    import os
    import subprocess
    import sys

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "cp1252"
    destino = tmp_path / "hostil.json"
    r = subprocess.run([sys.executable, "-m", "melate.informe", "--datos", str(snapshot),
                        "--sims", "2", "--salida", str(destino)],
                       cwd=raiz, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env=env)
    assert r.returncode == 0, f"murió con cp1252:\n{r.stdout[-1500:]}\n{r.stderr[-1500:]}"
    assert "UnicodeEncodeError" not in r.stderr
    assert destino.is_file(), "el informe no llegó a escribir el JSON"
