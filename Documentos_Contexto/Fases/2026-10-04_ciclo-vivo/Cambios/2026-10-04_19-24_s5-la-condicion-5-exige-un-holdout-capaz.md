# La condición 5 ya no se cumple con un holdout que no ve el efecto declarado

- **Fecha/hora:** 2026-10-04 19:24
- **Área:** Fases/2026-10-04_ciclo-vivo · **Acción:** Cambios
- **Chat / página:** sesión de la Fase 5 · la decisión C1, aprobada por el usuario
- **Archivos afectados:** `src/melate/protocolo.py`, `tests/test_protocolo.py`, `scripts/mutar.py`

## Qué se hizo

- **`protocolo.condicion_efecto_minimo`** (`src/melate/protocolo.py:182`) gana una comprobación antes
  de la de siempre (`:211`): si el preregistro declara un efecto y el mínimo detectable del holdout es
  mayor que él, la condición no se cumple, sea cual sea el delta. Si no lo declara, todo sigue como
  estaba. El nombre de la condición no cambia.
- **`protocolo._holdout_incapaz`** (`:222`), nueva, escribe el motivo: el detectable con ese tamaño
  de holdout, el declarado, cuántos sorteos hacen falta y cuántos faltan. Con el preregistro sellado y
  un sorteo: *«el mínimo detectable con 1 sorteo de holdout es 2.023745, mayor que el 0.048 declarado
  en el sello: hacen falta 1778 sorteos (faltan 1777), y hasta entonces ningún delta cuenta (delta
  medido +2.3571)»*.
- **Diez tests nuevos** en `tests/test_protocolo.py`, seis rápidos y cuatro lentos: un sorteo no basta;
  sin efecto declarado nada cambia; el efecto declarado gobierna la frontera, con dos valores (0,048
  → 1778 sorteos; 0,10 → 410); el motivo no promete plazos que no puede calcular; el «sí» sigue
  existiendo con el efecto declarado; y, con el laboratorio real, los cuatro sorteos históricos que
  declaraban ventaja con un holdout de un sorteo.
- **Dos mutaciones** en `scripts/mutar.py`, las primeras de la Fase 5: quitar la regla, y hacer que con
  efecto declarado la condición no se cumpla nunca. Detectadas las dos.

## Por qué

Lo decidió el usuario (C1, opción A) a las 18:58, antes del sorteo del 4274 y sin que nadie calculara
qué números elegiría la logística para él:
`Protocolo_Estadistico/Decisiones/2026-10-04_18-58_s5-la-condicion-5-exige-un-holdout-capaz.md`.
Con la regla anterior, el laboratorio real declaraba VENTAJA DEMOSTRADA con un holdout de un sorteo en
los sorteos 2928, 3419, 3953 y 4205, y bajo el azar le pasaba una vez de cada 303.

## Impacto en seguridad / conexiones / datos

- **Seguridad:** sin impacto. Una función pura, sin entrada nueva salvo el efecto que declara un
  preregistro sellado.
- **Conexiones:** ninguna.
- **Datos:** ninguna cifra publicada cambia. Los dos veredictos publicados tienen el holdout vacío, y
  su condición 5 falla por eso. El preregistro no se toca y su sello sigue verificando. La paridad con
  el oráculo, intacta.

## Lo medido

| Qué | Antes | Ahora |
|---|---|---|
| P(VENTAJA DEMOSTRADA \| azar) con 1 sorteo, el 0,048 declarado | 0,003297 | **0** |
| Ídem con 2 a 6 sorteos | entre 0,000301 y 0,002071 | **0** |
| Ídem sin efecto declarado | 0,003297 | 0,003297 (la regla solo endurece lo declarado) |
| Sorteo 4205, laboratorio real, holdout de 1 sorteo | VENTAJA DEMOSTRADA, 5 de 5 | sin ventaja demostrada, 4 de 5 |
| `tests/test_protocolo.py` | 46 | **56** en verde, 14,6 s |
| Bucle rápido | 213, 13,8 s | **219**, 10,5 s |

Las probabilidades salen de enumerar todas las combinaciones de aciertos de los tres juegos y llamar al
`declara_ventaja` real. La review del bloque, con sus cuatro hallazgos —tres de redacción del motivo
y una contraprueba que faltaba—, está en
`Fases/2026-10-04_ciclo-vivo/Bugs/2026-10-04_19-16_s5-review-c1-condicion-5.md`.

## Cómo verificar / revertir

```powershell
.venv\Scripts\python.exe -m pytest tests\test_protocolo.py -q        # 56 en verde
.venv\Scripts\python.exe scripts\mutar.py --solo "F5"                 # 2 de 2
```

Y el caso del 4205 con el laboratorio real, con el fragmento de «Cómo verificar» de la decisión:
tiene que imprimir `sin ventaja demostrada 4`.

**Revertir:** quitar de `protocolo.condicion_efecto_minimo` el bloque de `:211-213`, la función
`_holdout_incapaz`, `import math`, los diez tests nuevos y las dos mutaciones «F5». **No se
recomienda:** vuelve a abrir la puerta de declarar ventaja con un sorteo, una vez de cada 303 bajo el
azar, y alrededor del 1 % de las historias en los cien primeros sorteos de un ciclo que evalúa con
cada uno.

Relacionado: `Protocolo_Estadistico/Decisiones/2026-10-04_18-58_s5-la-condicion-5-exige-un-holdout-capaz.md`,
`Fases/2026-10-04_ciclo-vivo/Bugs/2026-10-04_19-16_s5-review-c1-condicion-5.md`,
`Fases/2026-10-04_ciclo-vivo/Decisiones/2026-10-04_18-59_s5-lo-que-decidio-el-usuario.md`.
