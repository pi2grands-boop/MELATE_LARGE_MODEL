# Qué hace falta para que este proyecto pueda afirmar algo

- **Fecha/hora:** 2026-10-03 01:30
- **Área:** Protocolo_Estadistico · **Acción:** Añadir
- **Chat / página:** sesión de arranque · emitido al cerrar la Fase 2
- **Archivos afectados:** `src/melate/lab.py`, `src/melate/protocolo.py`, `prereg/*.json`

## Qué se hizo

El proyecto ya no puede declarar una ventaja que no haya pasado el protocolo. Esto es el mecanismo.

### El preregistro: una apuesta con fecha

Un `prereg/*.json` declara, **antes de que existan los datos que lo juzgarán**, qué se va a mirar,
cómo se va a juzgar y con qué umbral. Dos campos lo convierten en algo más que buenas intenciones:

- **`sello_utc`** — la frontera. El holdout son los sorteos con `FECHA` **posterior** a esta fecha.
- **`sello_sha256`** — hash del JSON canónico de todo lo demás. Cambiar un byte lo invalida.

Y tres negativas que lo sostienen:

1. **Sin preregistro no se evalúa.**
2. **No se sobrescribe un sello.** Si la hipótesis cambia, se sella otro con otra fecha.
3. **No se sella en el pasado.** Un preregistro antedatado no preregistra nada: su holdout incluiría
   sorteos que ya se pueden mirar. Hay una hora de margen para desfases de reloj, y nada más.

Las cuatro formas obvias de hacer trampa a posteriori —aflojar el umbral, encoger la familia de
corrección, antedatar el sello, cambiar la hipótesis por otra— están cubiertas por tests sobre el
fichero real del repositorio.

### Las 5 condiciones de la regla 5, y qué mata cada una

Se evalúan **todas**, aunque la primera falle: cuando algo no pasa, lo útil es saber qué.

| # | Condición | El error que impide |
|---|---|---|
| 1 | Holdout futuro positivo | Mirar el pasado y llamarlo predicción |
| 2 | `q_BH_global` ≤ 0.05 | Pescar entre muchas pruebas y reportar la mejor |
| 3 | Estable al mover hiperparámetros | Un efecto que solo existe con una configuración concreta |
| 4 | Mismo signo en Melate, Revancha y Revanchita | Ruido de un juego disfrazado de patrón de la urna |
| 5 | Efecto ≥ mínimo detectable | Medir algo más pequeño que el error de medición |

**La 4 es la más dura y la que más hallazgos falsos mata.** Los tres juegos comparten mecánica: un
patrón real de la urna tendría que aparecer en los tres. Uno que solo sale en Revancha es ruido, y
es exactamente la forma del hallazgo exploratorio de la Fase 1.

**Un holdout vacío no es un empate.** Es la información de que todavía no se ha jugado nada a esa
carta, y la condición 1 lo dice con esas palabras.

### La familia de corrección se declara, no se elige después

`benjamini_hochberg` acepta ahora `m`, el tamaño de una familia fijada por adelantado. El holdout
corre 3 pruebas —una por juego— pero el preregistro declara pertenecer a una familia de 36:
corregir contra 3 sería aflojar el criterio después de haberlo fijado.

**`m` menor que las pruebas corridas se rechaza**, porque sería precisamente la manera de hacer
trampa. Y las variantes de hiperparámetros **no** cuentan como pruebas: son comprobaciones de
robustez de la misma hipótesis, y contarlas inflaría la familia sin añadir ninguna hipótesis.

### El veredicto de hoy

```
sin ventaja demostrada  (0 de 5 condiciones)
  [NO] holdout futuro positivo   holdout vacío: 0 sorteos posteriores al sello
```

Hoy es **imposible** declarar ventaja, y así debe ser.

## El coste honesto, dicho de antemano

Con un efecto mínimo detectable de 0.048 aciertos por boleto, la condición 5 necesita del orden de
**1 800 sorteos de holdout: unos 11 años** a tres sorteos por semana.

Eso no es un defecto del diseño. Es la medida de cuánta evidencia haría falta para afirmar algo
sobre un juego que, por lo que se sabe, es limpio. Y saberlo de antemano es mucho mejor que
descubrirlo después de haberse convencido: quien quiera recortar ese plazo tendrá que hacerlo
aflojando una condición, y entonces se verá.

## Por qué

Con 56 números, decenas de estrategias y miles de sorteos, **algo siempre destaca**. El problema no
es encontrar un patrón: es distinguirlo de uno real.

La Fase 1 lo vivió de primera mano. Su resultado más llamativo —regresión logística en Revancha, la
única de las 8 estrategias con p < 0.05 sin corregir— estaba en parte inflado por un número mal
transcrito en una fuente de respaldo. Con el dato correcto seguía siendo el que más invitaba a
seguir tirando del hilo. Ese es el momento exacto en el que un proyecto se autoengaña, y la
respuesta del `CLAUDE.md` es preregistrar antes de evaluar.

Un preregistro no hace que una corazonada sea cierta. Hace que sea **falsable**, y pone la fecha a
partir de la cual cuenta.

## Impacto en seguridad / conexiones / datos

- **Seguridad:** sin cambios en la superficie de ataque. Lo que cambia es la superficie de
  autoengaño.
- **Conexiones:** ninguna nueva.
- **Datos:** aparece `prereg/` como almacén de documentos sellados e inmutables.

## Cómo verificar

```powershell
.venv\Scripts\python.exe -m melate.lab --prereg .\prereg\2026-10-03_logistica-revancha.json --datos .\data\raw\2026-10-02
.venv\Scripts\python.exe -m pytest tests\test_protocolo.py -q        # 41 pruebas
```

Que el mecanismo protege, y que el camino afirmativo existe —que importa igual, porque un
laboratorio incapaz de decir "sí" ni en el caso perfecto no es prudente, está roto:

```powershell
.venv\Scripts\python.exe -m pytest tests\test_protocolo.py -k "manipular or camino_afirmativo" -v
```

Relacionado: `Protocolo_Estadistico/Decisiones/2026-10-03_00-13_s1-familias-benjamini-hochberg.md`,
`Fases/2026-10-03_protocolo/Cambios/2026-10-03_01-25_s2-laboratorio-y-preregistro.md`,
`Almacenamiento/Añadir/2026-10-03_01-30_s2-prereg-sellado.md`
