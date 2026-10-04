"""La base local de la app: `melate.duckdb`. `python -m melate.almacen` la construye.

Es un **índice** de lo que ya está publicado en `reportes/*.json` y `prereg/*.json`, no una fuente.
La decisión —qué entra, qué la genera y por qué no se publica— se escribió antes que este fichero:
`Documentos_Contexto/Almacenamiento/Decisiones/2026-10-04_00-40_s4-que-entra-en-melate-duckdb.md`.

Tres reglas, cada una con su test:

1. **Ningún número que no esté en un fichero publicado.** Se copia y se reordena; no se calcula
   ningún estadístico. Lo único que se calcula son comprobaciones de integridad: el SHA-256 de cada
   fichero, el sello de cada preregistro (con la función del propio laboratorio) y el enlace de cada
   veredicto con el suyo.
2. **Un veredicto solo vale si su sello es el de un preregistro que verifica**, y si es coherente
   consigo mismo. Si no, entra marcado como no válido y con su motivo: se ve que está y por qué no
   cuenta.
3. **Lo que explora no se llama veredicto.** El resumen de `protocolo_global` del informe entra como
   `resumen_exploratorio`. Una columna `veredicto` solo existe en la tabla de lo que juzga.

La lectura (`leer`, `frescura`, `veredicto_vigente`) no importa nada del cómputo ni de la red: la
app la usa, y la app no recalcula ni descarga. El laboratorio se importa solo al construir.
"""
import argparse
import datetime
import hashlib
import json
import os
import pathlib
import time

from .constantes import JUEGOS
from .protocolo import SIN_VENTAJA

VERSION_ESQUEMA = 1
SALIDA = "melate.duckdb"

# El texto afirmativo de `protocolo.declara_ventaja`. No se importa porque allí va escrito en línea;
# `tests/test_almacen.py` comprueba que los dos siguen siendo idénticos.
VENTAJA = "VENTAJA DEMOSTRADA"

# ---------------------------------------------------------------- el esquema
#
# Cada tabla declara su naturaleza —juzga, explora, mide o procedencia— y a qué mira: la urna, el
# dinero, los jugadores o los datos. Son las dos fronteras del proyecto (Mapa/Modificar/, fases 2
# y 3) escritas en los datos, para que la app no tenga que adivinarlas.

CATALOGO = [
    ("construccion", "procedencia", "datos", "Cuándo, con qué versión y desde qué carpetas se construyó esta base"),
    ("fuentes", "procedencia", "datos", "Cada fichero leído: ruta relativa, tipo, SHA-256 y si vale"),
    ("datos_informe", "procedencia", "datos", "Sobre qué datos se corrió cada informe: hash, origen y último sorteo"),
    ("catalogo", "procedencia", "datos", "Esta tabla: qué es cada tabla y si juzga, explora o mide"),
    ("preregistros", "juzga", "urna", "Las hipótesis selladas, y si su sello verifica"),
    ("veredictos", "juzga", "urna", "Las salidas de melate.lab, enlazadas con su preregistro"),
    ("condiciones", "juzga", "urna", "Las cinco condiciones de cada veredicto, con su motivo"),
    ("informes", "explora", "urna", "Cada salida de melate.informe o del oráculo, y su resumen exploratorio"),
    ("auditoria", "explora", "urna", "Los estadísticos de la urna por juego, con su p y sus q"),
    ("backtest", "explora", "urna", "Las estrategias por juego con su p y sus q, y el log-loss donde lo hay"),
    ("exploracion_juego", "explora", "urna", "Por juego: tramo de prueba, mínimo detectable y poder de la auditoría"),
    ("valor_esperado", "mide", "dinero", "El EV del sorteo siguiente al último del informe: con la constante del oráculo y con los menores medidos"),
    ("premios_mayores", "mide", "dinero", "Premios mayores detectados por bajas de BOLSA"),
    ("popularidad", "mide", "jugadores", "Cada ventana de melate.popularity: ventas, premios menores y efecto calendario"),
    ("carteras", "mide", "jugadores", "Cada cartera de melate.portfolio, con su valoración y su aviso"),
    ("cartera_boletos", "mide", "jugadores", "Los boletos de cada cartera"),
]

_T, _I, _B, _F, _L = "VARCHAR", "INTEGER", "BOOLEAN", "DOUBLE", "BIGINT"

