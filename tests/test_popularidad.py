"""Las tablas de ganadores: combinatoria, parseo, y el trato con el sitio.

El trato con el sitio **se comprueba, no se promete**. Un dictamen que dice "1 solicitud por
segundo" y no tiene test es una intención; con test es una propiedad del programa. Por eso la mitad
de este fichero mide el comportamiento de red con una sesión falsa, sin tocar internet.

Los tests marcados `red` sí salen a internet y están fuera del bucle rápido.
"""
import time

import pytest

from melate import popularity as pop
from melate.constantes import C, K, N

# Una página real, recortada: el sorteo 4272 de Melate tal como lo sirve el sitio. Conserva a
# propósito las DOS formas de escribir el adicional que conviven en la misma tabla real:
# "+ adicional" (2ndo) y "y el adicional" (6to). Un parser que solo entienda una se come
# categorías en silencio, y en silencio es la palabra importante.
PAGINA = """<!DOCTYPE html><html lang="es"><head><title>Sorteo 4272</title></head><body>
<div id="resultados">
<span class="numbox"><span class="numnatural"><b class="vertcent">4 </b></span></span>
<span class="numbox"><span class="numnatural"><b class="vertcent">6 </b></span></span>
<span class="numbox"><span class="numnatural"><b class="vertcent">24 </b></span></span>
<span class="numbox"><span class="numnatural"><b class="vertcent">33 </b></span></span>
<span class="numbox"><span class="numnatural"><b class="vertcent">37 </b></span></span>
<span class="numbox"><span class="numnatural"><b class="vertcent">56 </b></span></span>
<span class="numbox"><span class="numadicional"><b class="vertcent">32 </b></span></span>
</div>
<table>
<tr><th>Lugar</th><th>Aciertos</th><th>Número de ganadores</th><th>Premio individual</th></tr>
<tr><td>1er</td><td>6 números naturales</td><td>0</td><td>$0.00</td></tr>
<tr><td>2ndo</td><td>5 números naturales + adicional</td><td>0</td><td>$0.00</td></tr>
<tr><td>3ro</td><td>5 números naturales</td><td>14</td><td>$44,898.68</td></tr>
<tr><td>4to</td><td>4 números naturales + adicional</td><td>15</td><td>$4,835.24</td></tr>
<tr><td>5to</td><td>4 números naturales</td><td>650</td><td>$706.68</td></tr>
<tr><td>6to</td><td>3 números naturales y el adicional</td><td>664</td><td>$161.29</td></tr>
<tr><td>7mo</td><td>3 números naturales</td><td>14,300</td><td>$43.01</td></tr>
<tr><td>8vo</td><td>2 números naturales + adicional</td><td>8,313</td><td>$32.26</td></tr>
<tr><td>9no</td><td>2 números naturales</td><td>115,808</td><td>$26.88</td></tr>
</table></body></html>"""

PAGINA_REVANCHA = """<html><body><div id="resultados">
<span class="numnatural"><b>15</b></span><span class="numnatural"><b>16</b></span>
<span class="numnatural"><b>38</b></span><span class="numnatural"><b>40</b></span>
<span class="numnatural"><b>41</b></span><span class="numnatural"><b>50</b></span>
</div><table>
<tr><th>Lugar</th><th>Aciertos</th><th>Número de ganadores</th><th>Premio individual</th></tr>
<tr><td>1er</td><td>6 números naturales</td><td>0</td><td>$0.00</td></tr>
<tr><td>2ndo</td><td>5 números naturales</td><td>3</td><td>$206,628.31</td></tr>
<tr><td>3ro</td><td>4 números naturales</td><td>316</td><td>$1,821.54</td></tr>
<tr><td>4to</td><td>3 números naturales</td><td>8,826</td><td>$26.88</td></tr>
<tr><td>5to</td><td>2 números naturales</td><td>87,383</td><td>$10.75</td></tr>
</table></body></html>"""


