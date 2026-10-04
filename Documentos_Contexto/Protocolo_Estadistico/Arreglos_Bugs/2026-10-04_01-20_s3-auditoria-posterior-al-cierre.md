# Seis defectos encontrados auditando la Fase 3 ya cerrada

- **Fecha/hora:** 2026-10-04 01-20
- **Área:** Protocolo_Estadistico · **Acción:** Arreglos_Bugs

## Por qué hubo una auditoría después del cierre

La Fase 3 cerró con 161 pruebas en verde, los dos scripts bloqueantes en 0 y la paridad intacta.
El usuario pidió una pasada más antes de seguir. Es el mismo procedimiento que encontró siete
defectos en las fases 1 y 2 con 92 pruebas en verde
(`Protocolo_Estadistico/Bugs/2026-10-03_01-59_auditoria-retrospectiva-fases-1-y-2.md`), y vuelve a
funcionar: **seis hallazgos, todos en el hueco de lo que nadie pensó comprobar.**

## Lo que se hizo distinto esta vez: mutación

Antes de buscar fallos en el código, se comprobó que **los tests sirvan**. Se rompió una cosa a la
vez en los dos módulos nuevos y se miró si la suite se enteraba:

| Mutación | ¿Detectada? | Test que la caza |
|---|---|---|
| Quitar el límite de 1 solicitud/segundo | ✅ | `test_el_ritmo_por_defecto_es_el_del_dictamen` |
| Desactivar la caché | ✅ | `test_la_cache_evita_la_segunda_peticion` |
| Combinatoria de Melate: 50 donde va 49 | ✅ | `test_las_favorables_son_las_del_contrato` |
| Permitir que se pida Revanchita | ✅ | `test_revanchita_no_se_pide_nunca` |
| `User-Agent` que finge ser navegador | ✅ | `test_el_user_agent_se_identifica_y_no_finge…` |
| Aceptar una tabla con menos categorías | ✅ | `test_una_tabla_incompleta_falla_ruidosamente` |
| Quitar el tope de popularidad | ✅ | `test_la_ganancia_por_evitar_compartir_es_minuscula` |
| Fingir que nunca compartes la bolsa | ✅ | `test_compartir_crece_con_la_popularidad` |
| Quitar el aviso de que el EV es negativo | ✅ | `test_toda_valoracion_lleva_el_aviso` |

**9 de 9.** Un test que no falla cuando rompes lo que dice vigilar no vigila nada; estos vigilan.

> **Un aviso para quien repita esto:** el guion de mutación restauró el contenido de los ficheros
> pero los reescribió con finales de línea LF, y `git status` los dejó como modificados aunque
> `git diff --numstat` saliera vacío. Se restauró con `git checkout --`. Mutar ficheros
> versionados en Windows deja ese residuo; hay que comprobarlo antes de comitear.

---

## Defectos de código

### D1 · `analizar()` con un generador daba «0 pedidos, 3 usados»

`analizar` recorría `sorteos` y **después** hacía `len(list(sorteos))` para el recuento. Con un
generador ya consumido eso devuelve 0, así que el reporte decía *0 sorteos pedidos, 3 usados*, sin
error y sin que nada lo detectara.

No mordía desde la CLI porque ahí se pasa un `range`, que es re-iterable. **Por eso no se vio**: el
único camino probado era el que no falla.

**Arreglo:** `sorteos = list(sorteos)` antes del bucle.
**Test:** `test_el_recuento_de_sorteos_pedidos_no_depende_del_tipo_que_le_pases`, que lo prueba con
`list`, `tuple`, `iter` y una expresión generadora.

### D2 · `informe --popularidad <ruta mala>` moría tras dos minutos de cómputo

La ruta se abría **al final**, donde se usa. Una errata costaba toda la corrida: el backtest
completo gastado y un `FileNotFoundError` como premio.

**Es la misma forma de fallo que el proyecto ya arregló una vez**: el `UnicodeEncodeError` que
mataba el informe a mitad después de gastar el cómputo
(`Reproducibilidad/Modificar/2026-10-03_01-30_s2-la-suite-ya-no-depende-del-shell.md`). Que
reapareciera en otro sitio dice que la lección era más general que su arreglo:

> **Todo lo que pueda fallar por la entrada se valida antes de gastar un segundo de CPU.**

**Arreglo:** `informe.cargar_popularidad()`, llamada en la primera línea de `construir()`. Valida
que el fichero exista, que sea JSON legible y que parezca un reporte, y sale con `SystemExit` y un
mensaje que dice cómo generarlo.

| | Antes | Después |
|---|---|---|
| Ruta mala | `FileNotFoundError` a los ~130 s | `SystemExit` con instrucciones a los **2,2 s** |

**Tests:** `test_una_ruta_de_popularidad_mala_falla_antes_de_gastar_el_computo` (que además exige
que la validación tarde menos de 1 s: si algún día vuelve al final, el test lo dice) y
`test_el_informe_con_popularidad_buena_sigue_funcionando`.

---

## Defectos de procedencia y de documentación

### D3 · Dos cifras publicadas sin reporte comiteado, y una que mezclaba ventanas

El `CLAUDE.md` publicaba las ventas de Melate (mediana 0.98 M, rango 0.58–1.59 M) sobre la ventana
**3973-4272**, y el `README.md` el efecto calendario con **t = −18.7**. Pero el único reporte en
`reportes/` cubría **4173-4272**.

Peor: el README decía *«un 24 % menos de boletos (t de Welch = −18.7)»*, y **esas dos cifras son de
ventanas distintas**:

