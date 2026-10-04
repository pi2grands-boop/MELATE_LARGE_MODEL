"""Carteras de boletos con presupuesto fijo.

**Lo primero, porque es lo que más fácil es malentender: esto no mejora tus probabilidades de
ganar, y casi no mejora el valor esperado.** Nada lo hace. El valor esperado de un boleto de Melate
es de −59 % y sigue siéndolo después de pasar por aquí.

Lo que una cartera sí puede hacer, y es lo único que hace, es **no compartir la bolsa con medio
país si acertaras**. La bolsa es a repartir entre los acertantes, así que elegir una combinación que
nadie más juega no cambia la probabilidad de acertar —no hay nada que la cambie— pero sí cambia
cuánto te tocaría.

Y eso tiene un techo medido, no opinado (`Documentos_Contexto/Fases/2026-10-03_popularidad/`):

| Juego | Techo de evitar compartir | Suelo de una combinación muy jugada |
|---|---|---|
| Melate | **+0,27 %** del precio | −14,3 % |
| Revancha | **+0,58 %** | −31,4 % |
| Revanchita | **+1,63 %** | −87,6 % |

La asimetría es de **54 a 1**: lo que se puede perder eligiendo mal es 54 veces lo que se puede
ganar eligiendo bien. Por eso este módulo está escrito como un **seguro**, no como una estrategia.
Su trabajo es que no elijas 1-2-3-4-5-6, no hacerte ganar.

Las dos razones de que Revanchita sea donde más importa, y las dos son estructurales:
Revanchita solo paga 6 aciertos, así que **todo** su valor esperado está en la bolsa compartible; y
su valor esperado es el menos malo de los tres (−12 %), así que el mismo peso absoluto pesa más.

**Sobre el valor esperado de una cartera.** La esperanza es lineal: diez boletos valen diez veces lo
que vale uno, estén repartidos o solapados. Separarlos **no sube la media**, cambia la forma de la
distribución —sube la probabilidad de algún acierto pequeño y baja la de varios a la vez—. Si algún
texto de aquí sugiriera otra cosa, es un error y hay un test que lo persigue.
"""
import argparse
import json
import math
import pathlib
import random
from itertools import combinations

from .constantes import C, JUEGOS, K, N, PRECIO

# ---------------------------------------------------------------- el modelo de popularidad
#
# `popularity.py` mide una sola cosa de verdad: que el número adicional de un sorteo aparece en
# menos boletos cuando es > 31. De ahí sale un peso por número. Todo lo demás de este bloque son
# SUPUESTOS declarados, con nombre y valor visible, y se distinguen de lo medido a propósito: este
# proyecto no presenta una suposición como un hallazgo.

CORTE_CALENDARIO = 31

# Penalizaciones de patrón: cuánto MÁS jugada se supone una combinación con esa forma. Son
# supuestos, no mediciones: las tablas de ganadores no pueden medirlos, porque cada sorteo solo
# aísla el adicional. Vienen de la literatura de loterías y de lo que se ve en los volantes
# ganadores. Se exponen como parámetro para que se puedan cambiar y para que un test pueda darles
# dos valores distintos y comprobar que de verdad gobiernan algo.
PATRONES = {
    "todos_en_calendario": 2.0,   # las 6 <= 31: el patrón de cumpleaños, el más jugado de todos
    "consecutivos_3": 1.5,        # tres o más números seguidos
    "progresion_aritmetica": 3.0,  # 5-10-15-20-25-30 y familia
    "misma_decena": 2.5,          # los 6 en el mismo tramo de diez
    "todos_multiplos": 2.0,       # todos múltiplos de 3, 5, 7...
    "suma_central": 1.3,          # suma cerca de la media: donde se acumula casi todo el mundo
}


