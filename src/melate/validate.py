"""Validación de las reglas de datos del CLAUDE.md.

`validar()` es el traslado literal de baseline_auditoria.py:72-85 y no se toca: el reporte del
oráculo depende de que devuelva exactamente lo mismo.

Lo que se añade es `validar_era()`, que corre las mismas comprobaciones sobre la era 6/56. Motivo:
el fichero crudo de Melate arranca en 1984, cuando las bolsas eran mucho menores, así que
`validar()` reporta 174 filas con BOLSA < 1 M de las que solo 3 son errores reales. El dato útil
quedaba sepultado en el ruido.
"""
import numpy as np

from .constantes import N, PRIMER_SORTEO_56


def validar(juego, df):
    """Las 9 comprobaciones de la línea base, sobre el fichero tal cual llegó."""
    q = {"fuente": df.attrs.get("fuente"), "filas": len(df), "primero": int(df.CONCURSO.min()),
         "ultimo": int(df.CONCURSO.max()), "ultima_fecha": str(df.FECHA.max().date())}
    q["concursos_faltantes"] = sorted(set(range(q["primero"], q["ultimo"] + 1)) - set(df.CONCURSO))
    q["duplicados"] = int(df.CONCURSO.duplicated().sum())
    arr = np.array(df["nums"].tolist())
    q["fuera_de_rango"] = int(((arr < 1) | (arr > N)).sum())
    q["filas_no_ordenadas_o_repetidas"] = int((np.diff(arr, axis=1) <= 0).any(axis=1).sum())
    if juego == "Melate":
        q["adicional_repetido_en_naturales"] = int(sum(int(r7) in set(n) for r7, n in zip(df.R7, df.nums)))
    gaps = df.FECHA.diff().dt.days
    q["huecos_mayores_a_10_dias"] = [(int(c), str(f.date()), int(g)) for c, f, g in
                                     zip(df.CONCURSO[gaps > 10], df.FECHA[gaps > 10], gaps[gaps > 10])]
    q["bolsa_cero_o_invalida"] = [int(c) for c in df.CONCURSO[(df.BOLSA.fillna(0) < 1e6)]]
    return q


def era_56(juego, df):
    """Filtra la era 6/56. Revanchita nace en el 2371, pero su fichero ya empieza ahí."""
    d = df[df.CONCURSO >= PRIMER_SORTEO_56].reset_index(drop=True)
    assert np.array(d["nums"].tolist()).max() <= N
    return d


def validar_era(juego, df):
    """Las mismas comprobaciones, pero solo sobre la era 6/56: es la que se analiza."""
    d = era_56(juego, df)
    # era_56 es traslado literal y no se toca; la fuente se vuelve a poner aquí porque el
    # filtrado booleano no garantiza que attrs sobreviva.
    d.attrs["fuente"] = df.attrs.get("fuente")
    return validar(juego, d)
