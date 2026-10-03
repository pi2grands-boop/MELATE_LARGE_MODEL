"""Corrección por comparaciones múltiples.

Vive en su propio módulo por dos razones: `benjamini_hochberg` la usan `audit` y `backtest`, y la
familia global necesita un dueño único.

Sobre las familias — decisión tomada con el usuario:

La regla 3 del protocolo del CLAUDE.md pide Benjamini-Hochberg "sobre TODAS las pruebas corridas,
también las que no se reportan". `baseline_auditoria.py` lo aplica en dos familias separadas: 15
pruebas de auditoría (3 juegos x 5 estadísticos) y 21 de backtest (3 juegos x 7 estrategias, sin
contar la aleatoria, que es la referencia y no una hipótesis).

Se conservan las dos familias, porque son las que producen los `q` publicados en el CLAUDE.md, y
**se añade** la familia global de 36 pruebas bajo la clave `q_BH_global`. Para declarar ventaja
manda la global: es la que cumple la regla 3. La clave `q_BH` no se renombra porque el reporte del
oráculo depende de ella.
"""
import numpy as np

ESTADISTICOS = ("chi2_corr", "max_count", "min_count", "max_pair", "mean_overlap")


def benjamini_hochberg(ps):
    """q-valores de BH. Traslado literal de baseline_auditoria.py:140-144."""
    ps = np.asarray(ps, float); m = len(ps); orden = np.argsort(ps); q = np.empty(m); prev = 1.0
    for rank, i in list(enumerate(orden, 1))[::-1]:
        prev = min(prev, ps[i] * m / rank); q[i] = prev
    return q.tolist()


def claves_auditoria(auditoria):
    """Las 15 pruebas de la auditoría, en el orden del oráculo."""
    return [(j, k) for j in auditoria for k in ESTADISTICOS]


def claves_backtest(backtest):
    """Las 21 pruebas del backtest. La estrategia aleatoria es la referencia, no una hipótesis."""
    return [(j, s) for j, b in backtest.items() for s in b["estrategias"]
            if not s.startswith("Aleatorio")]


def aplicar_familias(auditoria, backtest):
    """Las dos familias del oráculo, bajo la clave `q_BH`. Modifica los dicts en sitio."""
    ca = claves_auditoria(auditoria)
    for (j, k), q in zip(ca, benjamini_hochberg([auditoria[j][k]["p_dos_colas"] for j, k in ca])):
        auditoria[j][k]["q_BH"] = round(q, 4)

    cb = claves_backtest(backtest)
    for (j, s), q in zip(cb, benjamini_hochberg([backtest[j]["estrategias"][s]["p"] for j, s in cb])):
        backtest[j]["estrategias"][s]["q_BH"] = round(q, 4)


def aplicar_global(auditoria, backtest):
    """La familia única de 36 pruebas que pide la regla 3, bajo `q_BH_global`.

    Devuelve un resumen con el tamaño de la familia y si alguna prueba sobrevive a q <= 0.05.
    """
    ca = claves_auditoria(auditoria)
    cb = claves_backtest(backtest)
    ps = ([auditoria[j][k]["p_dos_colas"] for j, k in ca]
          + [backtest[j]["estrategias"][s]["p"] for j, s in cb])
    qs = benjamini_hochberg(ps)

    for (j, k), q in zip(ca, qs[:len(ca)]):
        auditoria[j][k]["q_BH_global"] = round(q, 4)
    for (j, s), q in zip(cb, qs[len(ca):]):
        backtest[j]["estrategias"][s]["q_BH_global"] = round(q, 4)

    sobreviven = ([f"auditoria/{j}/{k}" for (j, k), q in zip(ca, qs[:len(ca)]) if q <= 0.05]
                  + [f"backtest/{j}/{s}" for (j, s), q in zip(cb, qs[len(ca):]) if q <= 0.05])
    return {
        "pruebas": len(ps),
        "pruebas_auditoria": len(ca),
        "pruebas_backtest": len(cb),
        "umbral": 0.05,
        "q_minima": round(min(qs), 4),
        "sobreviven_a_q_0.05": sobreviven,
        "veredicto": "sin ventaja demostrada" if not sobreviven else "revisar: hay pruebas con q <= 0.05",
    }
