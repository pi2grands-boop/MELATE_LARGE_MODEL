# El preregistro declaraba parámetros que el evaluador no leía

- **Fecha/hora:** 2026-10-03 01:59
- **Área:** Protocolo_Estadistico · **Acción:** Arreglos_Bugs
- **Chat / página:** sesión de arranque · auditoría retrospectiva
- **Archivos afectados:** `src/melate/lab.py`, `src/melate/protocolo.py`, `tests/test_protocolo.py`

## Qué se hizo

Tres campos del preregistro sellado que el evaluador ignoraba, ahora cableados.

| Campo del sello | Lo que pasaba | Lo que pasa |
|---|---|---|
| `efecto_minimo_declarado` | **Nadie lo leía.** La condición 5 usaba solo el detectable | El umbral es `max(detectable, declarado)` |
| `reentrenar_cada` | Valor por defecto de `_evaluar_una`, no sobrescrito | `evaluar()` lo pasa desde el `spec` |
| `semillas.backtest` | Fijado a `SEMILLA_BACKTEST` | `evaluar()` lo pasa desde el `spec` |

Y los dos últimos se devuelven ahora en `resultados` (`reentrenar_cada`, `semilla`), para que lo que
gobernó la corrida se vea en el reporte y no haya que creerse que se leyó.

### El agujero que abría `efecto_minimo_declarado`

Tenía una dirección concreta: **cuanto más grande el holdout, más baja el mínimo detectable, y más
fácil pasar la condición 5 con un efecto menor que el declarado.** Medido:

```
delta 0.0100 | emd calculado 0.0092 | declarado en el sello 0.048
condicion 5 -> CUMPLE | delta +0.0100 contra minimo detectable 0.0092
```

Un efecto cinco veces menor que el que el documento sellado decía que haría falta. Es aflojamiento
retroactivo del criterio —lo que el preregistro existe para impedir— por omisión en vez de por mala
fe, que a efectos del resultado es lo mismo.

El arreglo toma el **máximo** de los dos umbrales, y el motivo de la condición dice cuál mandó:

```
delta +0.0100 contra 0.0480 (declarado en el sello; detectable 0.0092, declarado 0.0480)
```

### Por qué no se vio antes

Los valores por defecto del código **coincidían** con los declarados en el preregistro: 100 y 7. Así
que todo producía el número correcto y las 92 pruebas estaban en verde. Un preregistro que declarara
otra cosa se habría ignorado en silencio, sin error ni aviso.

Es la peor forma de este fallo: no es que el mecanismo no funcionara, es que **parecía funcionar**.

### El impacto real sobre el preregistro vigente: ninguno, y por suerte

Medido, no supuesto. Para la regresión logística —la hipótesis que hay sellada— ni la semilla ni la
cadencia cambian el resultado:

| Estrategia | semilla 7 vs 99 | `reentrenar_cada` 100 vs 20 |
|---|---|---|
| **Regresión logística** | +0.124133 / +0.124133 — **igual** | +0.124133 / +0.124133 — **igual** |
| Calientes últimos 50 | +0.143551 / +0.104716 — **distinto** | — |
| Más frecuentes | −0.050624 / −0.040915 — **distinto** | — |
| Gradient boosting (HGB) | igual | −0.089459 / −0.108877 — **distinto** |

El motivo es instructivo: la semilla solo decide desempates de magnitud `1e-9` en `top6`, y las
probabilidades de una logística no empatan nunca; las frecuencias, que son discretas, empatan mucho.
Y una logística de 7 parámetros sobre 112 000 filas apenas se mueve con un 1 % más de datos,
mientras un árbol sí.

Así que el fallo era inocuo **para esta hipótesis** y no lo habría sido para otras. Que no hiciera
daño fue suerte, no diseño.

## Por qué

El preregistro es el documento que gobierna la evaluación: es su única razón de existir. Un sello que
protege la integridad de un documento cuyos campos nadie lee protege un trozo de papel.

El sello seguía siendo criptográficamente correcto —cambiar `reentrenar_cada` invalidaba el fichero,
como debe— pero el valor que protegía no llegaba a ninguna parte. Integridad sin efecto.

## Impacto en seguridad / conexiones / datos

- **Seguridad:** mejora el único control que importa aquí, que es contra uno mismo. El cambio solo
  puede endurecer: `max()` de dos umbrales, y pasar `declarado=None` deja el comportamiento anterior.
- **Conexiones:** sin cambios.
- **Datos:** ningún fichero tocado. `prereg/` sigue intacto — el campo ya estaba en él, y era
  importante que no hubiera que re-sellar nada para arreglar esto.

## Cómo verificar / revertir

```powershell
# A: el umbral declarado puede tumbar el veredicto
.venv\Scripts\python.exe -m pytest tests -k "efecto_minimo_declarado or efecto_declarado" -v

# B y C: los valores del sello llegan, y cambian el resultado donde pueden cambiarlo
.venv\Scripts\python.exe -m pytest tests -k "sello_llegan or cambiar_un_parametro" -v
```

Y a mano, que el reporte dice con qué corrió:

```powershell
.venv\Scripts\python.exe -c "import json;r=json.load(open('reportes/2026-10-03_veredicto.json',encoding='utf-8'));print(r['resultados'].get('reentrenar_cada'), r['resultados'].get('semilla'))"
```

**Revertir:** en `protocolo.condicion_efecto_minimo`, volver a usar solo
`res['efecto_minimo_detectable']`; en `lab.evaluar`, dejar de pasar `cada`, `semilla` y
`efecto_minimo_declarado`. **No se recomienda, y el primero menos:** se reintroduce la posibilidad de
cumplir la condición 5 con un efecto mucho menor que el declarado, justo cuando el holdout sea grande
— es decir, el día en que las cifras empiecen a importar.

Relacionado: `Protocolo_Estadistico/Bugs/2026-10-03_01-59_auditoria-retrospectiva-fases-1-y-2.md`,
`Protocolo_Estadistico/Añadir/2026-10-03_01-30_s2-preregistro-y-las-cinco-condiciones.md`,
`Estructura_Datos/Añadir/2026-10-03_01-30_s2-formato-del-preregistro.md`
