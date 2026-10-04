# La tercera fuente: las tablas de ganadores de melate-e.com

- **Fecha/hora:** 2026-10-03 05-15
- **Área:** Conexiones · **Acción:** Añadir

## Qué se añadió

Una fuente HTTP nueva, y la primera que **no es oficial**:

```
https://resultados.melate-e.com/{melate,revancha}/sorteo/{n}
```

Devuelve HTML estático (nginx + PHP, 5-8 KB, sin JavaScript) con la tabla de ganadores por
categoría: cuántos acertaron 5, 4, 3 y 2 números, y cuánto cobró cada uno. **Ese dato no está en
ningún CSV oficial**, y es el que permite estimar cuántas combinaciones se venden y cuánto paga de
verdad un boleto.

El cliente es `src/melate/popularity.py`, con Scrapling (`FetcherSession`), caché permanente en
disco y una solicitud por segundo.

## Por qué un tercero, habiendo fuente oficial

La hay, y el propio sitio la enlaza: la mascarilla de Pronósticos, que **redirige a
`loterianacional.gob.mx`** — el mismo dominio del que este proyecto ya carga los CSV. Se intentó:

| Comprobación | Resultado |
|---|---|
| `www.pronosticos.gob.mx` con TLS verificado | falla, `SEC_E_WRONG_PRINCIPAL` |
| Sin `www`, siguiendo el 301, TLS verificado | 200, `application/pdf`, 882.608 bytes |
| Texto extraíble | 25.885 caracteres: las **etiquetas** (`LUGAR`, `GANADORES`, `PREMIO INDIVIDUAL`) |
| Dígitos en ese texto | **1 en 25.885** |

Las cifras están dibujadas, no escritas. Sacarlas exigiría OCR, que es una fuente de error nueva y
silenciosa — y este proyecto ya tiene una cicatriz de un error silencioso de un tercero
(`Fases/2026-10-02_arranque/Bugs/2026-10-02_23-29_s1-porton-linea-base.md`).

**El tercero no se usa por comodidad: se usa porque la fuente oficial de este dato no es legible
por máquina.** Si algún día Lotería Nacional publica las tablas en CSV, esta decisión se reabre.

## El contrato con el sitio

Está en `Fases/2026-10-03_popularidad/Decisiones/2026-10-03_02-40_s3-dictamen-terminos-melate-e.md`,
escrito **antes** que el código. En corto, y todo con test:

| Regla | Valor |
|---|---|
| Ritmo | 1 solicitud/segundo, medida entre inicios |
| Caché | permanente en disco; una página descargada no se vuelve a pedir |
| Identificación | `MaquinaMelate/0.1 (analisis personal; github.com/…)`, sin `Mozilla/5.0` |
| Sin evasión | `impersonate=None`, `stealthy_headers=False` |
| Sin navegador | solo `Fetcher`/`FetcherSession`; `StealthyFetcher` y `DynamicFetcher` prohibidos |
| Revanchita | no se pide: **no tiene tabla** (solo paga 6 aciertos) |
| Ventana | obligatoria y declarada; el histórico completo no se descarga sin decisión del usuario |
| Si bloquean | se para y se pregunta |

Comportamiento real medido en la cosecha de la fase: **400 páginas, 398 peticiones, 399 segundos**
— 1,00 solicitudes por segundo.

## El regalo: una tercera fuente para la regla 7

La página publica **también los números sorteados**. No se usan para analizar —para eso manda el
CSV oficial— pero compararlos sale gratis, y es exactamente la comprobación que le habría ahorrado
al proyecto el error de Revancha 3827, invisible a cualquier validación de una sola fuente.

`popularity.discrepancias()` lo hace. Resultado sobre la ventana 4173-4272:

```
Melate    4173-4272: 0 discrepancias
Revancha  4173-4272: 0 discrepancias
```

**200 sorteos confirmados por una tercera fuente independiente del oficial y del espejo.**

## Qué NO cambia

- `src/melate/ingest.py` no se toca. El oficial sigue siendo la única carga y el espejo sigue
  siendo solo validación cruzada.
- El oráculo no conoce este módulo.
- Ningún camino de red nuevo entra en el informe por defecto: `--popularidad` es opcional y lee un
  fichero ya descargado.

## Cómo verificar

```powershell
.venv\Scripts\python.exe -m pytest tests/test_popularidad.py -q      # 36 pruebas
.venv\Scripts\python.exe -m pytest tests/test_popularidad.py -q -m red  # contra el sitio real
.venv\Scripts\python.exe -m melate.popularity --desde 4173 --hasta 4272 --datos data/raw/2026-10-02
```

La tercera, con la caché ya poblada, hace **0 peticiones de red** y lo imprime.

> **Nota del 2026-10-04 (Fase 4).** Dos cosas de este bloque ya no son así. `test_popularidad.py`
> tiene hoy 37 pruebas. Y la segunda orden **no iba contra el sitio real**: su test leía el sorteo
> 4272 de la caché permanente y hacía 0 peticiones. Ahora sí va, con una caché de usar y tirar, por
> decisión del usuario:
> `Conexiones/Modificar/2026-10-04_16-35_s4-el-test-del-sitio-pide-la-pagina-de-verdad.md`.

## Cómo revertir

Borrar `src/melate/popularity.py`, `tests/test_popularidad.py`, la línea `scrapling[fetchers]`
de `requirements.txt`, la entrada `data/cache/` de `.gitignore` y la carpeta `data/cache/`. El
resto del proyecto no depende de este módulo.

Relacionado: `Conexiones/Añadir/2026-10-03_00-13_s1-fuentes-de-datos.md`,
`Fases/2026-10-03_popularidad/Decisiones/2026-10-03_02-40_s3-dictamen-terminos-melate-e.md`,
`Seguridad/Añadir/2026-10-03_05-15_s3-trafico-saliente-a-un-tercero.md`,
`Almacenamiento/Añadir/2026-10-03_05-15_s3-cache-de-paginas.md`.
