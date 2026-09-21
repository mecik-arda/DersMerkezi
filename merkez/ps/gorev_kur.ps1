[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$GorevAdi,
    [Parameter(Mandatory = $true)][string]$PythonYolu,
    [Parameter(Mandatory = $true)][string]$BetikYolu,
    [Parameter(Mandatory = $true)][string]$Ders,
    [Parameter(Mandatory = $true)][string]$Gunler,
    [Parameter(Mandatory = $true)][string]$Saat,
    [string]$YedekYolu = ''
)
$ErrorActionPreference = 'Stop'
function Cikti($veri) { $veri | ConvertTo-Json -Compress -Depth 5 }
try {
    if ($GorevAdi -notmatch '^DersMerkezi_[a-z0-9]+(?:-[a-z0-9]+)*$') { throw 'Gorev adi gecersiz' }
    if ($Ders -notmatch '^[a-z0-9]+(?:-[a-z0-9]+)*$') { throw 'Ders kimligi gecersiz' }
    if ($Ders.Length -lt 2 -or $Ders.Length -gt 40) { throw 'Ders kimligi uzunlugu gecersiz' }
    if ($Saat -notmatch '^([01]\d|2[0-3]):[0-5]\d$') { throw 'Saat bicimi gecersiz' }
    if (-not (Test-Path -LiteralPath $PythonYolu)) { throw "Python yolu bulunamadi: $PythonYolu" }
    if (-not (Test-Path -LiteralPath $BetikYolu)) { throw "Betik yolu bulunamadi: $BetikYolu" }
    $gecerli = @('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')
    $gunlerDizi = @($Gunler.Split(',') | ForEach-Object { $_.Trim() } | Where-Object { $_ })
    if ($gunlerDizi.Count -eq 0) { throw 'En az bir gun gerekli' }
    foreach ($gun in $gunlerDizi) { if ($gecerli -notcontains $gun) { throw "Gecersiz gun: $gun" } }
    $arguman = '"{0}" --otomatik --ders {1} --sessiz' -f $BetikYolu, $Ders
    $bulunan = @(Get-CimInstance -Namespace 'root/Microsoft/Windows/TaskScheduler' -ClassName MSFT_ScheduledTask -ErrorAction Stop | Where-Object { $_.TaskName -eq $GorevAdi })
    if ($bulunan.Count -gt 0) {
        $mevcut = Get-ScheduledTask -TaskName $GorevAdi -ErrorAction Stop
        $mevcutEylemler = @($mevcut.Actions)
        $bizim = $false
        if ($mevcutEylemler.Count -eq 1) {
            $mevcutEylem = $mevcutEylemler[0]
            if ($mevcutEylem -and $mevcutEylem.Execute -and $mevcutEylem.Arguments) {
                $bizim = ($mevcutEylem.Execute.Trim().ToLowerInvariant() -eq $PythonYolu.Trim().ToLowerInvariant()) -and ($mevcutEylem.Arguments.Trim() -eq $arguman)
            }
        }
        if (-not $bizim) { throw "Ayni adli gorev bu kuruluma ait degil: $GorevAdi" }
        if ($YedekYolu) {
            $yedekKlasor = Split-Path -Parent $YedekYolu
            if ($yedekKlasor -and -not (Test-Path -LiteralPath $yedekKlasor)) {
                New-Item -ItemType Directory -Path $yedekKlasor -Force | Out-Null
            }
            Export-ScheduledTask -TaskName $GorevAdi | Set-Content -LiteralPath $YedekYolu -Encoding UTF8
        }
    }
    $eylem = New-ScheduledTaskAction -Execute $PythonYolu -Argument $arguman
    $gunEnum = @($gunlerDizi | ForEach-Object { [System.DayOfWeek]::$_ })
    $tetik = New-ScheduledTaskTrigger -Weekly -At $Saat -DaysOfWeek $gunEnum
    $ayar = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 30) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
    Register-ScheduledTask -TaskName $GorevAdi -Action $eylem -Trigger $tetik -Settings $ayar -Description "DersMerkezi otomatik cekme: $Ders" -Force | Out-Null
    $kayit = Get-ScheduledTask -TaskName $GorevAdi
    Cikti @{ ok = $true; gorev = $GorevAdi; gunler = @($gunlerDizi); saat = $Saat; durum = [string]$kayit.State }
} catch {
    Cikti @{ ok = $false; hata = $_.Exception.Message }
    exit 1
}
