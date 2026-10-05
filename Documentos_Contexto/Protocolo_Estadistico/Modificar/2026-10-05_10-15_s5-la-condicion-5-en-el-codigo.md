# La condición 5, en el código: un holdout que no ve el efecto declarado no cuenta

- **Fecha/hora:** 2026-10-05 10:15
- **Área:** Protocolo_Estadistico · **Acción:** Modificar
- **Chat / página:** cierre de la Fase 5 · `Fases/2026-10-04_ciclo-vivo/`
- **Archivos afectados:** `src/melate/protocolo.py`, `src/melate/lab.py`

## Qué cambia

`Protocolo_Estadistico/Añadir/2026-10-03_01-30_s2-preregistro-y-las-cinco-condiciones.md` dice que,
con un efecto mínimo detectable de 0,048 aciertos, la condición 5 «necesita del orden de 1 800
sorteos de holdout». **El código no lo exigía.** Comparaba el delta con el mínimo detectable del
propio holdout, que con un sorteo es 2,02 aciertos: un sorteo con tres aciertos en Revancha lo
superaba, y el laboratorio real declaraba VENTAJA DEMOSTRADA, 5 de 5, en cuatro sorteos históricos
(H1 del inventario de la Fase 5).

Desde la decisión del usuario del 2026-10-04 a las 18:58, antes del sorteo del 4274
(`Protocolo_Estadistico/Decisiones/2026-10-04_18-58_s5-la-condicion-5-exige-un-holdout-capaz.md`):

- **`protocolo.condicion_efecto_minimo`** (`src/melate/protocolo.py:187`): si el preregistro declara
  un efecto y el mínimo detectable del holdout es mayor que él, la condición no se cumple, sea cual sea
  el delta. Sin efecto declarado, como antes. El nombre de la condición y las cinco de la regla 5 no
  cambian.
- **El motivo dice cuánto falta** (`_holdout_incapaz`, `:227`): *«el mínimo detectable con 1 sorteo
  de holdout es 2.023745, mayor que el 0.048 declarado en el sello: hacen falta 1778 sorteos (faltan
  1777)…»*.
- **El veredicto publica la frontera**, `resultados.holdout_necesario` (`src/melate/lab.py:312`): 1 778
  con el preregistro sellado, 410 con un efecto de 0,10 y 103 con uno de 0,20. `lab.detectable(n)`
  es la única copia de la fórmula.

## Lo que asegura, medido

| Bajo el azar | Regla de antes | Ahora |
|---|---|---|
| P(VENTAJA DEMOSTRADA) con 1 sorteo de holdout | 0,003297 (1 de cada 303) | **0** |
| Ídem con 2 a 6 sorteos | entre 0,000301 y 0,002071 | **0** |
| Alguna declaración en 1 777 evaluaciones, una por sorteo | 1,40 % | **0 %**, por construcción |
| Ídem diez años después del sorteo 1 778 | 1,45 % | **0,095 %** |

Las probabilidades exactas, con el `declara_ventaja` real; el Monte Carlo, 200 000 historias con su
semilla. **Vueltas a medir al cerrar la fase, iguales**: el Monte Carlo, idéntico línea por línea.

## Qué NO cambia

- El preregistro sellado: su sello sigue verificando, y la prueba que declara tampoco cambia.
- El oráculo, la paridad y la familia de 36 pruebas.
- Que se pueda declarar ventaja: con el efecto declarado y un holdout capaz, el «sí» sigue existiendo
  (`test_con_el_efecto_declarado_el_camino_afirmativo_sigue_existiendo`).

## Cómo verificar

```powershell
.venv\Scripts\python.exe -m pytest tests\test_protocolo.py -q
.venv\Scripts\python.exe scripts\mutar.py --solo "F5"       # las 51 de la Fase 5; las tres de esto llevan «(C1)»
```

## Cómo revertir

Descrito en `Fases/2026-10-04_ciclo-vivo/Cambios/2026-10-04_19-24_s5-la-condicion-5-exige-un-holdout-capaz.md`.
**No se recomienda:** vuelve a abrir la puerta de declarar ventaja con un sorteo, una vez de cada 303
bajo el azar.

Relacionado: `Protocolo_Estadistico/Decisiones/2026-10-04_18-58_s5-la-condicion-5-exige-un-holdout-capaz.md`,
`Protocolo_Estadistico/Añadir/2026-10-03_01-30_s2-preregistro-y-las-cinco-condiciones.md`,
`Protocolo_Estadistico/Añadir/2026-10-05_10-26_s5-el-primer-veredicto-con-holdout.md`,
`Fases/2026-10-04_ciclo-vivo/Bugs/2026-10-04_19-16_s5-review-c1-condicion-5.md`.
