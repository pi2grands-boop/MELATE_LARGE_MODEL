# Fase: la app local

- **Abierta:** 2026-10-04
- **Estado:** cerrada el 2026-10-04, con la aprobación del usuario: ver
  `Fases/2026-10-04_app-local/99_CIERRE.md`. El resto de este documento es el alcance tal como se
  escribió al abrirla.
- **Decidida por:** usuario

Las fases 1 a 3 dejaron el proyecto capaz de **medir** la urna, de **juzgar** una hipótesis
preregistrada y de **medir a los jugadores**. Todo eso se usa hoy desde la línea de órdenes y se lee
en JSON. Esta fase le pone una pantalla encima.

El riesgo de una pantalla no es técnico. Es que **borre la frontera** que las fases anteriores
construyeron: en la línea de órdenes, `melate.informe` y `melate.lab` son dos programas distintos y
nadie confunde uno con otro; en una pantalla, una `p = 0.0165` y un veredicto pueden acabar en la
misma tabla, con el mismo tipo de letra, y entonces la frontera solo existe en la documentación.
Esta fase existe para que la app **no pueda** hacer eso, y para demostrarlo con tests.

## Qué entra

1. **`melate.duckdb` y lo que lo genera.** La decisión de qué entra, qué lo genera y si se publica
   se escribe en `Almacenamiento/Decisiones/` **antes** del código que dependa de ella, por
   instrucción del usuario. Es la única pieza de esta fase que se escribe directamente en un área
   base mientras la fase está abierta, y es a propósito: es una frontera permanente, como la de la
   familia de Benjamini-Hochberg de la Fase 3.
2. **`app/streamlit_app.py`**, local y de solo lectura:
   - consume `melate.duckdb`, que a su vez solo contiene lo que ya está en `reportes/*.json` y
     `prereg/*.json`. **La app no recalcula, no descarga y no escribe.**
   - textos en español, y **"sin ventaja demostrada" visible en cada pantalla**;
   - el veredicto sale **solo** del laboratorio, y solo de un preregistro cuyo sello verifica.
3. **La red de la app:** `streamlit run` escuchando **solo en loopback** (`127.0.0.1`), nunca en
   `0.0.0.0`, y **sin telemetría**. Configurado en `.streamlit/config.toml` y vigilado además desde
   dentro de la app, que se niega a mostrar nada si la dirección de escucha no es de loopback.
4. **Tests** de todo lo anterior. Los que importan no son los de "la pantalla carga", sino los que
   intentan que la app mienta: un informe sintético con `q ≤ 0.05`, un veredicto con el sello
   alterado, una base desactualizada, el cómputo y la red convertidos en excepciones.
5. **Dependencias** `streamlit` y `duckdb` fijadas exactas, con las versiones que ya reproducen la
   línea base intactas (pandas 2.3.3 sobre todo), y su `pip freeze` nuevo en `entorno/`.
6. **Un hueco del laboratorio encontrado al leer, antes de escribir código:** el veredicto de
   `melate.lab` no registra el hash de los datos sobre los que juzgó (regla 6 del protocolo). La app
   necesita decir *sobre qué datos* se juzgó, así que se arregla aquí. Detalle en el inventario.
7. **Del pendiente heredado nº 8:** la mutación de tests pasa a ser una herramienta del
   repositorio, porque esta fase tiene que mutar sus propios tests de todas formas.

## Qué NO entra

- **`baseline_auditoria.py` no se toca**, ni el defecto de `menores_brutos` de `src/melate/ev.py`.
  `tests/test_paridad.py` sigue siendo bloqueante con tolerancia cero.
- **La app no recalcula nada.** Ni el backtest, ni la auditoría, ni una cartera nueva con otro
  presupuesto: eso son las órdenes de siempre, y la app enseña cuál ejecutar. Si algo tarda dos
  minutos en un backend, no va en una pantalla.
- **La app no dispara descargas.** No llama a `ingest.cargar` sin snapshot ni a
  `popularity.Descargador`, y un test lo convierte en excepción.
- **No se añaden estrategias** ni pruebas: la familia sigue siendo de 36.
- **No se toca ningún preregistro** ni se sella ninguno nuevo.
- **No se despliega la app en ningún sitio.** Ni `0.0.0.0`, ni Streamlit Community Cloud, ni
  Docker. Si algún día dejara de ser local, se reabre
  `Seguridad/Decisiones/2026-10-03_00-13_s1-bitacora-publica.md`, que lo pone como premisa.
- **Los sorteos crudos no entran en la base** (lo argumenta la decisión de `Almacenamiento/`).
- Migrar a pandas 3 y optimizar el backtest siguen fuera de toda fase.

## Criterio de terminado

1. La decisión de `Almacenamiento/Decisiones/` existe y es **anterior** a `src/melate/almacen.py`.
2. `python -m melate.almacen` construye `melate.duckdb` desde `reportes/` y `prereg/`, verifica
   los sellos y enlaza cada veredicto con su preregistro. Dos construcciones seguidas dan el mismo
   contenido.
