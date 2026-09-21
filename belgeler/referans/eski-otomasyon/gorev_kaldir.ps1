[CmdletBinding()]
param(
    [string]$GorevAdi = 'DosyaOrganizasyonu_HaftalikCek'
)

$ErrorActionPreference = 'Stop'
$mevcut = Get-ScheduledTask -TaskName $GorevAdi -ErrorAction SilentlyContinue
if (-not $mevcut) {
    Write-Host "Görev bulunamadı: $GorevAdi"
    exit 0
}

try {
    Unregister-ScheduledTask -TaskName $GorevAdi -Confirm:$false
} catch {
    Write-Host "HATA: Görev kaldırılamadı: $($_.Exception.Message)"
    exit 1
}

Write-Host "Görev kaldırıldı: $GorevAdi"
exit 0