def pesos_por_numero(cociente_fuera_entre_dentro, corte=CORTE_CALENDARIO):
    """Peso de popularidad de cada número, normalizado a media 1.

    `cociente_fuera_entre_dentro` es lo que mide `popularity.efecto_calendario`: cuántas veces
    aparece un número > 31 en los boletos comparado con uno <= 31. Un 0,8 quiere decir que los
    números fuera del calendario están un 20 % menos jugados.

    La normalización es `sum(w) == 56`, que es lo que hace que un peso de 1 signifique "tan jugado
    como la media" y no "tan jugado como un número bajo".
    """
    if cociente_fuera_entre_dentro is None or cociente_fuera_entre_dentro <= 0:
        return {n: 1.0 for n in range(1, N + 1)}
    r = cociente_fuera_entre_dentro
    dentro = corte
    fuera = N - corte
    w_dentro = N / (dentro + fuera * r)
    return {n: (w_dentro if n <= corte else w_dentro * r) for n in range(1, N + 1)}


def _rachas(combo):
    """La racha de consecutivos más larga."""
    mejor = actual = 1
    for a, b in zip(combo, combo[1:]):
        actual = actual + 1 if b == a + 1 else 1
        mejor = max(mejor, actual)
    return mejor


def _es_progresion(combo):
    difs = {b - a for a, b in zip(combo, combo[1:])}
    return len(difs) == 1


def _todos_multiplos(combo):
    return any(all(x % m == 0 for x in combo) for m in (3, 4, 5, 6, 7, 8, 9, 10, 11))


def patrones_de(combo, corte=CORTE_CALENDARIO):
    """Qué patrones de los declarados cumple esta combinación. Lista de nombres."""
    c = sorted(combo)
    tiene = []
    if c[-1] <= corte:
        tiene.append("todos_en_calendario")
    if _rachas(c) >= 3:
        tiene.append("consecutivos_3")
    if _es_progresion(c):
        tiene.append("progresion_aritmetica")
    if (c[-1] - 1) // 10 == (c[0] - 1) // 10:
        tiene.append("misma_decena")
    if _todos_multiplos(c):
        tiene.append("todos_multiplos")
    media = K * (N + 1) / 2                       # 171 para 6 de 56
    if abs(sum(c) - media) <= 0.08 * media:
        tiene.append("suma_central")
    return tiene


def popularidad(combo, pesos=None, patrones=None, corte=CORTE_CALENDARIO):
    """Cuántas veces más jugada que la media se supone esta combinación.

    Un 1,0 es "tan jugada como la media". Un 12 es "doce veces más jugada". Un 0,7 es menos jugada
    que la media, que es donde queremos estar.

    El producto de los pesos por número es una **aproximación**: la popularidad real sobre
    combinaciones no es el producto de sus marginales —quien juega cumpleaños correlaciona los seis
    números a la vez— y las tablas de ganadores no dan para más. Para **ordenar** candidatas vale;
    para afirmar cuánta gente juega una combinación concreta, no, y no se usa para eso.
    """
    pesos = pesos or {n: 1.0 for n in range(1, N + 1)}
    patrones = PATRONES if patrones is None else patrones
    factor = 1.0
    for n in combo:
        factor *= pesos.get(n, 1.0)
    for p in patrones_de(combo, corte):
        factor *= patrones.get(p, 1.0)
    return factor


def compartiendo(combo, ventas, pesos=None, patrones=None):
    """El factor de reparto de la bolsa para esta combinación: E[1/(1+otros acertantes)].

    Los otros acertantes con la misma combinación son Poisson de media
    `lambda = ventas * popularidad / C`, y para esa Poisson
    `E[1/(1+W)] = (1 - exp(-lambda)) / lambda`. Es la misma fórmula que usa `ev.valor_esperado`
    para el caso medio; aquí se aplica combinación a combinación.

    Devuelve (factor, lambda). Un factor de 1 es "no compartes con nadie".
    """
    lam = ventas * popularidad(combo, pesos, patrones) / C
    if lam <= 0:
        return 1.0, 0.0
    return (1 - math.exp(-lam)) / lam, lam


# ---------------------------------------------------------------- armar la cartera


def _solape_maximo(combo, elegidas):
    return max((len(set(combo) & set(e)) for e in elegidas), default=0)


