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
    "raiz": ("reproducibilidad", "validacion_era_56", "protocolo_global"),
    "hoja": ("q_BH_global",),
}


def construir(carpeta=None, sims=2000):
    """El reporte completo, como dict. Separado de main() para que los tests no pasen por argparse."""
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
    a = ap.parse_args(argv)

    reporte = construir(a.datos, a.sims)
    salida = pathlib.Path(a.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)   # en un clon nuevo reportes/ no existe
    with open(salida, "w", encoding="utf-8") as f:
        json.dump(reporte, f, ensure_ascii=False, indent=1, default=str)
    print(f"\nReporte completo en {salida}")
    return reporte


if __name__ == "__main__":
    main()