ESQUEMA = {
    "construccion": [("version_esquema", _I), ("construido_utc", _T), ("melate", _T), ("duckdb", _T),
                     ("dir_reportes", _T), ("dir_prereg", _T), ("ficheros", _I)],
    "fuentes": [("ruta", _T), ("tipo", _T), ("sha256", _T), ("bytes", _L), ("fecha_utc", _T),
                ("valido", _B), ("motivo", _T)],
    "datos_informe": [("ruta", _T), ("juego", _T), ("vista", _T), ("sha256", _T), ("origen", _T),
                      ("bytes", _L), ("filas", _I), ("primero", _I), ("ultimo", _I),
                      ("ultima_fecha", _T), ("concursos_faltantes", _I), ("duplicados", _I),
                      ("fuera_de_rango", _I), ("bolsa_invalida", _T)],
    "catalogo": [("tabla", _T), ("naturaleza", _T), ("mira_a", _T), ("que_es", _T)],
    "preregistros": [("ruta", _T), ("id", _T), ("titulo", _T), ("hipotesis", _T),
                     ("juego_principal", _T), ("estrategia", _T), ("sello_utc", _T),
                     ("sello_sha256", _T), ("verificado", _B), ("motivo", _T), ("umbral_q", _F),
                     ("tamano_familia", _I), ("efecto_minimo_declarado", _F),
                     ("tolerancia_estabilidad", _F), ("reentrenar_cada", _I), ("semilla", _L),
                     ("variantes", _I), ("snapshot_al_sellar", _T), ("ultimo_concurso_al_sellar", _I),
                     ("notas", _T)],
    "veredictos": [("ruta", _T), ("prereg_id", _T), ("sello_sha256", _T), ("corrida_utc", _T),
                   ("veredicto", _T), ("ventaja", _B), ("cumplidas", _I), ("de", _I),
                   ("valido", _B), ("motivo", _T), ("estrategia", _T), ("juego_principal", _T),
                   ("sorteos_holdout", _I), ("delta", _F), ("q_bh_global", _F),
                   ("familia_declarada", _I), ("linea_base_azar", _F),
                   ("holdout_melate", _I), ("holdout_revancha", _I), ("holdout_revanchita", _I),
                   ("delta_melate", _F), ("delta_revancha", _F), ("delta_revanchita", _F),
                   ("datos_registrados", _B), ("ultimo_concurso_datos", _I),
                   ("ultimo_concurso_datos_min", _I),
                   ("ultima_fecha_datos", _T), ("sha256_melate", _T), ("sha256_revancha", _T),
                   ("sha256_revanchita", _T), ("origen_datos", _T)],
    "condiciones": [("ruta", _T), ("orden", _I), ("condicion", _T), ("cumple", _B), ("motivo", _T)],
    "informes": [("ruta", _T), ("tipo", _T), ("corrida_utc", _T), ("simulaciones", _I),
                 ("semilla_auditoria", _L), ("semilla_backtest", _L), ("semilla_hgb", _L),
                 ("pruebas", _I), ("pruebas_auditoria", _I), ("pruebas_backtest", _I),
                 ("umbral", _F), ("q_minima", _F), ("pruebas_bajo_umbral", _I),
                 ("bajo_umbral", _T), ("resumen_exploratorio", _T),
                 ("ev_medido_disponible", _B), ("ev_medido_motivo", _T), ("python", _T),
                 ("numpy", _T), ("pandas", _T), ("scipy", _T), ("scikit_learn", _T)],
    "auditoria": [("ruta", _T), ("juego", _T), ("estadistico", _T), ("obs", _F), ("media_sim", _F),
                  ("p", _F), ("q_familia", _F), ("q_global", _F)],
    "backtest": [("ruta", _T), ("juego", _T), ("orden", _I), ("estrategia", _T),
                 ("es_referencia", _B), ("media", _F), ("delta", _F), ("z", _F), ("p", _F),
                 ("q_familia", _F), ("q_global", _F), ("aciertos_3_o_mas", _I),
                 ("esperados_3_o_mas", _F), ("logloss_delta", _F), ("logloss_t", _F),
                 ("logloss_p", _F)],
    "exploracion_juego": [("ruta", _T), ("juego", _T), ("sorteos", _I),
                          ("sesgo_detectable_1_esfera", _F), ("sesgo_detectable_56_esferas", _F),
                          ("sorteos_prueba", _I), ("primer_concurso_prueba", _I),
                          ("media_azar", _F), ("efecto_minimo_detectable", _F),
                          ("logloss_azar", _F)],
    "valor_esperado": [("ruta", _T), ("variante", _T), ("juego", _T), ("proximo_sorteo", _I),
                       ("bolsa_bruta", _F), ("ev", _F), ("precio", _F), ("rendimiento", _F),
                       ("bolsa_de_equilibrio", _F), ("menores_brutos", _F),
                       ("procedencia_menores", _T), ("ventana_desde", _I), ("ventana_hasta", _I),
                       ("lambda", _F), ("s", _F), ("impuesto", _F)],
    "premios_mayores": [("ruta", _T), ("juego", _T), ("ganados", _I), ("sorteos", _I),
                        ("errores_de_bolsa", _I)],
    "popularidad": [("ruta", _T), ("juego", _T), ("ventana_desde", _I), ("ventana_hasta", _I),
                    ("sorteos_pedidos", _I), ("sorteos_usados", _I), ("fallos", _I),
                    ("sorteos_sin_premios", _I),
                    ("ventas_n", _I), ("ventas_mediana", _F), ("ventas_min", _F),
                    ("ventas_max", _F), ("ventas_cv", _F), ("menores_bolsa_n", _I),
                    ("menores_bolsa_mediana", _F), ("menores_bolsa_media", _F),
                    ("menores_bolsa_cv", _F), ("menores_bolsa_min", _F), ("menores_bolsa_max", _F),
                    ("menores_directo_mediana", _F), ("menores_directo_cv", _F),
                    ("calendario_corte", _I), ("calendario_cociente", _F), ("calendario_t", _F),
                    ("calendario_n_dentro", _I), ("calendario_n_fuera", _I),
                    ("descargado_utc", _T), ("peticiones_de_red", _I)],
    "carteras": [("ruta", _T), ("juego", _T), ("presupuesto", _F), ("precio_boleto", _F),
                 ("boletos", _I), ("coste", _F), ("sobrante", _F), ("numeros_cubiertos", _I),
                 ("tope_popularidad", _F), ("candidatas_aptas", _I), ("candidatas_descartadas", _I),
                 ("solape_maximo_real", _I), ("solape_medio", _F), ("popularidad_media", _F),
                 ("semilla", _L), ("ventas_supuestas", _F), ("valorada", _B),
                 ("bolsa", _F), ("menores_brutos", _F), ("impuesto", _F),
                 ("valor_esperado", _F), ("rendimiento", _F),
                 ("valor_esperado_sin_mirar_popularidad", _F),
                 ("ganancia_por_evitar_compartir", _F), ("ganancia_como_porcentaje_del_precio", _F),
                 ("aviso", _T)],
    "cartera_boletos": [("ruta", _T), ("orden", _I), ("numeros", _T), ("popularidad", _F),
                        ("patrones", _T), ("factor_reparto", _F), ("acertantes_esperados", _F)],
}


