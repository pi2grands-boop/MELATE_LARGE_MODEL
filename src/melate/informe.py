"""Informe completo: `python -m melate.informe`.

Reproduce el reporte de baseline_auditoria.py clave por clave, y le añade tres cosas, cada una
declarada en NUEVAS_CLAVES para que tests/test_paridad.py sepa qué puede ignorar:

* `reproducibilidad` — hash de los datos, semillas y versiones (regla 6 del protocolo).
* `validacion_era_56` — las mismas comprobaciones sobre la era que se analiza.
* `q_BH_global` y `protocolo_global` — la familia única de 36 pruebas (regla 3).

Nada más. Ninguna cifra del oráculo cambia.
"""
import argparse
import datetime
import json
import pathlib
import sys

import numpy as np

from . import protocolo
from .audit import auditar, sesgo_minimo
from .backtest import backtest
from .constantes import JUEGOS, SEMILLA_AUDITORIA, SEMILLA_BACKTEST, SEMILLA_HGB
from .ev import premios_mayores, valor_esperado
from .ingest import cargar, procedencia, versiones
from .validate import era_56, validar, validar_era

# Claves que el oráculo no tiene. tests/test_paridad.py las excluye de la comparación.
NUEVAS_CLAVES = {
    "raiz": ("reproducibilidad", "validacion_era_56", "protocolo_global", "valor_esperado_medido"),
    "hoja": ("q_BH_global",),
}


def _salida_robusta():
    """Que el informe no muera por la codificacion de la consola.

    El resumen imprime 'Δ', '≈' y '–', que no existen en las páginas de códigos ANSI de Windows
    (cp1252, cp850…). Cuando la salida va a una tubería o a un fichero, Python usa la codificación
    local y esos caracteres lanzan UnicodeEncodeError **a mitad del informe**, después de haber
    gastado el minuto de cómputo. En una consola de verdad no pasa, porque Windows usa un escritor
    UTF-16 aparte: de ahí que el fallo aparezca solo al redirigir, y que pueda pasar inadvertido
    durante mucho tiempo.

    Redirigido se pasa a UTF-8, que es lo que espera quien consume la salida. En consola se respeta
    su codificación y solo se añade errors="replace", para degradar a '?' en vez de reventar.
    """
    for flujo in (sys.stdout, sys.stderr):
        try:
            if flujo.isatty():
                flujo.reconfigure(errors="replace")
            else:
                flujo.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001 - un flujo sin reconfigure no debe tumbar el informe
            pass


def _valor_esperado_medido(juegos, popularidad):
    """El valor esperado con los premios menores MEDIDOS, no con la constante escrita a mano.

    `ev.valor_esperado` usa por defecto `{"Melate": 4.38, "Revancha": 2.10, "Revanchita": 0.0}`,
    que viene de las tablas de los sorteos 4271/4272. **Ese defecto no se toca**: el oráculo llama
    a `valor_esperado(juegos)` sin argumento y cualquier cambio rompería la paridad, que es
    bloqueante. Lo medido entra aquí, en una clave aparte y declarada.

    `popularidad` es la ruta del reporte de `melate.popularity`. Sin ella, esta clave dice que no
    hay medición y por qué — que es mejor que no estar, porque así se ve que falta.
    """
    if not popularidad:
        return {"disponible": False,
                "motivo": "sin --popularidad: el EV de arriba usa la constante escrita a mano, "
                          "que viene de las tablas 4271/4272 y caduca. "
                          "Mídela con `python -m melate.popularity`."}
    with open(popularidad, encoding="utf-8") as f:
        pop = json.load(f)

    # La mediana, no la media: el estimador por bolsa es estable pero un sorteo con una categoría
    # de pocos ganadores todavía puede tirar de la media.
    menores, procedencia_menores = {}, {}
    for juego in JUEGOS:
        r = (pop.get("juegos") or {}).get(juego)
        if juego == "Revanchita":
            # Estructural, no estimado: Revanchita solo paga 6 aciertos, así que no hay menores.
            menores[juego] = 0.0
            procedencia_menores[juego] = "0 por estructura del juego: solo paga 6 aciertos"
        elif r and r.get("menores_brutos_por_bolsa"):
            m = r["menores_brutos_por_bolsa"]
            menores[juego] = m["mediana"]
            procedencia_menores[juego] = (f"mediana de {m['n']} sorteos, estimador por bolsa, "
                                          f"cv {m['cv']:.3f}")
        else:
            return {"disponible": False, "motivo": f"el reporte de popularidad no trae {juego}"}

    out = valor_esperado(juegos, menores_brutos=menores)
    out["menores_brutos_usados"] = menores
    out["procedencia_menores"] = procedencia_menores
    out["ventana"] = pop.get("ventana")
    out["disponible"] = True
    out["nota"] = ("Esta es la clave con los premios menores medidos. La de arriba, "
                   "`valor_esperado_proximo`, conserva la constante del oráculo para que la "
                   "paridad siga siendo comparable.")
    return out


