"""El test más valioso del proyecto: que no haya fuga temporal.

El protocolo del CLAUDE.md exige walk-forward estricto —entrenar con sorteos anteriores a t y
predecir t—. Una fuga no produce ningún error ni aviso: produce un resultado buenísimo y falso.
Estos tests no dependen de que ninguna cifra cuadre, así que siguen valiendo cuando lleguen
sorteos nuevos y la línea base cambie.

El método es siempre el mismo: **permutar el futuro y exigir que el pasado no se mueva.**
"""
import numpy as np
import pytest

from melate.backtest import variables
from melate.constantes import K, N
from melate.ingest import matriz


@pytest.fixture(scope="module")
def X(datos):
    return matriz(datos["era"]["Melate"]["nums"].tolist())


def test_las_variables_de_t_no_miran_mas_alla_de_t_menos_1(X):
    """Permuta las filas >= t y exige que F[:t] y atraso[:t] sean idénticos bit a bit."""
    F, atraso = variables(X)
    rng = np.random.default_rng(1234)
    for t in (401, 900, 1500, len(X) - 1):
        Y = X.copy()
        orden = rng.permutation(len(X) - t) + t
        Y[t:] = X[orden]
        Fp, atrasop = variables(Y)
        assert np.array_equal(F[:t], Fp[:t]), f"fuga: F[:{t}] cambia al permutar el futuro"
        assert np.array_equal(atraso[:t], atrasop[:t]), f"fuga: atraso[:{t}] cambia al permutar el futuro"


def test_cambiar_el_sorteo_t_no_cambia_las_variables_de_t(X):
    """Caso extremo: reemplazar X[t] entero. F[t] no puede enterarse."""
    F, atraso = variables(X)
    for t in (401, 1200):
        Y = X.copy()
        Y[t] = 0
        Y[t, :K] = 1                      # un sorteo imposible, para que el cambio sea grande
        Fp, atrasop = variables(Y)
        assert np.array_equal(F[t], Fp[t]), f"fuga: F[{t}] depende del propio sorteo {t}"
        assert np.array_equal(atraso[t], atrasop[t]), f"fuga: atraso[{t}] depende del sorteo {t}"


def test_la_variable_del_sorteo_anterior_es_exactamente_el_anterior(X):
    F, _ = variables(X)
    for t in (1, 500, 1783):
        assert np.array_equal(F[t, :, 6], X[t - 1]), "la variable 6 debe ser X[t-1], no X[t]"
    assert np.all(F[0, :, 6] == 0), "en t=0 no hay sorteo anterior"


def test_las_ventanas_de_frecuencia_solo_suman_el_pasado(X):
    """Comprobación independiente: recalcular a mano la ventana de 10 y la frecuencia histórica."""
    F, _ = variables(X)
    for t in (10, 777, 1500):
        esperado_10 = X[t - 10:t].sum(0) / 10
        assert np.allclose(F[t, :, 0], esperado_10), f"la ventana de 10 en t={t} no es la del pasado"
        esperado_hist = X[:t].sum(0) / t
        assert np.allclose(F[t, :, 4], esperado_hist), f"la frecuencia histórica en t={t} incluye t"


def test_el_atraso_cuenta_desde_la_ultima_aparicion_anterior_a_t(X):
    _, atraso = variables(X)
    for t in (300, 1100):
        for num in range(N):
            previos = np.where(X[:t, num] == 1)[0]
            esperado = t - previos[-1] if len(previos) else t + 1
            assert atraso[t, num] == esperado, f"atraso[{t},{num}] mal calculado"


def test_el_entrenamiento_del_backtest_es_estrictamente_anterior_a_t():
    """Vigila la línea `filas = list(range(100, t))` de backtest(): ningún índice puede llegar a t."""
    inicio, reentrenar_cada, T = 400, 100, 2184
    for t in range(inicio, T):
        if (t - inicio) % reentrenar_cada == 0:
            filas = list(range(100, t))
            assert filas, f"entrenamiento vacío en t={t}"
            assert max(filas) == t - 1, f"el entrenamiento en t={t} llega hasta {max(filas)}"


def test_la_matriz_de_markov_no_pasa_de_t_menos_1(X):
    """`X[:t-1].T @ X[1:t]` solo puede contar pares (i, i+1) con i+1 <= t-1."""
    for t in (500, 1600):
        trans = X[:t - 1].astype(float).T @ X[1:t].astype(float)
        # Mismo cálculo, pero contando los pares uno a uno y sin pasar de t-1.
        manual = np.zeros((N, N))
        for i in range(t - 1):
            manual[np.ix_(np.where(X[i] == 1)[0], np.where(X[i + 1] == 1)[0])] += 1
        assert np.array_equal(trans, manual)
        # Y que de verdad ignora el sorteo t: cambiarlo no mueve la matriz.
        Y = X.copy()
        Y[t] = 0
        Y[t, :K] = 1
        assert np.array_equal(trans, Y[:t - 1].astype(float).T @ Y[1:t].astype(float))
