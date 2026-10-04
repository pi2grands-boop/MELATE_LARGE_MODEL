"""La cartera: que haga lo que dice, y sobre todo que no diga lo que no hace.

La mitad de este fichero no comprueba que el código funcione, sino que **no engañe**. Es un módulo
que reparte boletos de lotería: la forma más fácil de que haga daño no es un error de cálculo, es
una frase que sugiera que esto mejora tus probabilidades. No las mejora. Nada las mejora.
"""
import math

import pytest

from melate import portfolio as pf
from melate.constantes import C, N, PRECIO

COCIENTE = 0.7549   # medido sobre 300 sorteos de Melate, ventana 3973-4272


@pytest.fixture
def pesos():
    return pf.pesos_por_numero(COCIENTE)


# ---------------------------------------------------------------- los pesos


def test_los_pesos_suman_el_numero_de_esferas(pesos):
    """Normalizados a media 1: un peso de 1 es 'tan jugado como la media'."""
    assert sum(pesos.values()) == pytest.approx(N)


def test_los_numeros_fuera_del_calendario_pesan_menos(pesos):
    assert pesos[31] > pesos[32], "el corte está entre el 31 y el 32"
    assert pesos[32] / pesos[31] == pytest.approx(COCIENTE, rel=1e-9)


def test_sin_efecto_medido_los_pesos_son_todos_uno():
    """Si no hay medición, no se inventa una. Pesos planos y que se note."""
    for cociente in (None, 0, -1):
        p = pf.pesos_por_numero(cociente)
        assert set(p.values()) == {1.0}


def test_un_cociente_de_uno_deja_los_pesos_planos():
    assert all(p == pytest.approx(1.0) for p in pf.pesos_por_numero(1.0).values())


# ---------------------------------------------------------------- popularidad


def test_los_seis_primeros_son_lo_mas_jugado(pesos):
    """1-2-3-4-5-6 es la combinación con la que este módulo existe para no dejarte tropezar."""
    malo = pf.popularidad((1, 2, 3, 4, 5, 6), pesos)
    normal = pf.popularidad((2, 19, 33, 40, 47, 54), pesos)
    assert malo > 20 * normal, f"{malo} contra {normal}"


def test_los_patrones_se_detectan():
    assert "todos_en_calendario" in pf.patrones_de((1, 8, 15, 22, 29, 31))
    assert "todos_en_calendario" not in pf.patrones_de((1, 8, 15, 22, 29, 32))
    assert "consecutivos_3" in pf.patrones_de((4, 5, 6, 20, 35, 50))
    assert "consecutivos_3" not in pf.patrones_de((4, 5, 20, 21, 35, 50)), "dos parejas no son racha"
    assert "progresion_aritmetica" in pf.patrones_de((5, 10, 15, 20, 25, 30))
    assert "misma_decena" in pf.patrones_de((41, 42, 44, 46, 48, 50))
    assert "todos_multiplos" in pf.patrones_de((7, 14, 21, 28, 35, 42))


def test_una_combinacion_repartida_y_alta_no_dispara_ningun_patron():
    assert pf.patrones_de((2, 19, 33, 40, 47, 54)) == []


def test_las_penalizaciones_de_patron_gobiernan_de_verdad(pesos):
    """Dos valores distintos del parámetro, dos resultados distintos.

    Lo pide la auditoría de las fases 1 y 2: un parámetro declarado que no se lee es un defecto
    que ningún test de humo encuentra.
    """
    combo = (1, 2, 3, 4, 5, 6)
    suave = pf.popularidad(combo, pesos, patrones={})
    dura = pf.popularidad(combo, pesos, patrones=dict(pf.PATRONES, todos_en_calendario=10.0))
    assert dura > suave * 4, "las penalizaciones no se están aplicando"


def test_sin_pesos_ni_patrones_toda_combinacion_vale_uno():
    assert pf.popularidad((1, 2, 3, 4, 5, 6), patrones={}) == pytest.approx(1.0)


def test_compartir_crece_con_la_popularidad(pesos):
    """Más jugada = más gente con la que repartir = peor factor."""
    f_mala, lam_mala = pf.compartiendo((1, 2, 3, 4, 5, 6), 1.2e6, pesos)
    f_buena, lam_buena = pf.compartiendo((2, 19, 33, 40, 47, 54), 1.2e6, pesos)
    assert lam_mala > lam_buena
    assert f_mala < f_buena <= 1.0


# ---------------------------------------------------------------- la cartera


