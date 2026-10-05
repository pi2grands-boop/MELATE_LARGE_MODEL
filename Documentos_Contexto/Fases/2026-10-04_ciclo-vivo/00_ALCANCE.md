# Fase: el ciclo vivo

- **Abierta:** 2026-10-04
- **Estado:** abierta. **El alcance está pendiente de la aprobación del usuario**, y lleva delante
  tres consultas (C1-C3) que se contestan antes que el código.
- **Nota del 2026-10-04, 18:59:** el usuario contestó. **C1, opción A, y C3, aprobadas; C2 sigue
  abierta**, a la espera de la explicación que pidió:
  `Fases/2026-10-04_ciclo-vivo/Decisiones/2026-10-04_18-59_s5-lo-que-decidio-el-usuario.md`. El resto
  de este documento queda como se escribió.
- **Nota del 2026-10-04, 20:10:** C2 cerrada (C2.2 y, por tanto, Revanchita con dos fuentes), y el
  usuario da la salida: «dale con C3». La decisión del ciclo, antes de su código:
  `Almacenamiento/Decisiones/2026-10-04_20-10_s5-el-ciclo-vivo.md`.
- **Nota del 2026-10-05, 10:37:** el trabajo está terminado, con el 4274 congelado y juzgado, y el
  cierre escrito en `Fases/2026-10-04_ciclo-vivo/99_CIERRE.md`. **La fase sigue abierta hasta que el
  usuario lo apruebe.**
- **Nota del 2026-10-05, 11:56: cerrada**, con la aprobación del usuario, que corrió la guía de pruebas
  y recorrió la app: *«Ya ejecuté todo, me gusta como se ve. Sube todo y la documentación también»*.
- **Decidida por:** usuario

Las fases 1 a 4 trabajaron sobre una foto fija: `data/raw/2026-10-02/`, hasta el sorteo 4272. Esta
fase hace que el proyecto incorpore los sorteos que van llegando **sin romper la reproducibilidad**:
cada sorteo nuevo entra en un snapshot nuevo, congelado por una orden y no a mano, validado con tres
fuentes antes de usarse; y sobre él, el primer veredicto que juzga el holdout, el valor esperado del
sorteo siguiente, la popularidad de los sorteos nuevos y la base de la app al día.

El riesgo no es técnico. Es doble. Primero, que una descarga en vivo se cuele como dato publicado. Y
segundo, que el primer sorteo del holdout parezca más de lo que es. El inventario encontró que esto
segundo es peor de lo que el proyecto creía: con el código de hoy, un solo sorteo puede producir un
«VENTAJA DEMOSTRADA» de verdad, no solo parecerlo (H1).

## Antes de empezar: lo que este alcance no puede decidir solo

Tres asuntos tocan el protocolo, el dictamen o código de otra fase. Van con su evidencia y una
recomendación, y **no se aplica nada antes de la respuesta del usuario**.

### C1 · El protocolo: con un sorteo de holdout se puede declarar ventaja

La evidencia completa está en H1 del inventario. En corto: el laboratorio real da **VENTAJA
DEMOSTRADA, 5 de 5**, con un holdout de un sorteo, en cuatro sorteos históricos (el último, el 4205,
de abril de 2026). Bajo el azar le pasa **1 de cada 303 veces** en la primera evaluación; evaluando con
cada sorteo nuevo, como hará el ciclo, **el 1,40 %** de las historias declara ventaja antes del sorteo
1 778 del holdout. La causa es que la condición 5 compara el delta con el mínimo detectable **del
propio holdout**: con un sorteo es 2,02 aciertos, y un sorteo con tres aciertos lo supera.

