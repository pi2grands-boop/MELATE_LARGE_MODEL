# Reglas de documentación — Máquina Melate

Este documento declara cómo se documenta el proyecto. Es el contrato: si algo no cumple lo que
está aquí, no está documentado.

La bitácora vive en `Documentos_Contexto/`. El código dice **qué hace** el sistema hoy; no dice por
qué se decidió así, qué se verificó, qué no es un bug, ni cómo volver atrás. Eso es lo primero que se
pierde, y es lo que esta bitácora conserva. Su público es **quien no estuvo**, incluido tú dentro de
seis meses.

---

## 0 · Regla 0, invertida a propósito

La regla por defecto de una bitácora es que **nunca llega a producción**, porque contiene rutas
internas y detalles de implementación.

**En este proyecto no aplica, por decisión explícita del usuario:** la bitácora **sí se publica**, en
el repositorio público `pi2grands-boop/MELATE_LARGE_MODEL`. Se publica el funcionamiento y la
documentación. No se publica nada personal: contraseñas, usuarios, direcciones, rutas de la máquina.

Esto no es una relajación de la regla, es un cambio de su naturaleza, y tiene consecuencias que son
contrato desde el primer documento:

1. **Rutas relativas siempre.** Nunca la ruta absoluta de la máquina, nunca el usuario de Windows,
   nunca rutas de almacenamiento personal. Un documento se escribe desde la raíz del repositorio:
   `src/melate/ingest.py`, no la ruta completa del disco.
2. **Ningún correo personal**, ni en documentos ni en los metadatos de los commits. La identidad de
   git de este repositorio usa la forma `users.noreply.github.com`.
3. **Colador antes de cada push.** La receta está en `Documentos_Contexto/_MAPA.md`. Si imprime algo,
   no se sube.
4. **Este proyecto no tiene secretos.** Las fuentes de datos son HTTP GET público sin autenticación.
   No hay `.env`, ni tokens, ni credenciales. Si alguna fuente futura llegara a pedirlas, eso cambia
   y se replantea con su documento en `Seguridad/Decisiones/`.

El porqué completo de esta inversión está en `Seguridad/Decisiones/`.

---

## 1 · El pipeline — el `.md` es el ÚLTIMO paso

Documentar antes de verificar produce documentación que miente, y una bitácora en la que no se
confía es peor que ninguna.

```
  1. IMPLEMENTAR
        ↓
  2. REVIEW #1  ─────────→  abre <Área>/Bugs/<fecha>_<slug>.md   (documento VIVO)
        ↓
        ├── ¿bug? → CORREGIR → <Área>/Arreglos_Bugs/…
        │              └── ¿conviene dejarlo? → CONSULTAR AL USUARIO SIEMPRE.
        │                                        Él da el porqué. Se registra.
        ↓
  3. OPTIMIZAR (sin código muerto, sin bloat)
        ↓
  4. REVIEW #2  +  REVIEW DE SEGURIDAD          (dos modos mentales distintos)
        ↓
  5. Solo si está limpio → ESCRIBIR el .md FINAL
```

**Excepción única — los documentos de inventario (`s0`):** el estado heredado se escribe *antes* de
tocar nada, porque después ya no se puede reconstruir. No documenta un cambio; documenta un punto de
partida.

### Documento vivo vs documento final

| | `Bugs/` (vivo) | `Añadir` · `Modificar` · `Eliminar` · `Decisiones` (final) |
|---|---|---|
| Cuándo | *durante* el trabajo | al terminar, una vez |
| Qué | el proceso: qué se probó, qué salió | el resultado: qué quedó y por qué |
| Tono | log, con ✅/❌ y evidencia cruda | narrativa cerrada |
| ¿Se edita? | **sí**, hasta cerrarlo | **no** — si cambia, se escribe uno nuevo |

Cerrar un `Bugs/` es añadirle un bloque fechado al final con el resultado.

---

## 2 · La rejilla — 12 áreas × 6 acciones

**Ningún `.md` vive fuera de una celda `<Área>/<Acción>/`.**

### Las 8 áreas base — no se tocan ni se renombran nunca

| Área | Pregunta que responde |
|---|---|
| **Mapa** | ¿Cuál es el mapa del sistema? Qué módulo responde a qué pregunta |
| **Estructura_Carpetas** | ¿Aparecen o se mueven directorios y ficheros? |
| **Estructura_Datos** | ¿Cambia la forma de los datos? Esquemas, columnas, forma del JSON de reporte |
| **Almacenamiento** | ¿Dónde y cómo persiste algo? Snapshots, duckdb, ficheros de reporte |
| **Conexiones** | ¿Quién llama a quién? Las fuentes HTTP, los contratos entre módulos |
| **Interconexion** | ¿Cómo se enlazan las piezas de la app? Pantallas, navegación, formularios |
| **Seguridad** | ¿Cambia la superficie de ataque o lo que queda expuesto? |
| **Red** | ¿Qué se sirve y desde dónde? Puertos, direcciones de escucha, caché HTTP |