3. La app abre la base en **solo lectura** y no recalcula ni sale a la red: hay tests que convierten
   el cómputo y la red en excepciones y recorren todas las pantallas.
4. "sin ventaja demostrada" aparece en **cada** pantalla, con un test por pantalla.
5. **La frontera, con test:** ninguna cifra exploratoria en la pantalla del veredicto; un `q ≤ 0.05`
   exploratorio sintético se presenta como candidato a preregistrar y nunca como ventaja; un
   veredicto cuyo sello no verifica no se usa.
6. `streamlit run` escucha solo en `127.0.0.1`, **comprobado en vivo** con la tabla de conexiones
   del sistema y con un intento de conexión desde la IP de la red local, que tiene que fallar.
7. `pytest tests` en verde con la paridad intacta, y el bucle rápido medido y publicado.
8. **El procedimiento de cierre:** cada número publicado, vuelto a medir; cada parámetro del que se
   diga que gobierna algo, con dos valores; los tests propios, mutados; y la pregunta de qué
   documento del índice permanente queda desactualizado, contestada documento por documento.
9. Bitácora íntegra, colador limpio, y la hoja de ruta del `_MAPA.md` al día. **El cierre lo
   aprueba el usuario.**

## Estado de partida

`Inventario/2026-10-04_00-36_s0-estado-de-partida.md`, escrito antes de tocar nada.

## Qué emitirá a las áreas base al cerrar

| Área | Por qué |
|---|---|
| `Almacenamiento/Decisiones/` | Qué entra en `melate.duckdb`. **Se escribe antes del código**, no al cerrar |
| `Mapa/Modificar/` | Entra un tercer modo de usar el proyecto, *mirar*, que no explora ni juzga |
| `Estructura_Carpetas/Modificar/` | `app/`, `.streamlit/`, el módulo nuevo y la base, que no se publica |
| `Estructura_Datos/Añadir/` | El esquema de `melate.duckdb` |
| `Interconexion/Añadir/` | Las pantallas y cómo se enlazan. Primer documento de esa área |
| `Red/Añadir/` | Qué se sirve, desde dónde y a quién. Primer documento de esa área |
| `Seguridad/Modificar/` | Un servidor local, la telemetría apagada y la superficie de dependencias |
| `Reproducibilidad/Arreglos_Bugs/` | El veredicto pasa a registrar los datos sobre los que juzga |
| `Rendimiento/Modificar/` | El bucle rápido y el coste de la base y de la app, medidos |
| `Despliegue/Añadir/` | La subida, después de la aprobación |

## Riesgos declarados

| Riesgo | Mitigación |
|---|---|
| Que una pantalla presente una cifra exploratoria como veredicto | El veredicto solo sale de `melate.lab` con sello verificado; tests con un `q ≤ 0.05` sintético y con un sello alterado |
| Streamlit escucha en todas las interfaces si no se le dice otra cosa | `.streamlit/config.toml`, guarda dentro de la app, y comprobación en vivo con `netstat` |
| Streamlit envía estadísticas de uso por defecto | `browser.gatherUsageStats = false`, y la guarda de la app también se niega si está activado |
| Una base desactualizada enseña cifras viejas como si fueran las de hoy | La base guarda el SHA-256 de cada fichero que leyó; la app los compara y avisa |
| Un binario se salta el colador, que solo lee texto | La base **no se publica**; el constructor guarda rutas relativas y un test busca rutas absolutas dentro de ella |
| Que `pip` arrastre pandas 3 con Streamlit (que admite `pandas<4`) | Se instala con las versiones fijadas como restricción; `requirements.txt` mantiene `pandas<3` |
| Texto de un JSON interpretado como Markdown (enlaces, imágenes, fórmulas con `$`) | Todo texto que venga de un fichero se escapa antes de pintarse; nunca `unsafe_allow_html` |
| Sin navegador en el entorno de trabajo, la maquetación no se ve | Las pantallas se prueban con `AppTest` y por HTTP; lo visual se declara pendiente si no se puede ver |
| El primer sorteo del holdout es el 4274, **hoy**: el veredicto cambiará pronto | La app dice siempre de qué corrida, con qué datos y en qué fecha es el veredicto que enseña. Nunca dice "hoy" |

## Premisas de las que depende

- `baseline_auditoria.py` es el oráculo y no se modifica.
- Para declarar ventaja manda `q_BH_global`, la familia de 36 pruebas; la popularidad está fuera.
- Un preregistro no se sobrescribe, no se sella en el pasado, y alterarlo lo invalida.
- El espejo de GitHub es solo validación cruzada.
- La bitácora se publica; rutas relativas, nada personal.
- `pandas < 3` mientras el oráculo use `df.attrs`.
- **La app es local**: es premisa de `Seguridad/Decisiones/2026-10-03_00-13_s1-bitacora-publica.md`.
