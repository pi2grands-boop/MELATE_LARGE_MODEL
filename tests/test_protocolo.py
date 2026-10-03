"""El laboratorio: preregistro sellado, holdout y las 5 condiciones.

Dos mitades, y la segunda es la que de verdad importa:

* Que el sistema **se niegue** cuando debe: sin preregistro, con un sello alterado, con un sello
  antedatado, con el holdout vacío.
* Que el sistema **funcione** cuando hay holdout. Un laboratorio que siempre dice "sin ventaja
  demostrada" es trivialmente correcto e inútil, y no se distingue de uno roto si nunca se prueba
  el otro camino. Para eso hay fixtures con sello antiguo, construidas a mano a propósito.
"""
import datetime
import json

import numpy as np
import pytest

from melate import lab, protocolo
from melate.constantes import JUEGOS, MEDIA_AZAR


# ---------------------------------------------------------------- utilidades de prueba
def spec_base(sello_utc, **extra):
    s = {
        "id": "prueba",
        "titulo": "fixture de prueba",
        "sello_utc": sello_utc,
        "juegos": list(JUEGOS),
        "juego_principal": "Revancha",
        "estrategias": ["Regresión logística"],
        "umbral_q": 0.05,
        "hiperparametros": {"max_iter": 500},
        "reentrenar_cada": 100,
    }
    s.update(extra)
    return s


def sellar_a_mano(spec, ruta):
    """Escribe un preregistro válido SIN pasar por lab.sellar().

    `sellar()` se niega a fechar en el pasado, y con razón. Pero sin un sello antiguo no hay
    holdout, y sin holdout no se puede probar que la evaluación funciona. Construirlo a mano cuesta
    trabajo y queda a la vista, que es justo la asimetría que se busca.
    """
    spec = dict(spec)
    spec.pop(lab.CLAVE_HASH, None)
    spec[lab.CLAVE_HASH] = lab.hash_preregistro(spec)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(spec, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                    encoding="utf-8")
    return spec


# ---------------------------------------------------------------- el preregistro real del proyecto
def test_el_preregistro_del_repositorio_esta_sellado_y_verifica(raiz):
    """El prereg/*.json que vive en el repositorio tiene que cargar sin quejas."""
    ruta = raiz / "prereg" / "2026-10-03_logistica-revancha.json"
    spec = lab.cargar_preregistro(ruta)
    assert spec["id"] == "2026-10-03_logistica-revancha"
    assert spec["juego_principal"] == "Revancha"
    assert spec["umbral_q"] == 0.05
    assert len(spec[lab.CLAVE_HASH]) == 64
    # Declara los tres juegos: la condicion 4 los necesita.
    assert set(spec["juegos"]) == set(JUEGOS)
    # Y declara variantes: sin ellas la condicion 3 no se puede evaluar.
    assert spec["hiperparametros_alternativos"]
    # Y el tamano de familia como NUMERO: sin el, la condicion 2 nunca podria pasar.
    assert spec["tamano_familia"] == 36


# ---------------------------------------------------------------- la familia declarada de BH
def test_bh_con_familia_declarada_es_mas_estricto():
    ps = [0.01, 0.04, 0.9]
    propia = protocolo.benjamini_hochberg(ps)
    declarada = protocolo.benjamini_hochberg(ps, m=36)
    assert all(d >= p for d, p in zip(declarada, propia))
    assert declarada[0] > propia[0], "corregir contra 36 tiene que penalizar mas que contra 3"


def test_bh_sin_m_es_identico_al_oraculo():
    """m=None tiene que dar exactamente lo de siempre, o se rompe la paridad de la Fase 1."""
    ps = [0.001, 0.01, 0.02, 0.3, 0.7, 0.99]
    assert protocolo.benjamini_hochberg(ps) == protocolo.benjamini_hochberg(ps, m=len(ps))


def test_bh_no_se_puede_aflojar():
    """m menor que las pruebas corridas seria exactamente la forma de hacer trampa."""
    with pytest.raises(ValueError, match="no se afloja"):
        protocolo.benjamini_hochberg([0.01, 0.02, 0.03], m=2)


