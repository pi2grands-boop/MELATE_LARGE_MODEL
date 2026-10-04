"""`melate.duckdb`: que sea un índice fiel de lo publicado, y que por la puerta del veredicto solo
entre lo que juzga.

La mitad de este fichero no comprueba que la base se construya, sino que **no se pueda colar** nada
por donde no toca: un preregistro alterado, un veredicto incoherente, un informe con una q bajo el
umbral. La decisión que fija todo esto es anterior al código:
`Documentos_Contexto/Almacenamiento/Decisiones/2026-10-04_00-40_s4-que-entra-en-melate-duckdb.md`.
"""
import ast
import hashlib
import json
import re

import pytest

from conftest import HUERFANO, MENOS_DATOS, PREREG_REAL, VEREDICTO_REAL, leer_json
from melate import almacen, protocolo
from melate.constantes import JUEGOS


@pytest.fixture(scope="module")
def tablas(base_real):
    return almacen.leer(base_real)


@pytest.fixture(scope="module")
def forjadas(base_forjada):
    return almacen.leer(base_forjada)


# ---------------------------------------------------------------- forma y contenido
def test_la_base_tiene_el_esquema_y_el_catalogo_completos(tablas):
    assert set(tablas) == set(almacen.ESQUEMA)
    assert almacen.problema_de_esquema(tablas) is None
    cat = tablas["catalogo"]
    assert set(cat["tabla"]) == set(almacen.ESQUEMA), "toda tabla declara su naturaleza, y solo ellas"
    assert set(cat["naturaleza"]) == {"juzga", "explora", "mide", "procedencia"}
    assert set(cat["mira_a"]) <= {"urna", "dinero", "jugadores", "datos"}


def test_la_columna_veredicto_solo_existe_en_lo_que_juzga():
    """Regla 3 de la decisión: lo que explora no se llama veredicto, ni siquiera en una columna."""
    naturaleza = {t: n for t, n, _, _ in almacen.CATALOGO}
    for tabla, columnas in almacen.ESQUEMA.items():
        if any(c.startswith("veredicto") for c, _ in columnas):
            assert naturaleza[tabla] == "juzga", f"{tabla} tiene una columna veredicto y no juzga"


def test_cada_fichero_queda_en_fuentes_con_su_hash(tablas, raiz):
    f = tablas["fuentes"].set_index("ruta")
    en_repo = sorted(p.relative_to(raiz).as_posix() for d in ("reportes", "prereg")
                     for p in (raiz / d).glob("*.json"))
    assert sorted(f.index) == en_repo
    for ruta, fila in f.iterrows():
        assert fila["sha256"] == hashlib.sha256((raiz / ruta).read_bytes()).hexdigest(), ruta
    assert "desconocido" not in set(f["tipo"]), "todos los reportes del repositorio se reconocen"
    assert f["valido"].all()


def test_el_contenido_es_el_de_los_reportes(tablas, raiz):
    """Ningún número que no esté en un fichero publicado: se comprueban unos cuantos, a mano."""
    inf = leer_json(raiz / "reportes" / "2026-10-03_informe-con-popularidad.json")
    bt = tablas["backtest"]
    rl = bt[(bt.ruta == "reportes/2026-10-03_informe-con-popularidad.json")
            & (bt.juego == "Revancha") & (bt.estrategia == "Regresión logística")].iloc[0]
    esperado = inf["backtest"]["Revancha"]["estrategias"]["Regresión logística"]
    assert (rl["p"], rl["q_familia"], rl["q_global"]) == (esperado["p"], esperado["q_BH"],
                                                          esperado["q_BH_global"])
    ev = tablas["valor_esperado"]
    medido = ev[(ev.ruta == "reportes/2026-10-03_informe-con-popularidad.json")
                & (ev.variante == "menores_medidos") & (ev.juego == "Revancha")].iloc[0]
    assert medido["rendimiento"] == inf["valor_esperado_medido"]["Revancha"]["rendimiento"]
    assert medido["menores_brutos"] == inf["valor_esperado_medido"]["menores_brutos_usados"]["Revancha"]
    po = tablas["popularidad"]
    largo = po[po.ruta == "reportes/2026-10-04_popularidad-melate-300-sorteos.json"].iloc[0]
    assert round(largo["calendario_t"], 2) == -18.67 and largo["sorteos_usados"] == 300
    # C1 de la Fase 4: tres sorteos sin premios publicados, fuera de los premios menores.
    assert largo["sorteos_sin_premios"] == 3 and largo["menores_bolsa_n"] == 297
    # C4: la valoración de la cartera dice con qué bolsa se hizo.
    ca = tablas["carteras"].iloc[0]
    assert (ca["bolsa"], ca["impuesto"]) == (76_200_000.0, 0.07)