| Opción | Qué hace | Lo que cuesta |
|---|---|---|
| **A (recomendada)** | La condición 5 exige además que el holdout **pueda detectar el efecto declarado**: mínimo detectable(n) ≤ `efecto_minimo_declarado`. Con el 0,048 del sello, desde el sorteo **1 778** del holdout. Sin efecto declarado, como hoy | Una función de la Fase 2 (`protocolo.condicion_efecto_minimo`), su motivo, sus tests y una mutación. **Solo endurece.** No toca el preregistro, cuyo sello sigue verificando, ni el oráculo ni la paridad |
| B | Dejarlo como está, y que la app avise | La cabecera diría VENTAJA DEMOSTRADA con un sorteo, una vez de cada 303. Un aviso debajo no lo arregla |
| C | Cambiar la prueba: una exacta, o una corrección por mirar muchas veces | Es cambiar lo que el sello declara (`"prueba"`), y exigiría otro preregistro. Y no arregla la condición 5 |
| D | Una sexta condición, «holdout mínimo» | Lo mismo que A, pero rompe «las cinco condiciones» del `CLAUDE.md`, del almacén —que exige cinco— y de la app |

**Por qué A**, con números medidos: bajo el azar y evaluando con cada sorteo, A da **0 %** de falsos
«VENTAJA DEMOSTRADA» hasta el sorteo 1 778 del holdout —por construcción— y **0,095 %** en los diez
años siguientes; la regla de hoy, 1,40 % y 1,45 %. Y A hace que el código diga lo que el proyecto
lleva cuatro fases afirmando en nueve documentos, incluidas las notas del propio preregistro: *«el
mínimo detectable de 0.048 aciertos necesita del orden de 1.800 sorteos de holdout para ser
alcanzable»*.

**Tiene fecha.** Lo que la logística elegirá para el 4274 ya lo determinan los datos hasta el 4273,
que el oficial ya publica. El 4274 se sortea **hoy a las 22:00, hora de esta máquina**.
Decidir antes, o al menos sin mirar si la logística acertó, es lo que mantiene la regla a ciegas; por
eso nadie ha calculado esa elección. Si se aprueba, su documento va a `Protocolo_Estadistico/Decisiones/`,
como el del log-loss en la Fase 4, y existe antes del primer veredicto con holdout.

### C2 · El dictamen: la tercera fuente de Revanchita

Validar cada sorteo con tres fuentes es gratis en Melate y Revancha: la página de la tabla de
ganadores trae también los números. Para Revanchita, **el dictamen prohíbe pedir la página** (H2).

| Opción | Qué hace |
|---|---|
| a | Revanchita se valida con dos fuentes, oficial y espejo, y la procedencia de cada snapshot (`data/raw/<carpeta>/PROCEDENCIA.md`) lo dice |
| **b (recomendada)** | Se amplía el dictamen: **una página de Revanchita por sorteo nuevo**, solo para comparar los números, con la misma caché, el mismo ritmo y la misma identificación, y nunca el histórico. Antes, una sola petición para comprobar que esa página trae los números en la forma que el código sabe leer |

Recomiendo b porque la tercera fuente es lo que encontró el error de Revancha 3827, y cuesta unas tres
peticiones por semana. Pero *«Revanchita no se pide»* es regla del usuario, así que hasta su
respuesta vale a.

### C3 · Código de la Fase 4 que este alcance toca

1. **La app** (H3, H4): que enseñe el holdout como lo que es y que la orden para un veredicto nuevo
   sea el ciclo, no el laboratorio sin `--datos`. Lo pide el usuario; se lista para que conste.
2. **El almacén**: enlazar cada veredicto e informe con su snapshot **por SHA-256**, contra los
   `data/raw/*/SHA256.txt`, y que **un veredicto cuyos datos no sean un snapshot congelado del
   repositorio no pueda ser el vigente**. Hoy, uno sin `datos` cuenta si no hay otro, y uno sobre una
   descarga en vivo cuenta como cualquiera. Lo recomiendo: convierte *«nunca sobre una descarga en
   vivo que no quede guardada»* de costumbre en regla con test. Lo publicado no cambia de cara: el
   veredicto del 2026-10-03, el que no registra sus datos, pasaría a «no válido», y ya hoy no es el
   vigente.

## Qué entra

