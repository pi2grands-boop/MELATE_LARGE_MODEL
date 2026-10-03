# Cierre de la fase protocolo

- **Fecha/hora:** 2026-10-03 01:35
- **Abierta el:** 2026-10-03 · **Duración:** una sesión, seguida de la Fase 1

La Fase 1 dejó el proyecto capaz de medir y de reproducir lo que mide. Esta le da lo que le faltaba
para poder **afirmar** algo — y, sobre todo, para no poder afirmarlo cuando no toca.

## Criterio de terminado — cumplido

| Criterio del `00_ALCANCE.md` | Evidencia |
|---|---|
| 1 · Pendientes heredados ejecutados y lo que encuentren, corregido | ✅ 3 ejecutados, 1 bug encontrado y corregido con test, 1 parcial, 3 que no dependen de mí |
| 2 · `melate.lab --prereg` corre y emite un veredicto razonado | ✅ 5 condiciones, cada una con su motivo en texto |
| 3 · El veredicto de hoy es "sin ventaja demostrada" por holdout vacío | ✅ 0 de 5, motivo *"holdout vacío: 0 sorteos posteriores al sello"* |
| 4 · Un preregistro alterado se rechaza, con test | ✅ Las 4 manipulaciones que importan, sobre el fichero real |
| 5 · `pytest tests` en verde con la paridad intacta | ✅ **92 pruebas**, 113 s |
| 6 · Bitácora íntegra y colador limpio | ✅ (ver abajo) |

## Lo que no estaba previsto

**La Fase 1 tenía 17 tests rotos y no lo sabía.** Al ejecutar su pendiente de clonar en limpio,
17 de 53 fallaban por una sola causa: el informe imprime `Δ`, `≈` y `–`, que no existen en cp1252, y
al redirigir la salida el proceso muere con `UnicodeEncodeError` a mitad del cómputo. En consola no
pasa. **El fallo dependía del shell desde el que se lanzara pytest**, así que la Fase 1 cerró con 52
en verde desde PowerShell mientras desde Bash fallaban 17.

Lo que lo salvó no fue el rigor del cierre —que fijó versiones, congeló datos y registró hashes—
sino haber dejado escrita la lista de pendientes y haberla ejecutado. Es el argumento más fuerte a
favor de esa práctica que ha dado el proyecto.

**La condición 2 no podía pasar nunca.** `lab.evaluar` no calculaba `q_BH_global`, lo leía de un campo
que nada rellenaba, así que `declara_ventaja` era incapaz de devolver "VENTAJA DEMOSTRADA" en ningún
escenario. Eso es peor que un falso negativo: un sistema que parece prudente y está roto es
indistinguible de uno prudente. Corregido calculando la `p` por juego y aplicando Benjamini-Hochberg
contra la familia **declarada** en el preregistro.

**Y hubo que re-sellar el preregistro**, que es justo lo que este módulo existe para impedir. Fue
legítimo porque el borrador nunca se había comiteado ni subido —`git log -- prereg/` sin salida— y
encontrar un defecto de formato mientras se escribe el evaluador es el momento correcto de
encontrarlo. Queda registrado con su evidencia para que nadie use el precedente: la pregunta que lo
autoriza no es "¿es un borrador?" sino "¿se puede demostrar que nadie lo ha visto?".

## Qué quedó fuera, y por qué

| Fuera | Por qué |
|---|---|
| Reinterpretar las cifras de la Fase 1 | Fueron exploratorias y lo seguirán siendo. Un preregistro no valida hacia atrás; eso es lo que impide |
| Estrategias nuevas | Agrandan la familia de pruebas: es una decisión con consecuencias estadísticas y lleva su documento |
| `popularity.py`, `portfolio.py`, la app | Fases 3 y 4 |
| Soporte de todas las estrategias en `lab._predecir` | Sin un preregistro que las use sería código sin consumidor. Levanta `ValueError` explícito |
| Tocar `baseline_auditoria.py`, que tiene el mismo fallo latente de codificación | Es el oráculo. Para los tests basta el arreglo del arnés; queda como limitación conocida del fichero heredado |

## Documentos emitidos a las áreas base

| Documento | Qué dice |
|---|---|
| `Protocolo_Estadistico/Añadir/…preregistro-y-las-cinco-condiciones.md` | Qué hace falta para poder afirmar algo, y qué error mata cada condición |
| `Almacenamiento/Añadir/…prereg-sellado.md` | `prereg/` como almacén inmutable que se autoverifica |
| `Estructura_Datos/Añadir/…formato-del-preregistro.md` | Los campos, el hash canónico y la forma del veredicto |
| `Mapa/Modificar/…entra-el-laboratorio.md` | La frontera entre explorar y juzgar |
| `Reproducibilidad/Modificar/…la-suite-ya-no-depende-del-shell.md` | El fallo de codificación y su arreglo |

## Bugs abiertos que se heredan

**Ninguno.** Los dos `Bugs/` del dossier están cerrados; los cuatro fallos encontrados entre ambos se
corrigieron en sus ciclos y todos tienen test.

## Pendiente de verificar en vivo

**Hereda la Fase 3.** Los dos primeros no son falta de esfuerzo: son el diseño funcionando.

1. **Una evaluación preregistrada de verdad.** El holdout no existirá hasta que se celebren sorteos
   posteriores al 2026-10-03T06:45Z. Hoy el camino con holdout está probado con fixtures de sello
   antiguo, que usan los mismos datos y el mismo código pero no son un preregistro legítimo.
2. **La condición 5 no es alcanzable en años.** Con 0.048 aciertos de efecto mínimo hacen falta del
   orden de 1 800 sorteos de holdout, unos 11 años a tres por semana. Está declarado en las notas del
   preregistro.
3. **El `SystemExit` de `_leer_bytes`.** Sigue sin ejercitarse: el sitio oficial no ha fallado. No se
   fuerza con un *mock*, que probaría el *mock*.
4. **Fuera de Windows**, todo lo que no sean finales de línea. Los comandos usan `.venv\Scripts\` y
   los scripts de verificación son PowerShell. El README no lo advierte y debería.
5. **La descripción del repositorio** y **el correo privado en GitHub**: los dos son de la cuenta del
   usuario.

## Integridad, comprobada

- `scripts/verificar-bitacora.ps1` — **0 hallazgos** en las 5 comprobaciones.
- `scripts/colador.ps1 -Autoprueba` — **0 coincidencias**, autoprueba 3/3.
- `pytest tests` — **92 en verde**, con `test_paridad.py` intacto.

## Una nota sobre lo que esta fase significa

El proyecto ahora tiene un mecanismo que le impide declarar una ventaja sin haber pasado cinco
condiciones a la vez, y el veredicto de hoy es que no hay ninguna. Eso puede leerse como un
resultado pobre. Es lo contrario: **es la primera vez que el proyecto puede decir "no lo sé" de una
forma que signifique algo.**

Antes de esta fase, "sin ventaja demostrada" era una frase en un documento. Ahora es la salida de un
programa que no puede decir otra cosa hasta que los datos lo obliguen.

Relacionado: `00_ALCANCE.md`, `Fases/2026-10-02_arranque/99_CIERRE.md`, y los cinco documentos
emitidos.