class SesionFalsa:
    """Una sesión que no toca la red y apunta cuándo la llaman."""

    def __init__(self, cuerpo=PAGINA, status=200):
        self.cuerpo, self.status = cuerpo, status
        self.momentos, self.urls = [], []

    def get(self, url):
        self.momentos.append(time.monotonic())
        self.urls.append(url)
        return type("R", (), {"status": self.status, "body": self.cuerpo.encode("utf-8")})()


# ---------------------------------------------------------------- combinatoria


def test_las_favorables_son_las_del_contrato():
    """Las cifras del CLAUDE.md, sección Constantes, una por una."""
    assert pop.favorables("Melate", 6) == 1
    assert pop.favorables("Melate", 5, True) == 6
    assert pop.favorables("Melate", 5) == 294
    assert pop.favorables("Melate", 4, True) == 735
    assert pop.favorables("Melate", 4) == 17640
    assert pop.favorables("Melate", 3, True) == 23520
    assert pop.favorables("Melate", 3) == 368480
    assert pop.favorables("Melate", 2, True) == 276360
    assert pop.favorables("Melate", 2) == 3178140
    assert pop.favorables("Revancha", 5) == 300
    assert pop.favorables("Revancha", 4) == 18375
    assert pop.favorables("Revanchita", 6) == 1
    assert pop.favorables("Revanchita", 5) == 0, "Revanchita solo paga 6 aciertos"


def test_las_categorias_de_melate_suman_el_universo():
    """Partición exacta: toda combinación de 6 cae en una y solo una categoría.

    Es la comprobación que atrapa un error de signo o un 49 donde iba un 50. Si las categorías no
    suman C(56,6), alguna fórmula está mal y todas las probabilidades que salgan de aquí también.
    """
    total = sum(pop.favorables("Melate", k, a)
                for k in range(K + 1) for a in (False, True))
    assert total == C, f"las categorías de Melate suman {total}, no {C}"


def test_las_categorias_de_revancha_suman_el_universo():
    assert sum(pop.favorables("Revancha", k) for k in range(K + 1)) == C


def test_revancha_no_tiene_adicional():
    assert pop.favorables("Revancha", 5, con_adicional=True) == 0


def test_un_juego_desconocido_no_se_inventa():
    with pytest.raises(ValueError):
        pop.favorables("Chispazo", 3)


# ---------------------------------------------------------------- parseo


def test_parsea_las_dos_formas_de_escribir_el_adicional():
    """'+ adicional' y 'y el adicional' conviven en la misma tabla real del sitio."""
    cats = pop.parsear(PAGINA, "Melate", 4272)
    assert len(cats) == 9
    con_a = [c for c in cats if c["adicional"]]
    assert len(con_a) == 4, "faltan categorías con adicional: ¿el parser solo entiende una forma?"
    sexta = next(c for c in cats if c["aciertos"] == 3 and c["adicional"])
    assert sexta["ganadores"] == 664, "la categoría escrita 'y el adicional' se perdió"


def test_parsea_los_miles_y_los_importes():
    cats = pop.parsear(PAGINA, "Melate", 4272)
    novena = next(c for c in cats if c["aciertos"] == 2 and not c["adicional"])
    assert novena["ganadores"] == 115808
    assert novena["premio"] == pytest.approx(26.88)


def test_una_tabla_incompleta_falla_ruidosamente():
    """Si el sitio cambia de forma, esto tiene que reventar, no devolver media tabla."""
    recortada = PAGINA.replace(
        "<tr><td>9no</td><td>2 números naturales</td><td>115,808</td><td>$26.88</td></tr>", "")
    with pytest.raises(ValueError, match="categorías"):
        pop.parsear(recortada, "Melate", 4272)


def test_una_categoria_que_no_existe_falla():
    raro = PAGINA.replace("6 números naturales", "9 números naturales")
    with pytest.raises(ValueError):
        pop.parsear(raro, "Melate", 4272)


def test_lee_los_numeros_de_la_pagina():
    assert pop.numeros_de_la_pagina(PAGINA) == ([4, 6, 24, 33, 37, 56], 32)