# ---------------------------------------------------------------- utilidades
def _sha256(ruta):
    return hashlib.sha256(pathlib.Path(ruta).read_bytes()).hexdigest()


def _relativa(ruta, base):
    """Ruta relativa a `base`, con barras normales. Nunca absoluta: esta base no se publica, pero
    la regla del proyecto es no escribir jamás una ruta de la máquina (REGLAS-DOCUMENTACION.md §0).
    Lo que quede fuera de `base` se guarda solo por su nombre."""
    try:
        return pathlib.Path(ruta).resolve().relative_to(base).as_posix()
    except ValueError:
        return pathlib.Path(ruta).name


def _num(x):
    return None if x is None else float(x)


def _ent(x):
    return None if x is None else int(x)


def _juego(d, juego):
    return (d or {}).get(juego) or {}


# ---------------------------------------------------------------- qué es cada fichero
def clasificar(doc):
    """El tipo de un reporte por su forma. Lo que no se reconoce es `desconocido`, no un error."""
    if not isinstance(doc, dict):
        return "desconocido"
    claves = set(doc)
    if {"preregistro", "holdout", "veredicto"} <= claves:
        return "veredicto"
    if {"auditoria", "backtest", "valor_esperado_proximo"} <= claves:
        return "informe" if "reproducibilidad" in claves else "informe_oraculo"
    if {"ventana", "juegos", "procedencia"} <= claves:
        return "popularidad"
    if {"juego", "presupuesto", "detalle"} <= claves:
        return "cartera"
    if {"sello_sha256", "sello_utc", "estrategias"} <= claves:
        return "preregistro"
    return "desconocido"