def test_la_cartera_cabe_en_el_presupuesto(pesos):
    for presupuesto in (100, 300, 1000):
        c = pf.cartera("Melate", presupuesto, pesos=pesos, candidatas=3000)
        assert c["coste"] <= presupuesto
        assert c["boletos"] == presupuesto // PRECIO["Melate"]
        assert c["sobrante"] == presupuesto - c["coste"]


def test_la_cartera_no_se_concentra_en_media_urna(pesos):
    """El defecto que tuvo la primera versión: minimizar popularidad a secas cubría 27 de 56.

    Como todos los números > 31 pesan igual, el mínimo global es jugar solo números altos. Eso no
    mejora el valor esperado y concentra la cartera en media urna. El tope de popularidad más la
    cobertura lo arreglan, y este test impide que vuelva.
    """
    c = pf.cartera("Melate", 300, pesos=pesos, candidatas=5000)
    assert c["numeros_cubiertos"] >= 50, f"solo cubre {c['numeros_cubiertos']} de {N}"
    bajos = [n for b in c["detalle"] for n in b["numeros"] if n <= 31]
    assert bajos, "ni un solo número del calendario: eso es concentración, no diversificación"


def test_el_tope_de_popularidad_gobierna_de_verdad(pesos):
    """Dos valores distintos, dos carteras distintas y en la dirección correcta."""
    floja = pf.cartera("Melate", 300, pesos=pesos, candidatas=5000, tope_popularidad=3.0)
    dura = pf.cartera("Melate", 300, pesos=pesos, candidatas=5000, tope_popularidad=0.7)
    assert dura["candidatas_aptas"] < floja["candidatas_aptas"]
    assert dura["popularidad_media"] < floja["popularidad_media"]


def test_un_tope_imposible_no_devuelve_una_cartera_vacia_en_silencio(pesos):
    with pytest.raises(ValueError, match="tope"):
        pf.cartera("Melate", 300, pesos=pesos, candidatas=500, tope_popularidad=1e-9)


def test_el_solape_maximo_gobierna_de_verdad(pesos):
    estricta = pf.cartera("Melate", 300, pesos=pesos, candidatas=5000, solape_maximo=1)
    laxa = pf.cartera("Melate", 300, pesos=pesos, candidatas=5000, solape_maximo=4)
    assert estricta["solape_maximo_real"] <= 1
    assert estricta["solape_medio"] <= laxa["solape_medio"]


def test_la_misma_semilla_da_la_misma_cartera(pesos):
    a = pf.cartera("Melate", 150, pesos=pesos, candidatas=3000, semilla=7)
    b = pf.cartera("Melate", 150, pesos=pesos, candidatas=3000, semilla=7)
    assert [x["numeros"] for x in a["detalle"]] == [x["numeros"] for x in b["detalle"]]


def test_semillas_distintas_dan_carteras_distintas(pesos):
    a = pf.cartera("Melate", 150, pesos=pesos, candidatas=3000, semilla=7)
    b = pf.cartera("Melate", 150, pesos=pesos, candidatas=3000, semilla=8)
    assert [x["numeros"] for x in a["detalle"]] != [x["numeros"] for x in b["detalle"]]


def test_no_hay_boletos_repetidos(pesos):
    c = pf.cartera("Melate", 600, pesos=pesos, candidatas=8000)
    numeros = [tuple(b["numeros"]) for b in c["detalle"]]
    assert len(numeros) == len(set(numeros))
    for b in c["detalle"]:
        assert len(set(b["numeros"])) == 6
        assert all(1 <= n <= N for n in b["numeros"])


def test_cada_juego_usa_su_precio(pesos):
    for juego, precio in PRECIO.items():
        c = pf.cartera(juego, 300, pesos=pesos, candidatas=2000)
        assert c["precio_boleto"] == precio
        assert c["boletos"] == 300 // precio


# ---------------------------------------------------------------- honestidad


def test_separar_los_boletos_no_cambia_la_media():
    """La esperanza es lineal. Esta es la afirmación que más fácil sería colar mal.

    Con pesos planos y sin patrones, todas las combinaciones tienen la misma popularidad, así que
    el valor esperado solo puede depender de CUÁNTOS boletos hay, no de cómo se solapen. Si algún
    día este test falla, alguien metió una ganancia que no existe.
    """
    planos = pf.pesos_por_numero(1.0)
    juntos = pf.cartera("Melate", 300, pesos=planos, patrones={}, candidatas=2000, solape_maximo=5)
    sueltos = pf.cartera("Melate", 300, pesos=planos, patrones={}, candidatas=2000, solape_maximo=1)
    v_juntos = pf.valorar(juntos, bolsa=76_200_000.0, menores_brutos=4.60)
    v_sueltos = pf.valorar(sueltos, bolsa=76_200_000.0, menores_brutos=4.60)
    assert v_juntos["valor_esperado"] == pytest.approx(v_sueltos["valor_esperado"], rel=1e-9)
    assert v_juntos["ganancia_por_evitar_compartir"] == pytest.approx(0.0, abs=1e-6)


