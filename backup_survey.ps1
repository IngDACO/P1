# backup_survey.ps1
# Uso: .\backup_survey.ps1 -Version 3 -Mensaje "descripcion del cambio"

param(
    [Parameter(Mandatory=$true)]
    [int]$Version,
    [Parameter(Mandatory=$true)]
    [string]$Mensaje
)

$rclone  = "C:\Users\diego\AppData\Local\Microsoft\WinGet\Packages\Rclone.Rclone_Microsoft.Winget.Source_8wekyb3d8bbwe\rclone-v1.74.1-windows-amd64\rclone.exe"
# ⚠️ El repo sale de DONDE ESTA ESTE FICHERO, no de una ruta escrita a mano: el script
# vive dentro de P1 desde el 20/09/2026 (antes estaba suelto en el home, sin historial,
# y un arreglo suyo no dejaba rastro en ningun sitio). Asi no puede apuntar a otro arbol.
$repo    = $PSScriptRoot
$src     = "$repo\survey_app"
$date    = Get-Date -Format "yyyy-MM-dd"
$zipName = "survey_app_v${Version}_${date}.zip"
$zipPath = "C:\Users\diego\Downloads\$zipName"
$driveRoot = "1PK7znRaCGWcycDJ6neUJPy72TqwgSxQW"
$subFolder = "v${Version} -- ${date}"

# 0. Actualizar VERSION
"v${Version}" | Set-Content -Path "$src\VERSION" -Encoding utf8 -NoNewline

# 1. Git push
Write-Host ""
Write-Host "[ 1/3 ] Git push a GitHub..." -ForegroundColor Cyan
Set-Location $repo
git add -A
$changes = git status --porcelain
if ($changes) {
    # El mensaje va por FICHERO, no por -m: pasarlo como argumento a un ejecutable
    # nativo rompe en cuanto lleva comillas dobles (PowerShell las come y git recibe
    # los trozos como si fueran rutas). Paso en v504: 30 errores de pathspec, el
    # commit sin hacer... y el script cantando OK. Por fichero no hay nada que escapar.
    # ⚠️ Sin BOM: `Set-Content -Encoding utf8` en PS 5.1 SIEMPRE lo escribe, y git se lo
    # traga dentro del mensaje — el asunto de cada commit empezaria por un caracter
    # invisible. Es el mismo BOM que obliga a leer VERSION con utf-8-sig.
    $msgFile = Join-Path $env:TEMP "copex_commit_msg.txt"
    [IO.File]::WriteAllText($msgFile, $Mensaje, (New-Object Text.UTF8Encoding($false)))
    git commit -F $msgFile
    $rcCommit = $LASTEXITCODE
    try { [IO.File]::Delete($msgFile) } catch {}
    if ($rcCommit -ne 0) {
        Write-Host "  Error en git commit (codigo $rcCommit): NO se ha desplegado nada" -ForegroundColor Red
        exit 1
    }

    git push origin main
    if ($LASTEXITCODE -ne 0) { Write-Host "Error en git push" -ForegroundColor Red; exit 1 }

    # Y se comprueba que el commit ESTA en el remoto. Un push sin nada que subir
    # tambien devuelve 0, asi que el codigo de salida del push por si solo no
    # distingue "subido" de "no habia nada" — que es como v504 dijo OK sin subir nada.
    $local = (git rev-parse HEAD).Trim()
    $remoto = (git rev-parse "@{u}").Trim()
    if ($local -ne $remoto) {
        Write-Host "  El commit $($local.Substring(0,7)) NO esta en el remoto" -ForegroundColor Red
        exit 1
    }
    Write-Host "  GitHub OK ($($local.Substring(0,7))) -- Streamlit redeploy iniciado" -ForegroundColor Green
} else {
    Write-Host "  Sin cambios que commitear" -ForegroundColor Yellow
}

# 2. Crear ZIP
Write-Host ""
Write-Host "[ 2/3 ] Creando ZIP..." -ForegroundColor Cyan
$pyFiles = Get-ChildItem -Path $src -Recurse -Filter "*.py" | Select-Object -ExpandProperty FullName
Compress-Archive -Path $pyFiles -DestinationPath $zipPath -Force
$size = [math]::Round((Get-Item $zipPath).Length / 1KB, 1)
Write-Host "  $zipName ($size KB)" -ForegroundColor Green

# 3. Subir a Drive
Write-Host ""
Write-Host "[ 3/3 ] Subiendo a Google Drive..." -ForegroundColor Cyan
& $rclone mkdir --drive-root-folder-id $driveRoot "gdrive:$subFolder"
& $rclone copy $zipPath --drive-root-folder-id $driveRoot "gdrive:$subFolder"
if ($LASTEXITCODE -ne 0) { Write-Host "Error subiendo a Drive" -ForegroundColor Red; exit 1 }
Write-Host "  Drive OK -- $subFolder" -ForegroundColor Green

# Resumen
Write-Host ""
Write-Host "Todo listo!" -ForegroundColor Green
Write-Host "  GitHub   : https://github.com/IngDACO/P1"
Write-Host "  Streamlit: https://dwl6s39d7u3yfwfkbpcpah.streamlit.app/"
Write-Host "  Drive    : $subFolder"
