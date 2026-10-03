"""Premios mayores ganados y valor esperado del próximo sorteo.

Traslado literal de baseline_auditoria.py:240-262.

Dos cosas que hay que tener presentes al leer las cifras que salen de aquí:

* `valor_esperado` lee `df.BOLSA.iloc[-1]`, que por la regla 2 del CLAUDE.md es la bolsa anunciada
  para el sorteo SIGUIENTE al último del fichero. Con un snapshot congelado eso es un dato
  histórico, no una previsión: el "próximo sorteo" es el que seguía a ese snapshot.
* `menores_brutos` está escrito a mano con los valores de las tablas de ganadores 4271/4272 y
  **caduca**. Sustituirlo por un cálculo real es trabajo de popularity.py, en la Fase 3.
"""
import math

from .constantes import BOLSA_MINIMA, C, PRECIO


def premios_mayores(juego, df):
    """Una baja de BOLSA = premio mayor ganado. Excluye errores (baja seguida de un valor mayor que el anterior).

    Ese filtro es el que descarta, por ejemplo, Revancha 3221 (238.6 M entre 280.3 M y 286.4 M),
    que el CLAUDE.md documenta como error del oficial y no como un premio ganado.
    """
    b = df.BOLSA.where(df.BOLSA >= 1e6).ffill()
    prev, nxt = b.shift(1), b.shift(-1)
    baja = b < prev
    error = baja & (nxt > prev) & (b > 1.5 * BOLSA_MINIMA[juego])
    gano = baja & ~error
    g = df.loc[gano, ["CONCURSO", "FECHA"]].copy()
    g["bolsa_en_juego"] = prev[gano].values
    return g, df.CONCURSO[error].tolist()


def valor_esperado(juegos, combinaciones_vendidas=1.2e6, impuesto=0.07, menores_brutos=None):
    """EV por boleto, con corrección por bolsa compartida entre acertantes."""
    menores_brutos = menores_brutos or {"Melate": 4.38, "Revancha": 2.10, "Revanchita": 0.0}  # de las tablas 4271/4272
    lam = combinaciones_vendidas / C; S = (1 - math.exp(-lam)) / lam
    out = {"supuestos": {"lambda": round(lam, 4), "S": round(S, 4), "impuesto": impuesto}}
    for juego, df in juegos.items():
        J = float(df.BOLSA.iloc[-1])           # fila del último sorteo = bolsa del PRÓXIMO
        evb = J * (1 - impuesto) * S / C
        evm = menores_brutos[juego] * (1 - impuesto)
        out[juego] = {"proximo_sorteo": int(df.CONCURSO.iloc[-1]) + 1, "bolsa_bruta": J, "EV": round(evb + evm, 2),
                      "precio": PRECIO[juego], "rendimiento": round((evb + evm) / PRECIO[juego] - 1, 3),
                      "bolsa_de_equilibrio": round((PRECIO[juego] - evm) * C / ((1 - impuesto) * S))}
    return out
