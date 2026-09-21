[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$GorevAdi
)
$ErrorActionPreference = 'Stop'
function Cikti($veri) { $veri | ConvertTo-Json -Compress -Depth 5 }
try {
    if ($GorevAdi -notmatch '^[A-Za-z0-9_-]{1,120}$') { throw 'Gorev adi gecersiz' }
    $mevcut = Get-ScheduledTask -TaskName $GorevAdi -ErrorAction SilentlyContinue
    if (-not $mevcut) {
        Cikti @{ ok = $true; gorev = $GorevAdi; silindi = $false; mesaj = 'Gorev bulunamadi' }
        exit 0
    }
    Unregister-ScheduledTask -TaskName $GorevAdi -Confirm:$false
    Cikti @{ ok = $true; gorev = $GorevAdi; silindi = $true }
} catch {
    Cikti @{ ok = $false; hata = $_.Exception.Message }
    exit 1
}
