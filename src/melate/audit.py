"""Auditoría de aleatoriedad de la urna y poder estadístico.

Traslado de baseline_auditoria.py:99-157, con un solo cambio estructural: `auditar()` ya no
aplica Benjamini-Hochberg al final. Eso ahora lo hace `protocolo.aplicar_familias()`, porque la
corrección tiene que poder calcularse también sobre la familia global de 36 pruebas y necesita un
dueño único. El contenido del reporte no cambia.
"""
import math

import numpy as np
from scipy import stats

from .constantes import K, N
from .ingest import matriz


def estadisticas(X):
    """Los 5 estadísticos de la urna. Determinista: ni RNG ni modelos."""
    n = X.shape[0]
    cnt = X.sum(0).astype(float)
    E = n * K / N
    chi = ((cnt - E) ** 2 / E).sum() * (N - 1) / (N - K)      # corrección por extracción sin reemplazo
    Xf = X.astype(np.float32)
    pares = (Xf.T @ Xf)[np.triu_indices(N, 1)]
    repetidos = (X[1:] & X[:-1]).sum(1).mean()
    return {"chi2_corr": float(chi), "max_count": float(cnt.max()), "min_count": float(cnt.min()),
            "max_pair": float(pares.max()), "mean_overlap": float(repetidos)}


def simular(n, rng):
    """n sorteos uniformes de 6 de 56."""
    r = rng.random((n, N))
    idx = np.argpartition(r, K, axis=1)[:, :K]
    X = np.zeros((n, N), dtype=np.int8)
    np.put_along_axis(X, idx, 1, axis=1)
    return X


def auditar(juegos, nsim, rng):
    """Monte Carlo: observado contra nsim urnas limpias, p de dos colas.

    OJO: `rng` se comparte entre los tres juegos y se consume en el orden de `juegos`. Cambiar ese
    orden, o paralelizar, cambia todos los p-valores. No es un detalle de estilo.
    """
    res = {}
    for juego, df in juegos.items():
        X = matriz(df["nums"].tolist())
        obs = estadisticas(X)
        sims = [estadisticas(simular(len(df), rng)) for _ in range(nsim)]
        r = {"sorteos": len(df)}
        for k, v in obs.items():
            sv = np.array([s[k] for s in sims])
            p = min(1.0, 2 * min((np.sum(sv >= v) + 1) / (nsim + 1), (np.sum(sv <= v) + 1) / (nsim + 1)))
            r[k] = {"obs": round(v, 4), "media_sim": round(float(sv.mean()), 4), "p_dos_colas": round(p, 4)}
        cnt = X.sum(0)
        orden = np.argsort(-cnt)
        r["mas_frecuentes"] = [(int(i + 1), int(cnt[i])) for i in orden[:5]]
        r["menos_frecuentes"] = [(int(i + 1), int(cnt[i])) for i in orden[-5:]]
        res[juego] = r
    return res


def n_necesario(delta, alfa, poder=0.8):
    """Sorteos necesarios para detectar un sesgo relativo `delta` en una esfera."""
    p0 = K / N; p1 = p0 * (1 + delta)
    za = stats.norm.isf(alfa / 2); zb = stats.norm.isf(1 - poder)
    return (za * math.sqrt(p0 * (1 - p0)) + zb * math.sqrt(p1 * (1 - p1))) ** 2 / (p1 - p0) ** 2


def sesgo_minimo(n, alfa, poder=0.8):
    """El sesgo más pequeño detectable con n sorteos. Búsqueda binaria sobre n_necesario."""
    lo, hi = 0.001, 3.0
    for _ in range(80):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if n_necesario(mid, alfa, poder) > n else (lo, mid)
    return hi
