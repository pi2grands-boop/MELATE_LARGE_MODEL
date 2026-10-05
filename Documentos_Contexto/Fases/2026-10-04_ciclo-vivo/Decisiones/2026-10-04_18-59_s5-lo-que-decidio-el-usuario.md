# Lo que decidió el usuario sobre las consultas del alcance de la Fase 5

- **Fecha/hora:** 2026-10-04 18:59
- **Área:** Fases/2026-10-04_ciclo-vivo · **Acción:** Decisiones
- **Decidido por:** usuario, sobre las tres consultas de `Fases/2026-10-04_ciclo-vivo/00_ALCANCE.md`
- **Estado:** cerrada para C1 y C3. **C2 sigue abierta**: el usuario pidió una explicación a fondo
  antes de decidir, y está abajo
- **Nota del 2026-10-04, 20:10: C2 cerrada.** El usuario contestó «C 2.2» y «dale con C3». **C2.2,
  aprobada**: un testigo que discrepa para el ciclo; uno que falta hace esperar, y seguir sin él es
  explícito y queda escrito. **C2.1 se toma como la opción a**: el usuario había descartado la b por no
  viable, y la a es la que valía sin ampliar el dictamen; si no es así, se corrige. La regla, aplicada
  al diseño del ciclo, está en `Almacenamiento/Decisiones/2026-10-04_20-10_s5-el-ciclo-vivo.md`. El
  resto de este documento queda como se escribió.
- **Nota del 2026-10-04, 22:17: dos respuestas más, después de la review del ciclo.** **C4 · el bucle
  rápido**, que pasa de 13,8 a 25,0 s con los 30 tests rápidos del ciclo (B7 de
  `Fases/2026-10-04_ciclo-vivo/Bugs/2026-10-04_20-51_s5-review-ciclo.md`): se recomendó aceptarlo en
  vez de quitar vigilancia, y el usuario contestó «Si, mientras más mejor». **Aceptado.** **Esperar
  al 4274 antes de cerrar**: «Si, esperemos al 4274». La fase no se cierra hasta que el ciclo congele
  el 4274, emita el primer veredicto con holdout y ese veredicto se vea en la app.
- **Nota del 2026-10-05, 11:56: el cierre y la subida, aprobados.** Antes de las 10:52, el usuario pidió
  arreglar B15 —«Arregla eso que me dijiste primero»—, y se arregló. Después corrió él mismo la guía de
  pruebas y recorrió la app: *«Ya ejecuté todo, me gusta como se ve. Sube todo y la documentación
  también»*. **El texto del `CLAUDE.md` sigue sin decidir**: la propuesta del cierre no se ha aplicado.
- **Alcance:** `src/melate/protocolo.py` (C1); `app/streamlit_app.py` y `src/melate/almacen.py` (C3);
  la validación del ciclo de la Fase 5 (C2)

## Por qué hubo que preguntar

El inventario (`Fases/2026-10-04_ciclo-vivo/Inventario/2026-10-04_18-16_s0-estado-de-partida.md`)
dejó tres asuntos que tocaban el protocolo, el dictamen con melate-e.com y código de la Fase 4. Se
presentaron con su evidencia y **no se aplicó nada antes de la respuesta**.

| | Lo que se preguntó | Lo que contestó el usuario |
|---|---|---|
| C1 | Con un sorteo de holdout el laboratorio puede declarar ventaja: qué hacer con la condición 5 | «Opción A» |
| C2 | La tercera fuente de Revanchita: dos fuentes, o una página de Revanchita por sorteo nuevo | «Explícame a profundidad, porque no creo que sea viable a largo plazo» |
| C3 | Tocar la app y el almacén de la Fase 4 | «Ok» |

## C1 · Aprobada: la condición 5 exige un holdout capaz de detectar el efecto declarado

Tiene su documento en el índice permanente, porque cambia el protocolo:
`Protocolo_Estadistico/Decisiones/2026-10-04_18-58_s5-la-condicion-5-exige-un-holdout-capaz.md`.
Se decidió a las 18:58 hora local del 2026-10-04, **antes de que se sorteara el 4274** (22:00) y sin
que nadie calculara qué números elegiría la logística para ese sorteo.

