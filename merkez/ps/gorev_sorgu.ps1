[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$GorevAdi
)
$ErrorActionPreference = 'Stop'
function Cikti($veri) { $veri | ConvertTo-Json -Compress -Depth 5 }
try {
    if ($GorevAdi -notmatch '^DersMerkezi_[a-z0-9]+(?:-[a-z0-9]+)*$') { throw 'Gorev adi gecersiz' }
    $bulunan = @(Get-CimInstance -Namespace 'root/Microsoft/Windows/TaskScheduler' -ClassName MSFT_ScheduledTask -ErrorAction Stop | Where-Object { $_.TaskName -eq $GorevAdi })
    if ($bulunan.Count -eq 0) {
        Cikti @{ ok = $true; var = $false; gorev = $GorevAdi; eylemSayisi = 0 }
        exit 0
    }
    $gorev = Get-ScheduledTask -TaskName $GorevAdi -ErrorAction Stop
    $bilgi = Get-ScheduledTaskInfo -TaskName $GorevAdi
    $tetik = $gorev.Triggers | Select-Object -First 1
    $eylem = $gorev.Actions | Select-Object -First 1
    Cikti @{
        ok          = $true
        var         = $true
        gorev       = $GorevAdi
        durum       = [string]$gorev.State
        gunler      = @($tetik.DaysOfWeek)
        baslangic   = [string]$tetik.StartBoundary
        sonCalisma  = [string]$bilgi.LastRunTime
        sonSonuc    = $bilgi.LastTaskResult
        execute     = [string]$eylem.Execute
        eylem       = [string]$eylem.Arguments
        eylemSayisi = @($gorev.Actions).Count
    }
} catch {
    Cikti @{ ok = $false; hata = $_.Exception.Message }
    exit 1
}
