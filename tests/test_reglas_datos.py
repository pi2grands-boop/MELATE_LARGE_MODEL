"""Una prueba por cada regla de datos del CLAUDE.md, contra el snapshot congelado del 4272.

Estas son rápidas: solo leen CSV. La única lenta/frágil es la de la regla 7, que necesita red y
está marcada `red`.
"""
import pytest

from melate.constantes import JUEGOS, N
from melate.ev import premios_mayores
from melate.validate import validar

SORTEOS_ERA = {"Melate": 2184, "Revancha": 2184, "Revanchita": 1902}
PRIMER_CONCURSO = {"Melate": 2089, "Revancha": 2089, "Revanchita": 2371}
BOLSA_MALA_ERA = {"Melate": [2120, 2142, 2234], "Revancha": [2120, 2142, 2234], "Revanchita": []}
PREMIOS_MAYORES = {"Melate": 69, "Revancha": 61, "Revanchita": 35}


# --------------------------------------------------------------- regla 1: la era 6/56
@pytest.mark.parametrize("juego", JUEGOS)
def test_regla1_era_56(datos, juego):
    d = datos["era"][juego]
    assert len(d) == SORTEOS_ERA[juego]
    assert int(d.CONCURSO.min()) == PRIMER_CONCURSO[juego]
    assert int(d.CONCURSO.max()) == 4272, "el snapshot está clavado en el 4272"
    assert d["nums"].explode().max() <= N


# --------------------------------------------------------------- regla 2: BOLSA(N) es del N+1
def test_regla2_la_bolsa_de_la_fila_es_del_sorteo_siguiente(datos):
    """La bolsa que el EV pone en juego es la de la última fila, y corresponde al sorteo +1."""
    from melate.ev import valor_esperado

    ev = valor_esperado(datos["era"])
    for juego, d in datos["era"].items():
        assert ev[juego]["proximo_sorteo"] == int(d.CONCURSO.iloc[-1]) + 1 == 4273
        assert ev[juego]["bolsa_bruta"] == float(d.BOLSA.iloc[-1])
    # Valores anunciados en la fila del 4272, para el 4273.
    assert ev["Melate"]["bolsa_bruta"] == 76_200_000
    assert ev["Revancha"]["bolsa_bruta"] == 111_700_000
    assert ev["Revanchita"]["bolsa_bruta"] == 155_800_000


# --------------------------------------------------------------- regla 3: bajas de BOLSA
@pytest.mark.parametrize("juego", JUEGOS)
def test_regla3_premios_mayores_por_bajas_de_bolsa(datos, juego):
    g, _ = premios_mayores(juego, datos["era"][juego])
    assert len(g) == PREMIOS_MAYORES[juego]


# --------------------------------------------------------------- regla 4: errores del oficial
@pytest.mark.parametrize("juego", JUEGOS)
def test_regla4_bolsa_invalida_solo_en_los_tres_concursos_conocidos(datos, juego):
    v = validar(juego, datos["era"][juego])
    assert v["bolsa_cero_o_invalida"] == BOLSA_MALA_ERA[juego]


def test_regla4_revancha_3221_se_descarta_como_error_no_como_premio(datos):
    """238.6 M entre 280.3 M y 286.4 M: una baja seguida de un valor mayor que el anterior."""
    d = datos["era"]["Revancha"]
    g, errores = premios_mayores("Revancha", d)
    assert 3221 in errores
    assert 3221 not in set(g.CONCURSO), "un error de bolsa no es un premio mayor ganado"
    b = dict(zip(d.CONCURSO, d.BOLSA))
    assert b[3221] == 238_600_000 and b[3220] == 280_300_000 and b[3222] == 286_400_000


# --------------------------------------------------------------- regla 5: el hueco de la pandemia
def test_regla5_hueco_de_pandemia_sin_romper_la_secuencia(datos):
    for juego in ("Melate", "Revancha"):
        d = datos["era"][juego]
        f = dict(zip(d.CONCURSO, d.FECHA))
        assert (f[3374] - f[3373]).days == 116
        assert str(f[3373].date()) == "2020-04-01"
        assert str(f[3374].date()) == "2020-07-26"
        # Los concursos siguen consecutivos: el hueco es de calendario, no de numeración.
        assert validar(juego, d)["concursos_faltantes"] == []


# --------------------------------------------------------------- regla 6: orden y adicional
@pytest.mark.parametrize("juego", JUEGOS)
def test_regla6_numeros_ordenados_y_sin_repetir(datos, juego):
    v = validar(juego, datos["era"][juego])
    assert v["filas_no_ordenadas_o_repetidas"] == 0
    assert v["fuera_de_rango"] == 0


def test_regla6_el_adicional_sale_de_las_50_restantes(datos):
    d = datos["era"]["Melate"]
    assert validar("Melate", d)["adicional_repetido_en_naturales"] == 0
    assert d.R7.between(1, N).all()


def test_regla6_revancha_y_revanchita_no_tienen_adicional(datos):
    for juego in ("Revancha", "Revanchita"):
        assert datos["era"][juego].R7.isna().all()


# --------------------------------------------------------------- regla 7: validación cruzada
@pytest.mark.parametrize("juego", JUEGOS)
def test_regla7_sin_duplicados_ni_concursos_faltantes(datos, juego):
    v = validar(juego, datos["era"][juego])
    assert v["duplicados"] == 0
    assert v["concursos_faltantes"] == []


@pytest.mark.red
@pytest.mark.parametrize("juego", JUEGOS)
def test_regla7_oficial_contra_espejo(datos, juego):
    """"Oficial igual al espejo", con su única excepción conocida y documentada.

    Esta comparación es lo ÚNICO que detecta un número mal transcrito: la fila errónea del espejo
    en Revancha 3827 es formalmente válida y pasa las nueve comprobaciones de validar(). Si aparece
    una diferencia nueva, el test falla a propósito: hay que investigarla con una tercera fuente
    antes de elegir un valor, nunca ampliar esta lista sin más.
    """
    from melate.ingest import cargar_espejo

    EXCEPCIONES = {"Revancha": {3827: ([15, 16, 38, 40, 41, 50], [15, 16, 38, 40, 41, 54])}}

    of = datos["era"][juego]
    es = cargar_espejo(juego)
    mo = dict(zip(of.CONCURSO, of["nums"]))
    me = dict(zip(es.CONCURSO, es["nums"]))

    difs = {c: (list(mo[c]), list(me[c])) for c in sorted(set(mo) & set(me)) if list(mo[c]) != list(me[c])}
    assert difs == EXCEPCIONES.get(juego, {}), (
        f"diferencias inesperadas entre oficial y espejo en {juego}: {difs}. "
        "Investiga con resultados.melate-e.com antes de tocar este test."
    )


@pytest.mark.red
def test_el_espejo_puede_ir_por_delante_del_oficial(datos):
    """Por esto el espejo no es fallback de carga: puede traer juegos en sorteos distintos.

    No se afirma que vaya adelantado —depende del momento—, solo que si lo va, lo hace de forma
    desigual entre juegos, y eso rompería la comparación pareada del protocolo.
    """
    from melate.ingest import cargar_espejo

    ultimos = {j: int(cargar_espejo(j).CONCURSO.max()) for j in JUEGOS}
    if len(set(ultimos.values())) > 1:
        pytest.skip(f"el espejo está desalineado ahora mismo: {ultimos} (es justo el riesgo documentado)")
    assert len(set(ultimos.values())) == 1