## C3 · Aprobada: el código de la Fase 4 que este alcance toca

1. **La app** enseña el holdout como lo que es, y la orden para un veredicto nuevo es el ciclo y no
   el laboratorio sin `--datos`.
2. **El almacén** enlaza cada veredicto e informe con su snapshot por SHA-256, contra los
   `data/raw/*/SHA256.txt`, y **un veredicto cuyos datos no son un snapshot congelado del repositorio
   no puede ser el vigente**.

## C2 · Pendiente: la explicación que pidió el usuario

**Tiene razón, y no solo para Revanchita.** La recomendación b —una página de Revanchita por sorteo
nuevo— se retira. Y la pregunta destapa un problema mayor: tal como lo escribió el alcance, *«cada
sorteo nuevo se valida con las tres fuentes antes de usarse»*, el ciclo tampoco sería viable a largo
plazo en Melate y Revancha.

### 1 · El horizonte no es una fase: son unos once años

Con C1, el preregistro no puede juzgar nada antes de 1 778 sorteos de holdout. El ciclo tiene que
funcionar del orden de 1 800 veces, durante más de una década. Todo lo que el ciclo necesite en cada
sorteo lo va a necesitar 1 800 veces.

### 2 · Qué caza cada comprobación, y qué ha cazado de verdad

| Error posible | Casos reales | Lo detecta | ¿Hace falta un tercero? |
|---|---|---|---|
| Un sorteo mal transcrito en el oficial | **Ninguno conocido**: 0 en las 6 276 filas comparadas con el espejo, 0 en los 200 sorteos comparados con melate-e.com | solo un testigo independiente | **sí** |
| Una BOLSA mal en el oficial | 2120, 2142 y 2234 a cero; Revancha 3221 fuera de secuencia | `validar` y el filtro de `ev.premios_mayores` | no |
| Una descarga rota: página de error, fichero truncado | ninguno, y el `SystemExit` de `ingest._leer_bytes` nunca se ha ejercitado | la cabecera `CONCURSO`, el parseo y el sufijo de bytes | no |
| El pasado reescrito | ninguno | el sufijo de bytes del inventario | no |
| Juegos desalineados | el espejo, el 2026-10-02 | que los tres juegos terminen en el mismo sorteo | no |
| Un error del propio testigo | espejo 3827 (54 por 50) y espejo 3380 (la BOLSA) | — | es el testigo el que falla |

**Todos los errores que se han visto en el oficial los cazaron comprobaciones que no dependen de
nadie.** Los testigos, hasta hoy, solo han encontrado errores suyos. No son inútiles: son la única
defensa contra la primera fila de la tabla, que no ha pasado nunca pero sería invisible si pasara.
Es la lección de Revancha 3827: una fila mal transcrita es formalmente válida. Con 0 casos en 6 276
filas, la tasa de esos errores en el oficial está por debajo del 0,05 % por fila con un 95 % de
confianza (regla del tres). Eso es menos de uno cada 13 años en Revanchita y menos de uno cada 4,5
años en los tres juegos juntos.

### 3 · Por qué la opción b no es viable a largo plazo

1. **melate-e.com es insustituible para lo que de verdad aporta.** Las tablas de ganadores no tienen
   otra fuente legible por máquina: la mascarilla oficial es un PDF en imagen
   (`Fases/2026-10-03_popularidad/Decisiones/2026-10-03_02-40_s3-dictamen-terminos-melate-e.md`).
   Cada petición que no sea imprescindible gasta la tolerancia del único sitio que da ese dato. Si
   bloquearan al proyecto por las de Revanchita, se perdería también la popularidad de Melate y
   Revancha. La opción b arriesga el uso valioso a cambio de uno marginal.
2. **Cada testigo es un contrato que mantener durante una década**: una página de Revanchita que
   nunca se ha leído para sacar números, su parser y sus tests. El sitio corre PHP 7.3.33, sin soporte
   desde diciembre de 2021. Es un sitio pequeño que puede cambiar de plataforma o desaparecer
   cualquier año.
