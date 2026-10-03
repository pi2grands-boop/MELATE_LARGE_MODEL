# El mapa del sistema: qué módulo responde a qué pregunta

- **Fecha/hora:** 2026-10-03 00:13
- **Área:** Mapa · **Acción:** Añadir
- **Chat / página:** sesión de arranque · emitido al cerrar la Fase 1
- **Archivos afectados:** `baseline_auditoria.py`, `src/melate/*.py`, `tests/*.py`

## Qué se hizo

El proyecto pasa de dos ficheros a una estructura con dueños claros. Este es el mapa para quien
llega y no sabe por dónde entrar.

### La pieza que manda: hay dos programas y dan lo mismo

```
baseline_auditoria.py          el ORÁCULO. 322 líneas, un fichero, intacto desde el día uno.
                               NO se modifica nunca.
        ║
        ║  tests/test_paridad.py exige JSON idéntico, tolerancia cero
        ║
src/melate/  +  informe.py     DONDE SE TRABAJA. Mismo reporte, más tres claves declaradas.
```

Esta es la decisión estructural de la que dependen todas las demás. El oráculo existe para que
cualquier refactor sea **demostrable** y no una cuestión de fe: mientras esté intacto y la paridad en
verde, se puede reorganizar lo que haga falta. Si alguien lo modifica, el proyecto pierde su única
referencia y no hay forma de recuperarla.

### Qué pregunta responde cada módulo

| Pregunta | Módulo |
|---|---|
| ¿Cuánto vale un boleto? ¿Cuántas veces se ha ganado el mayor? | `ev.py` |
| ¿Es limpia la urna? ¿Qué sesgo podríamos detectar? | `audit.py` |
| ¿Alguna estrategia bate al azar? | `backtest.py` |
| ¿Me puedo creer ese resultado? | `protocolo.py` |
| ¿De dónde salen los datos y cuál es su hash? | `ingest.py` |
| ¿Cumplen los datos las 7 reglas del contrato? | `validate.py` |
| ¿Cuánto vale C(56,6), un boleto, o un acierto al azar? | `constantes.py` |
| Quiero el informe entero | `informe.py` → `python -m melate.informe` |

### El flujo de una corrida

```
ingest.cargar(juego, carpeta)        solo del oficial; deja sha256 y fuente en attrs
        ↓
validate.validar / validar_era       las 9 comprobaciones, en dos vistas
        ↓
validate.era_56                      CONCURSO >= 2089 (Revanchita >= 2371)
        ↓
   ┌────┴─────────────────┬──────────────────────┐
audit.auditar       backtest.backtest        ev.premios_mayores
(Monte Carlo,       (walk-forward,           ev.valor_esperado
 rng compartido      trng por juego)
 entre juegos)
   └────┬─────────────────┴──────────────────────┘
        ↓
protocolo.aplicar_familias  +  aplicar_global      15 + 21 = 36 pruebas
        ↓
informe: JSON + resumen en español + veredicto
```

### Los dos sitios donde el orden importa y no es estilo

1. **`audit.auditar` comparte un único `rng` entre los tres juegos**, en el orden de `JUEGOS`.
   Cambiar el orden de iteración, o paralelizar, cambia todos los p-valores de la auditoría.
2. **`backtest.backtest` crea su propio `trng` por juego**, pero dentro del bucle el orden de las 8
   asignaciones del diccionario `elec` fija qué número saca. Reordenarlo cambia los resultados de
   todas las estrategias posteriores.

Los dos llevan comentario en el código, y `tests/test_paridad.py` es lo que los vigila.

### Qué protege cada fichero de test

| Test | Qué impide | ¿Caduca? |
|---|---|---|
| `test_sin_fuga.py` | Que el proyecto se engañe con una fuga temporal | **No.** No depende de ninguna cifra |
| `test_paridad.py` | Que un refactor mueva una cifra en silencio | No, mientras exista el oráculo |
| `test_reglas_datos.py` | Que entren datos malos. Es el que detectó el error del espejo | Las cifras, al cambiar el snapshot |
| `test_linea_base.py` | Que el `CLAUDE.md` y el código se desincronicen | Sí, con datos o versiones nuevas |

### Lo que todavía no existe

`popularity.py` (Fase 3), `portfolio.py` (Fase 3), `lab.py` y `prereg/` (Fase 2),
`app/streamlit_app.py` y `melate.duckdb` (Fase 4). No se crearon vacíos: ficheros sin contenido para
parecerse a un diagrama son ruido.

## Por qué

Un fichero de 322 líneas que hace seis cosas no se puede extender sin miedo, y las fases 2 a 4
añaden preregistro, popularidad, cartera y una app. Sin piezas separadas, cada añadido toca el mismo
fichero y cualquier cambio puede mover una cifra publicada sin que nadie se entere.

## Impacto en seguridad / conexiones / datos

- **Seguridad:** `ingest.py` es el único módulo que abre conexiones, y solo al oficial.
- **Conexiones:** ver `Conexiones/Añadir/` del mismo cierre.
- **Datos:** ver `Estructura_Datos/Modificar/` y `Almacenamiento/Añadir/` del mismo cierre.

## Cómo verificar / revertir

```powershell
.venv\Scripts\python.exe -m melate.informe --datos .\data\raw\2026-10-02 --salida .\reportes\x.json
.venv\Scripts\python.exe -m pytest tests -q        # 52 en verde
```

**Revertir:** borrar `src/`, `tests/` y `pyproject.toml`. `baseline_auditoria.py` sigue funcionando
solo, porque nunca dependió de nada de esto — que es justamente para lo que está.

Relacionado: `Fases/2026-10-02_arranque/Cambios/2026-10-03_00-03_s1-paquete-src-melate.md`,
`Fases/2026-10-02_arranque/Cambios/2026-10-03_00-03_s1-tests.md`,
`Estructura_Carpetas/Añadir/2026-10-03_00-13_s1-arbol-del-proyecto.md`