# ---------------------------------------------------------------- de cada reporte, sus filas
def _filas_informe(ruta, doc, tipo, filas):
    rep = doc.get("reproducibilidad") or {}
    sem = rep.get("semillas") or {}
    ver = rep.get("versiones") or {}
    pg = doc.get("protocolo_global") or {}
    bajo = pg.get("sobreviven_a_q_0.05")
    vm = doc.get("valor_esperado_medido") or {}
    filas["informes"].append((
        ruta, tipo, rep.get("corrida_utc"), _ent(rep.get("simulaciones")),
        _ent(sem.get("auditoria")), _ent(sem.get("backtest")), _ent(sem.get("hgb")),
        _ent(pg.get("pruebas")), _ent(pg.get("pruebas_auditoria")), _ent(pg.get("pruebas_backtest")),
        _num(pg.get("umbral")), _num(pg.get("q_minima")),
        None if bajo is None else len(bajo), None if bajo is None else ", ".join(bajo),
        pg.get("veredicto"),
        bool(vm.get("disponible")) if vm else None, vm.get("motivo"),
        ver.get("python"), ver.get("numpy"), ver.get("pandas"), ver.get("scipy"),
        ver.get("scikit-learn"),
    ))

    vista = "era_56" if "validacion_era_56" in doc else "cruda"
    val = doc.get("validacion_era_56") or doc.get("validacion") or {}
    datos = rep.get("datos") or {}
    for juego in JUEGOS:
        v, d = _juego(val, juego), _juego(datos, juego)
        if not v and not d:
            continue
        filas["datos_informe"].append((
            ruta, juego, vista, d.get("sha256"), d.get("origen") or v.get("fuente"),
            _ent(d.get("bytes")), _ent(v.get("filas")), _ent(v.get("primero")),
            _ent(v.get("ultimo")), v.get("ultima_fecha"),
            None if v.get("concursos_faltantes") is None else len(v["concursos_faltantes"]),
            _ent(v.get("duplicados")), _ent(v.get("fuera_de_rango")),
            None if v.get("bolsa_cero_o_invalida") is None
            else ", ".join(str(c) for c in v["bolsa_cero_o_invalida"]),
        ))

    for juego, a in (doc.get("auditoria") or {}).items():
        for est, r in a.items():
            if isinstance(r, dict) and "p_dos_colas" in r:
                filas["auditoria"].append((ruta, juego, est, _num(r.get("obs")),
                                           _num(r.get("media_sim")), _num(r.get("p_dos_colas")),
                                           _num(r.get("q_BH")), _num(r.get("q_BH_global"))))

    poder = doc.get("poder") or {}
    for juego, b in (doc.get("backtest") or {}).items():
        ll = b.get("logloss") or {}
        pw = _juego(poder, juego)
        filas["exploracion_juego"].append((
            ruta, juego, _ent(pw.get("sorteos")), _num(pw.get("sesgo_detectable_1_esfera")),
            _num(pw.get("sesgo_detectable_56_esferas")), _ent(b.get("sorteos_prueba")),
            _ent(b.get("primer_concurso_prueba")), _num(b.get("media_azar")),
            _num(b.get("efecto_minimo_detectable")), _num(ll.get("azar")),
        ))
        for orden, (est, r) in enumerate((b.get("estrategias") or {}).items()):
            lr = ll.get(est) if isinstance(ll.get(est), dict) else {}
            filas["backtest"].append((
                ruta, juego, orden, est, est.startswith("Aleatorio"), _num(r.get("media")),
                _num(r.get("delta")), _num(r.get("z")), _num(r.get("p")), _num(r.get("q_BH")),
                _num(r.get("q_BH_global")), _ent(r.get("3_o_mas")), _num(r.get("3_o_mas_esperados")),
                _num(lr.get("delta_vs_azar")), _num(lr.get("t")), _num(lr.get("p")),
            ))

    for juego, pm in (doc.get("premios_mayores") or {}).items():
        filas["premios_mayores"].append((ruta, juego, _ent(pm.get("ganados")), _ent(pm.get("sorteos")),
                                         len(pm.get("errores_de_bolsa") or [])))

    variantes = [("constante_del_oraculo", doc.get("valor_esperado_proximo") or {})]
    if vm.get("disponible"):
        variantes.append(("menores_medidos", vm))
    for variante, ev in variantes:
        sup = ev.get("supuestos") or {}
        ventana = ev.get("ventana") or [None, None]
        for juego in JUEGOS:
            e = _juego(ev, juego)
            if not e:
                continue
            filas["valor_esperado"].append((
                ruta, variante, juego, _ent(e.get("proximo_sorteo")), _num(e.get("bolsa_bruta")),
                _num(e.get("EV")), _num(e.get("precio")), _num(e.get("rendimiento")),
                _num(e.get("bolsa_de_equilibrio")),
                _num((ev.get("menores_brutos_usados") or {}).get(juego)),
                (ev.get("procedencia_menores") or {}).get(juego),
                _ent(ventana[0]), _ent(ventana[1]),
                _num(sup.get("lambda")), _num(sup.get("S")), _num(sup.get("impuesto")),
            ))


def _utc(iso):
    """Una fecha ISO del reporte, normalizada a UTC y a segundos, o None si no es una fecha.

    Se ordena por estas cadenas: sin normalizar, '…Z' y '…+00:00' no compararían bien como texto.
    """
    try:
        d = datetime.datetime.fromisoformat(str(iso))
    except (TypeError, ValueError):
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=datetime.timezone.utc)
    return d.astimezone(datetime.timezone.utc).isoformat(timespec="seconds")


def _filas_veredicto(ruta, doc, prereg_por_sello, filas):
    pre = doc.get("preregistro") or {}
    res = doc.get("resultados") or {}
    ver = doc.get("veredicto") or {}
    hold = doc.get("holdout") or {}
    por_juego = doc.get("por_juego") or {}
    datos = doc.get("datos") or {}
    valido, motivo = _validar_veredicto(doc, prereg_por_sello)
    ultimos = [d.get("ultimo_concurso") for d in datos.values() if d.get("ultimo_concurso")]
    fechas = [d.get("ultima_fecha") for d in datos.values() if d.get("ultima_fecha")]
    origenes = sorted({str(d.get("origen")) for d in datos.values() if d.get("origen")})
    filas["veredictos"].append((
        ruta, pre.get("id"), pre.get("sello_sha256"), _utc(doc.get("corrida_utc")),
        ver.get("veredicto"), bool(ver.get("ventaja")), _ent(ver.get("cumplidas")),
        _ent(ver.get("de")), valido, motivo, pre.get("estrategia"), pre.get("juego_principal"),
        _ent(res.get("sorteos_holdout")), _num(res.get("delta")), _num(res.get("q_BH_global")),
        _ent(res.get("familia_declarada")), _num(ver.get("linea_base_azar")),
        *(_ent(_juego(hold, j).get("sorteos")) for j in JUEGOS),
        *(_num(_juego(por_juego, j).get("delta")) for j in JUEGOS),
        bool(datos), _ent(max(ultimos)) if ultimos else None,
        _ent(min(ultimos)) if ultimos else None, max(fechas) if fechas else None,
        *(_juego(datos, j).get("sha256") for j in JUEGOS),
        " · ".join(origenes) or None,
    ))
    for orden, c in enumerate(ver.get("condiciones") or [], 1):
        filas["condiciones"].append((ruta, orden, c.get("condicion"), bool(c.get("cumple")),
                                     c.get("motivo")))
    return valido, motivo