| Ventana | Sorteos | Cociente | «menos de boletos» | t de Welch |
|---|---|---|---|---|
| 4173-4272 | 100 | 0,7609 | **23,91 %** | **−9,70** |
| 3973-4272 | 300 | 0,7549 | **24,51 %** | **−18,67** |

El 24 % venía de la ventana corta y el t de la larga. Ninguna de las dos produce ese par.

**Arreglo**, en tres partes:

1. Se generó y comiteó `reportes/2026-10-04_popularidad-melate-300-sorteos.json`, que es el
   artefacto que faltaba. **0 peticiones de red**: todo estaba en caché.
2. El README pasa a **24.5 % con t = −18.7**, los dos de la ventana de 300, y cita el fichero.
3. Cada cifra publicada dice ahora de qué ventana y de qué reporte sale. Son dos, y a propósito:
   el EV con menores medidos necesita **los dos juegos** (ventana 4173-4272), y el efecto
   calendario y las ventas solo existen para Melate, donde hay 300 sorteos cacheados.

El `CLAUDE.md` gana además la línea del efecto calendario, que antes solo estaba en el README y en
la bitácora.

### D4, D5, D6 · Números obsoletos

La regla §8 de `REGLAS-DOCUMENTACION.md`: *un dato numérico que se quedó obsoleto se corrige en
todos los documentos que lo citan.* Tres recuentos se quedaron atrás al añadir tests y documentos:

| Dónde | Decía | Es |
|---|---|---|
| `Conexiones/Añadir/…tablas-de-ganadores-melate-e.md` · `Estructura_Carpetas/Modificar/…arbol-tras-la-popularidad.md` | 38 pruebas | **36** |
| `Fases/2026-10-03_popularidad/Bugs/…review-popularidad-y-cartera.md` | 64 | **62** |
| `Fases/2026-10-03_popularidad/99_CIERRE.md` | 46 documentos | **50** |

Ninguno cambia una conclusión. Se corrigen porque un recuento equivocado repetido erosiona la
confianza en los que sí importan, y porque este proyecto publica sus cifras.

### Nota sobre el tiempo de la suite

«133 s» aparecía como cifra exacta en ocho sitios. Medida cuatro veces: **128,7 · 131,0 · 133,5 ·
153,9 s**. Pasa a escribirse como **~130 s**, con tilde, que es lo que es. El bucle rápido da 5,4 s
por el contador de pytest y 6,2 s de reloj de pared; se publica el de pytest, que es el comparable
entre corridas.

---

## Lo que se comprobó y estaba bien

| Camino sin test, probado a mano | Resultado |
|---|---|
| Caché truncada a medio fichero | `ValueError` ruidoso, y **no** reintenta por red |
| Cartera con presupuesto menor que un boleto | 0 boletos, sin reventar |
| Más boletos pedidos que candidatas aptas | Entrega las que hay, no inventa |
| Reporte de popularidad con JSON válido pero ajeno | Dice `disponible: false` con su motivo |
| Cifras de cabecera re-derivadas desde el informe publicado | 65,6 % · +0,27 % · +0,59 % · +1,63 % · 53,6:1 |

Las de la última fila se habían publicado como 65,5 % · +0,27 % · +0,58 % · +1,63 % · 54:1. La
diferencia es de redondeo —partir del EV exacto o del publicado— y se deja como está, porque «54 a
1» cubre honestamente 53,6 y 53,8.

## Cómo verificar

```powershell
.venv\Scripts\python.exe -m pytest tests -q -m "not lento and not red"   # 135, ~5 s
.venv\Scripts\python.exe -m pytest tests -q                              # 164, ~130 s

# D2, en vivo: tiene que morir en segundos, no en minutos
.venv\Scripts\python.exe -m melate.informe --datos data\raw\2026-10-02 --popularidad no\existe.json

# D3: el reporte que respalda las cifras del contrato, con 0 peticiones de red
.venv\Scripts\python.exe -m melate.popularity --juegos Melate --desde 3973 --hasta 4272 `
    --datos data\raw\2026-10-02 --salida reportes\comprobacion.json
```

## Cómo revertir

```powershell
git revert <sha de este commit>
```

Devuelve `len(sorteos)` a `len(list(sorteos))`, quita `informe.cargar_popularidad` y su llamada en
la primera línea de `construir()`, borra los tres tests nuevos y
`reportes/2026-10-04_popularidad-melate-300-sorteos.json`, y deja los recuentos antiguos. Nada de
esto toca el oráculo ni la paridad.

## Pendiente de verificar

1. **Un bloqueo real del sitio.** Sigue sin ocurrir. *(heredado)*
2. **Fuera de Windows.** Sigue sin probarse. *(heredado)*
3. **La mutación no está automatizada.** Se corrió a mano con un guion del scratchpad, que no
   queda en el repositorio. Si alguien debilita un test, nada lo detectará hasta la próxima
   auditoría manual. Convertirlo en una herramienta del proyecto es trabajo de otra fase.

Relacionado: `Protocolo_Estadistico/Bugs/2026-10-03_01-59_auditoria-retrospectiva-fases-1-y-2.md`,
`Fases/2026-10-03_popularidad/99_CIERRE.md`,
`Fases/2026-10-03_popularidad/Bugs/2026-10-03_04-10_s3-review-popularidad-y-cartera.md`,
`Reproducibilidad/Modificar/2026-10-03_01-30_s2-la-suite-ya-no-depende-del-shell.md`.
