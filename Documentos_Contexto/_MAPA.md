# Cómo leer esta bitácora

> Rutas de lectura, no un listado. Se actualiza al cerrar cada fase.
> Si el mapa miente, es peor que si no existe.

Esta bitácora **se publica**, al contrario de lo habitual. El porqué y las reglas que impone están
en `REGLAS-DOCUMENTACION.md` §0 y en `Seguridad/Decisiones/`.

## Si acabas de llegar

1. `README.md` (en la raíz) — qué es el proyecto y qué no. Empieza por "esto no predice números".
2. `Mapa/Añadir/2026-10-03_00-13_s1-mapa-del-sistema.md` — qué módulo responde a qué pregunta, y la
   pieza de la que depende todo: hay dos programas y dan lo mismo.
3. `Mapa/Modificar/2026-10-03_01-30_s2-entra-el-laboratorio.md` — la frontera entre **explorar** y
   **juzgar**. Las cifras del informe no bastan para afirmar nada; solo el laboratorio puede.
4. `Fases/2026-10-03_protocolo/99_CIERRE.md` — dónde está el proyecto hoy y qué queda pendiente.

## Si tienes 15 minutos y quieres entender por qué este proyecto es desconfiado

Lee estos cuatro, en orden. Cuentan la historia completa:

1. `Fases/2026-10-02_arranque/Bugs/2026-10-02_23-29_s1-porton-linea-base.md` — dos de las doce
   cifras del contrato no reproducían. No era el código: era un número mal transcrito en una fuente
   de respaldo, y había inflado el resultado más llamativo del proyecto.
2. `Protocolo_Estadistico/Decisiones/2026-10-03_00-13_s1-familias-benjamini-hochberg.md` — por qué
   un p = 0.017 se convierte en q = 0.35 cuando se cuentan las 36 pruebas, y por qué el número que
   manda se decide **antes** de ver los resultados.
3. `Protocolo_Estadistico/Añadir/2026-10-03_01-30_s2-preregistro-y-las-cinco-condiciones.md` — qué
   hace falta para poder afirmar algo, qué error mata cada una de las cinco condiciones, y cuántos
   años de datos haría falta: unos once.
4. `Fases/2026-10-03_protocolo/Bugs/2026-10-03_01-05_s2-pendientes-heredados.md` — la Fase 1 cerró
   con 52 tests en verde y 17 de ellos fallaban en otro shell. Lo que lo descubrió fue haber dejado
   escrita la lista de pendientes y haberla ejecutado.

## Si vas a tocar código

- **Antes:** las `Decisiones/` de tu área. Están cerradas y tienen su porqué.
- **Antes, si tocas `src/melate/`:** `baseline_auditoria.py` **no se modifica nunca.** Es el oráculo
  y `tests/test_paridad.py` compara contra él con tolerancia cero. Si lo tocas, el proyecto pierde su
  única referencia y no se recupera.
- **Después:** el pipeline del `REGLAS-DOCUMENTACION.md` §1. El `.md` es el último paso, nunca el
  primero.

```powershell
.venv\Scripts\python.exe -m pytest tests -m "not lento and not red" -q   # 72 pruebas, ~2.5 s
.venv\Scripts\python.exe -m pytest tests -q                              # 100 pruebas, ~136 s
```

> Estas dos cifras se vuelven a medir al cerrar cada fase. Ya envejecieron una vez: dos tests de
> subproceso sin marcar dejaron el bucle rápido en 30 s mientras este mapa decía 5
> (`Rendimiento/Arreglos_Bugs/2026-10-03_01-59_la-suite-rapida-no-era-rapida.md`).

**Y si lo que quieres es saber si una estrategia funciona:** no mires el informe. Sella un
preregistro y espera. `Protocolo_Estadistico/Añadir/` explica por qué, y
`python -m melate.lab --prereg prereg/<fichero>.json` es el único camino que puede afirmar algo.

## Si vas a subir algo

**El colador es bloqueante.** Si imprime algo, no se sube.

```powershell
.\scripts\colador.ps1 -Autoprueba
```

## Si buscas algo concreto

