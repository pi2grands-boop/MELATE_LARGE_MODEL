# `prereg/`: documentos sellados e inmutables

- **Fecha/hora:** 2026-10-03 01:30
- **Área:** Almacenamiento · **Acción:** Añadir
- **Chat / página:** sesión de arranque · emitido al cerrar la Fase 2
- **Archivos afectados:** `prereg/2026-10-03_logistica-revancha.json`, `src/melate/lab.py`

## Qué se hizo

Un almacén nuevo, con una propiedad que ninguno de los anteriores tenía: **sus ficheros se
autoverifican**.

```
prereg/
  2026-10-03_logistica-revancha.json    sello 2026-10-03T06:45:00Z
                                        sello_sha256 36edc964461c0152...
```

### Reglas del almacén

- **Un fichero por hipótesis preregistrada.** El nombre lleva la fecha del sello y un slug de la
  hipótesis.
- **Inmutable.** `lab.sellar()` se niega a sobrescribir. Si la hipótesis cambia, se sella otro con
  otra fecha; el viejo se queda como constancia de lo que se pensaba entonces.
- **Se autoverifica.** `sello_sha256` es el SHA-256 del JSON canónico de todo el contenido menos ese
  campo: claves ordenadas, sin espacios, UTF-8. `lab.cargar_preregistro()` lo recalcula y **se niega
  a devolver el fichero si no cuadra**.
- **No se puede sellar en el pasado.** Una hora de margen para desfases de reloj, y nada más.
- **Se sube al repositorio.** Un preregistro que solo existe en la máquina de quien lo escribió no
  preregistra gran cosa.

### Qué cubre el hash, y qué no

Cubre **el contenido**, no los bytes. El hash se calcula sobre el JSON canónico del documento ya
parseado, así que:

- Reindentar el fichero, reordenar sus claves o añadirle un BOM **no** invalida el sello. Es lo
  correcto: no son cambios de contenido, y un editor de Windows puede hacerlos sin avisar.
- Cambiar **cualquier valor** sí lo invalida. Comprobado sobre el fichero real con las cuatro
  manipulaciones que importan: aflojar `umbral_q`, encoger `tamano_familia`, antedatar `sello_utc` y
  cambiar `juego_principal`.

Por eso la lectura usa `utf-8-sig`: con `utf-8` a secas, un BOM daba un error de JSON que no decía
nada en vez del mensaje del sello.

### El preregistro ancla el snapshot

`datos_al_sellar` guarda los tres SHA-256 del snapshot vigente y su último concurso. Es la regla 6
del protocolo aplicada al propio preregistro: queda constancia de **qué datos existían cuando se
sellaron las reglas**, que es lo que permite afirmar que el holdout es de verdad futuro. Hay un test
que comprueba que esos hashes cuadran con `data/raw/2026-10-02/SHA256.txt`.

## Por qué

Los otros almacenes del proyecto guardan hechos: los sorteos que salieron, las cifras que se
midieron. `prereg/` guarda **compromisos**, y un compromiso que se puede editar después no es un
compromiso.

El mecanismo del hash existe por eso y no por seguridad informática: nadie va a atacar este
repositorio. Lo que protege es contra uno mismo, dentro de seis meses, con un resultado que casi
pasa el umbral y la tentación de que el umbral era un poco estricto.

## Impacto en seguridad / conexiones / datos

- **Seguridad:** un fichero de `prereg/` no contiene nada sensible —es metodología— y el colador lo
  inspecciona como todo lo demás. El hash no es una medida de seguridad: es de integridad.
- **Conexiones:** ninguna.
- **Datos:** un fichero JSON de unos 4 KB por hipótesis. Crece a razón de una por hipótesis
  preregistrada, lo que a este ritmo es nada.

## Cómo verificar / revertir

```powershell
.venv\Scripts\python.exe -c "from melate import lab; s = lab.cargar_preregistro('prereg/2026-10-03_logistica-revancha.json'); print('verificado:', s['id'], s['sello_utc'])"
.venv\Scripts\python.exe -m pytest tests\test_protocolo.py -k "preregistro or manipular or bom" -v
```

Y a mano, que el hash es el que dice ser:

```powershell
.venv\Scripts\python.exe -c "import json; from melate import lab; s = json.load(open('prereg/2026-10-03_logistica-revancha.json', encoding='utf-8')); print(s[lab.CLAVE_HASH] == lab.hash_preregistro(s))"
```

**Revertir:** borrar `prereg/`. **Lo que se reintroduce:** la posibilidad de decidir el criterio
después de ver el resultado.

Relacionado: `Protocolo_Estadistico/Añadir/2026-10-03_01-30_s2-preregistro-y-las-cinco-condiciones.md`,
`Almacenamiento/Añadir/2026-10-03_00-13_s1-snapshots-congelados.md`,
`Estructura_Datos/Añadir/2026-10-03_01-30_s2-formato-del-preregistro.md`
