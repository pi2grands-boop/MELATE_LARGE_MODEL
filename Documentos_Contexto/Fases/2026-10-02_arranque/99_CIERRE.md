# Cierre de la fase arranque

- **Fecha/hora:** 2026-10-03 00:13
- **Abierta el:** 2026-10-02 · **Duración:** una sesión, con un reinicio del equipo en medio

El proyecto empezó con dos ficheros: un contrato y un script de 322 líneas que no podía ejecutarse
porque faltaban cuatro dependencias. Cierra con un paquete, 52 tests, un snapshot congelado, una
bitácora y todo público en un repositorio.

## Criterio de terminado — cumplido

| Criterio del `00_ALCANCE.md` | Evidencia |
|---|---|
| 1 · El paquete produce un JSON idéntico al del oráculo | ✅ `tests/test_paridad.py` compara los dos recursivamente con tolerancia cero. En verde |
| 2 · `pytest tests` en verde, incluidas reglas de datos, línea base y no-fuga | ✅ **52 pruebas, 105 s.** Las 31 rápidas en 2.4 s |
| 3 · Cada cifra de "Línea base verificada" con su evidencia y su versión | ✅ `Reproducibilidad/Añadir/`, tabla de 12 filas. Versiones en `entorno/` |
| 4 · La receta de integridad de la bitácora no imprime nada | ✅ **19 documentos**, 0 hallazgos en las 5 comprobaciones de `scripts/verificar-bitacora.ps1` |
| 5 · El colador no imprime nada | ✅ 41 ficheros, 0 coincidencias, exit 0, autoprueba 3/3 |
| 6 · Ningún correo que no sea `users.noreply.github.com` | ⚠️ Los 8 commits de la fase, sí. El `Initial commit` de GitHub, no — ver abajo |

El portón del alcance —punto 4, reproducir la línea base— **no falló, pero tampoco salió limpio**, y
eso cambió la fase.

## Lo que no estaba previsto y acabó siendo lo más importante

**Dos de las doce cifras del contrato estaban mal.** La chi-cuadrada de Revancha y la regresión
logística de Revancha no reproducían. El diagnóstico aisló una causa raíz única: el espejo de GitHub
tiene mal el sexto número del sorteo 3827 de Revancha —dice 54 donde el oficial y melate-e.com dan
50— y la línea base del contrato se había calculado con el espejo.

Lo que esto significa, en orden de importancia:

1. **El código nunca estuvo mal.** Alimentando el script con el dato erróneo reproduce 42.03 y
   0.6861 al cuarto decimal. No hubo que bisecar ninguna versión de scikit-learn.
2. **La cifra más llamativa del proyecto estaba inflada por un error de un tercero.** La regresión
   logística en Revancha era la única estrategia que parecía acercarse a batir al azar. Con el dato
   correcto pasa de 0.6861 (p = 0.011) a 0.6839 (p = 0.0165).
3. **La conclusión no cambia:** q = 0.35 contra el 0.05 que exige el protocolo. Sigue siendo *sin
   ventaja demostrada*. Pero el hilo que más invitaba a seguir tirando era, en parte, una errata.
4. **Ninguna validación de una sola fuente podía encontrarlo.** La fila del espejo es formalmente
   válida: seis números distintos, en rango, ordenados. Pasa las nueve comprobaciones de `validar()`
   sin levantar una bandera. Solo lo encuentra la comparación entre fuentes — la regla 7 del
   contrato, que no estaba implementada en ninguna parte.

**Y el sorteo 4273 se celebró a mitad de la fase.** Se descubrió al comparar con el espejo, que ya lo
traía para Revancha y Revanchita pero no para Melate, mientras el oficial no había publicado
ninguno. Dos consecuencias: congelar el snapshot antes de la corrida fue lo que hizo posible todo el
diagnóstico, y el espejo quedó demostrado como fuente de carga poco fiable —cargar de él habría dado
los tres juegos terminando en sorteos distintos, rompiendo la comparación pareada del protocolo.

### Un error atrapado en el último momento

`.gitattributes`. Los CSV oficiales vienen con CRLF y `core.autocrlf` vale `true` en Windows: git
normalizaba los CSV a LF en el repositorio, así que **un clon en Linux o macOS habría recibido otros
bytes y otro SHA-256**, dejando inservible el hash publicado justo para quien lo necesita. Marcado
`data/raw/** -text` y verificado con `git hash-object` contra el blob del índice.

## Qué quedó fuera, y por qué

| Fuera | Por qué |
|---|---|
| `popularity.py`, `portfolio.py`, `lab.py`, `prereg/`, `app/` | Fases 2, 3 y 4. No se crearon vacíos: ficheros sin contenido para parecerse a un diagrama son ruido |
| Migración a pandas 3 | La 3.0 cambia la propagación de `df.attrs`, que el oráculo usa. Es un cambio aparte, con su propia paridad |
| Optimizar el backtest | Es el 85 % del coste y crece cuadráticamente, pero son 62 s hoy y ~110 s en cinco años. Optimizar lo que no duele introduce fallos a cambio de nada |
| Scraping de tablas de ganadores | Fase 3, con Scrapling. Su primer paso es el dictamen de términos del sitio |
| Reescribir el historial para quitar el correo del `Initial commit` | Ya era público antes de empezar, y borrarlo de un repositorio público no es real |

