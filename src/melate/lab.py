"""El laboratorio: preregistro sellado, holdout y veredicto.

La regla 4 del protocolo del `CLAUDE.md` dice: *"Preregistro en `prereg/*.json` con su hash antes de
evaluar; el holdout son los sorteos posteriores a la fecha del sello."*

Por qué hace falta todo este aparato, en una frase: con 56 números, decenas de estrategias y miles
de sorteos, **algo siempre destaca**. La Fase 1 lo vivió — el resultado más llamativo del proyecto
estaba en parte inflado por un error de datos de un tercero, y aun corregido seguía siendo la
estrategia que más invitaba a seguir tirando del hilo. Un preregistro sellado convierte esa
corazonada en una apuesta con fecha: se declara qué se va a mirar, cómo se va a juzgar y con qué
umbral, **antes** de que existan los datos que lo juzgarán.

Tres propiedades que este módulo garantiza, y que son el motivo de que exista:

1. **Sin preregistro no se evalúa.** `evaluar()` exige uno cargado y verificado.
2. **Un preregistro alterado no sirve.** Su hash cubre todo su contenido menos el propio hash.
   Cambiar un byte —un umbral, una estrategia, la fecha— lo invalida.
3. **El holdout no puede incluir el pasado.** Son los sorteos con `FECHA` posterior al sello. Hoy
   eso es el conjunto vacío, así que hoy es **imposible** declarar ventaja. Así debe ser.
"""
import argparse
import datetime
import hashlib
import json
import pathlib

import numpy as np
from scipy import stats

from . import protocolo
from .backtest import variables
from .constantes import JUEGOS, K, MEDIA_AZAR, N, SEMILLA_BACKTEST, VAR_AZAR
from .ingest import cargar, matriz, versiones
from .validate import era_56

CLAVE_HASH = "sello_sha256"