def test_el_resumen_del_informe_no_se_llama_veredicto(tablas):
    inf = tablas["informes"]
    assert "veredicto" not in inf.columns
    assert set(inf.loc[inf.tipo == "informe", "resumen_exploratorio"]) == {protocolo.SIN_VENTAJA}


def test_ninguna_ruta_absoluta_entra_en_la_base(tablas, base_real):
    """La base no se publica, pero la regla del proyecto es no escribir jamás una ruta de la máquina.

    Una letra de unidad sola, no precedida de otra letra (así `https://` no cuenta), o un directorio
    de usuario, en cualquier celda de texto de cualquier tabla.
    """
    patron = re.compile(r"(?<![A-Za-z])[A-Za-z]:[\\/]|[\\/]Users[\\/]|/home/")
    propia = str(base_real.parent)
    for nombre, df in tablas.items():
        for col in df.columns:
            for valor in df[col]:
                if isinstance(valor, str):
                    assert not patron.search(valor), f"{nombre}.{col}: {valor!r}"
                    assert propia not in valor, f"{nombre}.{col} contiene la ruta de la base"


# ---------------------------------------------------------------- lo que juzga
def test_el_preregistro_del_repositorio_verifica_en_la_base(tablas):
    p = tablas["preregistros"].iloc[0]
    assert p["verificado"] and p["motivo"] is None
    assert p["tamano_familia"] == 36 and p["variantes"] == 4


def test_los_veredictos_del_repositorio_valen_y_dicen_sin_ventaja(tablas):
    assert tablas["veredictos"]["valido"].all()
    vig = almacen.veredicto_vigente(tablas)
    assert vig["veredicto"] == protocolo.SIN_VENTAJA and not vig["por_defecto"]
    r = vig["vigentes"][0]
    assert r["ruta"] == f"reportes/{VEREDICTO_REAL}", "el vigente es el último por fecha de corrida"
    assert r["datos_registrados"] and r["ultimo_concurso_datos"] == 4272


def test_el_veredicto_viejo_queda_marcado_sin_datos(tablas):
    """El de la Fase 2 es anterior al arreglo de H1: vale, pero no dice sobre qué datos juzgó."""
    v = tablas["veredictos"].set_index("ruta").loc["reportes/2026-10-03_veredicto.json"]
    assert v["valido"] and not v["datos_registrados"]


@pytest.fixture(scope="module")
def rotas(base_sello_roto):
    return almacen.leer(base_sello_roto)


def test_un_preregistro_alterado_invalida_sus_veredictos(rotas):
    """Aflojar el umbral después de sellar: el sello no cuadra y nada que dependa de él llega a la
    cabecera. Las otras manipulaciones del sello están en `test_protocolo.py`."""
    p = rotas["preregistros"].iloc[0]
    assert not p["verificado"] and "no cuadra" in p["motivo"].lower()
    v = rotas["veredictos"].set_index("ruta")
    for ruta in ("reportes/2026-10-03_veredicto.json", f"reportes/{VEREDICTO_REAL}"):
        assert not v.loc[ruta, "valido"] and "no verifica" in v.loc[ruta, "motivo"]
    vig = almacen.veredicto_vigente(rotas)
    assert vig["por_defecto"] and vig["veredicto"] == protocolo.SIN_VENTAJA


def test_un_veredicto_sin_su_preregistro_no_cuenta(rotas):
    v = rotas["veredictos"].set_index("ruta").loc[f"reportes/{HUERFANO}"]
    assert not v["valido"] and "ningún preregistro" in v["motivo"]


def test_un_veredicto_incoherente_no_cuenta(forjadas):
    """Proclama la ventaja con cinco condiciones que no se cumplen: no llega a la cabecera."""
    v = forjadas["veredictos"].set_index("ruta").loc["reportes/2026-10-05_veredicto.json"]
    assert not v["valido"] and "incoherente" in v["motivo"]
    vig = almacen.veredicto_vigente(forjadas)
    assert vig["veredicto"] == protocolo.SIN_VENTAJA
    assert vig["vigentes"][0]["ruta"] == f"reportes/{VEREDICTO_REAL}"


