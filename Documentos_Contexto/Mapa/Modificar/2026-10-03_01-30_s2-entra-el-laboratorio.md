# El mapa gana una pieza: `lab.py`, y una frontera

- **Fecha/hora:** 2026-10-03 01:30
- **Área:** Mapa · **Acción:** Modificar
- **Chat / página:** sesión de arranque · emitido al cerrar la Fase 2
- **Archivos afectados:** `src/melate/lab.py`, `src/melate/protocolo.py`

## Qué se hizo

El mapa de la Fase 1 (`Mapa/Añadir/2026-10-03_00-13_s1-mapa-del-sistema.md`) sigue siendo válido.
Lo que cambia es que ahora hay **dos modos de usar el proyecto**, y conviene no confundirlos.

```
EXPLORAR                                  JUZGAR
python -m melate.informe                  python -m melate.lab --prereg <fichero>

mide las 8 estrategias sobre todo          mide SOLO lo que el preregistro declara,
el histórico                               SOLO sobre su holdout

da p y q de 36 pruebas                     da el veredicto de las 5 condiciones

sirve para encontrar candidatos            sirve para decidir si uno vale

sus cifras NO pueden declarar ventaja      es el único que puede
```

**La frontera entre los dos es la que la Fase 1 no tenía.** Su informe midió, encontró un candidato
—regresión logística en Revancha— y no había nada que impidiera tratarlo como un hallazgo. Ahora el
informe explora y el laboratorio juzga, y lo segundo necesita un sello previo.

### El mapa actualizado

| Pregunta | Módulo |
|---|---|
| ¿Cuánto vale un boleto? ¿Cuántas veces se ha ganado el mayor? | `ev.py` |
| ¿Es limpia la urna? ¿Qué sesgo podríamos detectar? | `audit.py` |
| ¿Alguna estrategia **parece** batir al azar? | `backtest.py` → `informe.py` |
| ¿**Puedo afirmar** que una estrategia bate al azar? | `lab.py` |
| ¿Me puedo creer ese número? | `protocolo.py` |
| ¿De dónde salen los datos y cuál es su hash? | `ingest.py` |
| ¿Cumplen los datos las 7 reglas del contrato? | `validate.py` |
| ¿Cuánto vale C(56,6), un boleto, o un acierto al azar? | `constantes.py` |

`protocolo.py` crece y pasa a ser la pieza central del criterio: ahí viven
`benjamini_hochberg` —ahora con familia declarable—, las dos familias del oráculo, la global, y las
cinco funciones de condición más `declara_ventaja`.

### Lo que sigue sin existir

`popularity.py` y `portfolio.py` (Fase 3), `app/streamlit_app.py` y `melate.duckdb` (Fase 4).

## Por qué

Un lector que llega al proyecto y ve `informe.py` dando p-valores puede creer razonablemente que
eso es el resultado. No lo es: es la fase exploratoria, y sus cifras no bastan para afirmar nada.
Esa distinción no estaba en el mapa y es la aportación de esta fase.

## Impacto en seguridad / conexiones / datos

- **Seguridad:** sin cambios. `lab.py` no abre conexiones propias.
- **Conexiones:** `lab.py` depende de `ingest`, `validate`, `backtest` y `protocolo`. No añade
  fuentes.
- **Datos:** `prereg/` entra en el mapa como almacén.

## Cómo verificar / revertir

```powershell
.venv\Scripts\python.exe -m melate.informe --datos .\data\raw\2026-10-02 --salida .\reportes\x.json
.venv\Scripts\python.exe -m melate.lab --prereg .\prereg\2026-10-03_logistica-revancha.json --datos .\data\raw\2026-10-02
```

El primero da cifras exploratorias; el segundo, un veredicto. Que digan cosas distintas no es una
incoherencia: es la frontera.

**Revertir:** borrar `lab.py`, `prereg/` y el bloque de las 5 condiciones de `protocolo.py`. El mapa
vuelve al de la Fase 1, con un único modo de uso y nada que distinga explorar de afirmar.

Relacionado: `Mapa/Añadir/2026-10-03_00-13_s1-mapa-del-sistema.md`,
`Protocolo_Estadistico/Añadir/2026-10-03_01-30_s2-preregistro-y-las-cinco-condiciones.md`,
`Fases/2026-10-03_protocolo/Cambios/2026-10-03_01-25_s2-laboratorio-y-preregistro.md`
