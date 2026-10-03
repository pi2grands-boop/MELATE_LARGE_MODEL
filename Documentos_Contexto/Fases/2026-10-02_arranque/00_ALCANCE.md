# Fase: arranque

- **Abierta:** 2026-10-02
- **Estado:** abierta
- **Decidida por:** usuario

El proyecto arranca con dos ficheros y nada más: `CLAUDE.md`, que es el contrato, y
`baseline_auditoria.py`, que el contrato declara "la línea base probada: reprodúcela antes de cambiar
nada". No existe paquete, ni tests, ni bitácora, ni entorno capaz de ejecutar el script.

Esta fase convierte eso en un proyecto: levanta la bitácora, hace reproducible la línea base, y
traslada el script a un paquete sin cambiar un solo número.

## Qué entra

1. **La bitácora** — rejilla de 12 áreas × 6 acciones, este dossier, `REGLAS-DOCUMENTACION.md` con
   las 4 áreas opcionales declaradas y congeladas, y el inventario `s0` del estado heredado escrito
   antes de tocar nada.
2. **El entorno** — `.venv` local y `requirements.txt` con versiones fijadas. Sin Docker: las nueve
   dependencias tienen wheel precompilado para `cp313-win_amd64` o son Python puro, así que nada
   compila y un venv ya aísla.
3. **El snapshot congelado** — `data/raw/2026-10-02/` con los tres CSV oficiales tal cual llegaron,
   su SHA-256 y su procedencia. Sin esto, el primer sorteo nuevo hace que la línea base deje de
   reproducir y no haya forma de saber si el culpable es el código o los datos.
4. **El portón: reproducir la línea base** — correr `baseline_auditoria.py` contra el snapshot y
   comparar cifra por cifra contra la sección "Línea base verificada" del `CLAUDE.md`.
5. **El paquete `src/melate/`** — traslado literal de las funciones, sin mejoras de paso.
   `baseline_auditoria.py` **no se toca**: queda como oráculo.
6. **Tres añadidos al reporte**, cada uno con su documento: hash y semillas en el JSON (regla 6 del
   protocolo), la `q` de Benjamini-Hochberg sobre la familia global de 36 pruebas junto a la de las
   dos familias actuales, y la validación separada por era.
7. **Los tests** — reglas de datos, línea base, paridad numérica contra el oráculo, y no-fuga
   temporal.
8. **La publicación** — enlace con el repositorio público, `.gitignore`, `README.md`, identidad de
   git sin correo personal, y el colador antes de cada push.

## Qué NO entra

- **`baseline_auditoria.py` no se modifica.** Es el oráculo contra el que se valida el paquete. Si se
  toca, no hay con qué comparar.
- **`popularity.py`, `portfolio.py` y `lab.py` no se crean.** Aún no tienen contenido; crear ficheros
  vacíos para parecerse a la estructura sugerida es ruido.
- **No se migra a pandas 3.** La 3.0 cambia la propagación de `attrs`, que el script usa. La línea
  base se reproduce con `pandas>=2.3,<3` y la migración es un cambio aparte, con su documento.
- **No se instalan `duckdb`, `streamlit` ni `scrapling`.** Son de las fases 3 y 4.
- **No se descarga nada de `resultados.melate-e.com`.** La ingesta de tablas de ganadores es de la
  Fase 3, y su primer paso es el dictamen de términos del sitio.
- **No se corre ninguna evaluación nueva.** Sin `prereg/` sellado no se evalúa, y `prereg/` es de la
  Fase 2. Esta fase reproduce lo que ya existe; no busca ventaja.
- **No se reescribe el historial del remoto ni se toca su `LICENSE`.** El repositorio ya tiene un
  commit que no es nuestro y se respeta.

## Criterio de terminado

Verificable, punto por punto:

1. `python -m melate.informe --datos data/raw/2026-10-02` produce un JSON **idéntico** al de
   `baseline_auditoria.py --datos data/raw/2026-10-02`, salvo las claves nuevas declaradas en el
   punto 6 del alcance. Lo comprueba `tests/test_paridad.py`.
2. `pytest tests` sale en verde, incluidos los tests de las 7 reglas de datos, de la línea base y de
   no-fuga temporal.
3. Cada cifra de la sección "Línea base verificada" del `CLAUDE.md` tiene su línea de evidencia en el
   documento de `Reproducibilidad/`, con la versión de librería que la produce.
4. La receta de integridad de la bitácora no imprime nada: ningún nombre de fichero fuera de patrón,
   ningún `Bugs/` abierto, ningún enlace `Relacionado:` roto.
5. El colador no imprime nada: ninguna ruta absoluta de la máquina, ningún correo personal, en
   ningún fichero que se suba.
