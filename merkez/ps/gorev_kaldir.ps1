[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$GorevAdi,
    [Parameter(Mandatory = $true)][string]$BeklenenExecute,
    [Parameter(Mandatory = $true)][string]$BeklenenArguman
)
$ErrorActionPreference = 'Stop'
function Cikti($veri) { $veri | ConvertTo-Json -Compress -Depth 5 }
try {
    if ($GorevAdi -notmatch '^DersMerkezi_[a-z0-9]+(?:-[a-z0-9]+)*$') { throw 'Gorev adi gecersiz' }
    if (-not $BeklenenExecute -or -not $BeklenenArguman) { throw 'Sahiplik parametreleri bos olamaz' }
    $bulunan = @(Get-CimInstance -Namespace 'root/Microsoft/Windows/TaskScheduler' -ClassName MSFT_ScheduledTask -ErrorAction Stop | Where-Object { $_.TaskName -eq $GorevAdi })
    if ($bulunan.Count -eq 0) {
        Cikti @{ ok = $true; gorev = $GorevAdi; silindi = $false; mesaj = 'Gorev bulunamadi' }
        exit 0
    }
    $mevcut = Get-ScheduledTask -TaskName $GorevAdi -ErrorAction Stop
    $eylemler = @($mevcut.Actions)
    if ($eylemler.Count -ne 1) { throw "Gorev tek eylem icermeli: $GorevAdi" }
    $eylem = $eylemler[0]
    $bizim = $false
    if ($eylem -and $eylem.Execute -and $eylem.Arguments) {
        $bizim = ($eylem.Execute.Trim().ToLowerInvariant() -eq $BeklenenExecute.Trim().ToLowerInvariant()) -and ($eylem.Arguments.Trim() -eq $BeklenenArguman)
    }
    if (-not $bizim) { throw "Ayni adli gorev bu kuruluma ait degil: $GorevAdi" }
    Unregister-ScheduledTask -TaskName $GorevAdi -Confirm:$false
    Cikti @{ ok = $true; gorev = $GorevAdi; silindi = $true }
} catch {
    Cikti @{ ok = $false; hata = $_.Exception.Message }
    exit 1
}