1. **La decisión del ciclo, antes del código**, en `Almacenamiento/Decisiones/`. Con la de C1, si se
   aprueba, son los únicos documentos que se escriben en un área base con la fase abierta, como el de
   `melate.duckdb` en la Fase 4. Contesta qué orden lo lanza; qué descarga y cuándo; en qué orden valida; cómo se nombra cada snapshot; qué pasa si el
   oficial falla a mitad (H7), si los juegos van desalineados, si el pasado cambió, si una fuente va
   atrasada o discrepa, si melate-e.com bloquea o sirve una página a medias (H5); que nunca se escribe
   encima de nada (H6); qué registra `data/raw/<carpeta>/PROCEDENCIA.md`; y cómo dice cada reporte
   de qué snapshot sale.
2. **`src/melate/ciclo.py`**, con su orden de terminal. Descarga, valida y congela; y sobre el
   snapshot nuevo, la popularidad de los sorteos nuevos, el informe (valor esperado del sorteo
   siguiente), el veredicto de cada preregistro sellado y la base. Cada paso se puede repetir solo. Nada
   queda a medias en disco y nada se sobrescribe.
3. **El primer snapshot real, congelado por el ciclo** y no a mano, con lo que sirva el oficial cuando
   el ciclo esté listo. Hoy sería el 4273, con el holdout todavía vacío; mañana, probablemente el
   4274.
4. **El primer veredicto con holdout**, sobre un snapshot con el 4274 y después de C1. Con uno o dos
   sorteos tiene que decir *sin ventaja demostrada*; con A, lo dice por construcción.
5. **El valor esperado del sorteo siguiente con su bolsa**, del snapshot nuevo, con la constante del
   oráculo y con los premios menores medidos. Cada cifra dice de qué snapshot sale. Las de la línea
   base del `CLAUDE.md` no cambian.
6. **La popularidad de los sorteos nuevos**, con el dictamen: solo sus páginas —dos por sorteo, Melate
   y Revancha, más la de Revanchita si C2 es b—, a 1 por segundo, con la caché permanente y la ventana
   declarada. Qué ventana, en la decisión; probablemente las 100 últimas, para que el EV medido siga
   siendo comparable con el publicado (4173-4272).
7. **La app**: el holdout como lo que es —en singular cuando es uno, frente a los 1 778 sorteos que la
   condición 5 necesita si C1 es A, y con los aciertos junto al delta—; la orden del ciclo en vez de
   «sin `--datos`»; y de qué snapshot sale cada cifra.
8. **Tests.** El ciclo contra un oficial falso servido en local, nunca contra el real: el camino
   bueno; el oficial que falla en el segundo juego; los juegos desalineados; el pasado cambiado; el
   espejo atrasado o en desacuerdo; melate-e.com en desacuerdo, bloqueando o sin la página; nada nuevo;
   la carpeta que ya existe. Y uno de punta a punta con bytes reales: se quita la línea del 4272 del
   snapshot del 2026-10-02 para fabricar un «snapshot anterior», se sirve el fichero real como «el
   oficial de hoy», y el snapshot que congele el ciclo **tiene que tener los SHA-256 publicados**, byte
   a byte. Para C1, los cuatro sorteos históricos tienen que dar *sin ventaja demostrada*.
   **La suite no gana ni una petición a la red**: sigue en 7 conexiones, medidas con el proxy al cerrar.
9. **`scripts/mutar.py`**: una mutación por cada protección nueva, y todas detectadas.
10. **En vivo**: el ciclo real por el proxy que solo apunta —conexiones por destino, y las páginas
    contadas por `Descargador.peticiones` y por la caché—, y la app en Edge sin interfaz, con clics de
    verdad.
11. **La bitácora**: este dossier, las decisiones, las reviews y el cierre; lo que se emite a las áreas
    base al cerrar; y la hoja de ruta. Al cerrar propondré, sin aplicarlo, lo que el `CLAUDE.md`
    tendría que decir del ciclo, como se hizo con la app en la Fase 4.

## Qué NO entra