def test_revancha_no_trae_adicional_en_la_pagina():
    nat, adi = pop.numeros_de_la_pagina(PAGINA_REVANCHA)
    assert nat == [15, 16, 38, 40, 41, 50]
    assert adi is None


# ---------------------------------------------------------------- el trato con el sitio


def test_la_cache_evita_la_segunda_peticion(tmp_path):
    """El efecto que de verdad protege al servidor: una página descargada no se vuelve a pedir."""
    s = SesionFalsa()
    d = pop.Descargador(cache=tmp_path, pausa=0, sesion=s)
    for _ in range(5):
        d.tabla("Melate", 4272)
    assert d.peticiones == 1, f"{d.peticiones} peticiones para la misma página"
    assert len(s.urls) == 1


def test_la_cache_sobrevive_a_un_descargador_nuevo(tmp_path):
    """La caché es permanente, no de proceso: una corrida nueva no vuelve a molestar al sitio."""
    pop.Descargador(cache=tmp_path, pausa=0, sesion=SesionFalsa()).tabla("Melate", 4272)
    s2 = SesionFalsa()
    d2 = pop.Descargador(cache=tmp_path, pausa=0, sesion=s2)
    d2.tabla("Melate", 4272)
    assert d2.peticiones == 0 and not s2.urls


def test_se_respeta_una_solicitud_por_segundo(tmp_path):
    """El dictamen fija el ritmo; esto lo mide con un reloj.

    Pausa de 0,25 s para que el test no tarde tres segundos: lo que se comprueba es el mecanismo,
    y el valor real (1,0 s) es la constante PAUSA_SEGUNDOS, que se verifica aparte.
    """
    s = SesionFalsa()
    d = pop.Descargador(cache=tmp_path, pausa=0.25, sesion=s)
    for sorteo in (4270, 4271, 4272):
        d.tabla("Melate", sorteo)
    assert d.peticiones == 3
    huecos = [b - a for a, b in zip(s.momentos, s.momentos[1:])]
    assert all(h >= 0.24 for h in huecos), f"huecos demasiado cortos: {huecos}"


def test_el_ritmo_por_defecto_es_el_del_dictamen():
    assert pop.PAUSA_SEGUNDOS == 1.0, "cambiar esto es cambiar el trato con el sitio"


def test_revanchita_no_se_pide_nunca(tmp_path):
    """No tiene tabla de ganadores: pedirla sería gastar peticiones ajenas para no obtener nada."""
    s = SesionFalsa()
    d = pop.Descargador(cache=tmp_path, pausa=0, sesion=s)
    with pytest.raises(ValueError, match="no tiene tabla"):
        d.html("Revanchita", 4272)
    assert not s.urls, "se pidió Revanchita a pesar de todo"


def test_el_user_agent_se_identifica_y_no_finge_ser_un_navegador():
    assert "Mozilla" not in pop.UA, "este User-Agent es para un tercero: nos identificamos"
    assert "MaquinaMelate" in pop.UA
    assert "github.com" in pop.UA, "tiene que poder saber quiénes somos y bloquearnos"


def test_no_se_importa_nada_de_navegador():
    """`StealthyFetcher` y `DynamicFetcher` están prohibidos por el CLAUDE.md.

    Además de prohibidos son innecesarios: la página es HTML estático. Esto lo fija en el código.
    """
    fuente = __import__("pathlib").Path(pop.__file__).read_text(encoding="utf-8")
    assert "StealthyFetcher" not in fuente
    assert "DynamicFetcher" not in fuente
    assert "PlayWrightFetcher" not in fuente


def test_un_bloqueo_para_la_descarga(tmp_path):
    """Ante un 403 se levanta SitioBloqueado, que el dictamen traduce en 'parar y preguntar'."""
    d = pop.Descargador(cache=tmp_path, pausa=0, sesion=SesionFalsa(status=403))
    with pytest.raises(pop.SitioBloqueado, match="403"):
        d.html("Melate", 4272)


