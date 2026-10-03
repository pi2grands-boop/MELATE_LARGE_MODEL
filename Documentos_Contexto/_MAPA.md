# Cómo leer esta bitácora

> Rutas de lectura, no un listado. Se actualiza al cerrar cada fase.
> Si el mapa miente, es peor que si no existe.

Esta bitácora **se publica**, al contrario de lo habitual. El porqué y las reglas que impone están
en `REGLAS-DOCUMENTACION.md` §0 y en `Seguridad/Decisiones/`.

## Si acabas de llegar

1. `README.md` (en la raíz) — qué es el proyecto y qué no. Empieza por "esto no predice números".
2. `Mapa/Añadir/2026-10-03_00-13_s1-mapa-del-sistema.md` — qué módulo responde a qué pregunta, y la
   pieza de la que depende todo: hay dos programas y dan lo mismo.
3. `Fases/2026-10-02_arranque/99_CIERRE.md` — dónde está el proyecto hoy y qué queda pendiente.

## Si tienes 10 minutos y quieres entender por qué este proyecto es desconfiado

Lee estos tres, en orden. Cuentan la historia completa de la primera fase:

1. `Fases/2026-10-02_arranque/Bugs/2026-10-02_23-29_s1-porton-linea-base.md` — dos de las doce
   cifras del contrato no reproducían. No era el código: era un número mal transcrito en una fuente
   de respaldo, y había inflado el resultado más llamativo del proyecto.
2. `Protocolo_Estadistico/Decisiones/2026-10-03_00-13_s1-familias-benjamini-hochberg.md` — por qué
   un p = 0.017 se convierte en q = 0.35 cuando se cuentan las 36 pruebas, y por qué el número que
   manda se decide **antes** de ver los resultados.
3. `Reproducibilidad/Añadir/2026-10-03_00-13_s1-linea-base-reproducida.md` — por qué una cifra sin
   su hash y sin sus versiones de librería no es un resultado.

## Si vas a tocar código

- **Antes:** las `Decisiones/` de tu área. Están cerradas y tienen su porqué.
- **Antes, si tocas `src/melate/`:** `baseline_auditoria.py` **no se modifica nunca.** Es el oráculo
  y `tests/test_paridad.py` compara contra él con tolerancia cero. Si lo tocas, el proyecto pierde su
  única referencia y no se recupera.
- **Después:** el pipeline del `REGLAS-DOCUMENTACION.md` §1. El `.md` es el último paso, nunca el
  primero.

```powershell
.venv\Scripts\python.exe -m pytest tests -m "not lento and not red" -q   # 31 pruebas, 2.4 s
.venv\Scripts\python.exe -m pytest tests -q                              # 52 pruebas, ~105 s
```

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
| ¿Me puedo creer este resultado? | Protocolo_Estadistico |
| ¿Cuánto tarda y dónde se va el tiempo? | Rendimiento |
| ¿Qué se subió al repositorio y cuándo? | Despliegue |
| ¿Por qué se eligió A y no B? | `<Área>/Decisiones` |

## Fases

Un cambio normal va directo a la rejilla. Los bloques grandes viven en `Fases/<fecha>_<nombre>/` y,
al cerrarse, emiten a las áreas base **solo el estado final**. El proceso se queda en el dossier.

- `Fases/2026-10-02_arranque/` — **cerrada el 2026-10-03.** Bitácora, entorno, snapshot congelado,
  reproducción de la línea base, paquete `src/melate/` con paridad, 52 tests y primer push. Empieza
  por su `Fases/2026-10-02_arranque/00_ALCANCE.md`; la historia está en sus dos `Bugs/`.

## Estado ahora mismo

- **Bugs abiertos:** ninguno.
- **Fases abiertas:** ninguna. La siguiente es la Fase 2 (preregistro y `lab.py`), y **no empieza sin
  que el usuario la apruebe** (`CLAUDE.md`).
- **Pendiente de verificar en vivo** — los siete puntos de
  `Fases/2026-10-02_arranque/99_CIERRE.md`. Los dos que más importan:
  clonar el repositorio en limpio y recalcular los SHA-256 **en Linux o macOS**, que es donde la
  conversión de finales de línea habría dado la cara; y correr el informe sin `--datos`, cuyo camino
  de red no se ha ejercitado desde que se le quitó el respaldo al espejo.
- **Decisiones cerradas que atan el proyecto:**
  - `baseline_auditoria.py` es el oráculo y no se modifica.
  - El espejo es solo validación cruzada, nunca carga.
  - Para declarar ventaja manda `q_BH_global`, la familia de 36 pruebas.
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