def _validar_veredicto(doc, prereg_por_sello):
    """¿Cuenta este veredicto? Solo si apunta a un preregistro que verifica y es coherente.

    Lo que esto NO puede comprobar, y se dice: que el veredicto lo produjera de verdad el
    laboratorio. Eso exigiría recalcularlo, y para eso está `python -m melate.lab`. Lo que sí
    comprueba es lo que se puede comprobar sin cómputo: el enlace con un sello válido, que tenga
    fecha de corrida, y que el texto, la marca de ventaja y las cinco condiciones digan lo mismo.
    """
    if _utc(doc.get("corrida_utc")) is None:
        return False, "sin fecha de corrida: no se puede saber cuándo se emitió"
    pre = doc.get("preregistro") or {}
    p = prereg_por_sello.get(pre.get("sello_sha256"))
    if p is None:
        return False, "su sello no es el de ningún preregistro de la carpeta leída"
    if not p["verificado"]:
        return False, f"su preregistro ({p['ruta']}) no verifica: {p['motivo']}"
    if pre.get("id") != p["id"]:
        return False, "su id no es el del preregistro con ese sello"
    ver = doc.get("veredicto") or {}
    conds = ver.get("condiciones") or []
    if len(conds) != 5:
        return False, f"trae {len(conds)} condiciones; la regla 5 del protocolo tiene 5"
    cumplen = sum(1 for c in conds if c.get("cumple") is True)
    todas = cumplen == 5
    if ver.get("ventaja") is not todas:
        return False, "incoherente: la marca de ventaja no corresponde a sus condiciones"
    if ver.get("veredicto") != (VENTAJA if todas else SIN_VENTAJA):
        return False, "incoherente: el texto del veredicto no corresponde a sus condiciones"
    if ver.get("cumplidas") != cumplen:
        return False, "incoherente: 'cumplidas' no cuenta las condiciones que cumple"
    return True, None


def _filas_preregistro(ruta, ruta_disco, doc, filas):
    """Verifica con `lab.cargar_preregistro`, que es la definición de 'verifica' del laboratorio."""
    from .lab import cargar_preregistro

    try:
        cargar_preregistro(ruta_disco)
        verificado, motivo = True, None
    except (ValueError, json.JSONDecodeError) as e:
        verificado, motivo = False, str(e).splitlines()[0]
    d = doc if isinstance(doc, dict) else {}
    sem = d.get("semillas") or {}
    al_sellar = d.get("datos_al_sellar") or {}
    fila = {"ruta": ruta, "id": d.get("id"), "sello_sha256": d.get("sello_sha256"),
            "verificado": verificado, "motivo": motivo}
    filas["preregistros"].append((
        ruta, d.get("id"), d.get("titulo"), d.get("hipotesis"), d.get("juego_principal"),
        (d.get("estrategias") or [None])[0], d.get("sello_utc"), d.get("sello_sha256"),
        verificado, motivo, _num(d.get("umbral_q")), _ent(d.get("tamano_familia")),
        _num(d.get("efecto_minimo_declarado")), _num(d.get("tolerancia_estabilidad")),
        _ent(d.get("reentrenar_cada")), _ent(sem.get("backtest")),
        len(d.get("hiperparametros_alternativos") or []), al_sellar.get("snapshot"),
        _ent(al_sellar.get("ultimo_concurso")), d.get("notas"),
    ))
    return fila


def _filas_popularidad(ruta, doc, filas):
    for juego, r in (doc.get("juegos") or {}).items():
        v = r.get("ventas") or {}
        mb = r.get("menores_brutos_por_bolsa") or {}
        md = r.get("menores_brutos_directo") or {}
        ec = r.get("efecto_calendario") or {}
        ventana = r.get("ventana") or doc.get("ventana") or [None, None]
        # Los reportes anteriores a la Fase 4 no miraban si había premios: ahí no es 0, es "no se sabe".
        sin_premios = r.get("sorteos_sin_premios")
        filas["popularidad"].append((
            ruta, juego, _ent(ventana[0]), _ent(ventana[1]), _ent(r.get("sorteos_pedidos")),
            _ent(r.get("sorteos_usados")), len(r.get("fallos") or []),
            None if sin_premios is None else len(sin_premios),
            _ent(v.get("n")), _num(v.get("mediana")), _num(v.get("min")), _num(v.get("max")),
            _num(v.get("cv")), _ent(mb.get("n")), _num(mb.get("mediana")), _num(mb.get("media")),
            _num(mb.get("cv")), _num(mb.get("min")), _num(mb.get("max")),
            _num(md.get("mediana")), _num(md.get("cv")),
            _ent(ec.get("corte")), _num(ec.get("cociente_fuera_entre_dentro")),
            _num(ec.get("t_welch")), _ent(_juego(ec, "dentro_del_calendario").get("n")),
            _ent(_juego(ec, "fuera_del_calendario").get("n")),
            (doc.get("procedencia") or {}).get("descargado_utc"),
            _ent((doc.get("procedencia") or {}).get("peticiones_de_red")),
        ))


