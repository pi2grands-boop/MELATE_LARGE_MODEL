# Fase: protocolo

- **Abierta:** 2026-10-03
- **Estado:** **cerrada el 2026-10-03** — ver `Fases/2026-10-03_protocolo/99_CIERRE.md`
- **Decidida por:** usuario

La Fase 1 dejó el proyecto capaz de **medir** y de **reproducir** lo que mide. Esta fase le da lo que
le falta para poder afirmar algo: un mecanismo que haga imposible declarar una ventaja que no ha
pasado el protocolo.

El punto de partida incómodo: el laboratorio de la Fase 1 encontró un resultado que parecía
prometedor —regresión logística en Revancha, p = 0.0165— y resultó estar en parte inflado por un
error de datos de un tercero. Con el dato correcto sigue sin pasar el umbral. **Esa es exactamente la
situación en la que un proyecto se autoengaña**, y la respuesta del `CLAUDE.md` es su regla 4:
preregistrar antes de evaluar, con un sello y un hash, y tomar como holdout solo los sorteos
posteriores a ese sello.

## Qué entra

1. **Los pendientes heredados de la Fase 1.** Se ejecutan primero: un ciclo no está cerrado mientras
   su lista de pendientes no se haya corrido, y la Fase 1 los dejó anotados para aquí.
2. **`prereg/*.json`** — el formato de preregistro, con su sello UTC, el hash de su propio contenido
   y el hash del snapshot de datos vigente al sellar. Y un preregistro real escrito: la regresión
   logística en Revancha, que es la única hipótesis que la fase exploratoria dejó sobre la mesa.
3. **`src/melate/lab.py`** — carga un preregistro, verifica su sello, calcula el holdout y evalúa
   **solo lo declarado**. Sin preregistro no evalúa: se niega.
4. **`protocolo.declara_ventaja()`** — las 5 condiciones de la regla 5 del `CLAUDE.md`, cada una con
   su veredicto y su motivo. Por defecto devuelve "sin ventaja demostrada".
5. **Tests** de todo lo anterior, incluido el caso que de verdad importa: que con el holdout vacío
   —que es la situación de hoy— el sistema **no pueda** declarar ventaja.

## Qué NO entra

- **`baseline_auditoria.py` no se toca.** Sigue siendo el oráculo. La paridad de la Fase 1 sigue
  siendo bloqueante.
- **No se reinterpretan las cifras de la Fase 1.** Aquellas fueron exploratorias y lo seguirán
  siendo; un preregistro no convierte retroactivamente en válido lo que se midió antes de sellarlo.
  Eso es precisamente lo que impide.
- **`popularity.py` y `portfolio.py`** son de la Fase 3. **La app** es de la Fase 4.
- **No se añaden estrategias nuevas.** Añadirlas agranda la familia de pruebas y es una decisión con
  consecuencias estadísticas; se hace cuando toque y con su documento.
- **No se declara ninguna ventaja.** Hoy es imposible por construcción, y así debe ser: el holdout de
  un sello de hoy está vacío.

## Criterio de terminado

1. Los pendientes heredados, ejecutados y documentados, con lo que hayan encontrado corregido.
2. `python -m melate.lab --prereg prereg/<fichero>.json` corre, verifica el sello y emite un
   veredicto con sus 5 condiciones razonadas.
3. **El veredicto de hoy es "sin ventaja demostrada" con motivo "holdout vacío".** Si algún día
   dijera otra cosa sin que hayan pasado sorteos, hay un fallo grave.
4. Modificar un byte de un preregistro sellado hace que `lab.py` se niegue a usarlo, y hay un test
   que lo comprueba.
5. `pytest tests` en verde, con la paridad de la Fase 1 intacta.
6. Bitácora íntegra y colador limpio.

## Estado de partida

El `99_CIERRE.md` de la Fase 1 y los diez documentos que emitió a las áreas base. No se escribe un
inventario nuevo: el estado heredado es el que esa fase dejó documentado, y hace horas, no meses.

Lo que sí se registra aquí es la ejecución de sus pendientes, en `Bugs/`, porque eso es trabajo de
verificación con hallazgos propios.

## Qué emitirá a las áreas base al cerrar

| Área | Por qué |
|---|---|
| `Protocolo_Estadistico/Añadir/` | El preregistro y las 5 condiciones: qué hace falta para poder afirmar algo |
| `Estructura_Datos/Añadir/` | El formato de `prereg/*.json` y su hash |
| `Almacenamiento/Añadir/` | `prereg/` como almacén de documentos sellados e inmutables |
| `Mapa/Modificar/` | `lab.py` entra en el mapa del sistema |
| `Reproducibilidad/Modificar/` | Si el camino de red o los hashes cambian al ejecutar los pendientes |
| `Despliegue/Añadir/` | La subida, si cambia código o datos |

## Riesgos declarados

| Riesgo | Mitigación |
|---|---|
| Que el preregistro se convierta en un trámite que se rellena después | El sello lleva el hash del propio contenido y el del snapshot vigente. Alterar un byte invalida el fichero, y `lab.py` se niega. Hay test |
| Que el holdout vacío se interprete como "aún no sabemos" y alguien afloje el criterio | El veredicto es "sin ventaja demostrada" con motivo explícito, no un "indeterminado". Un holdout vacío es información: significa que todavía no se ha jugado nada a esta carta |
| Que las 5 condiciones se implementen como un `and` opaco | Cada condición devuelve su propio veredicto y su motivo en texto. El reporte las enseña una por una |
| Que la condición de estabilidad sea vaga | El preregistro declara por adelantado la rejilla de hiperparámetros alternativos. Si no está declarada, no hay condición 3 que evaluar y el veredicto lo dice |
| Que el reloj de la máquina ensucie el sello | El sello es UTC explícito en el fichero, y el holdout se calcula contra la `FECHA` de los sorteos, no contra la hora de la corrida |

## Premisas de las que depende

- `baseline_auditoria.py` es el oráculo y no se modifica. La paridad sigue siendo bloqueante.
- El espejo es solo validación cruzada, nunca carga.
- **Para declarar ventaja manda `q_BH_global`**, la familia de 36 pruebas
  (`Protocolo_Estadistico/Decisiones/2026-10-03_00-13_s1-familias-benjamini-hochberg.md`). Esta fase
  lo implementa; si esa decisión se reabre, hay que volver aquí.
- La bitácora se publica y nada personal sale de la máquina.
- `pandas < 3` mientras el oráculo use `df.attrs`.
