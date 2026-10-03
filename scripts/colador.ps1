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

  "autoprueba:"
  "  detecta ruta absoluta  : $okRuta"
  "  detecta correo         : $okCorreo"
  "  respeta la lista blanca: $okBlanca"
  [IO.Directory]::Delete($tmp, $true)
  if (-not ($okRuta -and $okCorreo -and $okBlanca)) {
    Write-Error "el colador NO tiene dientes: no sirve de nada ejecutarlo"
    exit 2
  }
  ""
}

$raiz = Split-Path -Parent $PSScriptRoot
$ficheros = @(Candidatos $raiz)
$hits = @(Colar $ficheros)

"colador sobre $($ficheros.Count) ficheros de $raiz"
if ($hits.Count -eq 0) {
  "  limpio: 0 coincidencias. Se puede subir."
  exit 0
}
"  $($hits.Count) COINCIDENCIAS. NO subir:"
$hits | ForEach-Object {
  $rel = $_.Path.Substring($raiz.Length + 1)
  $txt = $_.Line.Trim()
  if ($txt.Length -gt 100) { $txt = $txt.Substring(0, 100) + '...' }
  "    ${rel}:$($_.LineNumber)  $txt"
}
exit 1
