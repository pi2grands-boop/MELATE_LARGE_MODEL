"""Carga de los CSV históricos.

Diferencia deliberada con baseline_auditoria.py: **el espejo ya no es un fallback de carga.**
`cargar()` lee solo del oficial; si el oficial falla, falla ruidosamente. El espejo se obtiene
con `cargar_espejo()`, de forma explícita, y su único uso es la validación cruzada de la regla 7.

El motivo está documentado en Documentos_Contexto; en corto: el espejo tiene un error en los
números de Revancha 3827 y puede estar parcialmente actualizado (se observó con dos juegos en el
sorteo N+1 y uno en el N). Un fallback silencioso convierte una caída del sitio oficial en datos
malos sin aviso, y en juegos terminando en sorteos distintos, lo que rompe la comparación pareada
que exige el protocolo.
"""
import hashlib
import io
import os
import sys

import numpy as np
import pandas as pd

from .constantes import ESPEJO, N, OFICIAL

_UA = {"User-Agent": "Mozilla/5.0 (proyecto personal de análisis)"}
_COLS_R = ("R1", "R2", "R3", "R4", "R5", "R6")
_COLS_F = ["F1", "F2", "F3", "F4", "F5", "F6"]


def _descargar(url):
    """GET con las mismas cabeceras y validación que la línea base. Devuelve los bytes crudos."""
    import requests

    r = requests.get(url, timeout=30, headers=_UA)
    if not r.ok:
        raise OSError(f"{url} respondió HTTP {r.status_code}")
    if "CONCURSO" not in r.content[:200].decode("utf-8-sig", errors="replace"):
        raise OSError(f"{url} respondió algo que no es el CSV esperado")
    return r.content


def _leer_bytes(juego, carpeta):
    """Lee de una carpeta local, o descarga del oficial. Sin fallback al espejo: ver el docstring.

    Devuelve los BYTES, no el texto: el SHA-256 que se publica es el del fichero tal cual, y
    rehidratarlo desde el texto decodificado daría otro hash.
    """
    if carpeta:
        ruta = os.path.join(carpeta, f"{juego}.csv")
        with open(ruta, "rb") as f:
            return f.read(), ruta
    url = OFICIAL.format(juego)
    try:
        return _descargar(url), url
    except Exception as e:  # noqa: BLE001
        raise SystemExit(
            f"No pude descargar {juego} del oficial ({url}): {e}\n"
            "El espejo NO se usa como respaldo de carga a propósito: tiene un error conocido en los\n"
            "números de Revancha 3827 y puede estar parcialmente actualizado. Si lo necesitas para\n"
            "validar, usa melate.ingest.cargar_espejo(). Para reproducir cifras publicadas, usa un\n"
            "snapshot congelado con --datos."
        ) from e


def _normalizar(crudo, fuente):
    """El parseo común a oficial y espejo. Indexa por NOMBRE de columna, nunca por posición."""
    texto = crudo.decode("utf-8-sig")
    df = pd.read_csv(io.StringIO(texto))
    df.columns = [c.strip().upper() for c in df.columns]
    # El espejo trae columnas extra (ID, PRIMOS, REPETIDOS, MEDIA): por posición se rompería.
    cols = [c for c in _COLS_R if c in df.columns] or _COLS_F
    # Formato oficial: dd/mm/aaaa; espejo: aaaa-mm-dd. La '/' es propiedad del fichero entero,
    # así que mirar la primera fila antes de ordenar es correcto (ver el Bugs del portón).
    df["FECHA"] = pd.to_datetime(df["FECHA"], dayfirst="/" in str(df["FECHA"].iloc[0]))
    df = df.sort_values("CONCURSO").reset_index(drop=True)
    df["nums"] = df[cols].astype(int).values.tolist()
    if "R7" not in df.columns:
        df["R7"] = np.nan
    df["BOLSA"] = pd.to_numeric(df["BOLSA"], errors="coerce")
    df.attrs["fuente"] = fuente
    df.attrs["sha256"] = hashlib.sha256(crudo).hexdigest()
    df.attrs["bytes"] = len(crudo)
    return df[["CONCURSO", "FECHA", "nums", "R7", "BOLSA"]]


def cargar(juego, carpeta=None):
    """DataFrame con CONCURSO, FECHA, nums (lista de 6), R7 (solo Melate), BOLSA.

    En `attrs` deja `fuente`, `sha256` y `bytes` de lo que realmente se leyó: así el hash que se
    publica es el de los datos analizados, y no el de una segunda descarga que podría traer ya el
    sorteo siguiente.
    """
    crudo, fuente = _leer_bytes(juego, carpeta)
    return _normalizar(crudo, fuente)


def cargar_espejo(juego):
    """El espejo de GitHub, explícitamente. Solo para validación cruzada, nunca para analizar."""
    url = ESPEJO.format(juego)
    return _normalizar(_descargar(url), url)


def matriz(nums_list):
    """Lista de sorteos -> matriz indicadora T x 56 de int8."""
    X = np.zeros((len(nums_list), N), dtype=np.int8)
    for i, ns in enumerate(nums_list):
        X[i, np.array(ns) - 1] = 1
    return X


def procedencia(crudos):
    """Hash, origen y tamaño de lo que se cargó. Regla 6: sin esto una cifra no es reproducible.

    Toma los DataFrames ya cargados a propósito. La versión anterior volvía a descargar para
    hashear, y con el oficial publicando un sorteo nuevo a media corrida eso podía registrar el
    hash de unos datos distintos de los analizados.
    """
    return {j: {"sha256": d.attrs["sha256"], "origen": d.attrs["fuente"], "bytes": d.attrs["bytes"]}
            for j, d in crudos.items()}


def versiones():
    """Las versiones que producen las cifras. Sin ellas, 'reproducible' es una palabra vacía."""
    import scipy
    import sklearn

    return {
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
        "scikit-learn": sklearn.__version__,
    }
