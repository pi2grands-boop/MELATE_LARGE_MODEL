# Review de la Fase 5 — C1: la condición 5 exige un holdout capaz

- **Fecha/hora:** 2026-10-04 19:16
- **Área:** Fases/2026-10-04_ciclo-vivo · **Acción:** Bugs
- **Chat / página:** sesión de la Fase 5 · `src/melate/protocolo.py`
- **Archivos afectados:** `src/melate/protocolo.py`, `tests/test_protocolo.py`, `scripts/mutar.py`
- **Estado:** CERRADO el 2026-10-04 a las 19:23 (bloque al final)

Review del primer bloque de código de la fase: la decisión C1
(`Protocolo_Estadistico/Decisiones/2026-10-04_18-58_s5-la-condicion-5-exige-un-holdout-capaz.md`),
aplicada en `protocolo.condicion_efecto_minimo` y en una función nueva, `_holdout_incapaz`, que
escribe su motivo. **Este documento se abre tarde**: B1-B3 se encontraron minutos antes, leyendo los
motivos que producía el código recién escrito. Queda dicho, como en la Fase 4.

## Limitaciones del entorno, por delante

- **Windows 11, PowerShell 5.1 y Git Bash.** Nada probado en Linux ni macOS.
- **El holdout real sigue vacío.** El 4274 se sortea hoy a las 22:00 y el oficial no lo trae. El camino
  con holdout se prueba con copias del preregistro real **selladas a mano en el pasado**, como el resto
  de `tests/test_protocolo.py`, sobre los cuatro sorteos históricos con los que el laboratorio
  declaraba ventaja.
- **Lo que es exacto y lo que es simulado.** Las probabilidades de n = 1 a 6 salen de enumerar todas
  las combinaciones de aciertos y llamar al `protocolo.declara_ventaja` real. Las de horizontes largos
  (0,016 % y 0,095 % después del sorteo 1 778) salen de un Monte Carlo que **replica** las reglas en
  forma vectorizada; la versión de la regla vieja se validó contra el exacto (0,00324 contra 0,00330), y
  la de la regla nueva añade una línea, la de la capacidad, que no se ha validado aparte contra el
  código.

## Review #1 — lo que se encontró

### B1 · El motivo decía «con 1 sorteos de holdout»

Es el mismo plural de H4 del inventario, y el motivo lo enseña la app en la tabla de condiciones.
**Arreglo:** singular cuando es uno. **Test:** `test_un_sorteo_de_holdout_no_basta_para_declarar_ventaja`
exige «con 1 sorteo de holdout», que no es subcadena del texto viejo.

### B2 · En la frontera, el motivo decía «0.0480, mayor que el 0.0480»

Con 1 777 sorteos el detectable es 0,048008 y el declarado 0,048: con cuatro decimales se escriben
igual, y la frase parece falsa justo donde más importa leerla bien. **Arreglo:** las dos cifras con sus
decimales significativos («0.048008, mayor que el 0.048»). **Test:**
`test_el_efecto_declarado_gobierna_el_holdout_minimo` exige el detectable entero en el motivo, con
los dos valores del efecto declarado.

### B3 · Sin el tamaño del holdout, «hasta entonces» no tenía a qué referirse

Un resultado sin `sorteos_holdout` —solo pasa con diccionarios hechos a mano— daba «…declarado en el
sello, y hasta entonces ningún delta cuenta». **Arreglo:** «y mientras lo sea ningún delta cuenta», sin
prometer un plazo que no se puede calcular. **Test:**
`test_el_motivo_sin_tamano_de_holdout_no_promete_un_plazo`.

### B4 · Faltaba la contraprueba: que con un efecto declarado el «sí» siga siendo posible

Los tests nuevos demostraban que la regla dice «no» cuando debe, y el proyecto ya vigilaba que el
camino afirmativo existiera, pero **sin efecto declarado** (`test_el_camino_afirmativo_existe_y_es_alcanzable`).
Nada comprobaba que, con el 0,048 del sello, la condición 5 se pudiera cumplir alguna vez. Una regla
que la hiciera imposible habría pasado todos los tests. **Arreglo:**
`test_con_el_efecto_declarado_el_camino_afirmativo_sigue_existiendo`, con 1 800 sorteos y un efecto
que lo supera todo: 5 de 5. **Y una mutación que solo él caza**, «F5 con efecto declarado la condición
5 no se cumple nunca», que cambia la comparación por `calculado > 0`. Detectada.

## Lo que se comprobó y estaba bien

- ✅ **Los tests nuevos fallaban con el código de antes**: 7 de 8 en rojo, y los cuatro sorteos
  históricos daban `VENTAJA DEMOSTRADA`. El octavo, que sin efecto declarado nada cambia, pasaba antes y
  pasa ahora: es su papel.
- ✅ **Con el código nuevo, la probabilidad exacta bajo el azar es 0** de n = 1 a 6 con el 0,048
  declarado. Sin efecto declarado sigue siendo la de antes (0,003297 con n = 1): la regla solo endurece
  lo que el sello declaró.