### Las 4 áreas opcionales de este proyecto — declaradas y CONGELADAS

Añadir un área es un contrato: se declara aquí con su pregunta guía, se explica por qué no cabía en
ninguna existente, y a partir de ahí es tan permanente como las base.

| Área | Pregunta que responde | Por qué no cabía en ninguna base |
|---|---|---|
| **Reproducibilidad** | ¿Se puede volver a obtener este número exacto? Hash del dataset, semillas, versiones de librerías, snapshot congelado | `Estructura_Datos` es la *forma* de los datos, no su identidad ni su procedencia. `Mapa` es el mapa del sistema. "Con qué versión de scikit-learn sale 0.6160" no tiene celda, y es la pregunta central del proyecto |
| **Protocolo_Estadistico** | ¿Qué prueba se corrió, contra qué línea base, con qué corrección múltiple, y qué se declaró? | El protocolo de evaluación del `CLAUDE.md` es no negociable y tiene sus propias decisiones cerradas: la familia de Benjamini-Hochberg, el preregistro, el mínimo efecto detectable, y cada veredicto de "sin ventaja demostrada". Forzarlo a `Estructura_Datos` lo haría imposible de encontrar |
| **Rendimiento** | ¿Cuánto tarda y cuánta memoria usa? | El backtest walk-forward de los tres juegos ronda los 2 minutos y crecerá con cada sorteo. Es una restricción real de diseño, no una propiedad de los datos ni del mapa |
| **Despliegue** | ¿Qué se subió al repositorio público, cuándo, con qué commit, y qué dijo el colador? | Qué quedó público y cuándo es exactamente lo que no se puede reconstruir después. No es `Red` (nada se sirve) ni `Seguridad` (que guarda el *criterio*, no el registro de cada subida) |

### Las 6 acciones

| Acción | Cuándo |
|---|---|
| **Añadir** | Algo que antes no existía |
| **Modificar** | Algo que ya existía y cambia de comportamiento |
| **Eliminar** | Algo que se retira — registra qué dependía de ello |
| **Bugs** | Documento vivo de review/QA de un ciclo |
| **Arreglos_Bugs** | La corrección de un fallo concreto |
| **Decisiones** | Una decisión cerrada que **no cambia código**: por qué A y no B |

### Regla del abanico

**Casi ningún cambio real cae en una sola área.** Si cruza fronteras, se escribe un `.md` por área
afectada y se enlazan con `Relacionado:`. Cada uno cuenta *su* ángulo, sin repetir.

Dentro de seis meses nadie busca "el refactor de octubre". Se busca "¿por qué `protocolo.py` existe?"
o "¿con qué versión de sklearn reproduce el gradient boosting?".

---

## 3 · Nombres

```
AAAA-MM-DD_HH-MM_<slug-kebab-case>.md
```

- **Guion en la hora, nunca `:`** — ilegal en Windows.
- **Hora real del trabajo.** Es lo que permite reconstruir el orden.
- **Slug del contenido, no del fichero tocado:** ✅ `s1-paridad-numerica` · ❌ `fix`, `cambios`.
- **Prefijo de fase** (`s0-`, `s1-`…) cuando el trabajo pertenece a una sección del plan.

---

## 4 · Fases

El caso normal es escribir directo en la rejilla. Los bloques de trabajo grandes —un arranque, un
cambio de tecnología, una funcionalidad extensa— viven en `Fases/<fecha>_<nombre>/` con su
`00_ALCANCE.md`, su `Inventario/`, sus `Decisiones/`, `Cambios/`, `Bugs/` y su `99_CIERRE.md`.

**Mientras la fase está abierta**, todo su movimiento vive dentro del dossier; las áreas base no se
tocan. **Al cerrarla**, el dossier *emite* un número pequeño de documentos a las áreas base — solo el
estado final, nunca el proceso. Cada documento emitido enlaza al dossier.

Los dossiers cerrados no se borran: son la única prueba de por qué el sistema es como es.

---

## 5 · Reglas de contenido

1. **Verificable, no aspiracional.** No "se validó la entrada", sino el comando concreto y su
   resultado. Si no puedes citar evidencia, no lo has verificado.
2. **Cita líneas y resultados reales.** `baseline_auditoria.py:68` · `2184 sorteos` ·
   `0 enlaces rotos`. Un número concreto vale más que un párrafo.
3. **"Cómo revertir" es obligatorio y literal.** `git revert <sha>` con el SHA escrito, o "borrar
   `src/melate/protocolo.py` y la línea 12 de `informe.py`". Nunca "deshacer los cambios".
4. **Marca lo intencional como intencional.** Toda excepción a una regla se documenta con su porqué,
   o alguien la tratará como bug.