def _filas_cartera(ruta, doc, filas):
    val = doc.get("valoracion") or {}
    filas["carteras"].append((
        ruta, doc.get("juego"), _num(doc.get("presupuesto")), _num(doc.get("precio_boleto")),
        _ent(doc.get("boletos")), _num(doc.get("coste")), _num(doc.get("sobrante")),
        _ent(doc.get("numeros_cubiertos")), _num(doc.get("tope_popularidad")),
        _ent(doc.get("candidatas_aptas")), _ent(doc.get("candidatas_descartadas")),
        _ent(doc.get("solape_maximo_real")), _num(doc.get("solape_medio")),
        _num(doc.get("popularidad_media")), _ent(doc.get("semilla")),
        _num(doc.get("ventas_supuestas")), bool(val), _num(val.get("bolsa")),
        _num(val.get("menores_brutos")), _num(val.get("impuesto")), _num(val.get("valor_esperado")),
        _num(val.get("rendimiento")), _num(val.get("valor_esperado_sin_mirar_popularidad")),
        _num(val.get("ganancia_por_evitar_compartir")),
        _num(val.get("ganancia_como_porcentaje_del_precio")), val.get("aviso"),
    ))
    for orden, b in enumerate(doc.get("detalle") or [], 1):
        filas["cartera_boletos"].append((
            ruta, orden, " - ".join(f"{n:02d}" for n in b.get("numeros") or []),
            _num(b.get("popularidad")), ", ".join(b.get("patrones") or []),
            _num(b.get("factor_reparto")), _num(b.get("acertantes_esperados")),
        ))


