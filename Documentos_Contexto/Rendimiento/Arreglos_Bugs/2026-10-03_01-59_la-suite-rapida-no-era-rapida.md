# La suite "rápida" tardaba 30 s, no 2.4 s

- **Fecha/hora:** 2026-10-03 01:59
- **Área:** Rendimiento · **Acción:** Arreglos_Bugs
- **Chat / página:** sesión de arranque · auditoría retrospectiva
- **Archivos afectados:** `tests/test_paridad.py`, `Documentos_Contexto/_MAPA.md`, `README.md`

## Qué se hizo

El `_MAPA.md` anunciaba `~5 s` para `pytest -m "not lento and not red"`. Medido: **29.85 s**.

Causa, con los dos culpables cronometrados:

```
13.93s  test_paridad.py::test_el_informe_sobrevive_a_una_codificacion_hostil
13.77s  test_paridad.py::test_la_salida_se_crea_aunque_no_exista_la_carpeta
 0.29s  (el siguiente)
```

Los dos arrancan un informe completo en subproceso y **ninguno estaba marcado `lento`**. 28 de los
30 segundos. El `--sims 2` que llevan abarata la auditoría Monte Carlo, pero **no toca el backtest**,
que es el 85 % del coste de un informe.

El bucle del día a día que la Fase 1 diseñó para 2.4 s se había degradado **doce veces** sin que
nadie lo notara, porque nadie vuelve a cronometrar lo que ya midió una vez.

### El arreglo, sin perder cobertura

Marcar los dos como `lento` dejaría el fallo de codificación fuera del bucle rápido, y es justo el
tipo de fallo que conviene pillar temprano —tumbó 17 tests en la Fase 1—. Así que:

- Los dos tests de subproceso pasan a `lento`, que es su coste honesto.
- Se añade `test_salida_robusta_no_revienta_con_una_pagina_de_codigos_estrecha`, que cubre la misma
  causa raíz —un `TextIOWrapper` en cp1252 y un `Δ`— **sin subproceso y en milisegundos**.
- Verificado que el test nuevo tiene dientes: desactivando `_salida_robusta()`, falla; restaurándolo,
  pasa.

### Las cifras, corregidas

Sustituyen a las que publicaba `Rendimiento/Añadir/…coste-del-informe.md`, que eran de la Fase 1:

| Qué | Antes (Fase 1) | Ahora |
|---|---|---|
| `pytest -m "not lento and not red"` | 31 pruebas, 2.4 s | **72 pruebas, 2.5 s** |
| `pytest tests` | 52 pruebas, ~105 s | **100 pruebas, ~136 s** |
| `pytest -m lento` | — | 24 pruebas |
| `pytest -m red` | — | 4 pruebas |

El reparto por etapas del informe —backtest 85 %, auditoría 15 %, pico de 61 MB— **no cambia**: no se
tocó nada del cómputo.

## Por qué

Una suite de dos minutos deja de ejecutarse, y una suite que no se ejecuta no protege nada. Esa es
la razón por la que existen los *markers*, y el argumento está escrito en el documento de tests de
la Fase 1 — que es lo que hace más llamativo que se rompiera dos horas después.

El fallo de fondo no es el marcador que falta: es que **una cifra de rendimiento publicada envejece
y nadie la vuelve a medir**. Un número en un documento es una afirmación con fecha, y esta llevaba
dos horas siendo falsa por un factor de doce.

## Impacto en seguridad / conexiones / datos

Sin impacto en ninguno de los tres. Cambia qué tests corren en qué conjunto y dos cifras en dos
documentos.

**La cobertura no baja:** los dos tests marcados `lento` siguen corriendo en `pytest tests`, que es
lo que se ejecuta antes de cerrar cualquier cosa, y el mecanismo que protegen tiene ahora también
cobertura rápida.

## Cómo verificar / revertir

```powershell
Measure-Command { .venv\Scripts\python.exe -m pytest tests -m "not lento and not red" -q }   # ~2.5 s
.venv\Scripts\python.exe -m pytest tests -k pagina_de_codigos -v                             # el test nuevo
.venv\Scripts\python.exe -m pytest tests -m "not lento and not red" -q --durations=5         # nada por encima de 0.3 s
```

Que el test rápido de verdad protege: quitar el bloque `if flujo.isatty(): … else: …` de
`melate.informe._salida_robusta` y volver a correrlo. Tiene que fallar. Deshacer después.

**Revertir:** quitar los dos `@pytest.mark.lento` de `tests/test_paridad.py` y borrar el test rápido.
**No se recomienda:** el bucle del día a día vuelve a tardar 30 s, y en dos semanas nadie lo corre.

Relacionado: `Rendimiento/Añadir/2026-10-03_00-13_s1-coste-del-informe.md`,
`Protocolo_Estadistico/Bugs/2026-10-03_01-59_auditoria-retrospectiva-fases-1-y-2.md`,
`Fases/2026-10-02_arranque/Cambios/2026-10-03_00-03_s1-tests.md`
