"""Corrección por comparaciones múltiples.

Vive en su propio módulo por dos razones: `benjamini_hochberg` la usan `audit` y `backtest`, y la
familia global necesita un dueño único.

Sobre las familias — decisión tomada con el usuario:

La regla 3 del protocolo del CLAUDE.md pide Benjamini-Hochberg "sobre TODAS las pruebas corridas,
también las que no se reportan". `baseline_auditoria.py` lo aplica en dos familias separadas: 15
pruebas de auditoría (3 juegos x 5 estadísticos) y 21 de backtest (3 juegos x 7 estrategias, sin
contar la aleatoria, que es la referencia y no una hipótesis).

Se conservan las dos familias, porque son las que producen los `q` publicados en el CLAUDE.md, y
**se añade** la familia global de 36 pruebas bajo la clave `q_BH_global`. Para declarar ventaja
manda la global: es la que cumple la regla 3. La clave `q_BH` no se renombra porque el reporte del
oráculo depende de ella.
"""
import numpy as np

from .constantes import JUEGOS, MEDIA_AZAR

ESTADISTICOS = ("chi2_corr", "max_count", "min_count", "max_pair", "mean_overlap")

UMBRAL_Q = 0.05
SIN_VENTAJA = "sin ventaja demostrada"


def benjamini_hochberg(ps, m=None):
    """q-valores de BH. Traslado literal de baseline_auditoria.py:140-144 cuando `m` es None.

    `m` permite corregir contra una familia **declarada por adelantado** mayor que el número de
    p-valores que se le pasan. Es lo que necesita una evaluación preregistrada: el holdout corre 3
    pruebas (una por juego), pero el preregistro declaró pertenecer a una familia de 36, y usar
    m = 3 sería aflojar el criterio después de haberlo fijado.

    Con `m` explícito la corrección es más conservadora, nunca menos. No se puede usar al revés:
    m < len(ps) se rechaza, porque sería exactamente la manera de hacer trampa.
    """
    ps = np.asarray(ps, float)
    n = len(ps)
    if m is None:
        m = n
    if m < n:
        raise ValueError(f"familia declarada m={m} menor que las {n} pruebas corridas: no se afloja BH")
    orden = np.argsort(ps); q = np.empty(n); prev = 1.0
    for rank, i in list(enumerate(orden, 1))[::-1]:
        prev = min(prev, ps[i] * m / rank); q[i] = prev
    return q.tolist()


def claves_auditoria(auditoria):
    """Las 15 pruebas de la auditoría, en el orden del oráculo."""
    return [(j, k) for j in auditoria for k in ESTADISTICOS]


def claves_backtest(backtest):
    """Las 21 pruebas del backtest. La estrategia aleatoria es la referencia, no una hipótesis."""
    return [(j, s) for j, b in backtest.items() for s in b["estrategias"]
            if not s.startswith("Aleatorio")]


def aplicar_familias(auditoria, backtest):
    """Las dos familias del oráculo, bajo la clave `q_BH`. Modifica los dicts en sitio."""
    ca = claves_auditoria(auditoria)
    for (j, k), q in zip(ca, benjamini_hochberg([auditoria[j][k]["p_dos_colas"] for j, k in ca])):
        auditoria[j][k]["q_BH"] = round(q, 4)

    cb = claves_backtest(backtest)
    for (j, s), q in zip(cb, benjamini_hochberg([backtest[j]["estrategias"][s]["p"] for j, s in cb])):
        backtest[j]["estrategias"][s]["q_BH"] = round(q, 4)