# ---------------------------------------------------------------- sellado y verificación
def _canonico(spec):
    """El JSON canónico sobre el que se calcula el hash: claves ordenadas, sin el propio hash."""
    limpio = {k: v for k, v in spec.items() if k != CLAVE_HASH}
    return json.dumps(limpio, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def hash_preregistro(spec):
    """SHA-256 del contenido del preregistro, excluyendo su propio campo de hash."""
    return hashlib.sha256(_canonico(spec)).hexdigest()


MARGEN_SELLO = datetime.timedelta(hours=1)


def sellar(spec, ruta, ahora=None):
    """Escribe el preregistro con su hash. No sobrescribe y no sella en el pasado.

    Las dos negativas son el preregistro. Si se puede reescribir un sello, o fecharlo antes de
    mirar los datos, no prueba nada: se convierte en un trámite que se rellena después, que es
    exactamente lo que la regla 4 del protocolo existe para impedir.

    `MARGEN_SELLO` de una hora absorbe desfases de reloj y zona horaria sin abrir la puerta a
    antedatar de verdad. Un preregistro con fecha pasada se puede construir a mano con
    `hash_preregistro` —los tests lo hacen para poder ejercitar el camino con holdout—, y esa
    asimetría es deliberada: cuesta trabajo y queda a la vista.
    """
    ruta = pathlib.Path(ruta)
    if ruta.exists():
        raise FileExistsError(
            f"{ruta} ya existe. Un preregistro sellado es inmutable: si la hipótesis cambia, "
            "se sella otro con otra fecha. Reescribir este destruiría la única garantía que da."
        )
    if "sello_utc" not in spec:
        raise ValueError("el borrador no lleva sello_utc")
    sello = datetime.datetime.fromisoformat(spec["sello_utc"])
    if sello.tzinfo is None:
        sello = sello.replace(tzinfo=datetime.timezone.utc)
    ahora = ahora or datetime.datetime.now(datetime.timezone.utc)
    if sello < ahora - MARGEN_SELLO:
        raise ValueError(
            f"sello_utc ({spec['sello_utc']}) está más de {MARGEN_SELLO} en el pasado.\n"
            "Un preregistro antedatado no preregistra nada: el holdout incluiría sorteos que ya "
            "se pueden mirar. Sella con la fecha de ahora, o con una futura."
        )
    spec = dict(spec)
    spec.pop(CLAVE_HASH, None)
    spec[CLAVE_HASH] = hash_preregistro(spec)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        json.dump(spec, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    return spec


def cargar_preregistro(ruta):
    """Carga y **verifica** un preregistro. Si el hash no cuadra, se niega a devolverlo.

    Se lee con `utf-8-sig` porque un editor de Windows puede dejar un BOM al guardar, y entonces
    `utf-8` falla con un error de JSON que no dice nada útil. El BOM no afecta al sello: el hash se
    calcula sobre el JSON canónico del contenido ya parseado, no sobre los bytes del fichero.
    """
    ruta = pathlib.Path(ruta)
    spec = json.loads(ruta.read_text(encoding="utf-8-sig"))
    guardado = spec.get(CLAVE_HASH)
    if not guardado:
        raise ValueError(f"{ruta.name} no lleva {CLAVE_HASH}: no es un preregistro sellado")
    calculado = hash_preregistro(spec)
    if guardado != calculado:
        raise ValueError(
            f"{ruta.name}: el sello NO cuadra.\n"
            f"  guardado:   {guardado}\n"
            f"  recalculado:{calculado}\n"
            "El fichero se ha modificado después de sellarlo, así que ya no prueba nada sobre lo "
            "que se iba a evaluar. No se usa."
        )
    for campo in ("id", "sello_utc", "juegos", "estrategias", "umbral_q"):
        if campo not in spec:
            raise ValueError(f"{ruta.name}: falta el campo obligatorio '{campo}'")
    return spec


# ---------------------------------------------------------------- holdout
def _sello(spec):
    return datetime.datetime.fromisoformat(spec["sello_utc"])


def holdout(spec, juegos):
    """Los sorteos posteriores al sello, por juego. Hoy: vacío, y eso es información, no un error.

    **La frontera excluye el día del sello, a propósito.** `FECHA` es una fecha sin hora, así que
    pandas la trata como medianoche: un sorteo celebrado el mismo día del sello nunca es `> sello`,
    sea cual sea la hora del sello. Es decir, el holdout empieza al día siguiente.

    Se deja así porque el error cae del lado seguro. Un sorteo del día del sello pudo celebrarse
    antes o después de sellar —no hay forma de saberlo con una fecha sin hora— y meterlo en el
    holdout significaría, en el peor caso, evaluar contra un sorteo que ya se podía mirar.
    Perder un sorteo no cuesta nada; contaminar el holdout lo cuesta todo.
    """
    corte = _sello(spec)
    corte_naive = corte.replace(tzinfo=None)
    out = {}
    for juego, df in juegos.items():
        posteriores = df[df.FECHA > corte_naive]
        out[juego] = {
            "sorteos": int(len(posteriores)),
            "primer_concurso": int(posteriores.CONCURSO.min()) if len(posteriores) else None,
            "ultimo_concurso": int(posteriores.CONCURSO.max()) if len(posteriores) else None,
            "indices": posteriores.index.tolist(),
        }
    return out


# ---------------------------------------------------------------- evaluación de lo declarado
def _predecir(estrategia, F, atraso, X, t, modelo, rng):
    """La elección de 6 números de una estrategia en el sorteo t. Solo con datos anteriores a t."""
    from .backtest import top6

    if estrategia == "Regresión logística" or estrategia == "Gradient boosting (HGB)":
        return top6(modelo.predict_proba(F[t])[:, 1], rng)
    if estrategia == "Calientes últimos 50":
        return top6(F[t, :, 2], rng)
    if estrategia == "Más frecuentes (todo el histórico)":
        return top6(F[t, :, 4], rng)
    if estrategia == "Fríos / atrasados":
        return top6(atraso[t], rng)
    if estrategia == "Repetir sorteo anterior":
        return np.where(X[t - 1] == 1)[0]
    raise ValueError(f"estrategia no soportada en el laboratorio: {estrategia!r}")


def _entrenar(estrategia, F, X, t, hiper):
    """Entrena con `range(100, t)`: estrictamente anterior a t. Sin fuga, igual que el backtest."""
    if estrategia == "Regresión logística":
        from sklearn.linear_model import LogisticRegression
        p = {"max_iter": 500}
        p.update(hiper or {})
        filas = list(range(100, t))
        return LogisticRegression(**p).fit(F[filas].reshape(-1, 7), X[filas].reshape(-1))
    if estrategia == "Gradient boosting (HGB)":
        from sklearn.ensemble import HistGradientBoostingClassifier
        p = {"max_iter": 150, "learning_rate": 0.05, "max_leaf_nodes": 15, "random_state": 0}
        p.update(hiper or {})
        filas = list(range(100, t))
        return HistGradientBoostingClassifier(**p).fit(F[filas].reshape(-1, 7), X[filas].reshape(-1))
    return None


def _evaluar_una(estrategia, df, indices, hiper, reentrenar_cada=100, semilla=SEMILLA_BACKTEST):
    """Aciertos por boleto de la estrategia en los sorteos `indices`. Devuelve None si están vacíos.

    `reentrenar_cada` y `semilla` los pasa `evaluar()` **desde el preregistro**. Tenían valor por
    defecto y nadie se los daba, así que un preregistro que declarara otro valor se ignoraba en
    silencio: el defecto coincidía con lo declarado y no se notaba. Ver el `Arreglos_Bugs/` de
    Protocolo_Estadistico.
    """
    if not indices:
        return None
    X = matriz(df["nums"].tolist())
    F, atraso = variables(X)
    rng = np.random.default_rng(semilla)
    modelo = None
    aciertos = []
    for k, t in enumerate(sorted(indices)):
        if k % reentrenar_cada == 0:
            modelo = _entrenar(estrategia, F, X, t, hiper)
        elec = _predecir(estrategia, F, atraso, X, t, modelo, rng)
        aciertos.append(int(X[t][elec].sum()))
    h = np.array(aciertos, dtype=float)
    n = len(h)
    se = float(np.sqrt(VAR_AZAR / n))
    media = float(h.mean())
    z = (media - MEDIA_AZAR) / se
    return {
        "sorteos_holdout": n,
        "media": round(media, 6),
        "delta": round(media - MEDIA_AZAR, 6),
        "z": round(z, 4),
        "p": round(float(2 * stats.norm.sf(abs(z))), 6),
        "efecto_minimo_detectable": round((1.959964 + 0.841621) * se, 6),
    }


def evaluar(spec, juegos=None, carpeta=None):
    """Corre **solo** lo que el preregistro declara, sobre **solo** su holdout.

    `spec` tiene que venir de `cargar_preregistro`: sin preregistro verificado no se evalúa.
    """
    if not isinstance(spec, dict) or CLAVE_HASH not in spec:
        raise ValueError("evaluar() exige un preregistro verificado (usa cargar_preregistro)")
    if juegos is None:
        juegos = {j: era_56(j, cargar(j, carpeta)) for j in JUEGOS}

    hold = holdout(spec, juegos)
    principal = spec.get("juego_principal") or spec["juegos"][0]
    estrategia = spec["estrategias"][0]
    variantes_declaradas = spec.get("hiperparametros_alternativos") or []

    # TODO lo que gobierna la corrida sale del preregistro, no de valores por defecto del código.
    # Antes `reentrenar_cada` y la semilla eran defectos de `_evaluar_una` que nadie sobrescribía:
    # el preregistro los declaraba y se ignoraban en silencio porque el defecto coincidía.
    cada = int(spec.get("reentrenar_cada") or 100)
    semilla = int((spec.get("semillas") or {}).get("backtest", SEMILLA_BACKTEST))
    hiper = spec.get("hiperparametros")

    por_juego = {}
    for juego in JUEGOS:
        if juego not in juegos:
            continue
        r = _evaluar_una(estrategia, juegos[juego], hold[juego]["indices"], hiper,
                         reentrenar_cada=cada, semilla=semilla)
        por_juego[juego] = r or {"sorteos_holdout": 0, "delta": None}

    base = por_juego.get(principal) or {"sorteos_holdout": 0, "delta": None}
    resultados = dict(base)
    resultados["variantes"] = [
        dict({"hiperparametros": h},
             **(_evaluar_una(estrategia, juegos[principal], hold[principal]["indices"], h,
                             reentrenar_cada=cada, semilla=semilla) or {"delta": None}))
        for h in variantes_declaradas
    ]
    resultados["reentrenar_cada"] = cada
    resultados["semilla"] = semilla

    # Benjamini-Hochberg sobre las pruebas del holdout, corrigiendo contra la familia que el
    # preregistro DECLARO, no contra las 3 que se acaban de correr. Usar m = 3 seria aflojar el
    # criterio despues de haberlo fijado, que es justo lo que el preregistro impide.
    # Las variantes de hiperparametros NO son pruebas: son comprobaciones de robustez de la misma
    # hipotesis, y contarlas inflaria la familia sin anadir ninguna hipotesis nueva.
    m = spec.get("tamano_familia")
    con_p = [(j, por_juego[j]) for j in JUEGOS if por_juego.get(j, {}).get("p") is not None]
    if con_p and m:
        qs = protocolo.benjamini_hochberg([r["p"] for _, r in con_p], m=m)
        for (j, _), q in zip(con_p, qs):
            por_juego[j]["q_BH_global"] = round(q, 6)
        resultados["q_BH_global"] = por_juego[principal].get("q_BH_global")
    else:
        resultados["q_BH_global"] = None
    resultados["familia_declarada"] = m
    resultados["pruebas_corridas"] = len(con_p)

    veredicto = protocolo.declara_ventaja(
        resultados, por_juego,
        umbral=spec.get("umbral_q", protocolo.UMBRAL_Q),
        tolerancia=spec.get("tolerancia_estabilidad", 0.5),
        efecto_minimo_declarado=spec.get("efecto_minimo_declarado"),
    )
    return {
        "preregistro": {"id": spec["id"], "sello_utc": spec["sello_utc"],
                        CLAVE_HASH: spec[CLAVE_HASH], "estrategia": estrategia,
                        "juego_principal": principal},
        "holdout": {j: {k: v for k, v in d.items() if k != "indices"} for j, d in hold.items()},
        "resultados": resultados,
        "por_juego": por_juego,
        "veredicto": veredicto,
        "corrida_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "versiones": versiones(),
    }


# ---------------------------------------------------------------- CLI
def _imprimir(r):
    v = r["veredicto"]
    p = r["preregistro"]
    print(f"== Preregistro {p['id']}")
    print(f"   sellado   {p['sello_utc']}")
    print(f"   sello     {p[CLAVE_HASH][:16]}... (verificado)")
    print(f"   hipotesis {p['estrategia']} en {p['juego_principal']}")
    print("== Holdout (sorteos posteriores al sello)")
    for juego, h in r["holdout"].items():
        rango = f"{h['primer_concurso']}-{h['ultimo_concurso']}" if h["sorteos"] else "-"
        print(f"   {juego:11s} {h['sorteos']:4d} sorteos  {rango}")
    print(f"== Veredicto: {v['veredicto']}  ({v['cumplidas']} de {v['de']} condiciones)")
    for c in v["condiciones"]:
        marca = "si" if c["cumple"] else "NO"
        print(f"   [{marca}] {c['condicion']:34s} {c['motivo']}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Evalua una hipotesis preregistrada. Sin preregistro no evalua.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--prereg", help="ruta de un prereg/*.json sellado, para evaluarlo")
    g.add_argument("--sellar", metavar="BORRADOR",
                   help="sella un borrador JSON (sin hash) y lo escribe en --salida. No sobrescribe")
    ap.add_argument("--datos", help="carpeta con los CSV (si no, descarga del oficial)")
    ap.add_argument("--salida", help="donde escribir el veredicto, o el preregistro al sellar")
    a = ap.parse_args(argv)

    if a.sellar:
        if not a.salida:
            ap.error("--sellar necesita --salida")
        borrador = json.loads(pathlib.Path(a.sellar).read_text(encoding="utf-8"))
        spec = sellar(borrador, a.salida)
        print(f"Sellado {spec['id']}")
        print(f"  sello_utc  {spec['sello_utc']}")
        print(f"  {CLAVE_HASH}  {spec[CLAVE_HASH]}")
        print(f"  escrito en {a.salida}")
        print("\nA partir de aqui es inmutable: cambiar un byte lo invalida.")
        return spec

    spec = cargar_preregistro(a.prereg)
    r = evaluar(spec, carpeta=a.datos)
    _imprimir(r)
    if a.salida:
        salida = pathlib.Path(a.salida)
        salida.parent.mkdir(parents=True, exist_ok=True)
        with open(salida, "w", encoding="utf-8") as f:
            json.dump(r, f, ensure_ascii=False, indent=1, default=str)
        print(f"\nVeredicto completo en {salida}")
    return r


if __name__ == "__main__":
    main()
