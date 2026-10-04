"""Máquina Melate — la app local.

    .venv\\Scripts\\python.exe -m melate.app      (el lanzador; vale desde cualquier carpeta)

Lee `melate.duckdb` —la construye `python -m melate.almacen`, y el lanzador si falta o está
desactualizada— en solo lectura. **No recalcula, no descarga y no escribe nada.** Si algo tarda dos
minutos en un backend, no va en una pantalla: la app enseña qué orden ejecutar.

Escucha solo en 127.0.0.1 y sin telemetría: el lanzador lo fuerza por línea de órdenes, y
`.streamlit/config.toml` lo dice para quien use `streamlit run` desde la raíz del repositorio, que es
la única carpeta desde la que se lee. Por eso la app **además** se niega a enseñar nada si la
dirección de escucha no es de loopback o si la telemetría está activada.

La frontera que esta app no puede borrar: **el informe explora, el laboratorio juzga.** La cabecera
de todas las pantallas sale de `almacen.veredicto_vigente`, que solo lee veredictos de `melate.lab`
con un preregistro que verifica. Las cifras exploratorias viven en su propia pantalla, con su aviso
delante, y nunca se llaman veredicto.
"""
import datetime
import pathlib

import pandas as pd
import streamlit as st

from melate import almacen
from melate.protocolo import SIN_VENTAJA

RAIZ = pathlib.Path(__file__).resolve().parent.parent

# Las únicas direcciones de escucha aceptables: las de esta máquina.
LOOPBACK = ("127.0.0.1", "localhost", "::1")

PANTALLAS = {
    "veredicto": "Veredicto",
    "exploracion": "Exploración",
    "valor-esperado": "Valor esperado",
    "jugadores": "Jugadores",
    "procedencia": "Procedencia",
}

ORDEN_LANZADOR = ".venv\\Scripts\\python.exe -m melate.app"
ORDEN_REPRODUCIR = (
    ".venv\\Scripts\\python.exe -m melate.almacen   # sin cerrar la app\n"
    f"{ORDEN_LANZADOR}          # o al abrirla: el lanzador la pone al día"
)

AVISO_EXPLORA = (
    "**Esto explora; no juzga.** Las p y las q de esta pantalla salen de `python -m melate.informe` "
    "sobre todo el histórico. Sirven para encontrar candidatas que preregistrar, nunca para afirmar "
    "una ventaja: eso solo lo hace el laboratorio, con un preregistro sellado y sobre sorteos "
    "posteriores al sello. El veredicto es el de la cabecera."
)
AVISO_DINERO = (
    "**Esto mide dinero, no la urna.** Es aritmética sobre la bolsa anunciada para el sorteo "
    "siguiente al último de los datos del informe. Con un snapshot congelado es un dato histórico, no "
    "una previsión, y no dice nada de qué números van a salir."
)
AVISO_JUGADORES = (
    "**Esto mide a los jugadores, no la urna.** El sorteo no sabe qué apostó nadie: nada de esta "
    "pantalla dice qué números van a salir, y por eso ninguna de estas pruebas entra en la familia de "
    "Benjamini-Hochberg."
)

ESTADISTICOS = {
    "chi2_corr": "chi-cuadrada corregida",
    "max_count": "frecuencia máxima",
    "min_count": "frecuencia mínima",
    "max_pair": "pareja más repetida",
    "mean_overlap": "repetidos con el sorteo anterior",
}


# ---------------------------------------------------------------- utilidades puras (con test)
_MARKDOWN = str.maketrans({c: "\\" + c for c in "\\`*_{}[]()#+-.!|<>$~:"})


def escapar(texto):
    """Texto de un fichero, listo para Markdown sin que nada se interprete.

    Un `$` abre una fórmula, `[x](url)` es un enlace y `![x](url)` una imagen que el navegador iría a
    buscar fuera. Ningún texto que venga de `reportes/` o `prereg/` se pinta sin pasar por aquí,
    salvo dentro de comillas invertidas, que van por `codigo()`.
    """
    return "" if nulo(texto) else str(texto).translate(_MARKDOWN)


def codigo(texto):
    """Texto de un fichero entre comillas invertidas. Ahí Markdown no interpreta nada —tampoco los
    escapes, que se verían como barras—, así que lo único que hay que impedir es otra comilla
    invertida que cierre el bloque antes de tiempo."""
    return "`" + ("" if nulo(texto) else str(texto)).replace("`", "'") + "`"


def nulo(x):
    try:
        return x is None or bool(pd.isna(x))
    except (TypeError, ValueError):
        return False


