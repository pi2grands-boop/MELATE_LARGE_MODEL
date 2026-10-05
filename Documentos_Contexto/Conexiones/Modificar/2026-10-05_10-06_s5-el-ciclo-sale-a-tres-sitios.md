# El ciclo sale a tres sitios, y cada uno tiene su papel

- **Fecha/hora:** 2026-10-05 10:06
- **Área:** Conexiones · **Acción:** Modificar
- **Chat / página:** cierre de la Fase 5 · `Fases/2026-10-04_ciclo-vivo/`
- **Archivos afectados:** `src/melate/ciclo.py`

## Qué cambia

Hasta la Fase 4, el oficial se pedía solo al explorar con datos de hoy, y melate-e.com solo para
ventanas declaradas de popularidad. **El ciclo los convierte en una relación recurrente**: lo que pide
en cada corrida, a quién y para qué. La tabla de
`Conexiones/Modificar/2026-10-04_16-35_s4-el-test-del-sitio-pide-la-pagina-de-verdad.md` queda así:

| Quién | A dónde | Cuándo | Para qué |
|---|---|---|---|
| `melate.ciclo` | `loterianacional.gob.mx` | **3 peticiones en cada corrida**, también con `--comprobar` | La única fuente de carga |
| `melate.ciclo` | `raw.githubusercontent.com` | 3, solo si hay sorteos nuevos | Testigo: el espejo, nunca carga |
| `melate.ciclo` | `resultados.melate-e.com` | **2 páginas por sorteo nuevo**, Melate y Revancha, a 1 por segundo; ninguna con `--comprobar` o `--sin-testigo melate-e`; nunca dos veces la misma | Testigo, y la tabla de ganadores de la popularidad |
| `melate.ingest.cargar` | `loterianacional.gob.mx` | solo sin `--datos`: un informe o un laboratorio con los datos de hoy | Explorar; un veredicto así ya no puede ser el vigente |
| `melate.popularity` | `resultados.melate-e.com` | solo las páginas que no están en la caché | Ventanas declaradas |
| `tests/test_reglas_datos.py` y `tests/test_popularidad.py`, los `red` | `raw.githubusercontent.com` y `resultados.melate-e.com` | en cada `pytest tests`: 7 conexiones, las mismas que antes de la fase | Vigilar a los testigos |
| `tests/test_ciclo.py` | nadie | — | Fuentes falsas y un servidor en `127.0.0.1` |
| La app y `python -m melate.app` | nadie | — | — |

## La regla de los testigos (C2.2, decidida por el usuario)

El oficial es la fuente; el espejo y melate-e.com, testigos de cada sorteo nuevo antes de congelarlo.

- **Un testigo que discrepa para el ciclo.** Es un hallazgo: se investiga con una tercera fuente antes
  de elegir un valor (regla 7 del `CLAUDE.md`), y ninguna opción lo salta.
- **Un testigo que falta hace esperar**: atrasado, caído, sin la página o con una página sin sus seis
  números. Seguir sin él se pide con `--sin-testigo`, y la procedencia del snapshot lo deja escrito.
- **Revanchita se valida con dos fuentes**, oficial y espejo (C2.1): el dictamen no permite pedir su
  página. Un desacuerdo ahí se desempata a mano.

## El dictamen con melate-e.com no cambia

Ritmo, caché permanente, identificación honesta, Revanchita no se pide, y si bloquea, se para y se
pregunta (el ciclo sale con el código 4). El ciclo es un llamador nuevo con la ventana acotada a los
sorteos nuevos. **Lo que sigue sin decidir**, y por eso se pregunta si pasa: volver a pedir una página
que llegó incompleta. La del 4273, pedida dos días después de su sorteo, y la del 4274, unas once horas
después, llegaron enteras.

## Medido en vivo, con un proxy que solo apunta

| Corrida | Conexiones |
|---|---|
| El ciclo con el 4274 (2026-10-05 09:22) | 3 al oficial, 3 a GitHub, 1 a melate-e.com con 2 páginas |
| `--comprobar` con un sorteo nuevo | 3 al oficial, 3 a GitHub, 0 a melate-e.com |
| «Nada nuevo» | 3 al oficial, ninguna más |
| La app con el veredicto del 4274 | ninguna |
| `pytest tests` | 7, como antes |

## Cómo verificar / revertir

```powershell
.venv\Scripts\python.exe -m melate.ciclo --comprobar      # «Peticiones de red de esta corrida: …»
.venv\Scripts\python.exe -m pytest tests\test_ciclo.py -k "byte_a_byte or nada_nuevo" -q
```

**Revertir** es quitar el ciclo
(`Fases/2026-10-04_ciclo-vivo/Cambios/2026-10-05_10-03_s5-el-ciclo-vivo.md`): las conexiones nuevas
desaparecen con él.

Relacionado: `Conexiones/Modificar/2026-10-04_16-35_s4-el-test-del-sitio-pide-la-pagina-de-verdad.md`,
`Conexiones/Añadir/2026-10-03_00-13_s1-fuentes-de-datos.md`,
`Conexiones/Añadir/2026-10-03_05-15_s3-tablas-de-ganadores-melate-e.md`,
`Fases/2026-10-03_popularidad/Decisiones/2026-10-03_02-40_s3-dictamen-terminos-melate-e.md`,
`Almacenamiento/Decisiones/2026-10-04_20-10_s5-el-ciclo-vivo.md`.