def test_el_preregistro_del_repositorio_ancla_el_snapshot(raiz):
    """El sello incluye el hash de los datos vigentes, que es la regla 6 aplicada al preregistro."""
    spec = lab.cargar_preregistro(raiz / "prereg" / "2026-10-03_logistica-revancha.json")
    publicado = dict(
        l.split()[::-1] for l in (raiz / "data" / "raw" / "2026-10-02" / "SHA256.txt")
        .read_text().splitlines() if l.strip()
    )
    for juego, sha in spec["datos_al_sellar"]["sha256"].items():
        assert publicado[f"{juego}.csv"] == sha, f"el sello de {juego} no cuadra con el snapshot"


# ---------------------------------------------------------------- se tiene que negar
def test_un_preregistro_alterado_no_sirve(tmp_path):
    """Cambiar un byte lo invalida. Es la unica garantia que da un sello."""
    ruta = tmp_path / "p.json"
    sellar_a_mano(spec_base("2024-01-01T00:00:00+00:00"), ruta)
    lab.cargar_preregistro(ruta)                      # tal cual, carga

    crudo = json.loads(ruta.read_text(encoding="utf-8"))
    crudo["umbral_q"] = 0.5                           # aflojar el umbral a posteriori
    ruta.write_text(json.dumps(crudo, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(ValueError, match="sello NO cuadra"):
        lab.cargar_preregistro(ruta)


@pytest.mark.parametrize("campo,valor", [
    ("umbral_q", 0.5),                             # aflojar el umbral
    ("tamano_familia", 3),                         # aflojar la correccion multiple
    ("sello_utc", "2020-01-01T00:00:00+00:00"),    # antedatar para ganar holdout
    ("juego_principal", "Melate"),                 # cambiar la hipotesis por otra
])
def test_manipular_el_preregistro_real_lo_invalida(raiz, tmp_path, campo, valor):
    """Las cuatro formas de hacer trampa a posteriori, sobre el fichero que vive en el repositorio."""
    orig = raiz / "prereg" / "2026-10-03_logistica-revancha.json"
    spec = json.loads(orig.read_text(encoding="utf-8"))
    spec[campo] = valor
    p = tmp_path / f"m-{campo}.json"
    p.write_text(json.dumps(spec, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    with pytest.raises(ValueError, match="sello NO cuadra"):
        lab.cargar_preregistro(p)


def test_un_bom_no_rompe_el_sello(raiz, tmp_path):
    """Un editor de Windows puede dejar un BOM al guardar. No debe invalidar nada.

    El hash se calcula sobre el JSON canonico del contenido parseado, no sobre los bytes, asi que
    el BOM es irrelevante para el sello. Lo que se arregla es la lectura, que con utf-8 a secas
    fallaba con un error de JSON que no decia nada util.
    """
    orig = raiz / "prereg" / "2026-10-03_logistica-revancha.json"
    p = tmp_path / "con-bom.json"
    p.write_bytes(b"\xef\xbb\xbf" + orig.read_bytes())
    assert lab.cargar_preregistro(p)["id"] == "2026-10-03_logistica-revancha"


@pytest.mark.parametrize("campo", ["id", "sello_utc", "juegos", "estrategias", "umbral_q"])
def test_faltan_campos_obligatorios(tmp_path, campo):
    s = spec_base("2024-01-01T00:00:00+00:00")
    del s[campo]
    ruta = tmp_path / f"sin-{campo}.json"
    sellar_a_mano(s, ruta)
    with pytest.raises(ValueError, match=f"'{campo}'|sello"):
        lab.cargar_preregistro(ruta)


def test_sin_hash_no_es_un_preregistro(tmp_path):
    ruta = tmp_path / "pelado.json"
    ruta.write_text(json.dumps(spec_base("2024-01-01T00:00:00+00:00")), encoding="utf-8")
    with pytest.raises(ValueError, match="no es un preregistro sellado"):
        lab.cargar_preregistro(ruta)


def test_no_se_puede_sellar_en_el_pasado(tmp_path):
    """Un preregistro antedatado no preregistra nada: el holdout incluiria sorteos ya visibles."""
    with pytest.raises(ValueError, match="pasado"):
        lab.sellar(spec_base("2020-01-01T00:00:00+00:00"), tmp_path / "viejo.json")


def test_no_se_sobrescribe_un_sello(tmp_path):
    ruta = tmp_path / "p.json"
    futuro = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=5)).isoformat()
    lab.sellar(spec_base(futuro), ruta)
    with pytest.raises(FileExistsError, match="inmutable"):
        lab.sellar(spec_base(futuro), ruta)


def test_evaluar_exige_un_preregistro_verificado(datos):
    """Sin preregistro no se evalua. Pasar un dict a pelo no vale."""
    with pytest.raises(ValueError, match="cargar_preregistro"):
        lab.evaluar(spec_base("2024-01-01T00:00:00+00:00"), datos["era"])
    with pytest.raises(ValueError, match="cargar_preregistro"):
        lab.evaluar({"id": "x"}, datos["era"])


# ---------------------------------------------------------------- el holdout
def test_el_holdout_de_hoy_esta_vacio(raiz, datos):
    """Con el sello de hoy y datos al 4272, el holdout es vacio. Por construccion."""
    spec = lab.cargar_preregistro(raiz / "prereg" / "2026-10-03_logistica-revancha.json")
    h = lab.holdout(spec, datos["era"])
    for juego in JUEGOS:
        assert h[juego]["sorteos"] == 0, f"{juego} no deberia tener holdout todavia"


def test_el_holdout_solo_mira_hacia_delante(datos):
    """Nunca puede incluir un sorteo anterior al sello, en ningun juego."""
    for sello in ("2015-06-01T00:00:00+00:00", "2020-07-26T00:00:00+00:00", "2026-01-01T00:00:00+00:00"):
        spec = spec_base(sello)
        h = lab.holdout(spec, datos["era"])
        corte = datetime.datetime.fromisoformat(sello).replace(tzinfo=None)
        for juego, df in datos["era"].items():
            idx = h[juego]["indices"]
            assert len(idx) == h[juego]["sorteos"]
            if idx:
                assert df.loc[idx, "FECHA"].min() > corte, f"{juego}: el holdout incluye el pasado"
                assert h[juego]["primer_concurso"] == int(df.loc[idx, "CONCURSO"].min())


def test_un_sello_antiguo_si_produce_holdout(datos):
    """La contraprueba del test anterior: si el sello es viejo, el holdout NO esta vacio.

    Sin esto, 'el holdout esta vacio' podria estar pasando porque el calculo este roto.
    """
    spec = spec_base("2024-01-01T00:00:00+00:00")
    h = lab.holdout(spec, datos["era"])
    for juego in JUEGOS:
        assert h[juego]["sorteos"] > 200, f"{juego}: {h[juego]['sorteos']} sorteos, esperaba cientos"
        assert h[juego]["ultimo_concurso"] == 4272


# ---------------------------------------------------------------- las 5 condiciones, una a una
def test_condicion_holdout_vacio_no_es_un_empate():
    c = protocolo.condicion_holdout_positivo({"sorteos_holdout": 0})
    assert not c["cumple"]
    assert "vacío" in c["motivo"]


def test_condicion_holdout_distingue_signo():
    assert protocolo.condicion_holdout_positivo({"sorteos_holdout": 500, "delta": 0.05})["cumple"]
    assert not protocolo.condicion_holdout_positivo({"sorteos_holdout": 500, "delta": -0.05})["cumple"]
    assert not protocolo.condicion_holdout_positivo({"sorteos_holdout": 500, "delta": 0.0})["cumple"]


def test_condicion_q_usa_la_familia_global():
    assert protocolo.condicion_q({"q_BH_global": 0.04})["cumple"]
    assert not protocolo.condicion_q({"q_BH_global": 0.06})["cumple"]
    # La q de familia no cuenta: manda la global (ver Protocolo_Estadistico/Decisiones).
    assert not protocolo.condicion_q({"q_BH": 0.01})["cumple"]


def test_condicion_estabilidad_exige_variantes_declaradas():
    c = protocolo.condicion_estabilidad({"delta": 0.05})
    assert not c["cumple"] and "no declaró" in c["motivo"]


def test_condicion_estabilidad_detecta_cambio_de_signo():
    base = {"delta": 0.05, "variantes": [{"delta": 0.04}, {"delta": -0.03}]}
    assert not protocolo.condicion_estabilidad(base)["cumple"]


def test_condicion_estabilidad_acepta_variacion_pequena():
    base = {"delta": 0.05, "variantes": [{"delta": 0.048}, {"delta": 0.055}]}
    assert protocolo.condicion_estabilidad(base)["cumple"]


def test_condicion_mismo_signo_es_la_mas_dura():
    tres_positivos = {j: {"delta": 0.02} for j in JUEGOS}
    assert protocolo.condicion_mismo_signo(tres_positivos)["cumple"]

    uno_negativo = dict(tres_positivos, Melate={"delta": -0.01})
    assert not protocolo.condicion_mismo_signo(uno_negativo)["cumple"]

    falta_uno = {j: {"delta": 0.02} for j in ("Melate", "Revancha")}
    c = protocolo.condicion_mismo_signo(falta_uno)
    assert not c["cumple"] and "Revanchita" in c["motivo"]


def test_condicion_efecto_minimo():
    assert protocolo.condicion_efecto_minimo({"delta": 0.06, "efecto_minimo_detectable": 0.048})["cumple"]
    assert not protocolo.condicion_efecto_minimo({"delta": 0.02, "efecto_minimo_detectable": 0.048})["cumple"]


# ---------------------------------------------------------------- el veredicto completo
def test_por_defecto_no_hay_ventaja():
    v = protocolo.declara_ventaja({}, {})
    assert v["veredicto"] == protocolo.SIN_VENTAJA
    assert v["ventaja"] is False
    assert v["cumplidas"] == 0 and v["de"] == 5
    assert len(v["por_que_no"]) == 5


def test_las_cinco_condiciones_se_evaluan_siempre():
    """Ninguna se cortocircuita: cuando algo falla, lo util es saber QUE fallo."""
    v = protocolo.declara_ventaja({"sorteos_holdout": 0}, {})
    assert len(v["condiciones"]) == 5
    assert [c["condicion"] for c in v["condiciones"]] == [
        "holdout futuro positivo", "q <= 0.05", "estable al mover hiperparámetros",
        "mismo signo en los tres juegos", "efecto >= mínimo detectable",
    ]


def test_cuatro_de_cinco_no_es_ventaja():
    """La regla 5 dice 'a la vez'. Casi no cuenta."""
    res = {"sorteos_holdout": 1800, "delta": 0.06, "q_BH_global": 0.04,
           "efecto_minimo_detectable": 0.048,
           "variantes": [{"delta": 0.058}, {"delta": 0.062}]}
    por_juego = {j: {"delta": 0.06} for j in JUEGOS}
    por_juego["Melate"] = {"delta": -0.01}          # rompe solo la condicion 4
    v = protocolo.declara_ventaja(res, por_juego)
    assert v["cumplidas"] == 4 and v["ventaja"] is False
    assert v["veredicto"] == protocolo.SIN_VENTAJA


def test_el_camino_afirmativo_existe_y_es_alcanzable():
    """Si las 5 se cumplen, el sistema SI declara ventaja.

    Importa tanto como lo demas: un laboratorio que no pueda decir 'si' ni en el caso perfecto no
    es prudente, esta roto, y no habria forma de distinguirlo de uno prudente.
    """
    res = {"sorteos_holdout": 1800, "delta": 0.06, "q_BH_global": 0.01,
           "efecto_minimo_detectable": 0.048,
           "variantes": [{"delta": 0.058}, {"delta": 0.062}, {"delta": 0.059}]}
    por_juego = {j: {"delta": 0.055} for j in JUEGOS}
    v = protocolo.declara_ventaja(res, por_juego)
    assert v["ventaja"] is True
    assert v["veredicto"] == "VENTAJA DEMOSTRADA"
    assert v["cumplidas"] == 5 and v["por_que_no"] == []


def test_el_veredicto_lleva_la_linea_base_del_azar():
    v = protocolo.declara_ventaja({}, {})
    assert v["linea_base_azar"] == pytest.approx(MEDIA_AZAR, abs=1e-6)


# ---------------------------------------------------------------- evaluación de punta a punta
def test_evaluar_con_holdout_vacio_da_sin_ventaja(raiz, datos):
    spec = lab.cargar_preregistro(raiz / "prereg" / "2026-10-03_logistica-revancha.json")
    r = lab.evaluar(spec, datos["era"])
    assert r["veredicto"]["veredicto"] == protocolo.SIN_VENTAJA
    assert r["veredicto"]["cumplidas"] == 0
    assert "vacío" in r["veredicto"]["condiciones"][0]["motivo"]
    assert all(h["sorteos"] == 0 for h in r["holdout"].values())
    assert r["preregistro"][lab.CLAVE_HASH] == spec[lab.CLAVE_HASH]


@pytest.mark.lento
def test_evaluar_con_holdout_de_verdad_mide_algo(tmp_path, datos):
    """El camino completo con holdout real: la maquinaria tiene que producir numeros, no ceros.

    Sello en 2026-01-01 para que el holdout sea de decenas de sorteos y el test no tarde minutos.
    Este es el test que distingue un laboratorio prudente de uno averiado.
    """
    ruta = tmp_path / "con-holdout.json"
    sellar_a_mano(
        spec_base("2026-01-01T00:00:00+00:00",
                  tamano_familia=36,
                  hiperparametros_alternativos=[{"max_iter": 200}]),
        ruta,
    )
    spec = lab.cargar_preregistro(ruta)
    r = lab.evaluar(spec, datos["era"])

    for juego in JUEGOS:
        assert r["holdout"][juego]["sorteos"] > 50, f"{juego}: holdout demasiado corto"
        pj = r["por_juego"][juego]
        assert pj["delta"] is not None
        assert 0 <= pj["media"] <= 6, "aciertos por boleto fuera de rango"
        assert 0 <= pj["p"] <= 1
        assert 0 <= pj["q_BH_global"] <= 1

    res = r["resultados"]
    assert res["sorteos_holdout"] > 50
    assert res["efecto_minimo_detectable"] > 0
    assert len(res["variantes"]) == 1 and res["variantes"][0]["delta"] is not None
    # La condicion 2 tiene que poder EVALUARSE, no solo fallar por falta de dato.
    assert res["familia_declarada"] == 36 and res["pruebas_corridas"] == 3
    assert res["q_BH_global"] is not None

    # Con un holdout de decenas de sorteos, el minimo detectable es grande: la condicion 5 no puede
    # pasar. Eso no es un fallo, es el tamano de muestra diciendo la verdad.
    v = r["veredicto"]
    assert v["veredicto"] == protocolo.SIN_VENTAJA
    cond = {c["condicion"]: c for c in v["condiciones"]}
    assert not cond["efecto >= mínimo detectable"]["cumple"]
    # Y las condiciones 1 y 2 si se pudieron evaluar de verdad, con numeros.
    assert "vacío" not in cond["holdout futuro positivo"]["motivo"]
    assert "sin q" not in cond["q <= 0.05"]["motivo"], "la condicion 2 no se pudo evaluar"
    assert "q_BH_global =" in cond["q <= 0.05"]["motivo"]


@pytest.mark.lento
def test_la_evaluacion_no_mira_el_futuro(tmp_path, datos):
    """Las variables del holdout se construyen igual con o sin los sorteos posteriores.

    Es el test de no-fuga de la Fase 1 aplicado al laboratorio: evaluar el holdout no puede
    depender de datos que en su momento no existian.
    """
    from melate.backtest import variables
    from melate.ingest import matriz

    df = datos["era"]["Revancha"]
    spec = spec_base("2026-01-01T00:00:00+00:00")
    idx = lab.holdout(spec, {"Revancha": df})["Revancha"]["indices"]
    t0 = min(idx)

    X = matriz(df["nums"].tolist())
    F, atraso = variables(X)
    recortado = matriz(df.iloc[:t0 + 1]["nums"].tolist())
    Fr, atrasor = variables(recortado)
    assert np.array_equal(F[t0], Fr[t0]), "las variables del primer sorteo del holdout ven el futuro"
    assert np.array_equal(atraso[t0], atrasor[t0])