def problemas_de_red(direccion, telemetria):
    """Qué impide enseñar algo. Lista vacía = se puede."""
    problemas = []
    if direccion not in LOOPBACK:
        donde = direccion or "todas las interfaces (server.address sin fijar)"
        problemas.append(f"el servidor escucha en {donde}, no solo en esta máquina")
    if telemetria:
        problemas.append("la telemetría de Streamlit está activada (browser.gatherUsageStats)")
    return problemas


def fecha(iso):
    if nulo(iso):
        return "sin fecha"
    d = datetime.datetime.fromisoformat(str(iso))
    return d.astimezone(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def num(x, decimales=4):
    return "—" if nulo(x) else f"{float(x):.{decimales}f}"


def pct(x, decimales=1):
    return "—" if nulo(x) else f"{float(x) * 100:+.{decimales}f} %"


def entero(x):
    return "—" if nulo(x) else f"{int(x):,}".replace(",", " ")


# ---------------------------------------------------------------- lectura
@st.cache_data(show_spinner=False)
def cargar(ruta, firma):
    """La base entera en memoria. `firma` (fecha y tamaño del fichero) invalida la caché al
    reconstruirla: sin ella, la app seguiría enseñando la base vieja."""
    return almacen.leer(ruta)


def tabla(df, columnas):
    """Un DataFrame con las columnas renombradas para la pantalla, en ese orden."""
    return df[list(columnas)].rename(columns=columnas)


def ver(df):
    """Toda tabla de la app pasa por aquí: entera, sin la barra que corta a partir de diez filas, y
    con un guion donde falta un valor en vez de la palabra None. Las dos cosas se vieron en una
    captura del navegador; ningún test las veía."""
    st.dataframe(df, hide_index=True, height="content", placeholder="—")


# ---------------------------------------------------------------- cabecera de todas las pantallas
def datos_del_veredicto(r):
    """Sobre qué datos se emitió un veredicto, dicho sin esconder que los juegos no coincidan."""
    if not r["datos_registrados"]:
        return "el veredicto no registra sobre qué datos se emitió"
    hasta, desde = r["ultimo_concurso_datos"], r["ultimo_concurso_datos_min"]
    sorteo = (f"el sorteo {hasta}" if hasta == desde
              else f"los sorteos {desde} a {hasta} (no todos los juegos llegan al mismo)")
    return f"datos hasta {sorteo} ({escapar(r['ultima_fecha_datos'])})"


def cabecera(vigente):
    """El veredicto, en todas las pantallas. Solo del laboratorio; sin él, el del protocolo."""
    if vigente["por_defecto"]:
        cuerpo = (f"**{SIN_VENTAJA}** · por defecto: la base no tiene ningún veredicto válido del "
                  "laboratorio, y sin él el protocolo no declara nada.")
    else:
        partes = []
        for r in vigente["vigentes"]:
            partes.append(f"{escapar(r['prereg_id'])}: {r['cumplidas']} de {r['de']} condiciones, "
                          f"holdout de {r['sorteos_holdout']} sorteos, corrida del "
                          f"{escapar(fecha(r['corrida_utc']))}, {datos_del_veredicto(r)}")
        cuerpo = (f"**{escapar(vigente['veredicto'])}** · veredicto de `melate.lab` sobre "
                  + "; ".join(partes) + ".")
    st.info(cuerpo + "\n\nEs lo único que juzga. Ninguna cifra de las demás pantallas puede cambiarlo.")


def aviso_de_frescura(fres):
    if not fres["comprobable"]:
        st.warning("No se puede comprobar si la base está al día: se construyó con carpetas que no "
                   "están en su mismo árbol.")
    elif not fres["al_dia"]:
        partes = [f"{len(v)} {nombre}" for nombre, v in
                  (("nuevos", fres["nuevos"]), ("cambiados", fres["cambiados"]),
                   ("borrados", fres["borrados"])) if v]
        st.warning("**La base no está al día.** Desde que se construyó hay en `reportes/` o `prereg/` "
                   f"ficheros {', '.join(partes)}. Lo que ves es lo que había entonces: "
                   "reconstrúyela con `python -m melate.almacen`.")


# ---------------------------------------------------------------- pantallas
def pantalla_veredicto(t, vigente):
    st.header("Veredicto del laboratorio")
    st.markdown(
        "Esta es **la única pantalla que juzga**. El veredicto sale de `python -m melate.lab`, que "
        "evalúa una hipótesis **preregistrada** solo sobre los sorteos posteriores a su sello y "
        "exige las cinco condiciones de la regla 5 a la vez. En las demás pantallas se explora y se "
        "mide; aquí se juzga.")
    pre, vds, con = t["preregistros"], t["veredictos"], t["condiciones"]
    if pre.empty:
        st.info("No hay ningún preregistro en `prereg/`. Sin preregistro no se evalúa nada.")
    for _, p in pre.iterrows():
        st.subheader(escapar(p["titulo"] or p["id"]))
        st.caption(f"Preregistro {escapar(p['id'])} · sellado el {escapar(fecha(p['sello_utc']))} · "
                   f"sello {escapar(str(p['sello_sha256'])[:16])}… · "
                   + ("**verifica**" if p["verificado"] else "**NO verifica**"))
        if not p["verificado"]:
            st.error(f"Este preregistro **no verifica**: {escapar(p['motivo'])}. Un preregistro "
                     "alterado no prueba nada, y ningún veredicto que apunte a él cuenta.")
        suyos = vds[vds["prereg_id"] == p["id"]].sort_values("corrida_utc")
        # El mismo vigente que la cabecera, elegido en un solo sitio: con dos reglas, la cabecera
        # y esta pantalla podían enseñar veredictos distintos.
        r = next((v for v in vigente["vigentes"] if v["prereg_id"] == p["id"]), None)
        if r is None:
            st.info("Este preregistro no tiene ningún veredicto válido todavía.")
        else:
            # El veredicto va en texto y no en un st.metric: el metric lo truncaba a
            # "sin ventaja demos…", visto en una captura del navegador.
            st.markdown(f"### {escapar(r['veredicto'])}")
            c1, c2 = st.columns(2)
            c1.metric("Condiciones que cumple", f"{r['cumplidas']} de {r['de']}")
            c2.metric(f"Holdout en {escapar(r['juego_principal'])}", f"{r['sorteos_holdout']} sorteos")
            sha = (f", SHA-256 de Revancha {escapar(str(r['sha256_revancha'])[:16])}…"
                   if r["datos_registrados"] else "")
            st.caption(f"Corrida del {escapar(fecha(r['corrida_utc']))} · {datos_del_veredicto(r)}"
                       f"{sha} · {codigo(r['ruta'])}")
            cond = con[con["ruta"] == r["ruta"]].sort_values("orden").copy()
            cond["cumple"] = cond["cumple"].map({True: "sí", False: "NO"})
            ver(tabla(cond, {"orden": "#", "condicion": "Condición", "cumple": "¿Cumple?",
                             "motivo": "Motivo"}))
            hold = pd.DataFrame({
                "Juego": ["Melate", "Revancha", "Revanchita"],
                "Sorteos posteriores al sello": [r["holdout_melate"], r["holdout_revancha"],
                                                 r["holdout_revanchita"]],
                "Δ aciertos sobre el azar": [num(r["delta_melate"]), num(r["delta_revancha"]),
                                             num(r["delta_revanchita"])],
            })
            ver(hold)
            st.caption(f"Línea base del azar: {num(r['linea_base_azar'], 6)} aciertos por boleto. "
                       f"Familia declarada en el sello: {r['familia_declarada']} pruebas.")
        with st.expander("El preregistro, tal como se selló"):
            st.markdown(f"**Hipótesis.** {escapar(p['hipotesis'])}")
            st.markdown(
                f"**Estrategia** {escapar(p['estrategia'])} en {escapar(p['juego_principal'])} · "
                f"**umbral** q ≤ {num(p['umbral_q'], 2)} · **familia** de {p['tamano_familia']} "
                f"pruebas · **efecto mínimo declarado** {num(p['efecto_minimo_declarado'], 3)} · "
                f"**variantes de hiperparámetros** {p['variantes']} · **datos al sellar** hasta el "
                f"sorteo {p['ultimo_concurso_al_sellar']}")
            st.markdown(f"**Notas.** {escapar(p['notas'])}")
        st.markdown("Para un veredicto nuevo, desde la raíz del repositorio:")
        st.code(f".venv\\Scripts\\python.exe -m melate.lab --prereg {p['ruta']} "
                "--salida reportes\\<fecha>_veredicto.json\n.venv\\Scripts\\python.exe -m melate.almacen",
                language="powershell", wrap_lines=True)
        st.caption("Sin `--datos`, el laboratorio descarga los CSV del oficial: es la única forma de que "
                   "entren sorteos posteriores al sello. La app no descarga nada por su cuenta.")
        if len(suyos) > 1 or not suyos["valido"].all():
            with st.expander(f"Todos los veredictos de este preregistro ({len(suyos)})"):
                h = suyos.copy()
                h["corrida_utc"] = h["corrida_utc"].map(fecha)
                h["valido"] = h["valido"].map({True: "sí", False: "NO"})
                ver(tabla(h, {"corrida_utc": "Corrida", "veredicto": "Veredicto",
                              "cumplidas": "Cumple", "sorteos_holdout": "Holdout",
                              "ultimo_concurso_datos": "Datos hasta", "valido": "¿Válido?",
                              "motivo": "Por qué no", "ruta": "Fichero"}))
    huerfanos = vds[~vds["prereg_id"].isin(pre["id"])]
    if not huerfanos.empty:
        st.error(f"{len(huerfanos)} veredicto(s) apuntan a un preregistro que no está en `prereg/` y "
                 "no cuentan.")
        ver(tabla(huerfanos, {"ruta": "Fichero", "prereg_id": "Preregistro",
                              "motivo": "Por qué no cuenta"}))


def elegir_informe(t, clave):
    inf = t["informes"].copy()
    if inf.empty:
        return None
    inf["_orden"] = inf["corrida_utc"].fillna("")
    inf = inf.sort_values(["_orden", "ruta"], ascending=False)

    def etiqueta(ruta):
        r = inf[inf["ruta"] == ruta].iloc[0]
        cuando = fecha(r["corrida_utc"]) if r["tipo"] == "informe" else "oráculo, sin fecha"
        sims = "" if nulo(r["simulaciones"]) else f" · {int(r['simulaciones'])} simulaciones"
        return f"{cuando}{sims} · {ruta}"

    ruta = st.selectbox("Informe", inf["ruta"].tolist(), format_func=etiqueta, key=clave)
    return inf[inf["ruta"] == ruta].iloc[0]


def procedencia_del_informe(t, inf):
    d = t["datos_informe"][t["datos_informe"]["ruta"] == inf["ruta"]]
    partes = [f"{escapar(r['juego'])} hasta el {r['ultimo']} ({escapar(r['ultima_fecha'])})"
              for _, r in d.iterrows()]
    sims = "sin registro" if nulo(inf["simulaciones"]) else f"{int(inf['simulaciones'])} simulaciones"
    st.caption(f"Datos: {', '.join(partes) or 'sin registro'} · {sims} · versiones: "
               f"scikit-learn {escapar(inf['scikit_learn'] or '—')}, numpy "
               f"{escapar(inf['numpy'] or '—')}, pandas {escapar(inf['pandas'] or '—')}")


def pantalla_exploracion(t):
    st.header("Exploración: el informe")
    st.warning(AVISO_EXPLORA)
    inf = elegir_informe(t, "informe_exploracion")
    if inf is None:
        st.info("La base no tiene ningún informe. Se genera con `python -m melate.informe`.")
        return
    procedencia_del_informe(t, inf)

    st.subheader("La familia de Benjamini-Hochberg")
    if inf["tipo"] == "informe" and nulo(inf["pruebas"]):
        st.info("Este informe es anterior a la familia global de 36 pruebas: solo trae las dos "
                "familias del oráculo.")
    elif inf["tipo"] == "informe":
        st.markdown(
            f"{int(inf['pruebas'])} pruebas —{int(inf['pruebas_auditoria'])} de auditoría y "
            f"{int(inf['pruebas_backtest'])} de backtest— corregidas como una sola familia. "
            f"**q mínima: {num(inf['q_minima'])}**. Pruebas con q ≤ {num(inf['umbral'], 2)}: "
            f"**{int(inf['pruebas_bajo_umbral'])}**.")
        st.caption(f"Resumen exploratorio que imprime el informe: «{escapar(inf['resumen_exploratorio'])}». "
                   "No es un veredicto: el veredicto es el de la cabecera.")
        if inf["pruebas_bajo_umbral"]:
            st.warning(
                f"En esta exploración, {int(inf['pruebas_bajo_umbral'])} prueba(s) quedan con q ≤ "
                f"{num(inf['umbral'], 2)}: {escapar(inf['bajo_umbral'])}. **Eso no es una ventaja**: "
                "es una candidata a preregistrar. Hay que sellar la hipótesis y esperar sorteos "
                "posteriores al sello; solo el laboratorio puede juzgarla.")
    else:
        st.info("Este es el informe del oráculo: corrige las 15 pruebas de auditoría y las 21 de "
                "backtest en dos familias separadas. La familia única de 36, que es la que manda, la "
                "añade el paquete.")

    bt = t["backtest"][t["backtest"]["ruta"] == inf["ruta"]]
    hipotesis = bt[~bt["es_referencia"]]
    if not hipotesis.empty:
        m = hipotesis.sort_values(["p", "juego", "orden"]).iloc[0]
        cual, q = (("global", m["q_global"]) if not nulo(m["q_global"])
                   else ("de su familia", m["q_familia"]))
        st.markdown(
            f"La p más baja del backtest es **{num(m['p'])}** ({escapar(m['estrategia'])} en "
            f"{escapar(m['juego'])}), y su q {cual} es **{num(q)}**. Con decenas de pruebas, algo "
            "siempre destaca: por eso manda la q, y por eso ni siquiera una q baja bastaría sin el "
            "laboratorio.")

    st.subheader("Auditoría de la urna")
    urnas = ("urnas simuladas (este informe no registra cuántas)" if nulo(inf["simulaciones"])
             else f"{int(inf['simulaciones'])} urnas simuladas")
    st.markdown(f"Cinco estadísticos por juego contra {urnas}; p de dos colas.")
    au = t["auditoria"][t["auditoria"]["ruta"] == inf["ruta"]].copy()
    au["estadistico"] = au["estadistico"].map(lambda e: ESTADISTICOS.get(e, e))
    ver(tabla(au, {"juego": "Juego", "estadistico": "Estadístico", "obs": "Observado",
                   "media_sim": "Media simulada", "p": "p", "q_familia": "q (familia)",
                   "q_global": "q (global)"}))
    ej = t["exploracion_juego"][t["exploracion_juego"]["ruta"] == inf["ruta"]]
    ver(tabla(ej, {"juego": "Juego", "sorteos": "Sorteos de la era 6/56",
                   "sesgo_detectable_1_esfera": "Sesgo detectable en 1 esfera",
                   "sesgo_detectable_56_esferas": "Sesgo detectable en cualquiera de 56"}))

    st.subheader("Backtest walk-forward")
    for juego in ej["juego"]:
        e = ej[ej["juego"] == juego].iloc[0]
        st.markdown(
            f"**{escapar(juego)}** — {int(e['sorteos_prueba'])} sorteos de prueba desde el "
            f"{int(e['primer_concurso_prueba'])}; el azar acierta {num(e['media_azar'])} por boleto "
            f"y el efecto mínimo detectable es {num(e['efecto_minimo_detectable'])}.")
        b = bt[bt["juego"] == juego].sort_values("orden").copy()
        b["estrategia"] = [f"{s} (referencia)" if ref else s
                           for s, ref in zip(b["estrategia"], b["es_referencia"])]
        ver(tabla(b, {"estrategia": "Estrategia", "media": "Aciertos por boleto",
                      "delta": "Δ sobre el azar", "z": "z", "p": "p",
                      "q_familia": "q (familia)", "q_global": "q (global)",
                      "aciertos_3_o_mas": "Boletos con 3+",
                      "esperados_3_o_mas": "Esperados al azar"}))
    ll = bt[bt["logloss_p"].notna()]
    if not ll.empty:
        st.markdown("**Log-loss frente al azar.** Un Δ **positivo** quiere decir que el modelo "
                    "reparte las probabilidades **peor** que el azar.")
        ver(tabla(ll, {"juego": "Juego", "estrategia": "Modelo",
                       "logloss_delta": "Δ log-loss (positivo = peor)", "logloss_t": "t",
                       "logloss_p": "p"}))
        st.caption(f"Estas {len(ll)} pruebas de log-loss se publican porque las calcula el oráculo, "
                   "pero no forman parte de la familia de 36: no son pruebas sobre la urna. Con una "
                   "urna limpia, todo modelo que no reparta las probabilidades por igual pierde en "
                   "log-loss, así que un Δ positivo es lo esperado; solo uno negativo y significativo "
                   "diría algo de la urna.")


def pantalla_valor_esperado(t):
    st.header("Valor esperado de un boleto")
    st.info(AVISO_DINERO)
    inf = elegir_informe(t, "informe_valor_esperado")
    if inf is None:
        st.info("La base no tiene ningún informe. Se genera con `python -m melate.informe`.")
        return
    procedencia_del_informe(t, inf)
    ev = t["valor_esperado"][t["valor_esperado"]["ruta"] == inf["ruta"]]
    base = ev[ev["variante"] == "constante_del_oraculo"].set_index("juego")
    medido = ev[ev["variante"] == "menores_medidos"].set_index("juego")
    if base.empty:
        st.info("Este informe no trae valor esperado.")
        return
    # Una fila por juego y variante: en columnas, la tabla no cabía y la bolsa de equilibrio de una
    # variante se mezclaba con la de la otra.
    variante = {"constante_del_oraculo": "constante del oráculo",
                "menores_medidos": "medidos"}
    ev = ev.sort_values(["juego", "variante"]).assign(
        variante=lambda d: d["variante"].map(variante),
        bolsa=lambda d: (d["bolsa_bruta"] / 1e6).round(1),
        rendimiento=lambda d: d["rendimiento"].map(pct),
        equilibrio=lambda d: (d["bolsa_de_equilibrio"] / 1e6).round(1))
    ver(tabla(ev, {"juego": "Juego", "proximo_sorteo": "Sorteo", "bolsa": "Bolsa (millones)",
                   "precio": "Precio", "variante": "Premios menores", "ev": "Valor esperado",
                   "rendimiento": "Rendimiento", "equilibrio": "Bolsa de equilibrio (millones)"}))
    if medido.empty:
        st.caption("Este informe no trae los premios menores medidos: se generó sin `--popularidad`, "
                   "así que solo tiene la constante escrita a mano en el oráculo.")
    else:
        detalle = "; ".join(f"{escapar(j)} {num(r['menores_brutos'])} ({escapar(r['procedencia_menores'])})"
                            for j, r in medido.iterrows())
        v = medido.iloc[0]
        st.caption(f"Premios menores medidos, ventana {int(v['ventana_desde'])}–{int(v['ventana_hasta'])}: "
                   f"{detalle}. Las filas de la constante del oráculo la conservan para que la paridad "
                   "siga siendo comparable.")
    if (base["rendimiento"] < 0).all() and (medido.empty or (medido["rendimiento"] < 0).all()):
        st.markdown("**En los tres juegos el boleto vale menos de lo que cuesta.**")
    else:
        st.warning("Con esta bolsa algún juego tiene valor esperado positivo. Es aritmética del premio "
                   "acumulado: no dice nada de qué números salen ni es una ventaja demostrada.")
    s = base.iloc[0]
    st.caption(f"Supuestos del informe: λ = {num(s['lambda'])}, S = {num(s['s'])}, impuesto "
               f"{pct(s['impuesto'], 0).replace('+', '')}.")
    st.subheader("Premios mayores")
    pm = t["premios_mayores"][t["premios_mayores"]["ruta"] == inf["ruta"]]
    ver(tabla(pm, {"juego": "Juego", "ganados": "Premios mayores detectados",
                   "sorteos": "Sorteos de la era 6/56"}))
    st.caption("Detectados por bajas de BOLSA (regla 3 de los datos); una baja seguida de un valor "
               "mayor que el anterior se descarta como error.")


def pantalla_jugadores(t):
    st.header("Los jugadores: popularidad y cartera")
    st.info(AVISO_JUGADORES)
    st.subheader("Qué juega la gente")
    po = t["popularidad"].sort_values(["ventana_desde", "juego"]).copy()
    if po.empty:
        st.info("La base no tiene ningún reporte de popularidad. Se genera con "
                "`python -m melate.popularity`, que pide páginas a un tercero a 1 por segundo.")
    else:
        po["ventana"] = [f"{a}–{b}" for a, b in zip(po["ventana_desde"], po["ventana_hasta"])]
        po["ventas"] = [f"{entero(m)} ({entero(a)} a {entero(b)})"
                        for m, a, b in zip(po["ventas_mediana"], po["ventas_min"], po["ventas_max"])]
        # Tres tablas y no una: en una sola no cabían, y las columnas del final quedaban cortadas.
        ver(tabla(po, {
            "ventana": "Ventana", "juego": "Juego", "sorteos_usados": "Sorteos", "fallos": "Fallos",
            "ventas": "Combinaciones vendidas: mediana (rango)"}))
        st.markdown("**Premios menores.** Lo que esperaría cobrar un boleto cualquiera en las "
                    "categorías que no son el premio mayor, estimado por la bolsa repartida entre las "
                    "ventas.")
        ver(tabla(po, {
            "ventana": "Ventana", "juego": "Juego",
            "sorteos_sin_premios": "Sorteos sin premios publicados",
            "menores_bolsa_n": "Sorteos que cuentan", "menores_bolsa_mediana": "Mediana",
            "menores_bolsa_cv": "cv", "menores_bolsa_min": "Mínimo", "menores_bolsa_max": "Máximo"}))
        st.caption("Un sorteo cuya tabla trae los ganadores pero no los importes cuenta para las "
                   "ventas y para el efecto calendario, y no para los premios menores. Un guion en "
                   "«sin premios publicados» quiere decir que el reporte es anterior a esa "
                   "comprobación.")
        # El efecto calendario va en su propia tabla: al final de la anterior quedaba cortado, y es
        # la cifra más importante de la pantalla.
        cal = po[po["calendario_cociente"].notna()].copy()
        cal["menos"] = [pct(c - 1) for c in cal["calendario_cociente"]]
        st.markdown("**El efecto calendario.** ¿Aparecen menos en los boletos los números que no "
                    "caben en una fecha?")
        ver(tabla(cal, {"ventana": "Ventana", "juego": "Juego",
                        "calendario_n_dentro": "Sorteos con adicional ≤ 31",
                        "calendario_n_fuera": "Sorteos con adicional > 31",
                        "calendario_cociente": "Cociente > 31 / ≤ 31",
                        "menos": "Boletos con un número > 31", "calendario_t": "t de Welch"}))
        st.caption("Mide la conducta de los jugadores, no la urna, y por eso no entra en la familia de "
                   "36. Solo Melate lo permite medir: cada sorteo aísla un número, su adicional.")

    st.subheader("Cartera")
    ca = t["carteras"]
    if ca.empty:
        st.info("La base no tiene ninguna cartera. Se genera con `python -m melate.portfolio`.")
    for _, c in ca.iterrows():
        if c["aviso"]:
            st.warning(escapar(c["aviso"]))
        st.markdown(
            f"**{escapar(c['juego'])}, presupuesto {entero(c['presupuesto'])} pesos**: "
            f"{int(c['boletos'])} boletos por {entero(c['coste'])} pesos, que cubren "
            f"{int(c['numeros_cubiertos'])} de 56 números; popularidad media {num(c['popularidad_media'])} "
            f"con tope {num(c['tope_popularidad'], 2)} · {codigo(c['ruta'])}")
        if c["valorada"]:
            v = pd.DataFrame([{
                "Coste": c["coste"], "Valor esperado": c["valor_esperado"],
                "Rendimiento": pct(c["rendimiento"]),
                "Sin mirar la popularidad": c["valor_esperado_sin_mirar_popularidad"],
                "Lo que aporta evitar compartir": c["ganancia_por_evitar_compartir"],
                "En % del precio": pct(c["ganancia_como_porcentaje_del_precio"], 2),
            }])
            ver(v)
            if nulo(c["bolsa"]):
                st.caption("La valoración se hizo con la bolsa que se pasó a `--bolsa`; este reporte "
                           "es anterior a que se registrara.")
            else:
                st.caption(f"Valorada con una bolsa de {num(c['bolsa'] / 1e6, 1)} millones, unos "
                           f"premios menores de {num(c['menores_brutos'])} por boleto y un impuesto "
                           f"del {pct(c['impuesto'], 0).replace('+', '')}.")
        with st.expander("Los boletos de esta cartera"):
            st.caption("No son números con más probabilidad de salir: no existen. Son combinaciones "
                       "poco jugadas, para repartir con menos gente si alguna acertara.")
            bo = t["cartera_boletos"][t["cartera_boletos"]["ruta"] == c["ruta"]]
            ver(tabla(bo, {"orden": "#", "numeros": "Números", "popularidad": "Popularidad",
                           "patrones": "Patrones", "factor_reparto": "Factor de reparto"}))


def pantalla_procedencia(t, ruta, fres):
    st.header("Procedencia")
    st.markdown(
        "De dónde sale cada cifra de esta app. `melate.duckdb` es un **índice** de `reportes/` y "
        "`prereg/`, que son la fuente de verdad y están en el repositorio. La base no se publica.")
    c = t["construccion"].iloc[0]
    estado = ("al día con `reportes/` y `prereg/`" if fres["al_dia"]
              else "**desactualizada**" if fres["comprobable"] else "sin poder comprobarse")
    st.markdown(f"Base {codigo(pathlib.Path(ruta).name)} construida el "
                f"{escapar(fecha(c['construido_utc']))} con melate {escapar(c['melate'])} y duckdb "
                f"{escapar(c['duckdb'])}, esquema {int(c['version_esquema'])}, "
                f"{int(c['ficheros'])} ficheros leídos: {estado}.")
    for nombre in ("nuevos", "cambiados", "borrados"):
        if fres[nombre]:
            st.markdown(f"Ficheros {nombre} desde la construcción: "
                        + ", ".join(codigo(r) for r in fres[nombre]))
    st.subheader("Ficheros leídos")
    f = t["fuentes"].copy()
    f["sha256"] = f["sha256"].str[:16]
    f["fecha_utc"] = f["fecha_utc"].map(lambda x: fecha(x) if not nulo(x) else "—")
    f["valido"] = f["valido"].map({True: "sí", False: "NO"})
    ver(tabla(f, {"ruta": "Fichero", "tipo": "Tipo", "fecha_utc": "Fecha que declara",
                  "sha256": "SHA-256 (inicio)", "bytes": "Bytes", "valido": "¿Vale?",
                  "motivo": "Por qué no"}))
    st.subheader("Sobre qué datos se corrió cada informe")
    d = t["datos_informe"].copy()
    d["sha256"] = d["sha256"].str[:16]
    ver(tabla(d, {"ruta": "Informe", "juego": "Juego", "vista": "Vista",
                  "ultimo": "Último sorteo", "ultima_fecha": "Fecha", "filas": "Sorteos",
                  "sha256": "SHA-256 (inicio)", "origen": "Origen",
                  "bolsa_invalida": "BOLSA inválida en"}))
    st.subheader("Qué es cada tabla de la base")
    ver(tabla(t["catalogo"], {"tabla": "Tabla", "naturaleza": "Naturaleza",
                                       "mira_a": "Mira a", "que_es": "Qué es"}))
    st.caption("**juzga**: solo lo que sale del laboratorio con un sello que verifica · **explora**: "
               "candidatas, nunca afirmaciones · **mide**: dinero y jugadores, fuera de la familia "
               "de 36 · **procedencia**: de dónde sale lo demás.")
    st.subheader("Esta app")
    escucha = f"{st.get_option('server.address')}:{st.get_option('server.port')}"
    st.markdown(
        f"Escucha en {codigo(escucha)} y la telemetría de Streamlit está **apagada**. Abre la base "
        "en solo lectura y no recalcula, no descarga ni escribe nada. Para ponerla al día:")
    st.code(ORDEN_REPRODUCIR, language="powershell")


# ---------------------------------------------------------------- el enrutador
def main():
    st.set_page_config(page_title="Máquina Melate", layout="wide")

    problemas = problemas_de_red(st.get_option("server.address"),
                                 st.get_option("browser.gatherUsageStats"))
    if problemas:
        cabecera(almacen.veredicto_vigente(None))
        st.error("**Esta app se niega a enseñar nada:** " + "; ".join(problemas) + ". Es una app "
                 "local. Ábrela con su lanzador, que la ata a 127.0.0.1 y apaga la telemetría se "
                 "lance desde donde se lance:")
        st.code(ORDEN_LANZADOR, language="powershell")
        st.stop()

    ruta = almacen.ruta_de_la_base(RAIZ)
    if not ruta.is_file():
        cabecera(almacen.veredicto_vigente(None))
        st.error(f"No encuentro la base {codigo(ruta.name)}. Constrúyela desde la raíz del "
                 "repositorio; tarda menos de dos segundos y no sale a la red. El lanzador "
                 "(`python -m melate.app`) la construye solo.")
        st.code(".venv\\Scripts\\python.exe -m melate.almacen", language="powershell")
        st.stop()

    info = ruta.stat()
    t = cargar(str(ruta), (info.st_mtime_ns, info.st_size))
    problema = almacen.problema_de_esquema(t)
    if problema:
        cabecera(almacen.veredicto_vigente(None))
        st.error(f"La base no se puede usar: {escapar(problema)}. Reconstrúyela con "
                 "`python -m melate.almacen`.")
        st.stop()

    vigente = almacen.veredicto_vigente(t)
    cabecera(vigente)
    fres = almacen.frescura(ruta, t)
    aviso_de_frescura(fres)

    # Cada pantalla tiene su URL (?pantalla=exploracion). Se lee y se escribe a mano: con
    # bind="query-params", Streamlit exige en la URL la etiqueta ("Exploración") y no el valor, y
    # descartaba ?pantalla=exploracion en silencio. Lo enseñó una captura del navegador; AppTest
    # no lo ve, porque no simula la URL de un widget ligado.
    pedida = st.query_params.get("pantalla")
    with st.sidebar:
        st.title("Máquina Melate")
        pantalla = st.radio("Pantalla", list(PANTALLAS), format_func=PANTALLAS.get, key="pantalla",
                            index=list(PANTALLAS).index(pedida) if pedida in PANTALLAS else 0)
        st.caption("Esto no predice números. Lee `melate.duckdb` en solo lectura: no recalcula, no "
                   "descarga y no escribe nada.")
    st.query_params["pantalla"] = pantalla

    if pantalla == "exploracion":
        pantalla_exploracion(t)
    elif pantalla == "valor-esperado":
        pantalla_valor_esperado(t)
    elif pantalla == "jugadores":
        pantalla_jugadores(t)
    elif pantalla == "procedencia":
        pantalla_procedencia(t, ruta, fres)
    else:
        pantalla_veredicto(t, vigente)


if __name__ == "__main__":
    main()