def test_el_camino_afirmativo_existe(base_con_ventaja):
    """Si el laboratorio dijera que sí, con un sello que verifica, la cabecera lo diría.

    Importa tanto como las negativas: una cabecera que no pudiera cambiar nunca sería
    indistinguible de una escrita a mano.
    """
    vig = almacen.veredicto_vigente(almacen.leer(base_con_ventaja))
    assert vig["ventaja"] and vig["veredicto"] == almacen.VENTAJA


def test_el_texto_afirmativo_es_el_del_protocolo():
    """`almacen.VENTAJA` copia un texto que `protocolo.declara_ventaja` escribe en línea."""
    res = {"sorteos_holdout": 1800, "delta": 0.06, "q_BH_global": 0.01,
           "efecto_minimo_detectable": 0.048,
           "variantes": [{"delta": 0.058}, {"delta": 0.062}, {"delta": 0.059}]}
    v = protocolo.declara_ventaja(res, {j: {"delta": 0.055} for j in JUEGOS})
    assert v["veredicto"] == almacen.VENTAJA


def test_un_informe_con_q_bajo_el_umbral_no_toca_el_veredicto(forjadas):
    """La frontera, en los datos: una q exploratoria de 0.01 se queda en la exploración."""
    inf = forjadas["informes"].set_index("ruta").loc["reportes/2026-10-05_informe-q-bajo.json"]
    assert inf["pruebas_bajo_umbral"] == 1
    assert inf["resumen_exploratorio"].startswith("revisar")
    vig = almacen.veredicto_vigente(forjadas)
    assert vig["veredicto"] == protocolo.SIN_VENTAJA and not vig["por_defecto"]


def test_lo_que_no_se_reconoce_no_rompe_la_construccion(forjadas):
    """Cuatro ficheros que no deberían estar ahí, y la base se construye igual con los demás."""
    f = forjadas["fuentes"].set_index("ruta")
    esperado = {"reportes/x-lista.json": ("desconocido", "forma no reconocida"),
                "reportes/x-roto.json": ("ilegible", "no es JSON"),
                "reportes/x-informe-roto.json": ("informe", "forma inesperada"),
                "reportes/x-prereg-fuera.json": ("preregistro", "fuera de prereg/")}
    for ruta, (tipo, motivo) in esperado.items():
        assert f.loc[ruta, "tipo"] == tipo and not f.loc[ruta, "valido"], ruta
        assert motivo in f.loc[ruta, "motivo"], (ruta, f.loc[ruta, "motivo"])
    assert "reportes/x-informe-roto.json" not in set(forjadas["informes"]["ruta"]), \
        "un fichero que falla no deja filas a medias"
    assert list(forjadas["preregistros"]["ruta"]) == [f"prereg/{PREREG_REAL}"], \
        "un preregistro fuera de prereg/ no se cuenta como preregistro"


def test_un_veredicto_sin_fecha_no_cuenta(forjadas):
    v = forjadas["veredictos"].set_index("ruta").loc["reportes/x-veredicto-sin-fecha.json"]
    assert not v["valido"] and "sin fecha" in v["motivo"]


def test_el_vigente_es_el_que_juzgo_con_mas_datos(forjadas):
    """El veredicto más reciente de la base forjada juzgó con menos datos (hasta el 4200): no
    desplaza al real, que llega al 4272. Volver a correr el laboratorio sobre un snapshot viejo no
    puede tapar un veredicto con más sorteos."""
    v = forjadas["veredictos"].set_index("ruta")
    assert v.loc[f"reportes/{MENOS_DATOS}", "valido"], "el de menos datos es válido: no es eso"
    assert v.loc[f"reportes/{MENOS_DATOS}", "corrida_utc"] > v.loc[f"reportes/{VEREDICTO_REAL}",
                                                                    "corrida_utc"]
    vig = almacen.veredicto_vigente(forjadas)
    assert [r["ruta"] for r in vig["vigentes"]] == [f"reportes/{VEREDICTO_REAL}"]