5. **Enlaza al cerrar.** `Relacionado:` con los hermanos del mismo cambio. Es un grafo, no una pila.
6. **Escribe para quien no estuvo.** Nada de "como hablamos" o "lo del otro chat".
7. **Un documento, un cambio.** Si escribes "y además…" sobre algo no relacionado, es otro documento.
8. **No repitas el código.** Documenta la decisión y la evidencia; el código ya está citado por ruta
   y línea.
9. **Rutas relativas a la raíz del repositorio.** Ver §0: esto se publica.

---

## 6 · Lo que un `grep` no ve

Hay una clase de fallos que ninguna revisión estática encuentra, porque son sintácticamente
correctos y semánticamente equivocados. En un proyecto estadístico son estos:

| Categoría | Ejemplo real de este dominio | Qué hace falta |
|---|---|---|
| **Fuga temporal** | Una variable que usa el sorteo `t` para predecir el sorteo `t` | Un test que permute el futuro y exija que el pasado no cambie |
| **Orden del RNG** | Reordenar un diccionario cambia qué número saca `default_rng` y con él todos los p-valores | Comparar el JSON completo contra el oráculo |
| **Versión de librería** | El mismo `random_state` da otro árbol en otra versión de scikit-learn | Fijar versiones y registrar el `pip freeze` |
| **Datos que crecen** | La línea base deja de reproducir porque llegó un sorteo nuevo, no porque el código esté roto | Snapshot congelado con su hash |
| **Múltiples comparaciones** | Correr 36 pruebas y reportar la mejor | Benjamini-Hochberg sobre **todas**, también las que no se reportan |

**Obligatorio en todo documento de `Bugs/`:** declarar las limitaciones del entorno por delante, y
terminar con una lista de **"pendiente de verificar"**. Un ciclo **no se cierra** mientras esa lista
no se haya ejecutado.

---

## 7 · Cuando una decisión invalida una premisa

El patrón que más veces muerde: se toma una decisión nueva y nadie vuelve sobre los documentos que
dependían de la premisa vieja.

**Al cerrar cualquier `Decisiones/`, hay un paso obligatorio:** buscar qué documentos dependían de la
premisa que acaba de cambiar y anotarlo. Si algo queda inválido, se escribe el `Modificar/`
correspondiente **en el mismo ciclo**, no "cuando dé problemas".

---

## 8 · Correcciones

Los documentos finales **no se editan**. Si el código cambia, se escribe uno nuevo en `Modificar/`
que dice qué cambió y por qué, y enlaza al anterior.

**Dos excepciones, ambas con marca visible:**
- Los `Bugs/` vivos se cierran con un bloque fechado al final.
- Un **dato numérico que se quedó obsoleto** se corrige en todos los documentos que lo citan. Un
  número equivocado repetido en cinco sitios erosiona la confianza en todo lo demás. Búscalo con
  `Select-String` antes de dar la fase por cerrada.

---

## 9 · Checklist antes de dar una tarea por terminada

- [ ] Review #1 volcada en `<Área>/Bugs/`, **con las limitaciones del entorno declaradas**
- [ ] Bugs corregidos → `Arreglos_Bugs/`; bugs dejados a propósito → **consultados** y registrados
      con el porqué del usuario
- [ ] Sección optimizada, sin código muerto
- [ ] Review #2 + review de seguridad
- [ ] `.md` final en **todas** las áreas que el cambio toca
- [ ] Nombre `AAAA-MM-DD_HH-MM_slug.md`, guion en la hora
- [ ] Cabecera completa · secciones Qué se hizo · Por qué · Impacto · Cómo verificar/revertir
- [ ] Evidencia citada: rutas, líneas, comandos, números
- [ ] `Relacionado:` enlaza los hermanos, y ningún enlace apunta a un fichero inexistente
- [ ] Lista de **pendiente de verificar**, si el entorno no lo permitió
- [ ] `_MAPA.md` actualizado si se cerró una fase
- [ ] **El colador sale vacío** antes de subir nada

---

## 10 · Anti-patrones

| ❌ | Por qué |
|---|---|
| Escribir el `.md` antes de la review | Documenta lo que creías, no lo que es |
| Un `.md` gigante por sesión | Ilocalizable; la rejilla deja de indexar |
| "Se mejoró el modelo" | Ni verificable ni reversible |
| Cerrar un `Bugs/` sin haber ejecutado nada | Convierte la bitácora en ficción |
| Dejar un bug sin preguntar | La decisión es del usuario, no tuya |
| Omitir "Cómo revertir" | Convierte cada cambio en irreversible |
| Crear áreas sobre la marcha, sin declararlas aquí | Rompe la rejilla; la próxima búsqueda falla |
| Volcar un bloque de trabajo entero en las áreas base | Ahoga el índice permanente |
| Una ruta absoluta de la máquina en un documento | Esto se publica. Ver §0 |
| Reportar una cifra sin la versión de librería que la produjo | No es reproducible, y este proyecto va de eso |
