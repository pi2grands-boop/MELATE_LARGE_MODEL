# La línea base, reproducida cifra por cifra, y con qué versiones

- **Fecha/hora:** 2026-10-03 00:13
- **Área:** Reproducibilidad · **Acción:** Añadir
- **Chat / página:** sesión de arranque · emitido al cerrar la Fase 1
- **Archivos afectados:** `CLAUDE.md`, `requirements.txt`, `entorno/pip-freeze-2026-10-02.txt`,
  `src/melate/ingest.py`, `src/melate/constantes.py`, `reportes/*.json`

## Qué se hizo

El portón de la fase: correr la línea base y comparar **las 12 cifras** del `CLAUDE.md` una por una.

```
.venv\Scripts\python.exe .\baseline_auditoria.py --datos .\data\raw\2026-10-02 --salida .\reportes\2026-10-02_oraculo.json
```

### El resultado, cifra por cifra

| Cifra del `CLAUDE.md` | Obtenido | |
|---|---|---|
| Sorteos era 6/56: 2 184 / 2 184 / 1 902 | 2184 / 2184 / 1902 | ✅ |
| Chi-cuadrada Melate 52.19 (p = 0.85) | 52.1889 (p = 0.8466) | ✅ |
| Chi-cuadrada Revancha 42.03 (p = 0.21) | **42.2889 (p = 0.2239)** | ❌ → cifra del contrato corregida |
| Chi-cuadrada Revanchita 54.83 (p = 0.98) | 54.8280 (p = 0.9815) | ✅ |
| Prueba desde el 2489 / 2771 | 2489 / 2489 / 2771 | ✅ |
| Regresión logística Revancha 0.6861 (p = 0.011, q = 0.24) | **0.6839 (p = 0.0165, q = 0.3465)** | ❌ → cifra del contrato corregida |
| Gradient boosting Melate 0.6160 | 0.6160 | ✅ |
| Aleatorio Melate 0.6328 | 0.6328 | ✅ |
| Premios mayores 69 / 61 / 35 | 69 / 61 / 35 | ✅ |
| EV del 4273: −59 % / −49 % / −12 % | −59 % / −49 % / −12 % | ✅ |
| Media del azar 0.642857, desviación 0.722357 | 0.6429 / 0.722357 | ✅ |
| Log-loss 0.340500, P(3+) = 1/79.06, efecto mínimo 0.048 | 0.34050 / 79.06 / 0.0477 | ✅ |

**Diez de doce exactas. Las dos fallas no eran del código: eran del contrato**, que se había
calculado con el espejo de GitHub, que tiene mal un número. Alimentando el script con ese dato
erróneo reproduce 42.03 y 0.6861 al cuarto decimal. El proceso de diagnóstico está en
`Fases/2026-10-02_arranque/Bugs/2026-10-02_23-29_s1-porton-linea-base.md`; las cifras del `CLAUDE.md`
quedaron corregidas.

### Las versiones que lo consiguen

No hubo que bisecar nada. La combinación instalada reproduce la línea base al cuarto decimal,
incluidas las dos cifras que pasan por scikit-learn:

```
Python 3.13.9 · numpy 2.5.3 · pandas 2.3.3 · scipy 1.18.1 · scikit-learn 1.9.1
```

`entorno/pip-freeze-2026-10-02.txt` tiene las 23 dependencias con su versión exacta.
`requirements.txt` guarda las restricciones, y una de ellas no es negociable:

**`pandas>=2.3,<3`.** La 3.0 cambia la propagación de `df.attrs`, que `baseline_auditoria.py` usa
—la escribe en la línea 68 y la lee en la 279, después de un recorte de columnas—. Migrar a pandas 3
es un cambio aparte, con su propio documento y su propia comprobación de paridad.

### Qué registra ahora cada corrida

La regla 6 del protocolo pide el hash del dataset y la semilla en cada corrida. El código heredado no
guardaba ninguno de los dos, aunque usaba tres semillas distintas. El paquete añade la clave
`reproducibilidad`:

```json
{"corrida_utc": "...", "simulaciones": 2000,
 "semillas": {"auditoria": 20261001, "backtest": 7, "hgb": 0},
 "datos": {"Melate": {"sha256": "51de5afd...", "origen": "...", "bytes": 206675}, ...},
 "versiones": {"python": "3.13.9", "numpy": "2.5.3", ...}}
```

Las semillas dejaron de ser literales sueltos en tres sitios y viven con nombre en
`constantes.py`: `SEMILLA_AUDITORIA`, `SEMILLA_BACKTEST`, `SEMILLA_HGB`.

**El hash sale de los bytes que se cargaron**, guardados en `df.attrs` por `ingest.cargar`. La
primera versión volvía a leer la fuente para hashear, en una segunda pasada: con el oficial a punto
de publicar el sorteo 4273, eso podía registrar el hash de unos datos distintos de los analizados,
que es exactamente lo contrario de lo que pide la regla. Está corregido y lo vigila
`tests/test_paridad.py::test_el_hash_registrado_es_el_de_los_datos_analizados`, que compara contra
los bytes del fichero **y** contra el `SHA256.txt` publicado.

### Y el `CLAUDE.md` también publica su procedencia

La sección "Línea base verificada" ganó un apartado con los tres SHA-256, las tres semillas y las
versiones. El hueco que permitió que el error pasara inadvertido durante quién sabe cuánto era
precisamente ese: **el documento publicaba cifras sin decir con qué datos ni con qué versiones se
obtuvieron.**

## Por qué

"Reproducible" sin versiones ni hash es una palabra vacía. Lo caro de este proyecto no es calcular,
es poder creerse el cálculo seis meses después — y la experiencia de esta misma fase lo demuestra:
sin el snapshot y sin saber qué datos produjeron cada cifra, la discrepancia de Revancha habría sido
indistinguible de un error de refactor, y se habría cerrado con un encogimiento de hombros.

## Impacto en seguridad / conexiones / datos

- **Seguridad:** sin impacto. Los hashes son de ficheros públicos.
- **Conexiones:** con `--datos` ninguna, que es la condición para que una corrida sea reproducible.
- **Datos:** sin cambios. El reporte gana la clave `reproducibilidad`.

## Cómo verificar / revertir

```powershell
.venv\Scripts\python.exe -m melate.informe --datos .\data\raw\2026-10-02 --salida .\reportes\x.json
.venv\Scripts\python.exe -m pytest tests\test_linea_base.py -v     # las 18 cifras
.venv\Scripts\python.exe -m pytest tests\test_paridad.py -v        # paridad y procedencia
```

Los tests de la línea base comprueban que el valor almacenado **redondea** a lo que publica el
`CLAUDE.md` (`round(p, 3) == 0.017`), no una tolerancia inventada. Esa diferencia es la que hace que
detecten una desincronización real entre documento y código.

**Revertir:** quitar la clave `reproducibilidad` de `informe.construir`, volver las semillas a
literales y relajar el pin de pandas. **No se recomienda, y la fase entera es el argumento:** se
pierde la capacidad de saber qué produjo cada cifra, que es lo único que permitió encontrar el error
del contrato.

Relacionado: `Almacenamiento/Añadir/2026-10-03_00-13_s1-snapshots-congelados.md`,
`Protocolo_Estadistico/Decisiones/2026-10-03_00-13_s1-familias-benjamini-hochberg.md`,
`Fases/2026-10-02_arranque/Bugs/2026-10-02_23-29_s1-porton-linea-base.md`