| Tu pregunta | Área |
|---|---|
| ¿Cuál es el mapa del sistema? | Mapa |
| ¿Dónde vive este fichero? ¿Por qué `src/`? | Estructura_Carpetas |
| ¿Qué forma tienen los datos y el reporte? | Estructura_Datos |
| ¿Dónde se guardan los datos? ¿Por qué un snapshot? | Almacenamiento |
| ¿De dónde salen los datos? ¿Por qué el espejo no vale para cargar? | Conexiones |
| ¿Cómo se enlazan las pantallas de la app? | Interconexion *(vacía: la app es de la Fase 4)* |
| ¿Qué cambia en la superficie de ataque? ¿Qué se publica? | Seguridad |
| ¿Qué sirve el servidor? | Red *(vacía: todo es local)* |
| ¿Se puede volver a obtener este número exacto? | Reproducibilidad |
| ¿Me puedo creer este resultado? ¿Qué hace falta para afirmar algo? | Protocolo_Estadistico |
| ¿Qué es un preregistro y por qué no se puede editar? | Protocolo_Estadistico · Almacenamiento |
| ¿Cuánto tarda y dónde se va el tiempo? | Rendimiento |
| ¿Qué se subió al repositorio y cuándo? | Despliegue |
| ¿Por qué se eligió A y no B? | `<Área>/Decisiones` |

## Fases

Un cambio normal va directo a la rejilla. Los bloques grandes viven en `Fases/<fecha>_<nombre>/` y,
al cerrarse, emiten a las áreas base **solo el estado final**. El proceso se queda en el dossier.

- `Fases/2026-10-02_arranque/` — **cerrada el 2026-10-03.** Bitácora, entorno, snapshot congelado,
  reproducción de la línea base, paquete `src/melate/` con paridad y primer push. Empieza
  por su `Fases/2026-10-02_arranque/00_ALCANCE.md`; la historia está en sus dos `Bugs/`.
- `Fases/2026-10-03_protocolo/` — **cerrada el 2026-10-03.** Los pendientes de la Fase 1 ejecutados
  (con un bug de 17 tests encontrado por el camino), `prereg/*.json` sellado, `lab.py` y las 5
  condiciones de la regla 5.

## Estado ahora mismo

- **Bugs abiertos:** ninguno.
- **Fases abiertas:** ninguna. La siguiente es la Fase 3 (EV, popularidad con Scrapling y cartera),
  y **no empieza sin que el usuario la apruebe** (`CLAUDE.md`).
- **El veredicto del proyecto, hoy:** `sin ventaja demostrada`, 0 de 5 condiciones, porque el holdout
  del preregistro está vacío. Es la respuesta correcta y seguirá siéndolo durante años.
- **Pendiente de verificar en vivo** — los cinco puntos de
  `Fases/2026-10-03_protocolo/99_CIERRE.md`. Los dos primeros no son falta de esfuerzo, son el
  diseño funcionando: no habrá una evaluación preregistrada de verdad hasta que pasen sorteos, y la
  condición 5 necesita del orden de once años de datos.
- **Decisiones cerradas que atan el proyecto:**
  - `baseline_auditoria.py` es el oráculo y no se modifica.
  - El espejo es solo validación cruzada, nunca carga.
  - Para declarar ventaja manda `q_BH_global`, la familia de 36 pruebas.
  - Un preregistro no se sobrescribe, no se sella en el pasado, y alterarlo lo invalida.
  - La bitácora se publica; nada personal sale de la máquina, y las rutas son siempre relativas.
  - `pandas < 3` mientras el oráculo use `df.attrs`.

## Receta de integridad

Antes de dar una fase por cerrada:

```powershell
$b = 'Documentos_Contexto'
$md = Get-ChildItem $b -Recurse -Filter *.md
"documentos: $($md.Count)"

# nombres fuera de patron (los 00_ALCANCE.md y 99_CIERRE.md estan exentos)
$md | Where-Object { $_.Name -notmatch '^([0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{2}-[0-9]{2}_[a-z0-9-]+|_MAPA|00_ALCANCE|99_CIERRE)\.md$' } | ForEach-Object Name

# cabecera y seccion de verificacion
$md | Where-Object { $t = [IO.File]::ReadAllText($_.FullName,[Text.Encoding]::UTF8)
  ($t -notmatch 'Fecha/hora') -or ($t -notmatch 'rea:') } | ForEach-Object Name

# documentos vivos sin cerrar
$md | Where-Object { $_.Directory.Name -eq 'Bugs' -and
  ([IO.File]::ReadAllText($_.FullName,[Text.Encoding]::UTF8) -notmatch 'CERRADO') } | ForEach-Object Name
```

Y los enlaces `Relacionado:` rotos, que es el que más importa: la bitácora es un grafo y un enlace
muerto lo parte. El script está en `scripts/verificar-bitacora.ps1`.