@pytest.mark.parametrize("filas,vigente", [
    # (ruta, datos hasta, corrida): gana el de más datos, aunque sea más viejo
    ([("a", 4300, "2026-10-01T00:00:00+00:00"), ("b", 4272, "2026-10-09T00:00:00+00:00")], "a"),
    # con los mismos datos, el más reciente
    ([("a", 4272, "2026-10-01T00:00:00+00:00"), ("b", 4272, "2026-10-09T00:00:00+00:00")], "b"),
    # uno sin datos registrados solo cuenta si no hay otro
    ([("a", None, "2026-10-09T00:00:00+00:00"), ("b", 4100, "2026-10-01T00:00:00+00:00")], "b"),
    ([("a", None, "2026-10-09T00:00:00+00:00")], "a"),
])
def test_el_criterio_del_vigente(filas, vigente):
    import pandas as pd

    df = pd.DataFrame([{"ruta": r, "prereg_id": "p", "valido": True, "ventaja": False,
                        "ultimo_concurso_datos": d, "corrida_utc": c} for r, d, c in filas])
    df["ultimo_concurso_datos"] = df["ultimo_concurso_datos"].astype("Int32")
    assert almacen.veredicto_vigente({"veredictos": df})["vigentes"][0]["ruta"] == vigente


def test_las_fechas_se_normalizan_antes_de_ordenarlas():
    """'…Z' y '…+00:00' son la misma hora; como texto no ordenarían igual."""
    assert almacen._utc("2026-10-06T00:00:00Z") == almacen._utc("2026-10-06T00:00:00+00:00")
    assert almacen._utc("2026-10-05T19:00:00-05:00") == "2026-10-06T00:00:00+00:00"
    assert almacen._utc(None) is None and almacen._utc("ayer") is None


def test_sin_carpetas_no_se_construye_nada(tmp_path):
    """Lanzada desde otra carpeta, la orden no puede dejar una base vacía en silencio."""
    with pytest.raises(SystemExit, match="raíz del repositorio"):
        almacen.construir(tmp_path / "reportes", tmp_path / "prereg", tmp_path / "x.duckdb")
    assert not (tmp_path / "x.duckdb").exists()


# ---------------------------------------------------------------- construir y leer
def test_dos_construcciones_dan_lo_mismo_y_ninguna_deja_la_base_abierta(base_real, tablas):
    """La misma entrada da la misma base, salvo la hora; sin restos del fichero temporal; y la base
    se puede mover después de leerla.

    Lo último importa en Windows: una base abierta no se puede sustituir, y `construir` necesita
    hacerlo con la app en marcha. Si `leer` dejara la conexión abierta, el renombrado fallaría.
    """
    arbol = base_real.parent
    ruta = almacen.construir(arbol / "reportes", arbol / "prereg", arbol / "otra.duckdb")["salida"]
    otra = almacen.leer(ruta)
    for nombre in almacen.ESQUEMA:
        x, y = tablas[nombre], otra[nombre]
        if nombre == "construccion":
            x, y = x.drop(columns="construido_utc"), y.drop(columns="construido_utc")
        assert x.equals(y), nombre
    assert not [p.name for p in arbol.iterdir() if "construyendo" in p.name or p.suffix == ".wal"]
    ruta.replace(arbol / "movida.duckdb")
    (arbol / "movida.duckdb").unlink()


def test_leer_es_de_solo_lectura(base_real, monkeypatch):
    import duckdb

    vistos = []
    original = duckdb.connect

    def espia(*a, **k):
        vistos.append(k.get("read_only"))
        return original(*a, **k)

    monkeypatch.setattr(duckdb, "connect", espia)
    almacen.leer(base_real)
    assert vistos == [True]


def test_la_frescura_ve_cada_cambio(base_real, tablas):
    """Un fichero nuevo, uno cambiado y uno borrado: tres cambios distintos, tres listas.

    Se hace sobre el árbol de la base compartida y se deja como estaba, pase lo que pase: construir
    otra base solo para esto costaría lo mismo que todo el test.
    """
    arbol = base_real.parent
    assert almacen.frescura(base_real, tablas)["al_dia"]
    nuevo = arbol / "reportes" / "2026-10-09_otro.json"
    objetivo = arbol / "reportes" / VEREDICTO_REAL
    original = objetivo.read_bytes()
    try:
        nuevo.write_text("{}", encoding="utf-8")
        assert almacen.frescura(base_real, tablas)["nuevos"] == ["reportes/2026-10-09_otro.json"]
        nuevo.unlink()
        objetivo.write_bytes(original + b" ")
        assert almacen.frescura(base_real, tablas)["cambiados"] == [f"reportes/{VEREDICTO_REAL}"]
        objetivo.unlink()
        f = almacen.frescura(base_real, tablas)
        assert f["borrados"] == [f"reportes/{VEREDICTO_REAL}"] and not f["al_dia"]
    finally:
        nuevo.unlink(missing_ok=True)
        objetivo.write_bytes(original)
    assert almacen.frescura(base_real, tablas)["al_dia"]