- ✅ **Los cuatro sorteos históricos dan ahora `sin ventaja demostrada`, 4 de 5**, con el laboratorio
  real, y solo falla la condición 5 (`test_el_laboratorio_real_ya_no_declara_con_un_sorteo`, `lento`).
- ✅ **Dos valores del parámetro que gobierna**: con 0,048 declarado, la frontera está entre 1 777 y
  1 778 sorteos; con 0,10, entre 409 y 410.
- ✅ **La mutación que quita la regla se detecta** («F5 la condición 5 acepta un holdout incapaz…»),
  en 2,0 s.
- ✅ **El fragmento de «Cómo verificar» de la decisión imprime lo que dice**: `sin ventaja demostrada 4`.
- ✅ **El bucle rápido**: 219 en verde, 10,5 s (11,2 de reloj); las cuatro pruebas lentas nuevas, en
  ~5 s.
- ✅ **La paridad, intacta**: los 28 tests lentos sin red —`tests/test_paridad.py` entre ellos—, en
  verde en 129,9 s. `protocolo.condicion_efecto_minimo` no la usa ni el oráculo ni el informe.

## Review #2 — limpieza

- **Sin código muerto.** `math` se usa solo en `_holdout_incapaz`; su `cifra` interna, dos veces en la
  misma función, y no merece salir de ella.
- **Una duplicación consciente**: el `detectable()` de los tests repite la fórmula y el redondeo de
  `lab._evaluar_una`, con un comentario que lo dice. Sacarla del laboratorio para importarla sería
  tocar más código de la Fase 2 del que la decisión pide.
- **El nombre de la condición no cambia** («efecto >= mínimo detectable»): el almacén exige cinco
  condiciones y la app y los tests las buscan por nombre.

## Review de seguridad

- ✅ **Sin superficie nueva**: una función pura, sin lectura ni escritura, sin red, sin dependencias.
- ✅ **La única entrada nueva es el efecto declarado**, que sale de un preregistro cuyo sello se
  verifica antes de evaluar. Un valor de otro tipo falla igual que fallaba antes con `max()`; uno
  negativo hace que la condición no se cumpla nunca, que es el lado seguro; uno nulo o cero se trata
  como «sin efecto declarado», y eso lo dice la decisión.
- ✅ **El motivo es texto generado**, sin nada que venga de fuera salvo cifras, y la app lo pinta como
  dato de una tabla, sin interpretarlo.

## Observación aceptada (no es de C1)

El motivo de la **condición 1** dice «en 1 sorteos de holdout» (`protocolo.condicion_holdout_positivo`,
código de la Fase 2). Es parte de H4 —cómo enseña la app el holdout—, que el usuario aprobó en C3, y se
arregla con ese bloque, no aquí.

## Pendiente de verificar en vivo

1. **El motivo en la app**, con el primer veredicto con holdout: cómo se lee en la tabla de condiciones
   de un navegador de verdad. Pasa al bloque de la app.

Relacionado: `Protocolo_Estadistico/Decisiones/2026-10-04_18-58_s5-la-condicion-5-exige-un-holdout-capaz.md`,
`Fases/2026-10-04_ciclo-vivo/Decisiones/2026-10-04_18-59_s5-lo-que-decidio-el-usuario.md`,
`Fases/2026-10-04_ciclo-vivo/Inventario/2026-10-04_18-16_s0-estado-de-partida.md`.

## Cómo verificar

```powershell
.venv\Scripts\python.exe -m pytest tests\test_protocolo.py -q          # 56, con las lentas
.venv\Scripts\python.exe scripts\mutar.py --solo "F5"                   # 2 de 2
```

## Resultado — CERRADO el 2026-10-04 a las 19:23

| # | Hallazgo | Arreglo | Test que lo fija |
|---|---|---|---|
| B1 | «con 1 sorteos de holdout» | singular cuando es uno | `test_un_sorteo_de_holdout_no_basta_para_declarar_ventaja` |
| B2 | «0.0480, mayor que el 0.0480» en la frontera | las cifras con sus decimales | `test_el_efecto_declarado_gobierna_el_holdout_minimo` |
| B3 | «hasta entonces» sin plazo | «mientras lo sea» | `test_el_motivo_sin_tamano_de_holdout_no_promete_un_plazo` |
| B4 | Sin contraprueba del «sí» con efecto declarado | un test y una mutación que solo él caza | `test_con_el_efecto_declarado_el_camino_afirmativo_sigue_existiendo` |

**Medido al cerrar:** `tests/test_protocolo.py`, 56 en verde en 14,6 s (las cuatro lentas incluidas,
y 46 de antes de la fase); el bucle
rápido, 219 en verde, 10,5 s; los 28 lentos sin red, en verde, con la paridad; las dos mutaciones de
la Fase 5, detectadas; y bajo el azar, con el código nuevo y el 0,048 declarado, **0** probabilidad de
declarar ventaja de n = 1 a 6, enumerada con el `declara_ventaja` real.

**Bugs abiertos: ninguno.** Ninguno dejado a propósito. **Queda pendiente**, y pasa al bloque de la app:
ver el motivo de la condición 5 en un navegador con el primer veredicto con holdout, y el plural de la
condición 1.
