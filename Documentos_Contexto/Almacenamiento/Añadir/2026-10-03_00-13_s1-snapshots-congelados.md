# Snapshots congelados: `data/raw/<fecha>/`, inmutables y con su hash

- **Fecha/hora:** 2026-10-03 00:13
- **Área:** Almacenamiento · **Acción:** Añadir
- **Chat / página:** sesión de arranque · emitido al cerrar la Fase 1
- **Archivos afectados:** `data/raw/2026-10-02/{Melate,Revancha,Revanchita}.csv`,
  `data/raw/2026-10-02/SHA256.txt`, `data/raw/2026-10-02/PROCEDENCIA.md`, `.gitattributes`

## Qué se hizo

Los datos de entrada se guardan en carpetas fechadas que **no se vuelven a tocar**.

```
data/raw/2026-10-02/
  Melate.csv        206 675 bytes   sha256 51de5afd3b7d348b...
  Revancha.csv      150 284 bytes   sha256 5d1b191e3c8bc52d...
  Revanchita.csv     88 235 bytes   sha256 06beda9ab84cf015...
  SHA256.txt                        los tres hashes, legible por máquina
  PROCEDENCIA.md                    URL, hora UTC, HTTP, bytes, y qué se puede concluir
```

Reglas del almacén, y son contrato:

- **Los nombres de fichero son obligatorios.** `cargar(juego, carpeta)` abre exactamente
  `{juego}.csv`. Renombrarlos rompe la carga.
- **Un snapshot no se actualiza.** Un sorteo nuevo no se añade aquí: se crea otra carpeta con su
  fecha. "Congelado" significa congelado.
- **Se guardan los bytes tal cual llegaron**, sin recodificar, con sus errores incluidos. El
  `CLAUDE.md` documenta tres (`BOLSA = 0` en 2120, 2142 y 2234) y uno fuera de secuencia (Revancha
  3221). El código los trata; el almacén no los esconde.
- **Se suben al repositorio.** 438 KB en total. Es lo que hace que el hash publicado signifique algo
  y que alguien de fuera pueda recomprobar las cifras.

### `.gitattributes` es parte del almacén, no una preferencia de formato

Los CSV oficiales vienen con **CRLF** y `core.autocrlf` vale `true` en Windows por defecto. Con los
atributos sin especificar, git normalizaba los CSV a LF dentro del repositorio: en Windows el viaje
de ida y vuelta devuelve CRLF y no se nota, pero **un clon en Linux o macOS recibiría los ficheros
con LF, otros bytes y otro SHA-256**. El hash publicado habría dejado de cuadrar justo para quien lo
necesita: alguien de fuera verificando.

```
data/raw/** -text
```

Comprobado con plumbing, no de oídas: el blob del índice tiene el mismo identificador que
`git hash-object` sobre los bytes crudos, en los tres ficheros. Los identificadores **cambiaron** al
añadir la regla (`22d6c31b` → `336ca194` en Melate), que es la prueba de que antes sí convertía. Y
los tamaños del árbol remoto coinciden byte a byte con los del disco.

### Lo que el snapshot evitó, en concreto

El portón de la fase se corrió contra el snapshot y no contra la descarga en vivo. Horas después se
descubrió que **el sorteo 4273 ya se había celebrado** y que el oficial estaba a punto de
publicarlo. Con una descarga en vivo no habría habido forma de distinguir "el refactor rompió algo"
de "llegaron datos nuevos", y el error del espejo que inflaba dos cifras publicadas probablemente no
se habría encontrado nunca.

### Lo que hay en `reportes/`

Los JSON de cada corrida, también versionados. Cada uno lleva dentro su propio bloque de
procedencia: hash de los datos, semillas, simulaciones y versiones de librería. Un reporte sin eso
no se puede volver a comprobar, así que guardarlo sería guardar una anécdota.

`reportes/` se crea solo si no existe: `informe.main` hace `mkdir(parents=True)` antes de escribir,
porque en un clon nuevo esa carpeta no está.

## Por qué

Las cifras de "Línea base verificada" del `CLAUDE.md` son al sorteo 4272, y los CSV oficiales crecen
con cada sorteo. Sin un snapshot fechado, toda cifra publicada caduca en días y deja de ser
verificable: no se puede saber si una diferencia viene del código o de los datos.

La regla 6 del protocolo pide el hash del dataset en cada corrida. Un hash solo vale si los bytes a
los que apunta siguen existiendo en algún sitio — y ese sitio es esta carpeta.

## Impacto en seguridad / conexiones / datos

- **Seguridad:** son datos públicos de Lotería Nacional. No hay nada personal. Publicarlos es lo que
  hace verificables las cifras.
- **Conexiones:** con `--datos` apuntando a un snapshot, **ninguna**. Es el modo en el que se
  reproducen las cifras publicadas, y que no toque la red es una propiedad, no una casualidad.
- **Datos:** 438 KB versionados. Crecerá una carpeta por snapshot; a este ritmo es irrelevante.

## Cómo verificar / revertir

```powershell
Get-FileHash .\data\raw\2026-10-02\*.csv -Algorithm SHA256 |
  ForEach-Object { "$($_.Hash.ToLower())  $(Split-Path $_.Path -Leaf)" }
Get-Content .\data\raw\2026-10-02\SHA256.txt
```

Tienen que coincidir línea por línea. Si no coinciden, el snapshot está corrupto o alguien lo
modificó: **no se arregla, se descarta** y se crea otro con su fecha.

Que git no toca los bytes:

```powershell
git check-attr text -- data/raw/2026-10-02/Melate.csv     # -> text: unset
git ls-files --stage -- data/raw/2026-10-02/Melate.csv    # el blob...
git hash-object -- data/raw/2026-10-02/Melate.csv         # ...debe dar el mismo id
```

**Revertir:** borrar `data/` y la línea `data/raw/** -text` de `.gitattributes`. **No se
recomienda:** sin snapshot, ninguna cifra publicada se puede volver a comprobar, y el hash del
protocolo pasa a apuntar a datos que ya no existen.

**Pendiente de verificar en vivo:** clonar el repositorio en limpio —preferiblemente en Linux o
macOS, que es donde la conversión habría dado la cara— y recalcular los tres hashes.

Relacionado: `Conexiones/Añadir/2026-10-03_00-13_s1-fuentes-de-datos.md`,
`Reproducibilidad/Añadir/2026-10-03_00-13_s1-linea-base-reproducida.md`,
`Despliegue/Añadir/2026-10-03_00-13_s1-primer-push.md`
