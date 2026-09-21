[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$GorevAdi,
    [Parameter(Mandatory = $true)][string]$XmlYolu,
    [Parameter(Mandatory = $true)][string]$BeklenenExecute,
    [Parameter(Mandatory = $true)][string]$BeklenenArguman
)
$ErrorActionPreference = 'Stop'
function Cikti($veri) { $veri | ConvertTo-Json -Compress -Depth 5 }
try {
    if ($GorevAdi -notmatch '^DersMerkezi_[a-z0-9]+(?:-[a-z0-9]+)*$') { throw 'Gorev adi gecersiz' }
    if (-not $BeklenenExecute -or -not $BeklenenArguman) { throw 'Sahiplik parametreleri bos olamaz' }
    if (-not (Test-Path -LiteralPath $XmlYolu)) { throw "Yedek XML bulunamadi: $XmlYolu" }
    $xmlMetin = Get-Content -LiteralPath $XmlYolu -Raw -Encoding UTF8
    $xml = New-Object System.Xml.XmlDocument
    $xml.LoadXml($xmlMetin)
    $ns = New-Object System.Xml.XmlNamespaceManager($xml.NameTable)
    $ns.AddNamespace('t', 'http://schemas.microsoft.com/windows/2004/02/mit/task')
    $eylemDugumleri = @($xml.SelectNodes('//t:Actions/*', $ns))
    if ($eylemDugumleri.Count -ne 1) { throw 'Yedek XML tek eylem icermeli' }
    if ($eylemDugumleri[0].LocalName -ne 'Exec') { throw 'Yedek XML yalnizca Exec eylemi icermeli' }
    $komut = [string]$eylemDugumleri[0].Command
    $arguman = [string]$eylemDugumleri[0].Arguments
    $uygun = ($komut.Trim().ToLowerInvariant() -eq $BeklenenExecute.Trim().ToLowerInvariant()) -and ($arguman.Trim() -eq $BeklenenArguman)
    if (-not $uygun) { throw 'Yedek XML bu kuruluma ait degil; geri yukleme iptal edildi' }
    Register-ScheduledTask -Xml $xmlMetin -TaskName $GorevAdi -Force | Out-Null
    $kayit = Get-ScheduledTask -TaskName $GorevAdi -ErrorAction Stop
    $kayitEylemler = @($kayit.Actions)
    if ($kayitEylemler.Count -ne 1) {
        Unregister-ScheduledTask -TaskName $GorevAdi -Confirm:$false
        throw 'Geri yuklenen gorev tek eylem icermiyor; geri yukleme iptal edildi'
    }
    $kayitEylem = $kayitEylemler[0]
    $dogrulandi = $false
    if ($kayitEylem -and $kayitEylem.Execute -and $kayitEylem.Arguments) {
        $dogrulandi = ($kayitEylem.Execute.Trim().ToLowerInvariant() -eq $BeklenenExecute.Trim().ToLowerInvariant()) -and ($kayitEylem.Arguments.Trim() -eq $BeklenenArguman)
    }
    if (-not $dogrulandi) {
        Unregister-ScheduledTask -TaskName $GorevAdi -Confirm:$false
        throw 'Yedek XML bu kuruluma ait degil; geri yukleme iptal edildi'
    }
    Cikti @{ ok = $true; gorev = $GorevAdi; durum = [string]$kayit.State }
} catch {
    Cikti @{ ok = $false; hata = $_.Exception.Message }
    exit 1
}