def test_un_404_no_es_un_bloqueo(tmp_path):
    """Pedir un sorteo que no existe es normal; confundirlo con un bloqueo esconde los de verdad.

    La primera versión levantaba `SitioBloqueado` también para el 404, y el guion de cosecha tuvo
    que mirar si el mensaje contenía "404" para decidir si parar. Ese apaño es la señal de que los
    dos casos son distintos y pedían tipos distintos.
    """
    d = pop.Descargador(cache=tmp_path, pausa=0, sesion=SesionFalsa(status=404))
    with pytest.raises(pop.SorteoNoPublicado):
        d.html("Melate", 99999)
    assert not issubclass(pop.SorteoNoPublicado, pop.SitioBloqueado)


def test_un_bloqueo_no_se_traga_en_el_agregado(tmp_path):
    """`analizar` anota los 404 y sigue, pero un bloqueo tiene que parar la corrida entera."""
    d = pop.Descargador(cache=tmp_path, pausa=0, sesion=SesionFalsa(status=403))
    with pytest.raises(pop.SitioBloqueado):
        pop.analizar("Melate", [4270, 4271], descargador=d)


def test_los_404_se_anotan_y_la_corrida_sigue(tmp_path):
    d = pop.Descargador(cache=tmp_path, pausa=0, sesion=SesionFalsa(status=404))
    r = pop.analizar("Melate", [4270, 4271], descargador=d)
    assert r["sorteos_usados"] == 0
    assert len(r["fallos"]) == 2
    assert r["ventana"] is None


def test_no_se_puede_escribir_fuera_de_la_cache(tmp_path):
    """`sorteo` y `juego` acaban en una ruta de fichero: se validan antes de construirla."""
    d = pop.Descargador(cache=tmp_path, pausa=0, sesion=SesionFalsa())
    for malo in ("../../fuera", "4272/../..", 0, -1, 1.5, True):
        with pytest.raises(ValueError):
            d.html("Melate", malo)
    with pytest.raises(ValueError):
        d.html("../../otro-sitio", 4272)


def test_una_respuesta_enorme_no_entra_en_la_cache(tmp_path):
    """Las páginas reales pesan 5-8 KB. Un megabyte es otra cosa y no se guarda como buena."""
    enorme = "<table>" + "x" * (pop.MAXIMO_BYTES + 1)
    d = pop.Descargador(cache=tmp_path, pausa=0, sesion=SesionFalsa(cuerpo=enorme))
    with pytest.raises(pop.SitioBloqueado, match="tope"):
        d.html("Melate", 4272)
    assert not list(tmp_path.rglob("*.html"))


def test_un_200_sin_tabla_tambien_es_sospechoso(tmp_path):
    """Una página de bloqueo suele venir con 200. Si no trae tabla, no se cachea como buena."""
    d = pop.Descargador(cache=tmp_path, pausa=0, sesion=SesionFalsa(cuerpo="<html>nada</html>"))
    with pytest.raises(pop.SitioBloqueado):
        d.html("Melate", 4272)
    assert not list(tmp_path.rglob("*.html")), "se cacheó una página mala"


# ---------------------------------------------------------------- estimadores


def test_las_ventas_salen_de_las_categorias_sin_adicional():
    """Mezclar las que exigen el adicional contaminaría las ventas con la popularidad."""
    cats = pop.parsear(PAGINA, "Melate", 4272)
    v = pop.ventas("Melate", cats)
    assert v["categorias_usadas"] == 4, "las 4 categorías puras con ganadores"
    assert v["ventas"] == pytest.approx(1_191_631, rel=1e-4)
    assert v["con_adicional"] == pytest.approx(971_704, rel=1e-4)


def test_la_razon_del_adicional_detecta_un_numero_poco_jugado():
    """El adicional del 4272 es el 32, justo fuera del calendario. Tiene que salir por debajo de 1."""
    cats = pop.parsear(PAGINA, "Melate", 4272)
    r = pop.razon_adicional("Melate", cats)
    assert r == pytest.approx(0.8154, abs=1e-3)
    assert r < 1, "el 32 está fuera del calendario: debería estar infrajugado"


