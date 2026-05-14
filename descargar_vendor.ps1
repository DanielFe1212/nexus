# ============================================================================
#  descargar_vendor.ps1  (v2)
# ============================================================================
#  Descarga las 6 librerias JS/CSS que el dashboard y el admin necesitan.
#  Uso:
#    1) Abre PowerShell en la raiz del proyecto Nexus.
#    2) Si bloquea por politica de ejecucion:
#         Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#    3) Ejecuta:
#         .\descargar_vendor.ps1
# ============================================================================

Write-Host "[1/3] Creando carpetas vendor..." -ForegroundColor Cyan
New-Item -ItemType Directory -Path "static\css\vendor" -Force | Out-Null
New-Item -ItemType Directory -Path "static\js\vendor"  -Force | Out-Null

$descargas = @(
    # Dashboard
    @{Url="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css";      Out="static\css\vendor\bootstrap.min.css"},
    @{Url="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"; Out="static\js\vendor\bootstrap.bundle.min.js"},
    @{Url="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js";                Out="static\js\vendor\chart.min.js"},
    @{Url="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js";          Out="static\js\vendor\xlsx.full.min.js"},
    # Admin form de Evento (Flatpickr para calendario y reloj)
    @{Url="https://cdn.jsdelivr.net/npm/flatpickr@4.6.13/dist/flatpickr.min.css";         Out="static\css\vendor\flatpickr.min.css"},
    @{Url="https://cdn.jsdelivr.net/npm/flatpickr@4.6.13/dist/flatpickr.min.js";          Out="static\js\vendor\flatpickr.min.js"},
    @{Url="https://cdn.jsdelivr.net/npm/flatpickr@4.6.13/dist/l10n/es.min.js";            Out="static\js\vendor\flatpickr.es.min.js"}
)

Write-Host "[2/3] Descargando librerias..." -ForegroundColor Cyan
foreach ($d in $descargas) {
    Write-Host ("  Descargando " + $d.Out + "...") -ForegroundColor Yellow
    try {
        Invoke-WebRequest -Uri $d.Url -OutFile $d.Out -ErrorAction Stop -UseBasicParsing
        $tam = (Get-Item $d.Out).Length / 1KB
        $msg = "    [OK] " + ("{0:N1}" -f $tam) + " KB"
        Write-Host $msg -ForegroundColor Green
    } catch {
        $err = "    [ERROR] " + $_.Exception.Message
        Write-Host $err -ForegroundColor Red
    }
}

# Limpieza: si quedo Chart.js v4 obsoleto, lo eliminamos
if (Test-Path "static\js\vendor\chart.umd.min.js") {
    Write-Host "[3/3] Eliminando Chart.js v4 obsoleto (chart.umd.min.js)..." -ForegroundColor Yellow
    Remove-Item "static\js\vendor\chart.umd.min.js" -Force
    Write-Host "    [OK] Eliminado" -ForegroundColor Green
} else {
    Write-Host "[3/3] No habia Chart.js v4 que eliminar" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Listo. Ahora ejecuta:" -ForegroundColor Cyan
Write-Host "    python manage.py collectstatic --noinput"
Write-Host "    python manage.py runserver"