def construir(carpeta=None, sims=2000, popularidad=None):
    """El reporte completo, como dict. Separado de main() para que los tests no pasen por argparse."""
    _salida_robusta()
    rng = np.random.default_rng(SEMILLA_AUDITORIA)

    crudos = {j: cargar(j, carpeta) for j in JUEGOS}
    reporte = {"validacion": {j: validar(j, d) for j, d in crudos.items()}}
    reporte["validacion_era_56"] = {j: validar_era(j, d) for j, d in crudos.items()}
    juegos = {j: era_56(j, d) for j, d in crudos.items()}

    print("== Datos (era 6/56)")
    for j, d in juegos.items():
        print(f"  {j:10s} {len(d):5d} sorteos  {int(d.CONCURSO.min())}–{int(d.CONCURSO.max())}  fuente: {crudos[j].attrs['fuente']}")

    print("== Auditoría de aleatoriedad (Monte Carlo, p de dos colas)")
    reporte["auditoria"] = auditar(juegos, sims, rng)
    for j, r in reporte["auditoria"].items():
        print(f"  {j:10s} chi2={r['chi2_corr']['obs']:.1f} (p={r['chi2_corr']['p_dos_colas']:.2f})  "
              f"max={r['max_count']['obs']:.0f} (p={r['max_count']['p_dos_colas']:.3f})  "
              f"repetidos={r['mean_overlap']['obs']:.3f} (p={r['mean_overlap']['p_dos_colas']:.2f})")

    reporte["poder"] = {j: {"sorteos": len(d), "sesgo_detectable_1_esfera": round(sesgo_minimo(len(d), 0.05), 3),
                            "sesgo_detectable_56_esferas": round(sesgo_minimo(len(d), 0.05 / 56), 3)} for j, d in juegos.items()}

    print("== Backtest walk-forward (aciertos por boleto de 6; azar = 0.643)")
    reporte["backtest"] = {j: backtest(d) for j, d in juegos.items()}

    # Las dos familias del oráculo, y encima la global que pide la regla 3.
    protocolo.aplicar_familias(reporte["auditoria"], reporte["backtest"])
    reporte["protocolo_global"] = protocolo.aplicar_global(reporte["auditoria"], reporte["backtest"])

    for j, b in reporte["backtest"].items():
        print(f"  -- {j}: {b['sorteos_prueba']} sorteos de prueba desde el {b['primer_concurso_prueba']}")
        for s, v in b["estrategias"].items():
            print(f"     {s:38s} {v['media']:.4f}  Δ={v['delta']:+.4f}  p={v['p']:.3f}  "
                  f"q={v.get('q_BH', '-')}  q_global={v.get('q_BH_global', '-')}")

    print("== Premios mayores (bajas de BOLSA)")
    reporte["premios_mayores"] = {}
    for j, d in juegos.items():
        g, errores = premios_mayores(j, d)
        reporte["premios_mayores"][j] = {"ganados": len(g), "sorteos": len(d), "errores_de_bolsa": errores,
                                         "mayores": g.sort_values("bolsa_en_juego", ascending=False).head(5).astype(str).values.tolist()}
        print(f"  {j:10s} {len(g)} premios mayores en {len(d)} sorteos (1 cada {len(d) / max(1, len(g)):.0f})")

    reporte["valor_esperado_proximo"] = valor_esperado(juegos)
    print("== Valor esperado del próximo sorteo (supuestos en el JSON)")
    for j in JUEGOS:
        v = reporte["valor_esperado_proximo"][j]
        print(f"  {j:10s} sorteo {v['proximo_sorteo']}: bolsa {v['bolsa_bruta'] / 1e6:.1f} M -> EV ${v['EV']:.2f} de ${v['precio']} "
              f"({v['rendimiento']:+.0%}); equilibrio ≈ {v['bolsa_de_equilibrio'] / 1e6:.0f} M")

    reporte["valor_esperado_medido"] = _valor_esperado_medido(juegos, popularidad)
    vm = reporte["valor_esperado_medido"]
    if vm.get("disponible"):
        print("== Valor esperado con los premios menores MEDIDOS (ventana "
              f"{vm['ventana'][0]}-{vm['ventana'][1]})")
        for j in JUEGOS:
            v, base = vm[j], reporte["valor_esperado_proximo"][j]
            print(f"  {j:10s} EV ${v['EV']:.2f} ({v['rendimiento']:+.1%})  "
                  f"contra ${base['EV']:.2f} ({base['rendimiento']:+.1%}) con la constante "
                  f"escrita a mano; menores {vm['menores_brutos_usados'][j]:.4f}")

    reporte["reproducibilidad"] = {
        "corrida_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "datos": procedencia(crudos),
        "semillas": {"auditoria": SEMILLA_AUDITORIA, "backtest": SEMILLA_BACKTEST, "hgb": SEMILLA_HGB},
        "simulaciones": sims,
        "versiones": versiones(),
    }

    g = reporte["protocolo_global"]
    print(f"== Protocolo: {g['pruebas']} pruebas en una sola familia -> {g['veredicto'].upper()} "
          f"(q mínima {g['q_minima']})")
    return reporte


def main(argv=None):
    ap = argparse.ArgumentParser(description="Informe de auditoría, backtest y valor esperado.")
    ap.add_argument("--datos", help="carpeta con Melate.csv, Revancha.csv y Revanchita.csv (si no, descarga del oficial)")
    ap.add_argument("--sims", type=int, default=2000)
    ap.add_argument("--salida", default="reportes/informe.json")
    ap.add_argument("--popularidad", help="reporte de `melate.popularity`, para el EV con los "
                                          "premios menores medidos en vez de la constante")
    a = ap.parse_args(argv)

    reporte = construir(a.datos, a.sims, a.popularidad)
    salida = pathlib.Path(a.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)   # en un clon nuevo reportes/ no existe
    with open(salida, "w", encoding="utf-8") as f:
        json.dump(reporte, f, ensure_ascii=False, indent=1, default=str)
    print(f"\nReporte completo en {salida}")
    return reporte


if __name__ == "__main__":
    main()
