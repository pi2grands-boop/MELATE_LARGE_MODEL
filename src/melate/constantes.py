"""Constantes del juego y de la línea base del azar.

Trasladadas literalmente de baseline_auditoria.py (líneas 29-36 y 160-162). Viven aquí porque
las comparten ingest, validate, audit, backtest y ev: duplicarlas en cada módulo es la forma
más rápida de que un día dejen de coincidir.
"""
from math import comb

N, K = 56, 6
C = comb(N, K)

OFICIAL = "https://www.loterianacional.gob.mx/Documentos/Historicos/{}.csv"
ESPEJO = "https://raw.githubusercontent.com/pakinja/pakin/master/{}.csv"
JUEGOS = ["Melate", "Revancha", "Revanchita"]

PRIMER_SORTEO_56 = 2089          # 12-dic-2007; Revanchita empieza en 2371 (25-ago-2010)
PRECIO = {"Melate": 15, "Revancha": 10, "Revanchita": 5}
BOLSA_MINIMA = {"Melate": 30e6, "Revancha": 20e6, "Revanchita": 10e6}

# Línea base del azar para un boleto de 6 números.
MEDIA_AZAR = K * K / N                                                   # 0.642857
VAR_AZAR = K * (K / N) * ((N - K) / N) * ((N - K) / (N - 1))             # desviación 0.722357
P_3_O_MAS = sum(comb(K, k) * comb(N - K, K - k) for k in range(3, 7)) / C  # 1/79.06

# Semillas de la línea base. Cambiarlas cambia todas las cifras publicadas en CLAUDE.md.
SEMILLA_AUDITORIA = 20261001
SEMILLA_BACKTEST = 7
SEMILLA_HGB = 0
