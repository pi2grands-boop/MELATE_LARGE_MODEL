"""
baseline_auditoria.py — Línea base verificada para Melate, Revancha y Revanchita (era 6/56).

Qué hace:
  1. Descarga los CSV oficiales de Lotería Nacional (si fallan, usa el espejo de GitHub) y los normaliza.
  2. Valida los datos (rangos, duplicados, concursos faltantes, errores de bolsa conocidos).
  3. Auditoría de aleatoriedad con Monte Carlo (chi-cuadrada corregida, máximos, pares, repetidos).
  4. Poder estadístico: qué tamaño de sesgo se puede detectar con los sorteos disponibles.
  5. Backtest walk-forward de 8 estrategias contra el azar (aciertos, log-loss, Benjamini-Hochberg).
  6. Premios mayores ganados (bajas de BOLSA) y valor esperado del próximo sorteo.

Uso:
  pip install pandas numpy scipy scikit-learn requests
  python baseline_auditoria.py                 # descarga y corre todo (≈2 min)
  python baseline_auditoria.py --datos ./data  # usa CSV locales (oficiales o del espejo)
  python baseline_auditoria.py --sims 500      # auditoría más rápida

Notas de datos (ver CLAUDE.md):
  * BOLSA de la fila N = bolsa anunciada para el sorteo N+1. La bolsa vigente en N es BOLSA(N-1).
  * R1..R6 vienen ordenados: el orden de extracción no está en el archivo.
"""
import argparse, io, json, math, os, sys
from math import comb

import numpy as np
import pandas as pd
from scipy import stats

N, K = 56, 6
C = comb(N, K)
OFICIAL = "https://www.loterianacional.gob.mx/Documentos/Historicos/{}.csv"
ESPEJO = "https://raw.githubusercontent.com/pakinja/pakin/master/{}.csv"
JUEGOS = ["Melate", "Revancha", "Revanchita"]
PRIMER_SORTEO_56 = 2089          # 12-dic-2007; Revanchita empieza en 2371 (25-ago-2010)
PRECIO = {"Melate": 15, "Revancha": 10, "Revanchita": 5}
BOLSA_MINIMA = {"Melate": 30e6, "Revancha": 20e6, "Revanchita": 10e6}

# ---------------------------------------------------------------- carga
def _leer_texto(juego, carpeta):
    if carpeta:
        ruta = os.path.join(carpeta, f"{juego}.csv")
        with open(ruta, encoding="utf-8-sig") as f:
            return f.read(), ruta
    import requests
    for plantilla in (OFICIAL, ESPEJO):
        url = plantilla.format(juego)
        try:
            r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0 (proyecto personal de análisis)"})
            if r.ok and "CONCURSO" in r.text[:200]:
                return r.content.decode("utf-8-sig"), url
        except Exception as e:  # noqa: BLE001
            print(f"  aviso: no se pudo leer {url}: {e}", file=sys.stderr)
    raise SystemExit(f"No pude descargar {juego}.csv (ni oficial ni espejo).")

def cargar(juego, carpeta=None):
    """Devuelve DataFrame con CONCURSO, FECHA, nums (lista de 6), R7 (solo Melate), BOLSA y la fuente."""
    texto, fuente = _leer_texto(juego, carpeta)
    df = pd.read_csv(io.StringIO(texto))
    df.columns = [c.strip().upper() for c in df.columns]
    cols = [c for c in ("R1", "R2", "R3", "R4", "R5", "R6") if c in df.columns] or ["F1", "F2", "F3", "F4", "F5", "F6"]
    # Formato oficial: dd/mm/aaaa; espejo: aaaa-mm-dd
    df["FECHA"] = pd.to_datetime(df["FECHA"], dayfirst="/" in str(df["FECHA"].iloc[0]))
    df = df.sort_values("CONCURSO").reset_index(drop=True)
    df["nums"] = df[cols].astype(int).values.tolist()
    if "R7" not in df.columns:
        df["R7"] = np.nan
    df["BOLSA"] = pd.to_numeric(df["BOLSA"], errors="coerce")
    df.attrs["fuente"] = fuente
    return df[["CONCURSO", "FECHA", "nums", "R7", "BOLSA"]]