- **`baseline_auditoria.py`, el defecto de `menores_brutos` de `src/melate/ev.py` y
  `tests/test_paridad.py`** no se tocan. Las cifras de la línea base del `CLAUDE.md` tampoco.
- **Ni estrategias ni pruebas nuevas**: la familia sigue en 36.
- **Ningún preregistro se toca, se vuelve a sellar o se sella nuevo.** Tampoco la prueba que declara el
  sello (C1, opción C).
- **El ciclo no se automatiza.** Es una orden de terminal que se lanza a mano. Una tarea programada
  pediría páginas a melate-e.com sin nadie delante, y el dictamen dice que si bloquean se para y se
  pregunta. Si se quiere, es otra decisión.
- **La app no lanza el ciclo**: ni descarga, ni recalcula, ni escribe.
- **De melate-e.com, solo los sorteos nuevos.** Ni el histórico, ni Revanchita sin C2 b.
- **Ningún test nuevo contra la red**, y ninguno contra el oficial real.
- **Lo ya publicado no se toca**: ni el snapshot del 2026-10-02, tampoco su
  `data/raw/2026-10-02/PROCEDENCIA.md`, ni los reportes viejos.
- Las ventas que supone el valor esperado (λ = 0,037): anotado en la Fase 3, no se toca.
- Actualizar Streamlit, migrar a pandas 3 y optimizar el backtest. Cada ciclo pagará los ~2 minutos
  del informe; se medirá y se dirá.
- Probar fuera de Windows.

## Criterio de terminado

1. **C1, C2 y C3 contestadas** por el usuario y registradas en `Decisiones/` de este dossier —C1,
   además, en `Protocolo_Estadistico/Decisiones/` si cambia el protocolo—, **antes** del primer
   veredicto con holdout.
2. La decisión del ciclo existe en `Almacenamiento/Decisiones/` y es **anterior** a `src/melate/ciclo.py`,
   por hora y por `git log`.
3. `python -m melate.ciclo` congela un snapshot real del oficial, byte a byte, con su `SHA256.txt` y
   su `data/raw/<carpeta>/PROCEDENCIA.md`, validado como diga la decisión; y el test de punta a punta
   reproduce los SHA-256 publicados del 2026-10-02.
4. Cada forma de fallar que enumere la decisión tiene su test, y en ninguna queda nada a medias en
   disco.
5. Sobre el snapshot nuevo: la popularidad de los sorteos nuevos, con las peticiones contadas y
   esperadas; el informe con el valor esperado del sorteo siguiente; el veredicto; y la base. Cada
   cifra dice de qué snapshot sale.
6. **Si el oficial trae el 4274 antes de cerrar:** el primer veredicto con holdout, *sin ventaja
   demostrada*, y la app enseñándolo como lo que es, vista en un navegador real con clics. **Si no:** el
   ciclo se cierra igual, el veredicto queda pendiente con su fecha, y el usuario decide si se espera.
7. `pytest tests` en verde con la paridad intacta; el bucle rápido, medido y publicado; y la suite
   completa, en las mismas 7 conexiones.
8. **El procedimiento de cierre:** cada número publicado, vuelto a medir; cada parámetro del que se
   diga que gobierna algo, con dos valores; los tests propios, mutados, y todas las mutaciones
   detectadas; y la pregunta de qué documento del índice permanente queda desactualizado, contestada
   documento por documento.
9. Bitácora íntegra, colador limpio y la hoja de ruta del `_MAPA.md` al día. **El cierre lo aprueba el
   usuario.**

## Estado de partida

`Inventario/2026-10-04_18-16_s0-estado-de-partida.md`, escrito antes de tocar nada.

## Qué emitirá a las áreas base al cerrar

