# =========================================================
#  Colador: nada personal sale al repositorio publico.
#
#  Uso:
#    .\scripts\colador.ps1              # revisa el arbol de trabajo
#    .\scripts\colador.ps1 -Autoprueba  # ademas comprueba que el patron tiene dientes
#
#  Salida vacia y codigo 0 -> se puede subir. Cualquier coincidencia -> no se sube.
#
#  Por que busca 'C:\Users\' y no el usuario de Windows a secas: el usuario de
#  Windows es prefijo del usuario de GitHub, que si es publico y legitimo.
#  Buscar la cadena corta daria falsos positivos en la propia URL del repositorio,
#  y un colador que grita siempre deja de usarse.
#
#  ASCII puro a proposito: PowerShell 5.1 lee un .ps1 sin BOM como ANSI.
# =========================================================
param([switch]$Autoprueba)

$ErrorActionPreference = 'Stop'

$PATRONES = @(
  'C:\\Users',                              # rutas absolutas de la maquina
  'OneDrive',
  'Escritorio',
  '[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}'          # cualquier correo
)
# Unica excepcion: la identidad de GitHub, que es publica por diseno.
$BLANCA = 'users\.noreply\.github\.com'

$EXTENSIONES = @('*.md', '*.py', '*.txt', '*.json', '*.toml', '*.csv', '*.ps1', '*.cfg', '*.yml')
$EXCLUIR = @('.venv', '.git', 'egg-info', 'node_modules')

# Este fichero se excluye de su propia pasada: contiene los patrones que busca y el cebo
# de la autoprueba, asi que siempre se encontraria a si mismo. Es la UNICA exclusion por
# nombre de fichero, y esta aqui a la vista justamente para que nadie use este hueco
# para esconder nada: la autoprueba demuestra que los patrones funcionan.
$YO = 'colador.ps1'

function Candidatos($raiz) {
  Get-ChildItem -Path $raiz -Recurse -File -Include $EXTENSIONES | Where-Object {
    $ruta = $_.FullName
    ($_.Name -ne $YO) -and
    -not ($EXCLUIR | Where-Object { $ruta.Contains([IO.Path]::DirectorySeparatorChar + $_) -or $ruta.Contains($_ + '.') })
  }
}

function Colar($ficheros) {
  if (-not $ficheros) { return @() }
  Select-String -Path $ficheros.FullName -Pattern $PATRONES |
    Where-Object { $_.Line -notmatch $BLANCA }
}

# Una base de datos binaria no se publica nunca: el colador no puede leer lo que lleva dentro, y
# una ruta o un correo dentro de un .duckdb pasarian sin verse. .gitignore la excluye, pero un
# `git add -f` se lo salta; esto mira el indice de git, no el disco, porque en disco si debe estar.
# Ver Documentos_Contexto/Almacenamiento/Decisiones/ (Fase 4).
$BINARIOS = @('*.duckdb', '*.duckdb.wal')

function Versionados($repo) {
  @(git -C $repo ls-files -- $BINARIOS 2>$null | Where-Object { $_ })
}

if ($Autoprueba) {
  # Un colador que no encuentra nada puede ser un colador que no esta mirando.
  $tmp = Join-Path ([IO.Path]::GetTempPath()) ("colador-autoprueba-" + [Guid]::NewGuid().ToString('N'))
  New-Item -ItemType Directory -Path $tmp | Out-Null
  $cebo = Join-Path $tmp 'cebo.md'
  $enc = New-Object System.Text.UTF8Encoding($false)
  [IO.File]::WriteAllText($cebo, @'
ruta C:\Users\alguien\cosa
correo prueba@ejemplo.com
permitido pi2grands-boop@users.noreply.github.com
'@, $enc)

  $d = @(Colar (Get-ChildItem $cebo))
  $lineas = ($d | ForEach-Object { $_.Line.Trim() })
  $okRuta   = [bool]($lineas -match 'C:')
  $okCorreo = [bool]($lineas -match 'ejemplo')
  $okBlanca = -not [bool]($lineas -match 'noreply')

  # Y una base versionada a la fuerza, en un repositorio de usar y tirar.
  $repo = Join-Path $tmp 'repo'
  New-Item -ItemType Directory -Path $repo | Out-Null
  git -C $repo init -q 2>$null | Out-Null
  [IO.File]::WriteAllText((Join-Path $repo 'cebo.duckdb'), 'x', $enc)
  git -C $repo add -f cebo.duckdb 2>$null | Out-Null
  $okBase = (@(Versionados $repo).Count -eq 1)

  "autoprueba:"
  "  detecta ruta absoluta  : $okRuta"
  "  detecta correo         : $okCorreo"
  "  respeta la lista blanca: $okBlanca"
  "  detecta base versionada: $okBase"
  # Remove-Item y no [IO.Directory]::Delete: los objetos de git son de solo lectura en Windows.
  Remove-Item -LiteralPath $tmp -Recurse -Force
  if (-not ($okRuta -and $okCorreo -and $okBlanca -and $okBase)) {
    Write-Error "el colador NO tiene dientes: no sirve de nada ejecutarlo"
    exit 2
  }
  ""
}

$raiz = Split-Path -Parent $PSScriptRoot
$ficheros = @(Candidatos $raiz)
$hits = @(Colar $ficheros)
$versionados = @(Versionados $raiz)

"colador sobre $($ficheros.Count) ficheros de $raiz"
if ($hits.Count -eq 0 -and $versionados.Count -eq 0) {
  "  limpio: 0 coincidencias. Se puede subir."
  exit 0
}
"  $($hits.Count + $versionados.Count) COINCIDENCIAS. NO subir:"
$hits | ForEach-Object {
  $rel = $_.Path.Substring($raiz.Length + 1)
  $txt = $_.Line.Trim()
  if ($txt.Length -gt 100) { $txt = $txt.Substring(0, 100) + '...' }
  "    ${rel}:$($_.LineNumber)  $txt"
}
$versionados | ForEach-Object { "    $_  base de datos en el indice de git: no se publica" }
exit 1
