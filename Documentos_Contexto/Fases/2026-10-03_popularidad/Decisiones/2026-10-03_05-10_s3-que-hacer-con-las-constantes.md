# Qué se hace con las dos constantes del contrato que la Fase 3 contradijo

- **Fecha/hora:** 2026-10-03 05-10
- **Área:** Fases/2026-10-03_popularidad · **Acción:** Decisiones
- **Estado:** cerrada · **Decidida por:** el usuario, consultado antes de cerrar la fase

## Por qué hubo que preguntar

Al medir las tablas de ganadores aparecieron dos cifras del `CLAUDE.md` que los datos no
sostienen. El `CLAUDE.md` es el contrato del proyecto, y
*"un bug no se deja sin preguntar: la decisión es del usuario"*. Se presentaron los cuatro
asuntos con su evidencia y **ninguno se aplicó antes de la respuesta.**

## C1 · El `menores_brutos` de Revancha → **nota al pie, sin tocar cifras**

### Lo que se midió

Reproduciendo las tablas 4271 y 4272 que cita `baseline_auditoria.py:252`:

| | 4271 | 4272 | Media | Escrito a mano |
|---|---|---|---|---|
| Melate, estimador directo | 4,3494 | 4,4106 | **4,3800** | **4,38** ✅ |
| Revancha, estimador directo | **2,0965** | 4,4083 | 3,2524 | **2,10** ❌ |

El 4,38 de Melate es la media de los dos sorteos, exacta a cuatro decimales. El 2,10 de Revancha
es **solo el 4271**. El 4272 daba 4,4083 porque su categoría de 5 aciertos tuvo 3 ganadores y el
premio individual se disparó a 206.628 $.

No se afirma qué pensó quien lo escribió. Se afirma lo medible: **las dos constantes se
calcularon con métodos distintos**, y eso es invisible sin reproducirlas.

Medido sobre 100 sorteos con el estimador estable: Melate **4,6013**, Revancha **2,6042**.

### La decisión

**El `CLAUDE.md` conserva sus cifras y añade una nota.** Las tres de EV (−59 %, −49 %, −12 %) son
las que reproduce `baseline_auditoria.py`, y esa sección existe justamente para ser reproducible:
cambiarlas la rompería.

La nota, fechada 2026-10-03, dice de dónde sale cada constante, que se calcularon con métodos
distintos, y cuál es el EV medido: **Melate −57,2 % y Revancha −44,4 %**. Es el mismo patrón que
la corrección del 2026-10-02, que también dejó la cifra vieja visible junto a la nueva.

Lo medido vive en la clave `valor_esperado_medido` del informe, declarada en `NUEVAS_CLAVES`.
**El oráculo y el defecto de `ev.valor_esperado` no se tocan.**

## C2 · El rango de ventas → **corregido con lo medido**

### Lo que se midió

El contrato decía *"1.06 a 1.18 millones de combinaciones de Melate por sorteo"*. Sobre 300
sorteos (ventana 3973-4272): **solo 47, el 16 %, caen en ese rango.** Mediana 982.693, rango real
583.212 a 1.586.604.

La causa no es un error de cálculo sino de forma: **las ventas suben con la bolsa**, así que
ningún rango estrecho puede describirlas. La estimación anterior salía de dos tablas (2021 y 2026)
y era correcta para ellas.

### La decisión

**Sustituir la constante** por la mediana y el rango medidos, citando la ventana, la fecha de
descarga y el comando que lo reproduce. Es un dato que antes estaba inferido de dos tablas y ahora
está medido sobre trescientas.

Se conserva la cifra anterior dentro de la frase, dicha como lo que es, para que quien la
recuerde entienda qué cambió.

## C3 · La prueba del calendario y la familia de BH → **fuera de la familia, confirmado**

El efecto calendario sale con **t de Welch = −18,67**. Al ser una prueba estadística nueva, y
habiendo dicho el usuario que ampliar la familia es decisión suya, se preguntó.

**Confirmado: no entra.** La familia sigue siendo de **36 pruebas** y `q_BH_global` mínima sigue
en **0,306**.

El argumento completo tiene documento propio en el índice permanente, porque es una frontera que
se va a volver a consultar:
`Protocolo_Estadistico/Decisiones/2026-10-03_05-10_s3-la-popularidad-no-entra-en-la-familia.md`.
En una línea: **dentro de la familia va todo lo que hable de la urna; fuera, todo lo que hable de
los jugadores**, porque el sorteo no sabe qué apostó nadie y por tanto ninguna medición de
popularidad puede convertirse en una afirmación sobre qué va a salir.

Hay además un argumento que cierra el asunto por sí solo: `prereg/2026-10-03_logistica-revancha.json`
**declara una familia de 36 y está sellado**. Cambiarla habría obligado a alterar un preregistro,
que es justo lo que este proyecto existe para impedir.

## C4 · La mascarilla oficial en PDF → **se deja documentado, sin OCR**

La fuente oficial de las tablas existe y está en el dominio que el proyecto ya usa, pero su capa
de texto trae **1 dígito en 25.885 caracteres**: las cifras están dibujadas. Sacarlas exigiría
OCR, una fuente de error nueva y silenciosa.

Queda documentado en el dictamen y en `Conexiones/Añadir/`, con las comprobaciones hechas, para
que nadie tenga que redescubrirlo. **No se intenta el OCR en esta fase.**

## Qué premisa invalida esto (§7 de las reglas)

| Documento que dependía de la premisa | Estado |
|---|---|
| `CLAUDE.md`, Constantes → ventas | **Actualizado** |
| `CLAUDE.md`, Línea base verificada → EV | **Nota añadida**, cifras intactas |
| `Protocolo_Estadistico/Decisiones/…familias-benjamini-hochberg.md` | Sigue válido: 36 pruebas |
| `prereg/2026-10-03_logistica-revancha.json` | Intacto, y debía estarlo |
| `Reproducibilidad/Añadir/…linea-base-reproducida.md` | Sigue válido: no cambia ninguna cifra del oráculo |

## Cómo verificar

```powershell
.venv\Scripts\python.exe -m pytest tests/test_paridad.py -q
.venv\Scripts\python.exe -m melate.informe --datos data\raw\2026-10-02 `
    --popularidad reportes\2026-10-03_popularidad.json
```

El informe imprime las cifras del oráculo **y**, debajo, las medidas. Las primeras no cambian.

## Cómo revertir

Quitar del `CLAUDE.md` la nota del 2026-10-03 de la sección «Línea base verificada» y devolver la
línea de ventas a *"Ventas estimadas (tablas de ganadores 2021 y 2026): 1.06 a 1.18 millones de
combinaciones de Melate por sorteo."*

Relacionado: `Fases/2026-10-03_popularidad/Bugs/2026-10-03_04-10_s3-review-popularidad-y-cartera.md`,
`Protocolo_Estadistico/Decisiones/2026-10-03_05-10_s3-la-popularidad-no-entra-en-la-familia.md`,
`Fases/2026-10-03_popularidad/00_ALCANCE.md`.