def aplicar_global(auditoria, backtest):
    """La familia única de 36 pruebas que pide la regla 3, bajo `q_BH_global`.

    Devuelve un resumen con el tamaño de la familia y si alguna prueba sobrevive a q <= 0.05.
    """
    ca = claves_auditoria(auditoria)
    cb = claves_backtest(backtest)
    ps = ([auditoria[j][k]["p_dos_colas"] for j, k in ca]
          + [backtest[j]["estrategias"][s]["p"] for j, s in cb])
    qs = benjamini_hochberg(ps)

    for (j, k), q in zip(ca, qs[:len(ca)]):
        auditoria[j][k]["q_BH_global"] = round(q, 4)
    for (j, s), q in zip(cb, qs[len(ca):]):
        backtest[j]["estrategias"][s]["q_BH_global"] = round(q, 4)

    sobreviven = ([f"auditoria/{j}/{k}" for (j, k), q in zip(ca, qs[:len(ca)]) if q <= UMBRAL_Q]
                  + [f"backtest/{j}/{s}" for (j, s), q in zip(cb, qs[len(ca):]) if q <= UMBRAL_Q])
    return {
        "pruebas": len(ps),
        "pruebas_auditoria": len(ca),
        "pruebas_backtest": len(cb),
        "umbral": UMBRAL_Q,
        "q_minima": round(min(qs), 4),
        "sobreviven_a_q_0.05": sobreviven,
        "veredicto": SIN_VENTAJA if not sobreviven else "revisar: hay pruebas con q <= 0.05",
    }


# ---------------------------------------------------------------- las 5 condiciones de la regla 5
#
# "Declarar ventaja solo si se cumplen a la vez: holdout futuro positivo; q <= 0.05; estable al
#  mover hiperparámetros; mismo signo en Melate, Revancha y Revanchita; efecto >= mínimo
#  detectable (0.048 aciertos con 1,784 sorteos de prueba)."   -- CLAUDE.md, protocolo, regla 5
#
# Cada condición devuelve su propio veredicto y su motivo en texto. No se colapsan en un `and`
# opaco a propósito: cuando algo no pasa, lo útil es saber QUÉ no pasó, y cuando todo pasa, lo
# honesto es poder revisar cada paso por separado.


def _cond(nombre, cumple, motivo):
    return {"condicion": nombre, "cumple": bool(cumple), "motivo": motivo}


def condicion_holdout_positivo(res):
    """1 · Holdout futuro positivo. Un holdout vacío NO es un empate: es que no se ha jugado nada."""
    n = res.get("sorteos_holdout", 0)
    if not n:
        return _cond("holdout futuro positivo", False,
                     "holdout vacío: 0 sorteos posteriores al sello. Todavía no hay nada que evaluar")
    d = res.get("delta")
    if d is None:
        return _cond("holdout futuro positivo", False, f"{n} sorteos en el holdout, pero sin delta medido")
    return _cond("holdout futuro positivo", d > 0,
                 f"delta {d:+.4f} aciertos sobre el azar en {n} sorteos de holdout")


def condicion_q(res, umbral=UMBRAL_Q):
    """2 · q <= 0.05, y manda la q de la familia global de 36 pruebas, no la de familia."""
    q = res.get("q_BH_global")
    if q is None:
        return _cond(f"q <= {umbral}", False, "sin q de la familia global: no se puede juzgar")
    return _cond(f"q <= {umbral}", q <= umbral,
                 f"q_BH_global = {q:.4f} contra el umbral {umbral}")


def condicion_estabilidad(res, tolerancia=0.5):
    """3 · Estable al mover hiperparámetros.

    Exige que TODAS las variantes declaradas en el preregistro tengan el mismo signo que la base y
    que ninguna se desvíe más de `tolerancia` veces el efecto base. Si el preregistro no declaró
    variantes, no hay nada que comprobar y la condición no se da por buena.
    """
    var = res.get("variantes") or []
    if not var:
        return _cond("estable al mover hiperparámetros", False,
                     "el preregistro no declaró hiperparámetros alternativos: no hay estabilidad que medir")
    base = res.get("delta")
    if base is None or base == 0:
        return _cond("estable al mover hiperparámetros", False, "sin efecto base contra el que comparar")
    deltas = [v["delta"] for v in var if v.get("delta") is not None]
    if len(deltas) != len(var):
        return _cond("estable al mover hiperparámetros", False, "alguna variante no produjo delta")
    mismo_signo = all(np.sign(d) == np.sign(base) for d in deltas)
    desvio = max(abs(d - base) for d in deltas) / abs(base)
    ok = mismo_signo and desvio <= tolerancia
    return _cond("estable al mover hiperparámetros", ok,
                 f"{len(deltas)} variantes; mismo signo: {mismo_signo}; "
                 f"desvío máximo {desvio:.0%} del efecto base (tolerancia {tolerancia:.0%})")