| Área | Por qué |
|---|---|
| `Almacenamiento/Decisiones/` | El ciclo. **Se escribe antes del código**, no al cerrar |
| `Protocolo_Estadistico/Decisiones/` | C1, si el usuario cambia la condición 5. **Antes del veredicto** |
| `Mapa/Modificar/` | Un modo nuevo de usar el proyecto, incorporar sorteos, junto a explorar, juzgar, medir y mirar |
| `Almacenamiento/Modificar/` | Los snapshots los hace una orden, con su nombre y sus reglas |
| `Conexiones/Modificar/` | Quién sale de la máquina y cuándo: el ciclo pide el oficial, el espejo y melate-e.com |
| `Seguridad/Modificar/` | Tráfico saliente que se repite, a un tercero entre otros |
| `Reproducibilidad/Modificar/` | Cada cifra dice de qué snapshot sale, y el enlace por SHA-256 |
| `Protocolo_Estadistico/Añadir/` | El primer veredicto con holdout, y lo que significa y no significa |
| `Interconexion/Modificar/` | Cómo enseña la app el holdout, y qué orden enseña |
| `Estructura_Carpetas/Modificar/` | El módulo nuevo y las carpetas de snapshot |
| `Estructura_Datos/Modificar/` | La forma de `data/raw/<carpeta>/PROCEDENCIA.md`, y el enlace con el snapshot en la base (si C3) |
| `Rendimiento/Modificar/` | Lo que cuesta un ciclo, y el bucle rápido |
| `Despliegue/Añadir/` | La subida, después de la aprobación |

## Riesgos declarados

| Riesgo | Mitigación |
|---|---|
| Que el 4274 no llegue al oficial antes de cerrar | El ciclo se construye y se prueba igual; solo espera el veredicto con holdout, con fecha |
| Decidir C1 después de ver el resultado del 4274 | Decidir antes de las 22:00 de hoy, o sin mirar; nadie ha calculado la elección de la logística |
| El oficial falla, o sirve algo que no es el CSV, a mitad | No se congela nada y no queda nada en disco; un test con un servidor que falla a propósito |
| El oficial a medio actualizar, con un juego por delante | El ciclo se niega a congelar; el espejo ya lo hizo en la Fase 1 |
| El oficial corrige una fila vieja | El sufijo de bytes deja de cuadrar: el ciclo para y se pregunta |
| El espejo, atrasado o en desacuerdo | Un sorteo sin validar no se usa; un desacuerdo es un hallazgo que se investiga con melate-e.com |
| melate-e.com bloquea | `SitioBloqueado`: se para y se pregunta, como dice el dictamen; nada se congela a medio validar |
| Una página de melate-e.com pedida antes de tiempo (H5) | Solo se piden sorteos que ya están en el oficial; una página sin premios no se usa, y la decisión dice si entra en la caché |
| El repositorio crece con cada snapshot (~445 KB en disco) | Medir lo que git guarda de verdad —empaqueta las diferencias entre ficheros casi iguales— y escribirlo en la decisión |
| Un reporte escrito encima de otro (H6) | El ciclo nunca escribe sobre un fichero que existe; con test |
| Que la app haga parecer mucho un sorteo | H4 entra en el alcance, y se mira en un navegador, no solo con `AppTest` |
| El proxy ve conexiones, no rutas | Las páginas se cuentan con `Descargador.peticiones` y con los ficheros de la caché |

## Premisas de las que depende

- `baseline_auditoria.py` es el oráculo y no se modifica; `tests/test_paridad.py` es bloqueante.
- Los snapshots son inmutables byte a byte, y un sorteo nuevo es una carpeta nueva.
- El espejo de GitHub es solo validación cruzada, nunca fuente de carga.
- La familia de Benjamini-Hochberg es de 36, y no se añaden estrategias sin consultar.
- Un preregistro no se sobrescribe, no se sella en el pasado y alterarlo lo invalida; ningún veredicto
  se publica sin registrar sobre qué datos juzgó.
- El dictamen de melate-e.com, con la excepción de la C8 de la Fase 4.
- La app es local, no recalcula, no descarga ni escribe, y su cabecera solo sale de un veredicto del
  laboratorio con un sello que verifica.
- `pandas < 3` mientras el oráculo use `df.attrs`.
- La bitácora se publica: rutas relativas y nada personal.
