[CmdletBinding()]
param(
    [string]$Saat = '09:00',
    [string]$GorevAdi = 'DosyaOrganizasyonu_HaftalikCek'
)

$ErrorActionPreference = 'Stop'
$AnaBetik = Join-Path $PSScriptRoot 'haftalik_cek.ps1'
if (-not (Test-Path -LiteralPath $AnaBetik)) { throw "Ana betik bulunamadı: $AnaBetik" }

$mevcut = Get-ScheduledTask -TaskName $GorevAdi -ErrorAction SilentlyContinue
if ($mevcut) {
    $bizim = $false
    foreach ($eylem in $mevcut.Actions) {
        if ($eylem.Arguments -and $eylem.Arguments.Contains($AnaBetik)) { $bizim = $true }
    }
    if (-not $bizim) {
        Write-Host "HATA: '$GorevAdi' adlı görev bu kuruluma ait değil; güvenlik gereği değiştirilmedi."
        exit 1
    }
    Write-Host "Mevcut görev bu kuruluma ait; güncellenecek."
}

Write-Host 'İlk senkron çalıştırılıyor...'
$ilk = Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', $AnaBetik) -Wait -PassThru -NoNewWindow
if ($ilk.ExitCode -ne 0) {
    Write-Host "HATA: İlk senkron başarısız (çıkış kodu: $($ilk.ExitCode)). Görev oluşturulmadı."
    exit 1
}

try {
    $eylem = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$AnaBetik`""
    $tetik = New-ScheduledTaskTrigger -Daily -At $Saat
    $ayar = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 30)
    Register-ScheduledTask -TaskName $GorevAdi -Action $eylem -Trigger $tetik -Settings $ayar -Description 'Dosya Organizasyonu haftalık içerik çekme' -Force | Out-Null
    $yontem = 'Register-ScheduledTask'
} catch {
    Write-Host "Register-ScheduledTask başarısız ($($_.Exception.Message)); schtasks ile deneniyor..."
    $komut = "powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$AnaBetik`""
    & schtasks /Create /TN $GorevAdi /TR $komut /SC DAILY /ST $Saat /F | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "HATA: Görev oluşturulamadı (schtasks kodu: $LASTEXITCODE)."
        exit 1
    }
    $yontem = 'schtasks'
}

Write-Host "Görev oluşturuldu: $GorevAdi (her gün $Saat, yöntem: $yontem)"
exit 0
