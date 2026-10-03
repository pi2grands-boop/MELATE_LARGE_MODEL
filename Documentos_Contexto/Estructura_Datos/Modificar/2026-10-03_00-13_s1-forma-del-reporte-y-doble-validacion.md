# La forma del reporte gana tres claves, y la validación pasa a dar dos vistas

- **Fecha/hora:** 2026-10-03 00:13
- **Área:** Estructura_Datos · **Acción:** Modificar
- **Chat / página:** sesión de arranque · emitido al cerrar la Fase 1
- **Archivos afectados:** `src/melate/informe.py`, `src/melate/validate.py`,
  `src/melate/protocolo.py`, `src/melate/ingest.py`, `reportes/2026-10-02_paquete.json`

## Qué se hizo

### La forma de los datos cargados

`cargar()` devuelve un `DataFrame` con cinco columnas, igual que el oráculo:

| Columna | Qué es |
|---|---|
| `CONCURSO` | entero, ascendente (el CSV oficial llega descendente y se ordena) |
| `FECHA` | `datetime` (oficial `dd/mm/aaaa`, espejo `aaaa-mm-dd`) |
| `nums` | lista de 6 enteros en 1..56, ascendentes |
| `R7` | el adicional; `NaN` en Revancha y Revanchita |
| `BOLSA` | float; la de la fila N es la anunciada para el sorteo N+1 |

**Novedad en `attrs`:** además de `fuente`, ahora lleva `sha256` y `bytes` de lo que realmente se
leyó. Es lo que alimenta el bloque de reproducibilidad, y sale de la carga y no de una segunda
lectura — ver el porqué en `Reproducibilidad/Añadir/`.

### Tres claves nuevas en el reporte, y ninguna cifra cambiada

Declaradas en `melate.informe.NUEVAS_CLAVES` para que el test de paridad sepa qué puede ignorar. El
resto del JSON es idéntico al del oráculo, con tolerancia cero.

```
validacion             igual que antes: sobre el fichero crudo
validacion_era_56      NUEVA: lo mismo, pero sobre la era 6/56
auditoria              + q_BH_global en cada estadístico
poder                  igual
backtest               + q_BH_global en cada estrategia
premios_mayores        igual
valor_esperado_proximo igual
protocolo_global       NUEVA: 36 pruebas, q mínima, supervivientes, veredicto
reproducibilidad       NUEVA: hash de datos, semillas, simulaciones, versiones, hora UTC
```

### Por qué la validación necesitaba dos vistas

`validar()` corre sobre el fichero **tal cual llegó**, y el de Melate arranca en 1984. En aquella
época las bolsas eran de otro orden de magnitud, así que el informe reportaba **174 filas con
`BOLSA` < 1 M** en Melate. De esas 174, **solo 3 son errores reales** —los sorteos 2120, 2142 y 2234
que el `CLAUDE.md` documenta—, y las otras 171 son simplemente bolsas pequeñas de hace cuarenta años.

El dato útil quedaba sepultado en el ruido, que es la forma más eficaz de que una validación deje de
leerse. Ahora:

- `validacion` — el fichero completo. **No se toca**: es lo que produce el oráculo.
- `validacion_era_56` — las mismas nueve comprobaciones sobre la era 6/56, que es la que se analiza.
  Aquí Melate da exactamente `[2120, 2142, 2234]`.

`validar_era()` reutiliza `validar()` en lugar de duplicar las comprobaciones, y vuelve a poner
`fuente` en `attrs` después del filtrado, porque un filtro booleano no garantiza que `attrs`
sobreviva.

### `q_BH` no se renombra

La clave del oráculo se queda como está y la familia global se añade como `q_BH_global`. Renombrarla
habría roto la paridad y, peor, habría hecho irreproducibles los `q` ya publicados en el `CLAUDE.md`.
**Una clave de reporte publicada es una interfaz.**

### Serialización

`json.dump(..., ensure_ascii=False, indent=1, default=str)`, igual que el oráculo. `default=str` es
necesario porque hay tipos de numpy y `Timestamp` en el reporte; `ensure_ascii=False` porque los
nombres de las estrategias llevan acentos y el `CLAUDE.md` pide los textos en español.

## Por qué

Dos de las tres claves nuevas son deuda del protocolo que el código heredado no cumplía: el hash y
las semillas (regla 6) y Benjamini-Hochberg sobre todas las pruebas (regla 3). La tercera es un
arreglo de legibilidad con consecuencias prácticas: una validación que grita 174 veces es una
validación que nadie mira.

Las tres se añaden **sin tocar ninguna clave existente**, para que la paridad con el oráculo siga
siendo una prueba y no una aproximación.

## Impacto en seguridad / conexiones / datos

- **Seguridad:** el reporte gana rutas de ficheros en `reproducibilidad.datos[*].origen`. Con los
  comandos documentados son **relativas**, y el colador lo comprueba antes de cada push. Si alguien
  corre el informe con una ruta absoluta, el reporte la llevará: no se sube.
- **Conexiones:** sin cambios.
- **Datos:** ningún fichero de datos se modificó. Cambia la forma del reporte, hacia atrás
  compatible: solo añade.

## Cómo verificar / revertir

```powershell
.venv\Scripts\python.exe -m pytest tests\test_paridad.py -v

# las dos vistas de validacion, con los 174 contra los 3
.venv\Scripts\python.exe -c "import json;r=json.load(open('reportes/2026-10-02_paquete.json',encoding='utf-8'));print('crudo :',len(r['validacion']['Melate']['bolsa_cero_o_invalida']));print('era   :',r['validacion_era_56']['Melate']['bolsa_cero_o_invalida'])"
# -> crudo : 174      era : [2120, 2142, 2234]
```

**Revertir:** quitar de `informe.construir` las tres claves y las dos llamadas de `protocolo`.
`validate.validar_era` puede quedarse sin usar o borrarse. **Lo que se reintroduce:** un reporte sin
hash ni semillas (incumple la regla 6), sin la corrección global (incumple la regla 3), y con la
validación ahogada en 171 falsos positivos.

Relacionado: `Reproducibilidad/Añadir/2026-10-03_00-13_s1-linea-base-reproducida.md`,
`Protocolo_Estadistico/Decisiones/2026-10-03_00-13_s1-familias-benjamini-hochberg.md`,
`Fases/2026-10-02_arranque/Cambios/2026-10-03_00-03_s1-paquete-src-melate.md`