def condicion_mismo_signo(por_juego):
    """4 · Mismo signo en Melate, Revancha y Revanchita.

    Es la condición más dura y la que más hallazgos falsos mata: un patrón real de la urna tendría
    que aparecer en los tres juegos, que comparten mecánica. Uno que solo sale en uno es ruido.
    """
    faltan = [j for j in JUEGOS if j not in por_juego or por_juego[j].get("delta") is None]
    if faltan:
        return _cond("mismo signo en los tres juegos", False,
                     f"sin delta para {', '.join(faltan)}: los tres hacen falta")
    signos = {j: int(np.sign(por_juego[j]["delta"])) for j in JUEGOS}
    ok = len(set(signos.values())) == 1 and 0 not in signos.values()
    detalle = ", ".join(f"{j} {por_juego[j]['delta']:+.4f}" for j in JUEGOS)
    return _cond("mismo signo en los tres juegos", ok, detalle)


def condicion_efecto_minimo(res, declarado=None):
    """5 · Efecto >= mínimo detectable.

    Si el efecto medido es menor que lo que el tamaño de muestra puede distinguir del azar, da igual
    que el signo sea favorable: no se está midiendo nada.

    El umbral es **el mayor** de dos cosas:

    * el mínimo detectable que permite el tamaño del holdout, y
    * el `efecto_minimo_declarado` del preregistro, si lo hay.

    Tomar solo el calculado abría un agujero concreto: con un holdout muy grande el mínimo
    detectable baja, y la condición pasaba con un efecto **mucho menor** que el que el documento
    sellado decía que haría falta. Se comprobó: delta 0.0100 contra un detectable de 0.0092 pasaba,
    con 0.048 declarado en el sello. Quien se compromete por adelantado a un umbral no puede
    beneficiarse después de que la muestra haya crecido.
    """
    calculado = res.get("efecto_minimo_detectable")
    d = res.get("delta")
    if d is None or (calculado is None and declarado is None):
        return _cond("efecto >= mínimo detectable", False, "falta el efecto o el mínimo detectable")
    umbral = max(x for x in (calculado, declarado) if x is not None)
    cual = "detectable" if umbral == calculado else "declarado en el sello"
    detalle = f"delta {d:+.4f} contra {umbral:.4f} ({cual}"
    if calculado is not None and declarado is not None:
        detalle += f"; detectable {calculado:.4f}, declarado {declarado:.4f}"
    return _cond("efecto >= mínimo detectable", d >= umbral, detalle + ")")


def declara_ventaja(resultados, por_juego=None, umbral=UMBRAL_Q, tolerancia=0.5,
                    efecto_minimo_declarado=None):
    """Las 5 condiciones de la regla 5, a la vez. Por defecto: sin ventaja demostrada.

    `resultados` es el resultado de la hipótesis preregistrada sobre su holdout.
    `por_juego` es el mismo resultado desglosado por juego, para la condición 4.

    Los tres últimos parámetros los pasa `lab.evaluar` **desde el preregistro**: el umbral de `q`,
    la tolerancia de estabilidad y el efecto mínimo declarado. Ninguno se decide aquí.

    Devuelve el veredicto **y** las cinco condiciones razonadas. Nunca lanza: si falta un dato, la
    condición correspondiente no se cumple y lo dice. Un sistema que se cae cuando le faltan datos
    invita a saltárselo.
    """
    por_juego = por_juego or {}
    condiciones = [
        condicion_holdout_positivo(resultados),
        condicion_q(resultados, umbral),
        condicion_estabilidad(resultados, tolerancia),
        condicion_mismo_signo(por_juego),
        condicion_efecto_minimo(resultados, efecto_minimo_declarado),
    ]
    incumplidas = [c for c in condiciones if not c["cumple"]]
    hay_ventaja = not incumplidas
    return {
        "veredicto": "VENTAJA DEMOSTRADA" if hay_ventaja else SIN_VENTAJA,
        "ventaja": hay_ventaja,
        "condiciones": condiciones,
        "cumplidas": len(condiciones) - len(incumplidas),
        "de": len(condiciones),
        "por_que_no": [c["motivo"] for c in incumplidas],
        "linea_base_azar": round(MEDIA_AZAR, 6),
    }
