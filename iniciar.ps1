$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$repo = "yagodiax/gerador-codigo-barras"
$api = "https://api.github.com/repos/$repo/releases/latest"
$appDir = Join-Path $env:LOCALAPPDATA "GeradorCodigoBarras"
$exePath = Join-Path $appDir "Gerenciador de Etiquetas.exe"
$versionPath = Join-Path $appDir "versao.txt"
New-Item -ItemType Directory -Force -Path $appDir | Out-Null

try {
    Write-Host "Verificando atualizacoes..."
    $release = Invoke-RestMethod -Uri $api -Headers @{ "User-Agent" = "GeradorCodigoBarras" } -TimeoutSec 20
    $asset = $release.assets | Where-Object { $_.name -eq "Gerenciador-de-Etiquetas.exe" } | Select-Object -First 1
    if (-not $asset) { throw "O executavel ainda nao foi publicado no GitHub Releases." }

    $remoteVersion = [string]$release.tag_name
    $localVersion = ""
    if (Test-Path $versionPath) { $localVersion = (Get-Content $versionPath -Raw).Trim() }

    if (-not (Test-Path $exePath) -or $localVersion -ne $remoteVersion) {
        Write-Host "Baixando versao $remoteVersion..."
        $tempExe = "$exePath.download"
        Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $tempExe -TimeoutSec 180
        if ((Get-Item $tempExe).Length -lt 1000000) {
            Remove-Item $tempExe -Force -ErrorAction SilentlyContinue
            throw "Download incompleto: o executavel recebido parece invalido."
        }
        Move-Item $tempExe $exePath -Force
        Set-Content -Path $versionPath -Value $remoteVersion -Encoding ASCII
        Write-Host "Atualizacao concluida."
    } else {
        Write-Host "O programa ja esta atualizado."
    }
}
catch {
    if (-not (Test-Path $exePath)) {
        Write-Host "Nao foi possivel baixar o programa: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
    Write-Host "Sem acesso ao GitHub. Iniciando a ultima versao instalada." -ForegroundColor Yellow
}

Start-Process -FilePath $exePath