3. **Lo que añade es poco.** En Revanchita, el oficial y el espejo ya detectan un desacuerdo. La
   tercera fuente solo hace falta para saber cuál de los dos se equivoca, y la regla 7 del
   `CLAUDE.md` dice que eso se investiga, no lo decide un programa. Un desempate que quizá haga falta
   una vez por década se puede hacer a mano, con un navegador o con una sola petición que autorice el
   usuario.
4. **El dictamen existe para esto.** Pide ventanas acotadas y declaradas. El ciclo ya convierte
   melate-e.com en una relación recurrente, dos páginas por sorteo; ampliarla sin necesidad va contra
   su espíritu.

### 4 · El problema mayor: «tres o nada» deja el ciclo en manos del testigo más débil

El espejo es el repositorio de GitHub de un particular, sin ningún compromiso. Ya se ha desalineado
entre juegos y tiene un error en los números y otro en la BOLSA. melate-e.com no tiene términos ni
contacto. En once años, lo prudente es diseñar suponiendo que alguno de los dos fallará; no hay forma
honesta de ponerle una probabilidad. Con «tres o nada», el día que un testigo muera el ciclo se
para, y el holdout se congela con él.

### 5 · Lo que se propone, en dos partes

- **C2.1 · Revanchita: la opción a.** Oficial y espejo, automático. La tercera fuente, solo para
  investigar un desacuerdo, a mano o con una petición única que autorice el usuario. El dictamen no se
  toca.
- **C2.2 · Una regla para los testigos, en los tres juegos.** El oficial es la fuente; el espejo y
  melate-e.com son testigos.
  - **Un testigo que contradice al oficial para el ciclo.** Es un hallazgo, se investiga y nunca se
    resuelve eligiendo un valor (regla 7).
  - **Un testigo que falta** —atrasado, caído, bloqueado o desaparecido— no contradice nada, pero
    tampoco pasa en silencio. El ciclo espera y dice por qué. Para congelar sin ese testigo, el
    usuario lo pide de forma explícita con una opción de la orden, y la procedencia del snapshot
    escribe qué testigos confirmaron cada sorteo nuevo. Si un testigo muere para siempre, se retira
    con una decisión.
  - **Lo que no depende de nadie se exige siempre**: el sufijo de bytes, `validar_era`, los tres
    juegos alineados y la BOLSA plausible.
  - **La salud de los testigos se ve.** Cada corrida dice hasta qué sorteo confirmó cada uno. Y los
    tests `red` de la suite completa, que piden el espejo y una página de melate-e.com, ya son la
    alarma: si un testigo muere, fallan, y es lo que tienen que hacer.

**Recomendación:** C2.1 = a; C2.2 = la regla de arriba, «un desacuerdo para; una ausencia espera, y
seguir sin un testigo es explícito y queda escrito».

## Cómo verificar

Las cifras de C2 salen de documentos ya publicados:

- 6 276 filas comparadas con el espejo y sus dos diferencias, ninguna del oficial:
  `Conexiones/Añadir/2026-10-03_00-13_s1-fuentes-de-datos.md`, «Estado comprobado del espejo».
- 0 discrepancias en 200 sorteos con melate-e.com: `README.md`, sección «Datos».
- Las BOLSA mal del oficial: regla 4 de los datos en el `CLAUDE.md`, y
  `tests/test_reglas_datos.py::test_regla4_bolsa_invalida_solo_en_los_tres_concursos_conocidos`.
- La regla del tres, a mano:

```powershell
.venv\Scripts\python.exe -c "r=3/6276; print(round(r*100,3), round(1/(r*156),1), round(1/(r*468),1))"
```

Tiene que imprimir `0.048 13.4 4.5`: el porcentaje por fila, y los años por error en Revanchita y en
los tres juegos.

Relacionado: `Fases/2026-10-04_ciclo-vivo/00_ALCANCE.md`,
`Fases/2026-10-04_ciclo-vivo/Inventario/2026-10-04_18-16_s0-estado-de-partida.md`,
`Protocolo_Estadistico/Decisiones/2026-10-04_18-58_s5-la-condicion-5-exige-un-holdout-capaz.md`,
`Fases/2026-10-03_popularidad/Decisiones/2026-10-03_02-40_s3-dictamen-terminos-melate-e.md`,
`Conexiones/Añadir/2026-10-03_00-13_s1-fuentes-de-datos.md`.