# ---------------------------------------------------------------- construir
def construir(reportes="reportes", prereg="prereg", salida=SALIDA, ahora=None):
    """Lee `reportes/*.json` y `prereg/*.json` y escribe la base. Devuelve un resumen.

    Las rutas que guarda son relativas a la carpeta de `salida`: la base indexa el árbol en el que
    vive, y la app comprueba su frescura contra ese mismo árbol.
    """
    import duckdb

    from . import __version__

    salida = pathlib.Path(salida)
    reportes, prereg = pathlib.Path(reportes), pathlib.Path(prereg)
    # Lo primero, antes de escribir nada: lanzada desde otra carpeta, la orden construiría una base
    # vacía en silencio. Es la lección de `informe.cargar_popularidad`: la entrada mala, al principio.
    for nombre, carpeta in (("reportes", reportes), ("preregistros", prereg)):
        if not carpeta.is_dir():
            raise SystemExit(f"No existe la carpeta de {nombre} '{carpeta}'. "
                             "¿Estás en la raíz del repositorio?")
    salida.parent.mkdir(parents=True, exist_ok=True)
    base = salida.resolve().parent
    filas = {t: [] for t in ESQUEMA}
    resumen = {"tipos": {}, "preregistros": [], "veredictos": []}

    # Primero los preregistros: los veredictos se validan contra ellos.
    prereg_por_sello = {}
    for carpeta, es_prereg in ((prereg, True), (reportes, False)):
        for f in sorted(carpeta.glob("*.json")):
            ruta = _relativa(f, base)
            crudo = f.read_bytes()
            fecha, valido, motivo = None, True, None
            # Cada fichero escribe en su propio lote, que solo se suma si sale entero: un reporte
            # malformado se queda en `fuentes` como no válido, sin filas a medias y sin tumbar la
            # construcción de los demás.
            lote = {t: [] for t in ESQUEMA}
            try:
                doc = json.loads(crudo.decode("utf-8-sig"))
                tipo = "preregistro" if es_prereg else clasificar(doc)
            except (UnicodeDecodeError, json.JSONDecodeError) as e:
                doc, tipo, valido, motivo = None, "ilegible", False, f"no es JSON legible: {e}"
            try:
                if tipo == "preregistro" and not es_prereg:
                    valido, motivo = False, "un preregistro fuera de prereg/ no cuenta"
                elif tipo == "preregistro":
                    p = _filas_preregistro(ruta, f, doc, lote)
                    if p["sello_sha256"]:
                        prereg_por_sello.setdefault(p["sello_sha256"], p)
                    fecha, valido, motivo = _utc(doc.get("sello_utc")), p["verificado"], p["motivo"]
                    resumen["preregistros"].append(p)
                elif tipo == "veredicto":
                    valido, motivo = _filas_veredicto(ruta, doc, prereg_por_sello, lote)
                    fecha = _utc(doc.get("corrida_utc"))
                    resumen["veredictos"].append((ruta, valido, motivo))
                elif tipo in ("informe", "informe_oraculo"):
                    _filas_informe(ruta, doc, tipo, lote)
                    fecha = _utc((doc.get("reproducibilidad") or {}).get("corrida_utc"))
                elif tipo == "popularidad":
                    _filas_popularidad(ruta, doc, lote)
                    fecha = _utc((doc.get("procedencia") or {}).get("descargado_utc"))
                elif tipo == "cartera":
                    _filas_cartera(ruta, doc, lote)
                elif tipo == "desconocido":
                    valido, motivo = False, "forma no reconocida: no es ningún reporte conocido"
            except (AttributeError, KeyError, TypeError, ValueError, IndexError) as e:
                lote = {t: [] for t in ESQUEMA}
                valido, motivo = False, f"forma inesperada para un {tipo}: {type(e).__name__}: {e}"
                if tipo == "veredicto":
                    resumen["veredictos"].append((ruta, valido, motivo))
            for t, nuevas in lote.items():
                filas[t].extend(nuevas)
            filas["fuentes"].append((ruta, tipo, hashlib.sha256(crudo).hexdigest(), len(crudo),
                                     fecha, valido, motivo))
            resumen["tipos"][tipo] = resumen["tipos"].get(tipo, 0) + 1
    filas["catalogo"] = list(CATALOGO)

    def _dentro(carpeta):
        """La carpeta relativa a la base, o None si está fuera: entonces no se puede vigilar."""
        try:
            return carpeta.resolve().relative_to(base).as_posix()
        except ValueError:
            return None

    ahora = ahora or datetime.datetime.now(datetime.timezone.utc)
    filas["construccion"] = [(VERSION_ESQUEMA, ahora.isoformat(timespec="seconds"), __version__,
                              duckdb.__version__, _dentro(reportes), _dentro(prereg),
                              len(filas["fuentes"]))]

    # Se escribe aparte y se sustituye de una vez: una app abierta nunca ve una base a medias.
    tmp = salida.with_name(salida.name + ".construyendo")
    for resto in (tmp, pathlib.Path(str(tmp) + ".wal")):
        resto.unlink(missing_ok=True)
    con = duckdb.connect(str(tmp))
    try:
        # Una sola transacción: con una por sentencia, la construcción tardaba el doble (0,31 s
        # contra 0,16 s, medido). El resto del tiempo es el checkpoint al cerrar, no las inserciones.
        con.execute("BEGIN TRANSACTION")
        for tabla, columnas in ESQUEMA.items():
            con.execute(f'CREATE TABLE "{tabla}" ('
                        + ", ".join(f'"{c}" {t}' for c, t in columnas) + ")")
            if filas[tabla]:
                marcas = ", ".join("?" for _ in columnas)
                con.executemany(f'INSERT INTO "{tabla}" VALUES ({marcas})', filas[tabla])
        con.execute("COMMIT")
    finally:
        con.close()
    try:
        os.replace(tmp, salida)
    except PermissionError as e:
        raise SystemExit(f"No puedo sustituir {salida}: otro proceso la tiene abierta. "
                         "Cierra la app (o espera a que termine de leer) y vuelve a construir.") from e
    resumen["ficheros"] = len(filas["fuentes"])
    resumen["salida"] = salida
    return resumen


# ---------------------------------------------------------------- leer (lo que usa la app)
def ruta_de_la_base(raiz):
    """La base que enseña la app: la de `MELATE_DUCKDB` si se fijó —los tests la usan para enseñarle
    bases forjadas—, o `melate.duckdb` en `raiz`.

    En un solo sitio porque la usan dos: la app, que la lee, y el lanzador (`melate.app`), que la
    pone al día. Con dos reglas, el lanzador podría poner al día una base y la app leer otra.
    """
    return pathlib.Path(os.environ.get("MELATE_DUCKDB") or pathlib.Path(raiz) / SALIDA)


def leer(ruta=SALIDA):
    """Todas las tablas como DataFrames. En **solo lectura**, y la base se cierra al salir.

    No se deja ninguna conexión abierta: en Windows una base abierta no se puede sustituir, y
    `construir` necesita poder hacerlo mientras la app está en marcha.
    """
    import duckdb

    con = duckdb.connect(str(ruta), read_only=True)
    try:
        nombres = [r[0] for r in con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main' "
            "ORDER BY table_name").fetchall()]
        return {n: con.execute(f'SELECT * FROM "{n}"').df() for n in nombres}
    finally:
        con.close()