# Tope de popularidad por defecto. Medido sobre 200.000 combinaciones al azar con los pesos
# medidos: la mediana está en 1,12 y el percentil 99 en 4,01, así que un tope de 1,0 deja pasar el
# 40 % de las combinaciones —13 millones— y corta justo la cola que hace daño.
TOPE_POPULARIDAD = 1.0


def cartera(juego, presupuesto, pesos=None, patrones=None, ventas=1.2e6,
            candidatas=20000, solape_maximo=2, tope_popularidad=TOPE_POPULARIDAD,
            semilla=20261003):
    """Una cartera de boletos para el presupuesto dado.

    **El objetivo no es minimizar la popularidad, y la diferencia importa.** Minimizarla a secas
    produce una cartera degenerada: como todos los números > 31 pesan lo mismo, el óptimo es jugar
    *solo* números altos, y una primera versión de esta función cubría 27 de los 56. Eso no mejora
    el valor esperado —la ganancia sigue siendo del 0,16 %— y concentra toda la cartera en media
    urna, que es un riesgo que nadie pidió.

    Lo correcto es lo que dice la asimetría de 54 a 1: **poner un techo, no perseguir un suelo.**

    1. **Se descarta lo que pase de `tope_popularidad`.** Ese es el seguro, y es el 95 % del valor
       de este módulo.
    2. **Entre las que pasan, se maximiza la cobertura**: cada boleto nuevo intenta aportar números
       que la cartera todavía no tiene, con el tope de `solape_maximo` números compartidos con
       cualquier boleto ya elegido.

    El punto 2 **no cambia la media** —la esperanza es lineal, diez boletos valen diez veces uno,
    solapados o no— sino la forma de la distribución: repartidos, es más probable algún acierto
    pequeño y menos probable varios a la vez. Hay un test que lo fija.

    Búsqueda voraz sobre una muestra con semilla fija: mismo presupuesto y misma semilla, misma
    cartera.
    """
    precio = PRECIO[juego]
    n_boletos = int(presupuesto // precio)
    rng = random.Random(semilla)

    pool, vistas = [], set()
    while len(pool) < candidatas:
        c = tuple(sorted(rng.sample(range(1, N + 1), K)))
        if c not in vistas:
            vistas.add(c)
            pool.append(c)
    pops = {c: popularidad(c, pesos, patrones) for c in pool}
    aptas = [c for c in pool if pops[c] <= tope_popularidad]
    if not aptas:
        raise ValueError(f"ninguna de las {candidatas} candidatas baja del tope "
                         f"{tope_popularidad}: ¿tope demasiado bajo?")

    # El solape de cada candidata contra lo ya elegido se lleva **al día** en vez de recalcularlo
    # entero en cada ronda. Recalcularlo hacía el bucle O(boletos x candidatas x elegidas) y puso
    # la suite rápida en 26 s; así es O(boletos x candidatas). El proyecto ya se dejó crecer el
    # bucle rápido una vez sin enterarse
    # (Rendimiento/Arreglos_Bugs/2026-10-03_01-59_la-suite-rapida-no-era-rapida.md).
    conj = {c: frozenset(c) for c in aptas}
    solape = dict.fromkeys(aptas, 0)
    elegidas, cubiertos = [], set()
    for tope in (solape_maximo, solape_maximo + 1, K):   # si el tope es inalcanzable, se relaja
        while len(elegidas) < n_boletos:
            # La que más números nuevos aporte; a igualdad, la menos popular.
            mejor, mejor_clave = None, None
            for c in aptas:
                if solape[c] > tope:
                    continue
                clave = (len(conj[c] - cubiertos), -pops[c])
                if mejor_clave is None or clave > mejor_clave:
                    mejor, mejor_clave = c, clave
            if mejor is None:
                break
            elegidas.append(mejor)
            cubiertos |= conj[mejor]
            aptas.remove(mejor)
            nuevo = conj.pop(mejor)
            for c in aptas:
                n_comun = len(conj[c] & nuevo)
                if n_comun > solape[c]:
                    solape[c] = n_comun
        if len(elegidas) >= n_boletos:
            break

    boletos = []
    for c in elegidas:
        factor, lam = compartiendo(c, ventas, pesos, patrones)
        boletos.append({"numeros": list(c), "popularidad": round(popularidad(c, pesos, patrones), 4),
                        "patrones": patrones_de(c), "factor_reparto": round(factor, 6),
                        "acertantes_esperados": round(lam, 6)})

    solapes = [len(set(a) & set(b)) for a, b in combinations(elegidas, 2)]
    return {
        "juego": juego,
        "presupuesto": presupuesto,
        "precio_boleto": precio,
        "boletos": len(boletos),
        "coste": len(boletos) * precio,
        "sobrante": presupuesto - len(boletos) * precio,
        "numeros_cubiertos": len(cubiertos),
        "tope_popularidad": tope_popularidad,
        "candidatas_aptas": sum(1 for c in pool if pops[c] <= tope_popularidad),
        "candidatas_descartadas": sum(1 for c in pool if pops[c] > tope_popularidad),
        "solape_maximo_real": max(solapes) if solapes else 0,
        "solape_medio": round(sum(solapes) / len(solapes), 3) if solapes else 0,
        "popularidad_media": round(sum(b["popularidad"] for b in boletos) / len(boletos), 4) if boletos else None,
        "semilla": semilla,
        "ventas_supuestas": ventas,
        "detalle": boletos,
    }


def valorar(cartera_, bolsa, menores_brutos, impuesto=0.07):
    """Lo que vale esta cartera, con el aviso que tiene que acompañarla siempre.

    Se calcula boleto a boleto porque el factor de reparto depende de la combinación. El término de
    menores NO depende de ella: las categorías menores no se comparten de la misma forma y el dato
    que tenemos es un promedio.
    """
    juego = cartera_["juego"]
    precio = cartera_["precio_boleto"]
    total = 0.0
    for b in cartera_["detalle"]:
        evb = bolsa * (1 - impuesto) * b["factor_reparto"] / C
        total += evb + menores_brutos * (1 - impuesto)
    coste = cartera_["coste"]
    # La referencia: la misma cartera si no se hubiera mirado la popularidad (factor medio).
    lam_medio = cartera_["ventas_supuestas"] / C
    s_medio = (1 - math.exp(-lam_medio)) / lam_medio if lam_medio else 1.0
    base = cartera_["boletos"] * (bolsa * (1 - impuesto) * s_medio / C + menores_brutos * (1 - impuesto))
    return {
        # Con qué se valoró. Sin esto el reporte daba un valor esperado sin decir de qué bolsa
        # salía, y la app tenía que confesar que no lo sabía.
        "bolsa": bolsa,
        "menores_brutos": menores_brutos,
        "impuesto": impuesto,
        "coste": coste,
        "valor_esperado": round(total, 2),
        "rendimiento": round(total / coste - 1, 4) if coste else None,
        "valor_esperado_sin_mirar_popularidad": round(base, 2),
        "ganancia_por_evitar_compartir": round(total - base, 4),
        "ganancia_por_boleto": round((total - base) / cartera_["boletos"], 6) if cartera_["boletos"] else None,
        "ganancia_como_porcentaje_del_precio": round((total - base) / (cartera_["boletos"] * precio), 6)
                                               if cartera_["boletos"] else None,
        "aviso": ("El valor esperado es NEGATIVO y esta cartera no lo arregla. Evitar combinaciones "
                  "compartidas no cambia la probabilidad de acertar: solo con cuánta gente "
                  "repartirías. Sin ventaja demostrada."),
    }


# ---------------------------------------------------------------- línea de órdenes


def _del_reporte(ruta, juego):
    """Saca de un reporte de `melate.popularity` lo que la cartera necesita."""
    with open(ruta, encoding="utf-8") as f:
        pop = json.load(f)
    # El efecto calendario solo lo mide Melate (es el único con adicional), pero describe la
    # conducta de los jugadores, no la mecánica del juego: se aplica a los tres.
    mel = (pop.get("juegos") or {}).get("Melate") or {}
    ec = mel.get("efecto_calendario") or {}
    propio = (pop.get("juegos") or {}).get(juego) or {}
    v = propio.get("ventas") or mel.get("ventas") or {}
    mb = propio.get("menores_brutos_por_bolsa") or {}
    return ec.get("cociente_fuera_entre_dentro"), v.get("mediana"), mb.get("mediana", 0.0)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Carteras de boletos con presupuesto fijo.",
        epilog="Esto NO mejora tus probabilidades de ganar. Solo evita que, si ganaras, "
               "tuvieras que repartir con mucha gente. El valor esperado sigue siendo negativo.")
    ap.add_argument("--juego", default="Melate", choices=JUEGOS)
    ap.add_argument("--presupuesto", type=float, required=True)
    ap.add_argument("--bolsa", type=float, help="bolsa en juego, para valorar la cartera")
    ap.add_argument("--popularidad", help="reporte de `melate.popularity` con el efecto medido")
    ap.add_argument("--tope", type=float, default=TOPE_POPULARIDAD)
    ap.add_argument("--solape", type=int, default=2)
    ap.add_argument("--semilla", type=int, default=20261003)
    ap.add_argument("--salida", default="reportes/cartera.json")
    a = ap.parse_args(argv)

    cociente, ventas_med, menores = None, 1.2e6, 0.0
    if a.popularidad:
        cociente, v, menores = _del_reporte(a.popularidad, a.juego)
        ventas_med = v or ventas_med
        print(f"Popularidad medida: los > {CORTE_CALENDARIO} aparecen en un "
              f"{1 - cociente:.0%} menos de boletos." if cociente else
              "El reporte no trae efecto calendario: pesos planos.")
    else:
        print("Sin --popularidad: pesos planos. La cartera solo evitará patrones, no números.")

    pesos = pesos_por_numero(cociente)
    car = cartera(a.juego, a.presupuesto, pesos=pesos, ventas=ventas_med,
                  tope_popularidad=a.tope, solape_maximo=a.solape, semilla=a.semilla)

    print(f"\n{car['boletos']} boletos de {a.juego} por ${car['coste']:.0f} "
          f"(sobran ${car['sobrante']:.0f})")
    print(f"  cubre {car['numeros_cubiertos']}/{N} números · solape máximo {car['solape_maximo_real']} "
          f"· popularidad media {car['popularidad_media']}")
    print(f"  descartadas por el tope {a.tope}: {car['candidatas_descartadas']} de "
          f"{car['candidatas_aptas'] + car['candidatas_descartadas']} candidatas\n")
    for i, b in enumerate(car["detalle"], 1):
        marca = f"  <- {', '.join(b['patrones'])}" if b["patrones"] else ""
        print(f"  {i:3d}  " + " ".join(f"{n:2d}" for n in b["numeros"]) +
              f"   popularidad {b['popularidad']:.3f}{marca}")

    if a.bolsa:
        car["valoracion"] = valorar(car, a.bolsa, menores)
        v = car["valoracion"]
        print(f"\n  valorada con una bolsa de {v['bolsa'] / 1e6:.1f} M y unos premios menores de "
              f"{v['menores_brutos']:.4f} por boleto, impuesto {v['impuesto']:.0%}")
        print(f"  coste ${v['coste']:.0f} · valor esperado ${v['valor_esperado']:.2f} "
              f"({v['rendimiento']:+.1%})")
        print(f"  lo que aporta evitar compartir: ${v['ganancia_por_evitar_compartir']:.2f} "
              f"en toda la cartera ({v['ganancia_como_porcentaje_del_precio']:+.2%} del precio)")

    salida = pathlib.Path(a.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    with open(salida, "w", encoding="utf-8") as f:
        json.dump(car, f, ensure_ascii=False, indent=1, default=str)
    print(f"\nCartera en {salida}")
    print("\nEl valor esperado es NEGATIVO. Esto no mejora tus probabilidades de ganar:")
    print("solo reduce con cuánta gente repartirías si, contra todo pronóstico, ganaras.")
    return car


if __name__ == "__main__":
    main()
