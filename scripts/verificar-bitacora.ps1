# =========================================================
#  Integridad de la bitacora. Se corre antes de cerrar una fase.
#
#  Uso:  .\scripts\verificar-bitacora.ps1
#
#  Salida vacia en las cinco comprobaciones y exit 0 -> la bitacora es
#  consistente. Cualquier hallazgo -> arreglar antes de cerrar.
#
#  La comprobacion que mas importa es la 5: la bitacora es un grafo y un
#  enlace muerto lo parte.
#
#  ASCII puro a proposito: PowerShell 5.1 lee un .ps1 sin BOM como ANSI, asi
#  que la enye de 'Anadir' y los acentos se componen por codigo.
# =========================================================
$ErrorActionPreference = 'Stop'

$N  = [char]0x00F1   # n con virgulilla
$A  = [char]0x00C1   # A con tilde

$raiz = Split-Path -Parent $PSScriptRoot
$b = Join-Path $raiz 'Documentos_Contexto'
if (-not (Test-Path $b)) { Write-Error "no existe $b"; exit 2 }

$md = @(Get-ChildItem $b -Recurse -Filter *.md)
$fallos = 0

function Seccion($n, $titulo) { ""; "$n. $titulo" }
function Resultado($items) {
  if ($items -and $items.Count) {
    $script:fallos += $items.Count
    $items | ForEach-Object { "     X  $_" }
  } else { "     ok" }
}

"integridad de la bitacora: $($md.Count) documentos"

# ---------------------------------------------------------------- 1
Seccion 1 'Nombres fuera de patron AAAA-MM-DD_HH-MM_slug.md'
$exentos = '^(_MAPA|00_ALCANCE|99_CIERRE)\.md$'
$patron  = '^[0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{2}-[0-9]{2}_[a-z0-9-]+\.md$'
Resultado @($md | Where-Object { $_.Name -notmatch $patron -and $_.Name -notmatch $exentos } |
            ForEach-Object { $_.Name })

# ---------------------------------------------------------------- 2
Seccion 2 'Cabecera incompleta (falta Fecha/hora o Area)'
Resultado @($md | Where-Object {
  if ($_.Name -match $exentos) { return $false }
  $t = [IO.File]::ReadAllText($_.FullName, [Text.Encoding]::UTF8)
  ($t -notmatch 'Fecha/hora') -or ($t -notmatch "${A}rea:")
} | ForEach-Object { $_.Name })

# ---------------------------------------------------------------- 3
Seccion 3 'Sin seccion de verificacion'
Resultado @($md | Where-Object {
  if ($_.Name -match '^(_MAPA|00_ALCANCE|99_CIERRE)\.md$') { return $false }
  $t = [IO.File]::ReadAllText($_.FullName, [Text.Encoding]::UTF8)
  $t -notmatch 'mo verificar'
} | ForEach-Object { $_.Name })

# ---------------------------------------------------------------- 4
Seccion 4 'Documentos vivos de Bugs sin cerrar'
Resultado @($md | Where-Object {
  $_.Directory.Name -eq 'Bugs' -and
  ([IO.File]::ReadAllText($_.FullName, [Text.Encoding]::UTF8) -notmatch 'CERRADO')
} | ForEach-Object { "ABIERTO: $($_.Name)" })

# ---------------------------------------------------------------- 5
Seccion 5 'Referencias a .md rotas'
#
# Se extrae toda ruta .md entre comillas invertidas y se intenta resolver, en
# este orden, contra:
#   1. la raiz de la bitacora   (la convencion: <Area>/<Accion>/fichero.md)
#   2. la raiz del repositorio  (CLAUDE.md, README.md, data/.../PROCEDENCIA.md)
#   3. la carpeta del propio documento (enlaces relativos dentro de un dossier)
# Las tres son formas en las que un lector encuentra el fichero. Solo se
# reporta lo que no resuelve en ninguna.
#
# Se omiten los marcadores de plantilla: una cadena con AAAA, < > o puntos
# suspensivos no es un enlace, es un ejemplo de formato.
$clases = "A-Za-z_${N}0-9-"
$rx = '`([' + $clases + '][' + $clases + './]*\.md)`'
$marcadores = 'AAAA|HH-MM|<|>|' + [char]0x2026
$rotos = @()
foreach ($d in $md) {
  $c = [IO.File]::ReadAllText($d.FullName, [Text.Encoding]::UTF8)
  foreach ($m in [regex]::Matches($c, $rx)) {
    $rel = $m.Groups[1].Value
    if ($rel -match $marcadores) { continue }
    $win = $rel -replace '/', '\'
    $resuelve = (Test-Path (Join-Path $b $win)) -or
                (Test-Path (Join-Path $raiz $win)) -or
                (Test-Path (Join-Path $d.Directory.FullName $win))
    if (-not $resuelve) { $rotos += "$($d.Name) -> $rel" }
  }
}
Resultado @($rotos | Sort-Object -Unique)

# ---------------------------------------------------------------- resumen
""
"celdas ocupadas de la rejilla:"
$md | Where-Object { $_.Name -notmatch '^_MAPA\.md$' } | ForEach-Object {
  $rel = $_.FullName.Substring($b.Length + 1)
  $partes = $rel.Split([IO.Path]::DirectorySeparatorChar)
  if ($partes.Count -ge 2) { ($partes[0..1] -join '/') } else { $partes[0] }
} | Group-Object | Sort-Object Name | ForEach-Object { "   {0,3}  {1}" -f $_.Count, $_.Name }

""
if ($fallos -eq 0) { "INTEGRA: 0 hallazgos en las 5 comprobaciones."; exit 0 }
"$fallos hallazgos. Arreglar antes de cerrar la fase."
exit 1