6. `git log --format='%ae'` no contiene ningún correo que no sea de la forma
   `users.noreply.github.com`.

Si el punto 1 no se cumple, la fase no se cierra. Si el portón del alcance punto 4 falla —la línea
base no reproduce—, la fase **se detiene ahí** y la discrepancia se documenta en `Bugs/`: un refactor
validado contra una línea base que no reproduce no vale nada.

## Estado de partida

`Inventario/2026-10-02_22-07_s0-estado-heredado.md` — escrito antes de crear el entorno, el snapshot
o el paquete. Recoge las funciones de `baseline_auditoria.py` con sus líneas, las cifras que el
`CLAUDE.md` declara verificadas, el entorno real de la máquina y la evidencia de datos comprobada
contra las fuentes oficiales el 2026-10-02.

## Qué emitirá a las áreas base al cerrar

Solo el estado final, nunca el proceso. El proceso se queda aquí.

| Área | Por qué |
|---|---|
| `Mapa/Añadir/` | Nace el mapa del sistema: qué módulo responde a qué pregunta |
| `Estructura_Carpetas/Añadir/` | Nace el árbol del proyecto, y dos módulos que no están en la estructura sugerida del `CLAUDE.md` |
| `Estructura_Datos/Modificar/` | La validación pasa a dar dos vistas (fichero completo y era 6/56), y el JSON de reporte gana claves |
| `Almacenamiento/Añadir/` | `data/raw/<fecha>/` como snapshot inmutable con su hash |
| `Conexiones/Añadir/` | Las dos fuentes HTTP, el fallback oficial → espejo, y el parseo por nombre de columna |
| `Reproducibilidad/Añadir/` | La reproducción de la línea base cifra por cifra, con las versiones que la consiguen |
| `Protocolo_Estadistico/Decisiones/` | La familia de Benjamini-Hochberg: dos familias + global, y cuál manda para declarar ventaja |
| `Seguridad/Decisiones/` | La inversión de la Regla 0: qué se publica y qué no, con el porqué del usuario |
| `Rendimiento/Añadir/` | Cuánto tarda cada etapa, medido |
| `Despliegue/Añadir/` | Un documento por subida: commit, ficheros, colador y `git revert` |

## Riesgos declarados

| Riesgo | Mitigación |
|---|---|
| La línea base no reproduce por versión de librería | Escalera de diagnóstico: las 6 estrategias no-ML dependen solo de numpy y los datos; la chi-cuadrada de numpy y scipy; la regresión logística y el gradient boosting de scikit-learn. El patrón de qué falla aísla la causa. Hay 9 versiones de sklearn con wheel cp313 sobre las que bisectar |
| Llega el sorteo 4273 a mitad de la fase | El snapshot congelado se hace **antes** de cualquier refactor, y todo corre con `--datos`. No hay copia de seguridad que hacer: los CSV oficiales son la fuente y el snapshot es su copia fechada |
| El refactor rompe la paridad por orden de consumo del RNG | `tests/test_paridad.py` es bloqueante. Los dos puntos donde el orden importa están documentados en el inventario `s0` |
| Fuga temporal introducida sin querer en el refactor | `tests/test_sin_fuga.py`, que no depende de que las cifras cuadren: permuta el futuro y exige que el pasado no cambie |
| Que algo personal acabe en un repositorio público | El colador es bloqueante antes de cada push, y las rutas relativas son contrato desde el primer documento, no un arreglo posterior. La identidad de git se configura **antes** del primer commit: después solo se quita reescribiendo el historial, y en un repo público ya clonado eso no se arregla del todo |
| El push falla por autenticación | `gh` no está instalado; el push usa Git Credential Manager, que abre el navegador la primera vez. Los commits quedan listos en local y el push es un paso aparte |

## Premisas de las que depende

- El `CLAUDE.md` es el contrato y su sección "Línea base verificada" es correcta. Comprobado
  parcialmente antes de abrir la fase: los recuentos de sorteos, los errores de `BOLSA` conocidos y
  el hueco de la pandemia cuadran exactamente con las fuentes oficiales al 2026-10-02. Las cifras
  estadísticas (chi-cuadrada, backtest, EV) se comprueban en el portón.
- El protocolo de evaluación del `CLAUDE.md` es no negociable: walk-forward, comparación contra la
  línea base exacta, Benjamini-Hochberg sobre todas las pruebas, preregistro antes de evaluar, y las
  5 condiciones para declarar ventaja.
- "No avanzar de fase sin que el usuario lo apruebe" (`CLAUDE.md`). Esta fase no empieza la Fase 2.
- La bitácora se publica (ver `REGLAS-DOCUMENTACION.md` §0). Si esa decisión se reabre, hay que
  volver aquí y revisar cada documento escrito bajo esta premisa.
