"""Backtest walk-forward de 8 estrategias contra el azar.

Traslado literal de baseline_auditoria.py:164-237. Es el módulo más delicado del proyecto por dos
motivos, y los dos están probados en tests/:

1. **No hay fuga temporal.** `variables()` construye F[t] usando solo X[0..t-1], el entrenamiento
   usa `range(100, t)`, y la matriz de Markov no pasa de t-1. tests/test_sin_fuga.py lo verifica
   permutando el futuro y exigiendo que el pasado no cambie.

2. **El orden de consumo del RNG fija los resultados.** `trng` es por juego, pero dentro del bucle
   el orden de las 8 asignaciones de `elec` determina qué número saca: `trng.choice` primero, y
   después cada `top6` consume `rng.random(56)`. Reordenar el diccionario cambia las cifras de
   todas las estrategias posteriores al cambio. tests/test_paridad.py lo vigila.
"""
import math

import numpy as np
from scipy import stats

from .constantes import K, MEDIA_AZAR, N, P_3_O_MAS, SEMILLA_BACKTEST, SEMILLA_HGB, VAR_AZAR
from .ingest import matriz

NOMBRES = ["Aleatorio (Melático)", "Calientes últimos 50", "Más frecuentes (todo el histórico)",
           "Fríos / atrasados", "Repetir sorteo anterior", "Markov (transición)",
           "Regresión logística", "Gradient boosting (HGB)"]


def variables(X):
    """7 variables por número, calculadas SOLO con sorteos anteriores a t."""
    T = X.shape[0]
    # La fila de ceros al principio es lo que hace que cs[t] sea la suma de X[0..t-1].
    cs = np.vstack([np.zeros((1, N)), np.cumsum(X, 0)])

    def ventana(t, w):
        a = max(0, t - w); return (cs[t] - cs[a]) / max(1, t - a)

    ultimo = np.full(N, -1); atraso = np.zeros((T, N))
    for t in range(T):
        atraso[t] = np.where(ultimo >= 0, t - ultimo, t + 1)
        ultimo[X[t] == 1] = t          # se actualiza DESPUÉS de leer: sin esto habría fuga
    F = np.zeros((T, N, 7))
    for t in range(T):
        F[t, :, 0] = ventana(t, 10); F[t, :, 1] = ventana(t, 25); F[t, :, 2] = ventana(t, 50); F[t, :, 3] = ventana(t, 100)
        F[t, :, 4] = cs[t] / max(1, t); F[t, :, 5] = np.minimum(atraso[t], 60) / 60.0
        F[t, :, 6] = X[t - 1] if t > 0 else 0
    return F, atraso


def top6(score, rng):
    """Los 6 mayores, con desempate aleatorio de magnitud 1e-9. Consume rng.random(len(score))."""
    return np.argsort(-(score + rng.random(len(score)) * 1e-9))[:K]


def backtest(df, inicio=400, reentrenar_cada=100):
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import HistGradientBoostingClassifier
    X = matriz(df["nums"].tolist()); T = len(X)
    F, atraso = variables(X)
    trng = np.random.default_rng(SEMILLA_BACKTEST)
    aciertos = {s: [] for s in NOMBRES}
    ll = {s: [] for s in ["Más frecuentes (todo el histórico)", "Regresión logística", "Gradient boosting (HGB)"]}
    p0 = K / N
    ll_azar = -(p0 * math.log(p0) + (1 - p0) * math.log(1 - p0))
    lr = hgb = None
    for t in range(inicio, T):
        y = X[t]
        if (t - inicio) % reentrenar_cada == 0:
            filas = list(range(100, t))          # estrictamente anterior a t
            Xtr = F[filas].reshape(-1, 7); ytr = X[filas].reshape(-1)
            lr = LogisticRegression(max_iter=500).fit(Xtr, ytr)
            hgb = HistGradientBoostingClassifier(max_iter=150, learning_rate=0.05, max_leaf_nodes=15,
                                                 random_state=SEMILLA_HGB).fit(Xtr, ytr)
        # El ORDEN de estas 8 asignaciones fija el consumo de trng. No reordenar.
        elec = {}
        elec["Aleatorio (Melático)"] = trng.choice(N, K, replace=False)
        elec["Calientes últimos 50"] = top6(F[t, :, 2], trng)
        elec["Más frecuentes (todo el histórico)"] = top6(F[t, :, 4], trng)
        elec["Fríos / atrasados"] = top6(atraso[t], trng)
        elec["Repetir sorteo anterior"] = np.where(X[t - 1] == 1)[0]
        trans = X[:t - 1].astype(float).T @ X[1:t].astype(float) + 1.0     # pares hasta t-1
        trans = trans / trans.sum(1, keepdims=True)
        elec["Markov (transición)"] = top6(trans[X[t - 1] == 1].sum(0), trng)
        p_lr = lr.predict_proba(F[t])[:, 1]; p_hgb = hgb.predict_proba(F[t])[:, 1]
        elec["Regresión logística"] = top6(p_lr, trng)
        elec["Gradient boosting (HGB)"] = top6(p_hgb, trng)
        for s, e in elec.items():
            aciertos[s].append(int(y[e].sum()))

        def logloss(p):
            p = np.clip(p, 1e-6, 1 - 1e-6); p = np.clip(p * K / p.sum(), 1e-6, 1 - 1e-6)
            return float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean())

        ll["Más frecuentes (todo el histórico)"].append(logloss(F[t, :, 4] + 1e-9))
        ll["Regresión logística"].append(logloss(p_lr))
        ll["Gradient boosting (HGB)"].append(logloss(p_hgb))
    n = T - inicio
    se = math.sqrt(VAR_AZAR / n)
    out = {"sorteos_prueba": n, "primer_concurso_prueba": int(df.CONCURSO.iloc[inicio]), "media_azar": round(MEDIA_AZAR, 4),
           "efecto_minimo_detectable": round((1.959964 + 0.841621) * se, 4), "estrategias": {}, "logloss": {"azar": round(ll_azar, 5)}}
    for s in NOMBRES:
        h = np.array(aciertos[s]); m = h.mean(); z = (m - MEDIA_AZAR) / se
        out["estrategias"][s] = {"media": round(float(m), 4), "delta": round(float(m - MEDIA_AZAR), 4), "z": round(float(z), 2),
                                 "p": round(float(2 * stats.norm.sf(abs(z))), 4), "3_o_mas": int((h >= 3).sum()),
                                 "3_o_mas_esperados": round(P_3_O_MAS * n, 1)}
    for s, v in ll.items():
        d = np.array(v) - ll_azar; tt = d.mean() / (d.std(ddof=1) / math.sqrt(len(d)))
        out["logloss"][s] = {"delta_vs_azar": round(float(d.mean()), 6), "t": round(float(tt), 2),
                             "p": round(float(2 * stats.t.sf(abs(tt), len(d) - 1)), 4)}
    return out