def test_una_base_de_otro_esquema_se_rechaza(tablas):
    otra = dict(tablas)
    otra["construccion"] = tablas["construccion"].assign(version_esquema=almacen.VERSION_ESQUEMA + 1)
    assert "esquema" in almacen.problema_de_esquema(otra)
    sin = {k: v for k, v in tablas.items() if k != "veredictos"}
    assert "veredictos" in almacen.problema_de_esquema(sin)
    vieja = dict(tablas, veredictos=tablas["veredictos"].drop(columns="ultimo_concurso_datos_min"))
    assert "ultimo_concurso_datos_min" in almacen.problema_de_esquema(vieja), \
        "una base de una versión anterior del código no se usa aunque tenga todas las tablas"


def test_la_base_no_se_publica(raiz):
    """Decisión de Almacenamiento: `.gitignore` excluye la base y el índice de git no la tiene.

    `.gitignore` no basta: `git add -f` se lo salta, y el colador no puede leer un binario. Por eso
    esto mira el índice. En una copia sin repositorio —la de `scripts/mutar.py`— no hay nada que
    mirar y se salta.
    """
    import subprocess

    r = subprocess.run(["git", "-C", str(raiz), "ls-files", "--", "*.duckdb", "*.duckdb.wal"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        pytest.skip("no es un repositorio de git")
    assert r.stdout.strip() == "", f"una base de datos en el índice de git: {r.stdout}"
    ignorada = subprocess.run(["git", "-C", str(raiz), "check-ignore", "-q", "melate.duckdb"])
    assert ignorada.returncode == 0, ".gitignore tiene que excluir melate.duckdb"


def test_la_lectura_no_arrastra_el_computo(raiz):
    """La app importa `melate.almacen`; su nivel superior no puede traer el laboratorio, el
    backtest ni nada que salga a la red. El laboratorio se importa solo dentro de `construir`."""
    arbol = ast.parse((raiz / "src" / "melate" / "almacen.py").read_text(encoding="utf-8"))
    arriba = set()
    for nodo in arbol.body:
        if isinstance(nodo, ast.Import):
            arriba |= {a.name for a in nodo.names}
        elif isinstance(nodo, ast.ImportFrom):
            arriba.add(("." * nodo.level) + (nodo.module or ""))
    prohibidos = {".lab", ".backtest", ".audit", ".ingest", ".informe", ".popularity",
                  ".portfolio", "requests", "scrapling", "sklearn"}
    assert not arriba & prohibidos, arriba & prohibidos


def test_el_veredicto_registra_los_datos_sobre_los_que_juzga(raiz, datos):
    """H1 de la Fase 4: regla 6 del protocolo en la pieza que juzga.

    Dos valores: los datos del snapshot dicen 4272; los mismos datos recortados dicen otra cosa. Si
    el campo no saliera de los datos usados, los dos darían lo mismo.
    """
    from melate import lab

    spec = lab.cargar_preregistro(raiz / "prereg" / PREREG_REAL)
    publicado = dict(reversed(l.split()) for l in
                     (raiz / "data" / "raw" / "2026-10-02" / "SHA256.txt").read_text().splitlines()
                     if l.strip())
    r = lab.evaluar(spec, carpeta=str(raiz / "data" / "raw" / "2026-10-02"))
    for juego in JUEGOS:
        assert r["datos"][juego]["sha256"] == publicado[f"{juego}.csv"]
        assert r["datos"][juego]["ultimo_concurso"] == 4272
    recortados = {j: d.iloc[:-10] for j, d in datos["era"].items()}
    r2 = lab.evaluar(spec, juegos=recortados)
    assert {d["ultimo_concurso"] for d in r2["datos"].values()} == {4262}
    assert json.dumps(r2["datos"])  # y se serializa: va al JSON del veredicto
