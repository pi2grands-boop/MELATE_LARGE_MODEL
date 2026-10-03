"""Reproducir la sección "Línea base verificada" del CLAUDE.md, cifra por cifra.

Las constantes del azar son exactas y se comprueban sin correr nada. Las cifras del reporte
necesitan la corrida completa y van marcadas `lento`.

Las dos cifras de Revancha son las corregidas el 2026-10-02: el CLAUDE.md daba 42.03 y 0.6861,
calculadas con el espejo, que tiene mal el sexto número de Revancha 3827. Evidencia en
Documentos_Contexto/Fases/2026-10-02_arranque/Bugs/.
"""
import math

import pytest

from melate.constantes import C, K, MEDIA_AZAR, N, P_3_O_MAS, PRECIO, VAR_AZAR


# --------------------------------------------------------------- constantes, sin correr nada
def test_constantes_del_juego():
    assert C == 32_468_436
    assert (N, K) == (56, 6)
    assert PRECIO == {"Melate": 15, "Revancha": 10, "Revanchita": 5}


def test_linea_base_del_azar():
    assert MEDIA_AZAR == pytest.approx(0.642857, abs=5e-7)
    assert math.sqrt(VAR_AZAR) == pytest.approx(0.722357, abs=5e-7)
    assert 1 / P_3_O_MAS == pytest.approx(79.06, abs=5e-3)


def test_log_loss_del_azar():
    p0 = K / N
    ll = -(p0 * math.log(p0) + (1 - p0) * math.log(1 - p0))
    assert ll == pytest.approx(0.340500, abs=5e-7)


def test_efecto_minimo_detectable_con_1784_sorteos():
    """Regla 5 del protocolo: 0.048 aciertos con 1,784 sorteos de prueba."""
    emd = (1.959964 + 0.841621) * math.sqrt(VAR_AZAR / 1784)
    assert emd == pytest.approx(0.048, abs=5e-4)


# --------------------------------------------------------------- cifras del reporte completo
@pytest.mark.lento
def test_sorteos_de_la_era(paquete):
    assert paquete["auditoria"]["Melate"]["sorteos"] == 2184
    assert paquete["auditoria"]["Revancha"]["sorteos"] == 2184
    assert paquete["auditoria"]["Revanchita"]["sorteos"] == 1902


@pytest.mark.lento
@pytest.mark.parametrize("juego,chi2,p", [
    ("Melate", 52.19, 0.85),
    ("Revancha", 42.29, 0.22),      # corregido: el CLAUDE.md decía 42.03 (dato del espejo)
    ("Revanchita", 54.83, 0.98),
])
def test_chi_cuadrada_corregida(paquete, juego, chi2, p):
    """El CLAUDE.md publica estas cifras redondeadas; se comprueba que el reporte redondea a ellas.

    Comparar así, y no con una tolerancia inventada, es lo que hace que el test detecte de verdad
    una discrepancia entre el documento y el código, que es justo lo que falló en el portón.
    """
    a = paquete["auditoria"][juego]["chi2_corr"]
    assert round(a["obs"], 2) == chi2
    assert round(a["p_dos_colas"], 2) == p


@pytest.mark.lento
def test_inicio_del_backtest(paquete):
    assert paquete["backtest"]["Melate"]["primer_concurso_prueba"] == 2489
    assert paquete["backtest"]["Revancha"]["primer_concurso_prueba"] == 2489
    assert paquete["backtest"]["Revanchita"]["primer_concurso_prueba"] == 2771
    assert paquete["backtest"]["Melate"]["sorteos_prueba"] == 1784
    assert paquete["backtest"]["Revanchita"]["sorteos_prueba"] == 1502


@pytest.mark.lento
def test_regresion_logistica_en_revancha(paquete):
    """La cifra corregida. El CLAUDE.md daba 0.6861 (p = 0.011, q = 0.24), calculada con el espejo.

    El reporte guarda p = 0.0165 y q = 0.3465; el CLAUDE.md los publica como 0.017 y 0.35, con los
    mismos decimales que usaba antes. Se comprueba el redondeo, no una tolerancia arbitraria.
    """
    e = paquete["backtest"]["Revancha"]["estrategias"]["Regresión logística"]
    assert e["media"] == 0.6839
    assert round(e["p"], 3) == 0.017
    assert round(e["q_BH"], 2) == 0.35
    # Y que sigue siendo el mejor caso de todo el proyecto, que es lo que lo hacía interesante.
    mejores = [(b["estrategias"][s]["p"], j, s) for j, b in paquete["backtest"].items()
               for s in b["estrategias"] if not s.startswith("Aleatorio")]
    assert min(mejores)[1:] == ("Revancha", "Regresión logística")


@pytest.mark.lento
def test_gradient_boosting_y_aleatorio_en_melate(paquete):
    e = paquete["backtest"]["Melate"]["estrategias"]
    assert e["Gradient boosting (HGB)"]["media"] == 0.6160
    assert e["Aleatorio (Melático)"]["media"] == 0.6328


@pytest.mark.lento
def test_premios_mayores(paquete):
    assert paquete["premios_mayores"]["Melate"]["ganados"] == 69
    assert paquete["premios_mayores"]["Revancha"]["ganados"] == 61
    assert paquete["premios_mayores"]["Revanchita"]["ganados"] == 35


@pytest.mark.lento
def test_valor_esperado_del_4273(paquete):
    v = paquete["valor_esperado_proximo"]
    assert v["supuestos"]["lambda"] == pytest.approx(0.037, abs=5e-4)
    assert v["supuestos"]["impuesto"] == 0.07
    assert v["Melate"]["rendimiento"] == pytest.approx(-0.59, abs=5e-3)
    assert v["Revancha"]["rendimiento"] == pytest.approx(-0.49, abs=5e-3)
    assert v["Revanchita"]["rendimiento"] == pytest.approx(-0.12, abs=5e-3)
    for juego in ("Melate", "Revancha", "Revanchita"):
        assert v[juego]["proximo_sorteo"] == 4273


@pytest.mark.lento
def test_ninguna_estrategia_bate_al_azar(paquete):
    """La conclusión del proyecto, como test. Si esto falla, hay que mirarlo muy en serio."""
    for juego, b in paquete["backtest"].items():
        for nombre, e in b["estrategias"].items():
            if nombre.startswith("Aleatorio"):
                continue
            assert e["q_BH_global"] > 0.05, f"{juego}/{nombre} sobrevive a q<=0.05: revisar"
    assert paquete["protocolo_global"]["veredicto"] == "sin ventaja demostrada"