# ---------------------------------------------------------------- validación
def validar(juego, df):
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
    q["huecos_mayores_a_10_dias"] = [(int(c), str(f.date()), int(g)) for c, f, g in zip(df.CONCURSO[gaps > 10], df.FECHA[gaps > 10], gaps[gaps > 10])]
    q["bolsa_cero_o_invalida"] = [int(c) for c in df.CONCURSO[(df.BOLSA.fillna(0) < 1e6)]]
    return q

def era_56(juego, df):
    d = df[df.CONCURSO >= PRIMER_SORTEO_56].reset_index(drop=True)
    assert np.array(d["nums"].tolist()).max() <= N
    return d

def matriz(nums_list):
    X = np.zeros((len(nums_list), N), dtype=np.int8)
    for i, ns in enumerate(nums_list):
        X[i, np.array(ns) - 1] = 1
    return X

# ---------------------------------------------------------------- auditoría
def estadisticas(X):
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
    r = rng.random((n, N))
    idx = np.argpartition(r, K, axis=1)[:, :K]
    X = np.zeros((n, N), dtype=np.int8)
    np.put_along_axis(X, idx, 1, axis=1)
    return X

def auditar(juegos, nsim, rng):
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
    # BH sobre las 15 pruebas
    claves = [(j, k) for j in res for k in ("chi2_corr", "max_count", "min_count", "max_pair", "mean_overlap")]
    q = benjamini_hochberg([res[j][k]["p_dos_colas"] for j, k in claves])
    for (j, k), qq in zip(claves, q):
        res[j][k]["q_BH"] = round(qq, 4)
    return res

def benjamini_hochberg(ps):
    ps = np.asarray(ps, float); m = len(ps); orden = np.argsort(ps); q = np.empty(m); prev = 1.0
    for rank, i in list(enumerate(orden, 1))[::-1]:
        prev = min(prev, ps[i] * m / rank); q[i] = prev
    return q.tolist()

# ---------------------------------------------------------------- poder
def n_necesario(delta, alfa, poder=0.8):
    p0 = K / N; p1 = p0 * (1 + delta)
    za = stats.norm.isf(alfa / 2); zb = stats.norm.isf(1 - poder)
    return (za * math.sqrt(p0 * (1 - p0)) + zb * math.sqrt(p1 * (1 - p1))) ** 2 / (p1 - p0) ** 2

def sesgo_minimo(n, alfa, poder=0.8):
    lo, hi = 0.001, 3.0
    for _ in range(80):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if n_necesario(mid, alfa, poder) > n else (lo, mid)
    return hi

# ---------------------------------------------------------------- backtest walk-forward
MEDIA_AZAR = K * K / N
VAR_AZAR = K * (K / N) * ((N - K) / N) * ((N - K) / (N - 1))
P_3_O_MAS = sum(comb(K, k) * comb(N - K, K - k) for k in range(3, 7)) / C

def variables(X):
    """7 variables por número, calculadas SOLO con sorteos anteriores a t."""
    T = X.shape[0]
    cs = np.vstack([np.zeros((1, N)), np.cumsum(X, 0)])
    def ventana(t, w):
        a = max(0, t - w); return (cs[t] - cs[a]) / max(1, t - a)
    ultimo = np.full(N, -1); atraso = np.zeros((T, N))
    for t in range(T):
        atraso[t] = np.where(ultimo >= 0, t - ultimo, t + 1)
        ultimo[X[t] == 1] = t
    F = np.zeros((T, N, 7))
    for t in range(T):
        F[t, :, 0] = ventana(t, 10); F[t, :, 1] = ventana(t, 25); F[t, :, 2] = ventana(t, 50); F[t, :, 3] = ventana(t, 100)
        F[t, :, 4] = cs[t] / max(1, t); F[t, :, 5] = np.minimum(atraso[t], 60) / 60.0
        F[t, :, 6] = X[t - 1] if t > 0 else 0
    return F, atraso

