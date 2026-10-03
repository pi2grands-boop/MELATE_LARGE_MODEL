# El formato de `prereg/*.json` y del veredicto

- **Fecha/hora:** 2026-10-03 01:30
- **Área:** Estructura_Datos · **Acción:** Añadir
- **Chat / página:** sesión de arranque · emitido al cerrar la Fase 2
- **Archivos afectados:** `prereg/2026-10-03_logistica-revancha.json`, `src/melate/lab.py`,
  `reportes/2026-10-03_veredicto.json`

## Qué se hizo

### El preregistro

Campos **obligatorios** —`cargar_preregistro` se niega si falta alguno—:

| Campo | Tipo | Para qué |
|---|---|---|
| `id` | texto | Identifica la hipótesis |
| `sello_utc` | ISO-8601 con zona | La frontera del holdout |
| `juegos` | lista | Los juegos que se evalúan. Hacen falta los tres para la condición 4 |
| `estrategias` | lista | La estrategia a evaluar |
| `umbral_q` | número | El umbral de `q`, fijado antes de medir |
| `sello_sha256` | hex de 64 | El hash del contenido canónico |

Campos que el evaluador **usa** si están:

| Campo | Qué cambia si falta |
|---|---|
| `juego_principal` | Se toma el primero de `juegos` |
| `tamano_familia` | **Sin él la condición 2 no se puede evaluar**, y el veredicto lo dice |
| `hiperparametros` | Se usan los de por defecto de la estrategia |
| `hiperparametros_alternativos` | **Sin ellos la condición 3 no se cumple**: no hay estabilidad que medir |
| `tolerancia_estabilidad` | 0.5 |
| `reentrenar_cada` | 100 |

Y campos que no se leen pero son el documento: `titulo`, `hipotesis`, `origen`, `advertencia`,
`metrica`, `linea_base`, `prueba`, `familia_de_correccion`, `entrenamiento`, `holdout`,
`criterio_de_declaracion`, `datos_al_sellar`, `semillas`, `entorno_al_sellar`, `notas`. Un
preregistro es para que lo lea una persona dentro de años; el código solo se encarga de que no se
pueda alterar.

**`tamano_familia` es un entero a propósito.** La primera versión lo decía en prosa
(`"global de 36 pruebas…"`) y eso obligaba a parsear texto para decidir un umbral estadístico.
`familia_de_correccion` se queda como la explicación en palabras; el número manda.

### El hash canónico

```python
json.dumps({k: v for k, v in spec.items() if k != "sello_sha256"},
           sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
```

Sobre eso, SHA-256. Que sea **canónico** es lo que hace que reindentar, reordenar claves o añadir un
BOM no invaliden el sello, mientras cambiar cualquier valor sí lo haga. El sello protege el
contenido, no el formato.

### El veredicto

```
preregistro    id, sello_utc, sello_sha256, estrategia, juego_principal
holdout        por juego: sorteos, primer_concurso, ultimo_concurso
resultados     del juego principal: sorteos_holdout, media, delta, z, p,
               q_BH_global, efecto_minimo_detectable,
               familia_declarada, pruebas_corridas, variantes[]
por_juego      lo mismo para los tres, que es lo que alimenta la condición 4
veredicto      veredicto, ventaja (bool), condiciones[5], cumplidas, de, por_que_no[]
corrida_utc    cuándo se evaluó
versiones      python, numpy, pandas, scipy, scikit-learn
```

Cada entrada de `condiciones` es `{condicion, cumple, motivo}`, y el `motivo` es texto para una
persona: *"delta +0.0664 aciertos sobre el azar en 430 sorteos de holdout"*, no un código de error.

**Las cinco condiciones están siempre**, cumplidas o no. No se cortocircuita: cuando algo falla, lo
útil es saber qué, y `por_que_no` recoge los motivos de las que no pasaron.

`indices` —la lista de posiciones del holdout— se calcula pero **no** se serializa: es un detalle
interno y engordaría el fichero sin aportar nada que no estén diciendo ya `primer_concurso` y
`ultimo_concurso`.

## Por qué

El formato tiene una restricción que los demás ficheros del proyecto no tienen: **tiene que seguir
siendo verificable sin el código que lo escribió.** De ahí que el hash sea canónico y no de bytes, y
que los campos obligatorios sean pocos y explícitos.

Y tiene un segundo público, que es el que de verdad importa: alguien —probablemente el propio
usuario— leyéndolo dentro de años con un resultado en la mano y ganas de que cuente. Por eso la
mitad de los campos son prosa que el código no mira.

## Impacto en seguridad / conexiones / datos

- **Seguridad:** sin impacto. Metodología, no datos.
- **Conexiones:** ninguna.
- **Datos:** dos formatos nuevos, los dos JSON UTF-8. El veredicto se escribe con
  `ensure_ascii=False, indent=1, default=str`, igual que el informe.

## Cómo verificar / revertir

```powershell
.venv\Scripts\python.exe -m pytest tests\test_protocolo.py -k "faltan_campos or preregistro" -v
.venv\Scripts\python.exe -c "import json;r=json.load(open('reportes/2026-10-03_veredicto.json',encoding='utf-8'));print([c['condicion'] for c in r['veredicto']['condiciones']])"
```

Tiene que imprimir las cinco condiciones, en orden.

**Revertir:** borrar `prereg/` y `lab.py`. El formato no lo usa nada más.

Relacionado: `Almacenamiento/Añadir/2026-10-03_01-30_s2-prereg-sellado.md`,
`Protocolo_Estadistico/Añadir/2026-10-03_01-30_s2-preregistro-y-las-cinco-condiciones.md`,
`Estructura_Datos/Modificar/2026-10-03_00-13_s1-forma-del-reporte-y-doble-validacion.md`