def problema_de_esquema(tablas):
    """None si la base es de este esquema; si no, por qué no se puede usar.

    Mira las columnas, no solo las tablas: una base construida con una versión anterior del código
    puede tener todas las tablas y que le falte una columna, y la app moriría al buscarla.
    """
    faltan = sorted(set(ESQUEMA) - set(tablas))
    if faltan:
        return f"le faltan tablas: {', '.join(faltan)}"
    for tabla, columnas in ESQUEMA.items():
        ausentes = [c for c, _ in columnas if c not in tablas[tabla].columns]
        if ausentes:
            return f"a la tabla {tabla} le faltan columnas: {', '.join(ausentes)}"
    c = tablas["construccion"]
    if c.empty:
        return "no tiene fila de construcción"
    v = int(c.iloc[0]["version_esquema"])
    if v != VERSION_ESQUEMA:
        return f"es del esquema {v} y este código es del {VERSION_ESQUEMA}"
    return None


def frescura(ruta_base, tablas):
    """¿Ha cambiado algo en `reportes/` o `prereg/` desde que se construyó la base?

    Compara el SHA-256 de cada fichero en disco con el que se guardó al construir. No interpreta
    nada: hashea unos cientos de KB. Lo que devuelve son listas de rutas relativas.
    """
    base = pathlib.Path(ruta_base).resolve().parent
    c = tablas["construccion"].iloc[0]
    registradas = dict(zip(tablas["fuentes"]["ruta"], tablas["fuentes"]["sha256"]))
    carpetas = [d for d in (c["dir_reportes"], c["dir_prereg"]) if isinstance(d, str) and d]
    if len(carpetas) < 2:
        return {"comprobable": False, "al_dia": None, "nuevos": [], "cambiados": [], "borrados": []}
    en_disco = {}
    for d in carpetas:
        for f in sorted((base / d).glob("*.json")):
            en_disco[_relativa(f, base)] = _sha256(f)
    nuevos = sorted(set(en_disco) - set(registradas))
    borrados = sorted(set(registradas) - set(en_disco))
    cambiados = sorted(r for r in set(en_disco) & set(registradas) if en_disco[r] != registradas[r])
    return {"comprobable": True, "al_dia": not (nuevos or borrados or cambiados),
            "nuevos": nuevos, "cambiados": cambiados, "borrados": borrados}


def veredicto_vigente(tablas):
    """El veredicto que la app enseña en cada pantalla, y el único que la app llama veredicto.

    Sale **solo** de veredictos válidos del laboratorio. Sin ninguno, el del protocolo por defecto:
    sin ventaja demostrada. Ningún informe, por bajas que sean sus q, puede llegar aquí: la tabla
    `informes` ni se lee.

    De cada preregistro vale **el que juzgó con más datos**; a igualdad, el más reciente. No el
    último que se corrió: volver a correr el laboratorio sobre el snapshot viejo, para reproducir
    una cifra, no puede desplazar a un veredicto con sorteos de holdout. Uno que no registra sobre
    qué datos juzgó solo cuenta si no hay otro.
    """
    v = (tablas or {}).get("veredictos")
    if v is None or v.empty or not v["valido"].any():
        return {"veredicto": SIN_VENTAJA, "ventaja": False, "por_defecto": True, "vigentes": []}
    validos = v[v["valido"]].assign(_datos=lambda d: d["ultimo_concurso_datos"].fillna(-1))
    validos = validos.sort_values(["_datos", "corrida_utc", "ruta"])
    vigentes = (validos.groupby("prereg_id", sort=True).tail(1).drop(columns="_datos")
                .to_dict("records"))
    hay = any(bool(r["ventaja"]) for r in vigentes)
    return {"veredicto": VENTAJA if hay else SIN_VENTAJA, "ventaja": hay, "por_defecto": False,
            "vigentes": vigentes}


# ---------------------------------------------------------------- línea de órdenes
def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Construye melate.duckdb a partir de reportes/ y prereg/. No recalcula nada.",
        epilog="La app solo lee esta base, en solo lectura. Su lanzador (python -m melate.app) la "
               "construye solo si falta o está desactualizada.")
    ap.add_argument("--reportes", default="reportes", help="carpeta de los reportes JSON")
    ap.add_argument("--prereg", default="prereg", help="carpeta de los preregistros sellados")
    ap.add_argument("--salida", default=SALIDA, help=f"dónde escribir la base (por defecto {SALIDA})")
    a = ap.parse_args(argv)

    t0 = time.perf_counter()
    r = construir(a.reportes, a.prereg, a.salida)
    print(f"{r['salida']} construida en {time.perf_counter() - t0:.2f} s, con {r['ficheros']} ficheros:")
    for tipo, n in sorted(r["tipos"].items()):
        print(f"  {n:3d}  {tipo}")
    for p in r["preregistros"]:
        estado = "verifica" if p["verificado"] else f"NO VERIFICA: {p['motivo']}"
        print(f"  preregistro {p['id']}: {estado}")
    for ruta, valido, motivo in r["veredictos"]:
        print(f"  veredicto {ruta}: {'válido' if valido else 'NO VÁLIDO: ' + motivo}")
    vig = veredicto_vigente(leer(r["salida"]))
    print(f"\nLo que la app enseñará en cada pantalla: {vig['veredicto']}"
          + ("  (por defecto: no hay ningún veredicto válido)" if vig["por_defecto"] else ""))
    return r


if __name__ == "__main__":
    main()