def test_revancha_no_tiene_razon_de_adicional():
    cats = pop.parsear(PAGINA_REVANCHA, "Revancha", 4272)
    assert pop.razon_adicional("Revancha", cats) is None


def test_los_dos_estimadores_de_menores_coinciden_cuando_no_hay_ruido():
    """Son el mismo número con `ganadores/N` en lugar de `p`. Con N coherente, coinciden.

    Aquí está la relación algebraica entre los dos estimadores, que es lo que justifica preferir
    el de bolsa: no mide otra cosa, mide lo mismo con menos varianza.
    """
    cats = pop.parsear(PAGINA, "Melate", 4272)
    v = pop.ventas("Melate", cats)["ventas"]
    assert pop.menores_brutos_directo(cats) == pytest.approx(4.4106, abs=1e-3)
    assert pop.menores_brutos_por_bolsa(cats, v) == pytest.approx(4.4172, abs=1e-3)


def test_el_estimador_por_bolsa_ignora_el_premio_mayor():
    """Son premios MENORES: la bolsa de 6 aciertos no entra."""
    cats = pop.parsear(PAGINA_REVANCHA, "Revancha", 4272)
    con_mayor = [dict(c, ganadores=1, premio=1e8) if c["aciertos"] == K else c for c in cats]
    assert pop.bolsa_repartida(cats) == pytest.approx(pop.bolsa_repartida(con_mayor))


def test_el_resumen_no_inventa_una_media_de_nada():
    assert pop._resumir([]) is None
    assert pop._resumir([None, None]) is None


def test_el_efecto_calendario_necesita_los_dos_lados():
    """Media de un grupo vacío no es 0, es nada. Devolver un número aquí sería mentir."""
    solo_bajos = [{"adicional": 7, "razon_adicional": 1.1},
                  {"adicional": 15, "razon_adicional": 1.2}]
    assert pop.efecto_calendario(solo_bajos) is None


def test_el_efecto_calendario_compara_los_dos_grupos():
    muestras = ([{"adicional": 5, "razon_adicional": 1.10},
                 {"adicional": 20, "razon_adicional": 1.14}]
                + [{"adicional": 40, "razon_adicional": 0.84},
                   {"adicional": 50, "razon_adicional": 0.86}])
    ec = pop.efecto_calendario(muestras)
    assert ec["dentro_del_calendario"]["n"] == 2
    assert ec["fuera_del_calendario"]["n"] == 2
    assert ec["cociente_fuera_entre_dentro"] == pytest.approx(0.85 / 1.12, rel=1e-3)
    assert ec["cociente_fuera_entre_dentro"] < 1


def test_el_corte_del_calendario_gobierna_de_verdad():
    """Dos valores distintos del parámetro tienen que dar resultados distintos.

    Es la comprobación que pide la auditoría de las fases 1 y 2: un parámetro del que se dice que
    gobierna algo y que en realidad no se lee es un defecto que ningún test de humo encuentra.
    """
    muestras = [{"adicional": n, "razon_adicional": 1.2 if n <= 20 else 0.8}
                for n in (5, 15, 25, 35, 45, 55)]
    c20 = pop.efecto_calendario(muestras, corte=20)["cociente_fuera_entre_dentro"]
    c40 = pop.efecto_calendario(muestras, corte=40)["cociente_fuera_entre_dentro"]
    assert c20 != c40, "el corte no cambia nada: ¿se está leyendo?"
    assert c20 == pytest.approx(0.8 / 1.2, rel=1e-6)


# ---------------------------------------------------------------- contra el sitio de verdad


@pytest.mark.red
def test_el_sitio_sigue_teniendo_la_forma_que_esperamos():
    """El único test que de verdad comprueba el contrato con el tercero.

    Si el sitio cambia la tabla, todo lo demás de este fichero sigue en verde sobre un fixture que
    ya no se parece a la realidad. Este es el que se entera.
    """
    with pop.Descargador() as d:
        cats = d.tabla("Melate", 4272)
    assert len(cats) == 9
    assert next(c for c in cats if c["aciertos"] == 2 and not c["adicional"])["ganadores"] == 115808
