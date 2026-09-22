[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$GorevAdi,
    [Parameter(Mandatory = $true)][string]$BeklenenExecute,
    [Parameter(Mandatory = $true)][string]$BeklenenArguman,
    [int]$ZamanAsimi = 60
)
$ErrorActionPreference = 'Stop'
function Cikti($veri) { $veri | ConvertTo-Json -Compress -Depth 5 }
try {
    if ($GorevAdi -notmatch '^DersMerkezi_[a-z0-9]+(?:-[a-z0-9]+)*$') { throw 'Gorev adi gecersiz' }
    if ($ZamanAsimi -lt 1 -or $ZamanAsimi -gt 600) { throw 'Zaman asimi gecersiz' }
    $bulunan = @(Get-CimInstance -Namespace 'root/Microsoft/Windows/TaskScheduler' -ClassName MSFT_ScheduledTask -ErrorAction Stop | Where-Object { $_.TaskName -eq $GorevAdi })
    if ($bulunan.Count -eq 0) { throw "Gorev bulunamadi: $GorevAdi" }
    $gorev = Get-ScheduledTask -TaskName $GorevAdi -ErrorAction Stop
    $eylemler = @($gorev.Actions)
    if ($eylemler.Count -ne 1) { throw 'Gorev tek eylemli degil' }
    $eylem = $eylemler[0]
    if (-not $eylem -or -not $eylem.Execute -or -not $eylem.Arguments) { throw 'Gorev eylemi okunamadi' }
    $bizim = ($eylem.Execute.Trim().ToLowerInvariant() -eq $BeklenenExecute.Trim().ToLowerInvariant()) -and ($eylem.Arguments.Trim() -eq $BeklenenArguman)
    if (-not $bizim) { throw "Gorev bu kuruluma ait degil: $GorevAdi" }
    $referans = [datetime](Get-ScheduledTaskInfo -TaskName $GorevAdi).LastRunTime
    Start-ScheduledTask -TaskName $GorevAdi -ErrorAction Stop
    $bekle = 0
    while ($bekle -lt $ZamanAsimi) {
        Start-Sleep -Seconds 1
        $bekle++
        $durum = [string](Get-ScheduledTask -TaskName $GorevAdi).State
        $yeni = [datetime](Get-ScheduledTaskInfo -TaskName $GorevAdi).LastRunTime
        if ($durum -notin @('Running', 'Queued') -and $yeni -gt $referans) { break }
    }
    $son = Get-ScheduledTaskInfo -TaskName $GorevAdi
    $sonDurum = [string](Get-ScheduledTask -TaskName $GorevAdi).State
    $sonCalisma = [datetime]$son.LastRunTime
    $tamam = ($sonDurum -notin @('Running', 'Queued')) -and ($sonCalisma -gt $referans)
    if (-not $tamam) {
        $ayar = (Get-ScheduledTask -TaskName $GorevAdi).Settings
        $logon = ''
        try { $logon = [string](Get-ScheduledTask -TaskName $GorevAdi).Principal.LogonType } catch { }
        $pilDurumu = ''
        try {
            $pil = Get-CimInstance -ClassName Win32_Battery -ErrorAction Stop | Select-Object -First 1
            if ($pil) { $pilDurumu = [string]$pil.PowerOnline }
        } catch { }
        Cikti @{
            ok         = $true
            gorev      = $GorevAdi
            zamanAsimi = $true
            durum      = $sonDurum
            sonCalisma = [string]$sonCalisma
            sonSonuc   = $son.LastTaskResult
            kosullar   = @{
                pilEngelli = [bool]$ayar.DisallowStartIfOnBatteries
                yalnizBosta = [bool]$ayar.RunOnlyIfIdle
                yalnizAg    = [bool]$ayar.RunOnlyIfNetworkAvailable
                logonTuru   = $logon
                pilDurumu   = $pilDurumu
            }
        }
        exit 0
    }
    Cikti @{
        ok         = $true
        gorev      = $GorevAdi
        zamanAsimi = $false
        durum      = $sonDurum
        sonCalisma = [string]$sonCalisma
        sonSonuc   = $son.LastTaskResult
    }
} catch {
    Cikti @{ ok = $false; hata = $_.Exception.Message }
    exit 1
}