def top6(score, rng):
    return np.argsort(-(score + rng.random(len(score)) * 1e-9))[:K]

def backtest(df, inicio=400, reentrenar_cada=100):
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import HistGradientBoostingClassifier
    X = matriz(df["nums"].tolist()); T = len(X)
    F, atraso = variables(X)
    trng = np.random.default_rng(7)
    nombres = ["Aleatorio (Melático)", "Calientes últimos 50", "Más frecuentes (todo el histórico)", "Fríos / atrasados",
               "Repetir sorteo anterior", "Markov (transición)", "Regresión logística", "Gradient boosting (HGB)"]
    aciertos = {s: [] for s in nombres}
    ll = {s: [] for s in ["Más frecuentes (todo el histórico)", "Regresión logística", "Gradient boosting (HGB)"]}
    p0 = K / N
    ll_azar = -(p0 * math.log(p0) + (1 - p0) * math.log(1 - p0))
    lr = hgb = None
    for t in range(inicio, T):
        y = X[t]
        if (t - inicio) % reentrenar_cada == 0:
            filas = list(range(100, t))
            Xtr = F[filas].reshape(-1, 7); ytr = X[filas].reshape(-1)
            lr = LogisticRegression(max_iter=500).fit(Xtr, ytr)
            hgb = HistGradientBoostingClassifier(max_iter=150, learning_rate=0.05, max_leaf_nodes=15, random_state=0).fit(Xtr, ytr)
        elec = {}
        elec["Aleatorio (Melático)"] = trng.choice(N, K, replace=False)
        elec["Calientes últimos 50"] = top6(F[t, :, 2], trng)
        elec["Más frecuentes (todo el histórico)"] = top6(F[t, :, 4], trng)
        elec["Fríos / atrasados"] = top6(atraso[t], trng)
        elec["Repetir sorteo anterior"] = np.where(X[t - 1] == 1)[0]
        trans = X[:t - 1].astype(float).T @ X[1:t].astype(float) + 1.0
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
    for s in nombres:
        h = np.array(aciertos[s]); m = h.mean(); z = (m - MEDIA_AZAR) / se
        out["estrategias"][s] = {"media": round(float(m), 4), "delta": round(float(m - MEDIA_AZAR), 4), "z": round(float(z), 2),
                                 "p": round(float(2 * stats.norm.sf(abs(z))), 4), "3_o_mas": int((h >= 3).sum()),
                                 "3_o_mas_esperados": round(P_3_O_MAS * n, 1)}
    for s, v in ll.items():
        d = np.array(v) - ll_azar; tt = d.mean() / (d.std(ddof=1) / math.sqrt(len(d)))
        out["logloss"][s] = {"delta_vs_azar": round(float(d.mean()), 6), "t": round(float(tt), 2),
                             "p": round(float(2 * stats.t.sf(abs(tt), len(d) - 1)), 4)}
    return out

# ---------------------------------------------------------------- bolsas y valor esperado
def premios_mayores(juego, df):
    """Una baja de BOLSA = premio mayor ganado. Excluye errores (baja seguida de un valor mayor que el anterior)."""
    b = df.BOLSA.where(df.BOLSA >= 1e6).ffill()
    prev, nxt = b.shift(1), b.shift(-1)
    baja = b < prev
    error = baja & (nxt > prev) & (b > 1.5 * BOLSA_MINIMA[juego])
    gano = baja & ~error
    g = df.loc[gano, ["CONCURSO", "FECHA"]].copy()
    g["bolsa_en_juego"] = prev[gano].values
    return g, df.CONCURSO[error].tolist()

def valor_esperado(juegos, combinaciones_vendidas=1.2e6, impuesto=0.07, menores_brutos=None):
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

# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datos", help="carpeta con Melate.csv, Revancha.csv y Revanchita.csv (si no, descarga)")
    ap.add_argument("--sims", type=int, default=2000)
    ap.add_argument("--salida", default="resultados_baseline.json")
    a = ap.parse_args()
    rng = np.random.default_rng(20261001)

    crudos = {j: cargar(j, a.datos) for j in JUEGOS}
    reporte = {"validacion": {j: validar(j, d) for j, d in crudos.items()}}
    juegos = {j: era_56(j, d) for j, d in crudos.items()}

    print("== Datos (era 6/56)")
    for j, d in juegos.items():
        print(f"  {j:10s} {len(d):5d} sorteos  {int(d.CONCURSO.min())}–{int(d.CONCURSO.max())}  fuente: {crudos[j].attrs['fuente']}")

    print("== Auditoría de aleatoriedad (Monte Carlo, p de dos colas)")
    reporte["auditoria"] = auditar(juegos, a.sims, rng)
    for j, r in reporte["auditoria"].items():
        print(f"  {j:10s} chi2={r['chi2_corr']['obs']:.1f} (p={r['chi2_corr']['p_dos_colas']:.2f})  "
              f"max={r['max_count']['obs']:.0f} (p={r['max_count']['p_dos_colas']:.3f})  "
              f"repetidos={r['mean_overlap']['obs']:.3f} (p={r['mean_overlap']['p_dos_colas']:.2f})")

    reporte["poder"] = {j: {"sorteos": len(d), "sesgo_detectable_1_esfera": round(sesgo_minimo(len(d), 0.05), 3),
                            "sesgo_detectable_56_esferas": round(sesgo_minimo(len(d), 0.05 / 56), 3)} for j, d in juegos.items()}

    print("== Backtest walk-forward (aciertos por boleto de 6; azar = 0.643)")
    reporte["backtest"] = {j: backtest(d) for j, d in juegos.items()}
    claves = [(j, s) for j, b in reporte["backtest"].items() for s in b["estrategias"] if not s.startswith("Aleatorio")]
    qs = benjamini_hochberg([reporte["backtest"][j]["estrategias"][s]["p"] for j, s in claves])
    for (j, s), q in zip(claves, qs):
        reporte["backtest"][j]["estrategias"][s]["q_BH"] = round(q, 4)
    for j, b in reporte["backtest"].items():
        print(f"  -- {j}: {b['sorteos_prueba']} sorteos de prueba desde el {b['primer_concurso_prueba']}")
        for s, v in b["estrategias"].items():
            print(f"     {s:38s} {v['media']:.4f}  Δ={v['delta']:+.4f}  p={v['p']:.3f}  q={v.get('q_BH', '-')}")

    print("== Premios mayores (bajas de BOLSA)")
    reporte["premios_mayores"] = {}
    for j, d in juegos.items():
        g, errores = premios_mayores(j, d)
        reporte["premios_mayores"][j] = {"ganados": len(g), "sorteos": len(d), "errores_de_bolsa": errores,
                                         "mayores": g.sort_values("bolsa_en_juego", ascending=False).head(5).astype(str).values.tolist()}
        print(f"  {j:10s} {len(g)} premios mayores en {len(d)} sorteos (1 cada {len(d) / max(1, len(g)):.0f})")

    reporte["valor_esperado_proximo"] = valor_esperado(juegos)
    print("== Valor esperado del próximo sorteo (supuestos en el JSON)")
    for j in JUEGOS:
        v = reporte["valor_esperado_proximo"][j]
        print(f"  {j:10s} sorteo {v['proximo_sorteo']}: bolsa {v['bolsa_bruta'] / 1e6:.1f} M -> EV ${v['EV']:.2f} de ${v['precio']} "
              f"({v['rendimiento']:+.0%}); equilibrio ≈ {v['bolsa_de_equilibrio'] / 1e6:.0f} M")

    with open(a.salida, "w", encoding="utf-8") as f:
        json.dump(reporte, f, ensure_ascii=False, indent=1, default=str)
    print(f"\nReporte completo en {a.salida}")

if __name__ == "__main__":
    main()