def test_el_valor_esperado_sigue_siendo_negativo(pesos):
    """Con las bolsas reales del sorteo 4273 y los menores medidos, los tres pierden."""
    reales = {"Melate": (76_200_000.0, 4.6500), "Revancha": (111_700_000.0, 2.6156),
              "Revanchita": (155_800_000.0, 0.0)}
    for juego, (bolsa, menores) in reales.items():
        c = pf.cartera(juego, 300, pesos=pesos, candidatas=3000)
        v = pf.valorar(c, bolsa=bolsa, menores_brutos=menores)
        assert v["rendimiento"] < 0, f"{juego} da rendimiento {v['rendimiento']}: revísalo"


def test_la_ganancia_por_evitar_compartir_es_minuscula(pesos):
    """El techo medido es +0,27 % del precio en Melate. Si sale mucho más, hay un error.

    Esta cota es lo que impide que el módulo se vuelva, sin querer, una promesa.
    """
    c = pf.cartera("Melate", 300, pesos=pesos, candidatas=5000)
    v = pf.valorar(c, bolsa=76_200_000.0, menores_brutos=4.6500)
    assert 0 < v["ganancia_como_porcentaje_del_precio"] < 0.003, v


def test_la_valoracion_dice_con_que_se_hizo(pesos):
    """Dos bolsas, dos registros: el reporte guarda la bolsa y los menores que recibió."""
    c = pf.cartera("Melate", 150, pesos=pesos, candidatas=2000)
    for bolsa, menores in ((76_200_000.0, 4.6013), (150_000_000.0, 4.6500)):
        v = pf.valorar(c, bolsa=bolsa, menores_brutos=menores)
        assert (v["bolsa"], v["menores_brutos"], v["impuesto"]) == (bolsa, menores, 0.07)


def test_toda_valoracion_lleva_el_aviso(pesos):
    c = pf.cartera("Revanchita", 100, pesos=pesos, candidatas=2000)
    v = pf.valorar(c, bolsa=155_800_000.0, menores_brutos=0.0)
    assert "NEGATIVO" in v["aviso"]
    assert "no cambia la probabilidad de acertar" in v["aviso"]
    assert "Sin ventaja demostrada" in v["aviso"]


def test_el_modulo_no_promete_mejorar_las_probabilidades():
    """Un grep sobre el propio fichero, pero uno que sepa leer una negación.

    La primera versión de este test fallaba contra la frase **honesta** del módulo —"esto no mejora
    tus probabilidades de ganar"— porque buscaba la subcadena a secas. Un test que no distingue
    "mejora X" de "no mejora X" en un fichero cuyo trabajo es justo negar esa frase es inútil: o lo
    borras o lo arreglas. Aquí se exige que toda aparición venga negada.
    """
    import pathlib
    import re

    fuente = pathlib.Path(pf.__file__).read_text(encoding="utf-8").lower()
    promesas = ("mejora tus probabilidades", "mejora la probabilidad", "más probable que salga",
                "aumenta la probabilidad de ganar", "números calientes", "predice los números")
    for frase in promesas:
        for m in re.finditer(re.escape(frase), fuente):
            antes = fuente[max(0, m.start() - 40):m.start()]
            assert re.search(r"\b(no|nada|ni|sin|tampoco)\b", antes), \
                f"el módulo dice {frase!r} sin negarlo: ...{antes}[{frase}]..."
    # Y que la negación esté, no vaya a pasar el test por no decir nada.
    assert "no mejora" in fuente and "no lo arregla" in fuente


def test_el_factor_de_reparto_nunca_pasa_de_uno(pesos):
    """E[1/(1+W)] <= 1 siempre. Un factor > 1 sería dinero inventado."""
    c = pf.cartera("Melate", 450, pesos=pesos, candidatas=5000)
    for b in c["detalle"]:
        assert 0 < b["factor_reparto"] <= 1.0


def test_la_formula_de_reparto_es_la_del_oraculo():
    """`(1-exp(-lam))/lam`, la misma que usa ev.valor_esperado. No hay dos definiciones de S."""
    lam = 1.2e6 * 1.0 / C
    esperado = (1 - math.exp(-lam)) / lam
    factor, lam_visto = pf.compartiendo((2, 19, 33, 40, 47, 54), 1.2e6, patrones={})
    assert lam_visto == pytest.approx(lam)
    assert factor == pytest.approx(esperado)