## Documentos emitidos a las áreas base

Diez. Solo el estado final; el proceso se queda en este dossier.

| Documento | Qué dice |
|---|---|
| `Mapa/Añadir/…mapa-del-sistema.md` | Qué módulo responde a qué pregunta, y los dos sitios donde el orden del RNG fija los resultados |
| `Estructura_Carpetas/Añadir/…arbol-del-proyecto.md` | El árbol, y por qué `constantes.py` y `protocolo.py` no estaban en el plano |
| `Estructura_Datos/Modificar/…forma-del-reporte-y-doble-validacion.md` | Las tres claves nuevas y las dos vistas de validación (174 avisos contra 3 reales) |
| `Almacenamiento/Añadir/…snapshots-congelados.md` | `data/raw/<fecha>/` inmutable, y por qué `.gitattributes` es parte del almacén |
| `Conexiones/Añadir/…fuentes-de-datos.md` | Una fuente de carga, una de validación, y por qué no se mezclan |
| `Reproducibilidad/Añadir/…linea-base-reproducida.md` | Las 12 cifras una por una, con las versiones que las producen |
| `Protocolo_Estadistico/Decisiones/…familias-benjamini-hochberg.md` | Dos familias más la global de 36, y cuál manda |
| `Seguridad/Decisiones/…bitacora-publica.md` | La Regla 0 invertida: qué se publica y qué no |
| `Rendimiento/Añadir/…coste-del-informe.md` | 72.6 s medidos por etapas; el backtest es el 85 % |
| `Despliegue/Añadir/…primer-push.md` | Los 8 commits, los 39 ficheros, el colador y cómo revertir |

## Bugs abiertos que se heredan

**Ninguno.** Los dos `Bugs/` del dossier están cerrados:

- `…_s1-porton-linea-base.md` — cerrado con sus cuatro pendientes ejecutados.
- `…_s1-review-refactor-y-tests.md` — cuatro fallos encontrados en el código nuevo, los cuatro
  corregidos en el mismo ciclo, tres con test propio. Ninguno se dejó a propósito.

## Pendiente de verificar en vivo

Lo que este entorno no permitió comprobar. **Hereda la Fase 2 y está en el `_MAPA.md`.**

1. **Clonar el repositorio en limpio y recalcular los tres SHA-256**, preferiblemente en Linux o
   macOS: es donde la conversión de finales de línea habría dado la cara. La comprobación con
   plumbing es sólida pero no es un clon real.
2. **Correr `pytest tests` en ese clon**, con un `.venv` nuevo desde `requirements.txt`. Es la única
   forma de saber que no falta nada de lo que se subió y que `pip install -e .` funciona de cero.
3. **El informe sin `--datos`**, contra la descarga en vivo. El camino de red de `_leer_bytes` no se
   ha ejercitado desde que se le quitó el respaldo al espejo. Toca con el 4273 ya publicado.
4. **El `SystemExit` de `_leer_bytes`** no se ha visto disparar: el oficial no falló en esta sesión.
5. **Nada se ha probado fuera de Windows.** Los comandos usan `.venv\Scripts\` y el colador es un
   `.ps1`.
6. **Cambiar la descripción del repositorio**, que sigue diciendo que la máquina predice resultados
   con más precisión. El usuario aprobó el texto nuevo; el cambio necesita la API de GitHub
   autenticada o su navegador.
7. **Activar *Keep my email addresses private*** en GitHub, para que no vuelva a pasar lo del
   `Initial commit`.

## Integridad de la bitácora, comprobada

**19 documentos, 0 hallazgos en las 5 comprobaciones.** Nombres en patrón, cabecera completa,
sección "Cómo verificar" presente, ningún `Bugs/` sin cerrar y ninguna referencia `.md` que no
resuelva. Se comprueba con `scripts/verificar-bitacora.ps1`.

Las dos primeras ejecuciones de ese script encontraron cosas, y conviene dejarlo escrito porque es la
lección repetida de esta fase:

- El `Bugs/` del refactor **estaba abierto**: decía "Bugs abiertos: ninguno" pero no tenía bloque de
  cierre, así que para cualquier comprobación automática seguía vivo.
- El propio verificador tenía un falso positivo masivo —resolvía las referencias solo contra la raíz
  de la bitácora— y de sus 39 hallazgos iniciales, 37 eran suyos. Las 8 que quedaron después de
  arreglarlo eran referencias reales pero ambiguas, y se completaron.

**Una herramienta de verificación que nadie ha verificado no es una garantía, es una opinión.** Le
pasó al colador, que se encontraba a sí mismo, y le pasó a este script. Los dos traen ahora su propia
comprobación: `colador.ps1 -Autoprueba` y las cinco secciones de este, que se leen una por una.

Relacionado: `00_ALCANCE.md`, y los diez documentos emitidos.
