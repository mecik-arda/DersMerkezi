[CmdletBinding()]
param(
    [string]$RepoOwner = 'emirozturk',
    [string]$RepoAdi = 'Dosya-Organizasyonu-2026',
    [string]$Dal = 'main',
    [string]$Desen = 'Hafta*.pdf',
    [string]$HedefKlasor,
    [string]$Token = $env:GITHUB_TOKEN,
    [string[]]$AdDogrula
)

$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$KokDizin = Split-Path -Parent $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($HedefKlasor)) { $HedefKlasor = Join-Path $KokDizin 'haftalik' }
$HedefKlasor = [IO.Path]::GetFullPath($HedefKlasor)
$DurumYolu = Join-Path $PSScriptRoot 'indirilenler.json'
$LogYolu = Join-Path $PSScriptRoot 'haftalik_cek.log'
$PythonBetik = Join-Path $PSScriptRoot 'pdf_to_md.py'
$MutexAdi = 'Local\DosyaOrganizasyonu_HaftalikCek'

function Write-Kayit {
    param([string]$Seviye, [string]$Mesaj)
    $satir = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] [$Seviye] $Mesaj"
    try {
        if ((Test-Path -LiteralPath $LogYolu) -and ((Get-Item -LiteralPath $LogYolu).Length -gt 1MB)) {
            if (Test-Path -LiteralPath "$LogYolu.old") { Remove-Item -LiteralPath "$LogYolu.old" -Force }
            Move-Item -LiteralPath $LogYolu -Destination "$LogYolu.old" -Force
        }
        [IO.File]::AppendAllText($LogYolu, $satir + [Environment]::NewLine, [Text.UTF8Encoding]::new($false))
    } catch { }
    Write-Host $satir
}

function Test-DosyaAdi {
    param([string]$Ad)
    if ([string]::IsNullOrWhiteSpace($Ad)) { return 'boş ad' }
    if ($Ad -ne [IO.Path]::GetFileName($Ad)) { return 'yol ayırıcı içeriyor' }
    if ($Ad -match '[<>:"/\\|?*]') { return 'geçersiz karakter içeriyor' }
    if ($Ad -match '[\x00-\x1f]') { return 'kontrol karakteri içeriyor' }
    if ($Ad.EndsWith('.') -or $Ad.EndsWith(' ')) { return 'sonda nokta veya boşluk var' }
    if ($Ad.Length -gt 180) { return 'ad çok uzun' }
    $taban = $Ad.Split('.')[0].ToUpperInvariant()
    if ($taban -match '^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])$') { return 'ayrılmış aygıt adı' }
    return $null
}

function Get-BlobSha {
    param([string]$Yol)
    $boyut = (Get-Item -LiteralPath $Yol).Length
    $sha = [Security.Cryptography.SHA1]::Create()
    $akis = $null
    try {
        $akis = [IO.File]::OpenRead($Yol)
        $bas = [Text.Encoding]::ASCII.GetBytes("blob $boyut`0")
        [void]$sha.TransformBlock($bas, 0, $bas.Length, $bas, 0)
        $tampon = New-Object byte[] 1048576
        while (($okunan = $akis.Read($tampon, 0, $tampon.Length)) -gt 0) {
            [void]$sha.TransformBlock($tampon, 0, $okunan, $tampon, 0)
        }
        [void]$sha.TransformFinalBlock([byte[]]@(), 0, 0)
        return [BitConverter]::ToString($sha.Hash).Replace('-', '').ToLowerInvariant()
    } finally {
        if ($akis) { $akis.Dispose() }
        $sha.Dispose()
    }
}

function Get-DepoListesi {
    $basliklar = @{
        'User-Agent' = 'Dosya-Organizasyonu-HaftalikCek'
        'Accept'     = 'application/vnd.github+json'
    }
    if (-not [string]::IsNullOrWhiteSpace($Token)) {
        $basliklar['Authorization'] = "Bearer $Token"
        Write-Kayit 'BILGI' 'Kimlik doğrulama: GITHUB_TOKEN kullanılıyor.'
    }
    $uri = "https://api.github.com/repos/$RepoOwner/$RepoAdi/contents/?ref=$([Uri]::EscapeDataString($Dal))&per_page=100"
    $tumu = @()
    $sayfa = 0
    while ($uri -and $sayfa -lt 10) {
        $sayfa++
        $yanit = Invoke-WebRequest -Uri $uri -Headers $basliklar -UseBasicParsing -ErrorAction Stop
        $tumu += @($yanit.Content | ConvertFrom-Json)
        $uri = $null
        $bag = $yanit.Headers['Link']
        if ($bag) {
            foreach ($parca in ($bag -split ',')) {
                if ($parca -match '<([^>]+)>\s*;\s*rel="next"') { $uri = $Matches[1] }
            }
        }
    }
    return $tumu
}

function Get-Durumlar {
    $sonuc = @{}
    if (-not (Test-Path -LiteralPath $DurumYolu)) { return $sonuc }
    try {
        $ham = [IO.File]::ReadAllText($DurumYolu, [Text.UTF8Encoding]::new($false))
        $veri = $ham | ConvertFrom-Json
        if ($veri -and $veri.dosyalar) {
            foreach ($ozellik in $veri.dosyalar.PSObject.Properties) {
                $sonuc[$ozellik.Name] = $ozellik.Value
            }
        }
    } catch {
        $yedek = "$DurumYolu.bozuk-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
        Move-Item -LiteralPath $DurumYolu -Destination $yedek -Force
        Write-Kayit 'UYARI' "Durum dosyası okunamadı; yedeklendi: $(Split-Path -Leaf $yedek)"
    }
    return $sonuc
}

function Save-Durum {
    param($Durumlar)
    $veri = [ordered]@{ surum = 1; guncelleme = (Get-Date).ToString('s'); dosyalar = $Durumlar }
    $gecici = "$DurumYolu.tmp"
    [IO.File]::WriteAllText($gecici, ($veri | ConvertTo-Json -Depth 6), [Text.UTF8Encoding]::new($false))
    Move-Item -LiteralPath $gecici -Destination $DurumYolu -Force
}

function Get-PythonKomutu {
    $adaylar = @(
        @{ Ad = 'py'; OnEk = @('-3') },
        @{ Ad = 'python'; OnEk = @() }
    )
    foreach ($aday in $adaylar) {
        if (-not (Get-Command $aday.Ad -ErrorAction SilentlyContinue)) { continue }
        $oncekiEap = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        try {
            & $aday.Ad @($aday.OnEk) '-c' 'import pypdf' *> $null
            $kod = $LASTEXITCODE
        } catch {
            $kod = 1
        } finally {
            $ErrorActionPreference = $oncekiEap
        }
        if ($kod -eq 0) { return $aday }
    }
    return $null
}

function Invoke-PdfDonusum {
    param([string]$PdfYolu, [string]$MdYolu, [string]$KaynakUrl, [string]$Sha)
    $python = Get-PythonKomutu
    if (-not $python) {
        Write-Kayit 'UYARI' 'pypdf destekli Python bulunamadı; Markdown dönüşümü atlandı.'
        return $false
    }
    $geciciMd = "$MdYolu.uretiliyor.tmp"
    if (Test-Path -LiteralPath $geciciMd) { Remove-Item -LiteralPath $geciciMd -Force }
    $oncekiEap = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $cikti = & $python.Ad @($python.OnEk) $PythonBetik $PdfYolu $geciciMd '--kaynak' $KaynakUrl '--sha' $Sha '--tarih' (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') 2>&1
        $kod = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $oncekiEap
    }
    foreach ($satir in @($cikti)) { Write-Kayit 'BILGI' "pypdf: $satir" }
    if ($kod -ne 0) {
        if (Test-Path -LiteralPath $geciciMd) { Remove-Item -LiteralPath $geciciMd -Force -ErrorAction SilentlyContinue }
        Write-Kayit 'UYARI' "Markdown dönüşümü başarısız (kod: $kod): $(Split-Path -Leaf $PdfYolu)"
        return $false
    }
    Move-Item -LiteralPath $geciciMd -Destination $MdYolu -Force
    Write-Kayit 'BILGI' "Bağlam üretildi: $(Split-Path -Leaf $MdYolu)"
    return $true
}

if ($AdDogrula) {
    foreach ($ad in $AdDogrula) {
        $sorun = Test-DosyaAdi $ad
        if ($sorun) { Write-Host "[RED] $ad -> $sorun" } else { Write-Host "[KABUL] $ad" }
    }
    exit 0
}

$mutex = New-Object Threading.Mutex($false, $MutexAdi)
$kilit = $false
try { $kilit = $mutex.WaitOne(0) } catch [Threading.AbandonedMutexException] { $kilit = $true }
if (-not $kilit) {
    Write-Kayit 'UYARI' 'Başka bir çalışma sürüyor; bu koşu atlandı.'
    exit 0
}

$hataVar = $false
$yeniSayi = 0
$guncelSayi = 0
$atlananSayi = 0
$mdSayi = 0

try {
    if (-not (Test-Path -LiteralPath $HedefKlasor)) { New-Item -ItemType Directory -Path $HedefKlasor -Force | Out-Null }
    Get-ChildItem -LiteralPath $HedefKlasor -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like '*.indiriliyor.tmp' -or $_.Name -like '*.uretiliyor.tmp' } |
        Remove-Item -Force -ErrorAction SilentlyContinue

    Write-Kayit 'BILGI' "Depo listeleniyor: $RepoOwner/$RepoAdi@$Dal"
    $liste = Get-DepoListesi
    $hedefler = @($liste | Where-Object { $_.type -eq 'file' -and $_.name -like $Desen } | Sort-Object -Property name)
    if ($hedefler.Count -eq 0) { Write-Kayit 'BILGI' "Desene uyan dosya yok: $Desen" }

    $durumlar = Get-Durumlar
    $gorulen = @{}

    foreach ($girdi in $hedefler) {
        $ad = [string]$girdi.name
        $anahtar = $ad.ToLowerInvariant()
        if ($gorulen.ContainsKey($anahtar)) {
            Write-Kayit 'HATA' "Büyük/küçük harf çakışması; atlandı: $ad"
            $hataVar = $true
            continue
        }
        $gorulen[$anahtar] = $true
        $adSorunu = Test-DosyaAdi $ad
        if ($adSorunu) {
            Write-Kayit 'HATA' "Dosya adı güvenlik nedeniyle reddedildi ($adSorunu): $ad"
            $hataVar = $true
            continue
        }
        try {
            $beklenenSha = [string]$girdi.sha
            $beklenenBoyut = [long]$girdi.size
            $yerel = Join-Path $HedefKlasor $ad
            $mdYolu = [IO.Path]::ChangeExtension($yerel, '.md')
            $kayit = $durumlar[$ad]
            $kaynakUrl = "https://raw.githubusercontent.com/$RepoOwner/$RepoAdi/$Dal/$([Uri]::EscapeDataString($ad))"

            $indirGerek = $true
            if ($kayit -and [string]$kayit.sha -eq $beklenenSha -and (Test-Path -LiteralPath $yerel)) {
                $yerelBoyut = (Get-Item -LiteralPath $yerel).Length
                if ($yerelBoyut -eq $beklenenBoyut) {
                    if ((Get-BlobSha $yerel) -eq $beklenenSha) { $indirGerek = $false }
                    else { Write-Kayit 'UYARI' "Yerel kopya bozuk; yeniden indirilecek: $ad" }
                } else {
                    Write-Kayit 'UYARI' "Yerel boyut uyuşmuyor; yeniden indirilecek: $ad"
                }
            }

            $indirildi = $false
            if ($indirGerek) {
                $gecici = "$yerel.indiriliyor.tmp"
                if (Test-Path -LiteralPath $gecici) { Remove-Item -LiteralPath $gecici -Force }
                Write-Kayit 'BILGI' "İndiriliyor: $ad"
                Invoke-WebRequest -Uri $kaynakUrl -OutFile $gecici -UseBasicParsing -ErrorAction Stop
                $geciciBoyut = (Get-Item -LiteralPath $gecici).Length
                $geciciSha = Get-BlobSha $gecici
                if ($geciciBoyut -ne $beklenenBoyut -or $geciciSha -ne $beklenenSha) {
                    Remove-Item -LiteralPath $gecici -Force -ErrorAction SilentlyContinue
                    throw "Doğrulama başarısız (boyut: $geciciBoyut, sha: $geciciSha)"
                }
                Move-Item -LiteralPath $gecici -Destination $yerel -Force
                $indirildi = $true
                if (-not $kayit) { $yeniSayi++ } else { $guncelSayi++ }
                Write-Kayit 'BILGI' "İndirildi ve doğrulandı: $ad ($beklenenBoyut bayt)"
            } else {
                $atlananSayi++
            }

            $mdHazir = $false
            if (-not $indirildi -and $kayit -and [bool]$kayit.md -and (Test-Path -LiteralPath $mdYolu)) {
                $mdHazir = $true
            }
            if (-not $mdHazir) {
                $mdHazir = Invoke-PdfDonusum -PdfYolu $yerel -MdYolu $mdYolu -KaynakUrl $kaynakUrl -Sha $beklenenSha
                if (-not $mdHazir) { $hataVar = $true }
            }
            if ($mdHazir) { $mdSayi++ }

            $indirilmeZamani = (Get-Date).ToString('s')
            if ($kayit -and $kayit.indirildi -and -not $indirildi) { $indirilmeZamani = [string]$kayit.indirildi }
            $durumlar[$ad] = [pscustomobject]@{
                sha       = $beklenenSha
                boyut     = $beklenenBoyut
                indirildi = $indirilmeZamani
                md        = $mdHazir
            }
            Save-Durum -Durumlar $durumlar
        } catch {
            Write-Kayit 'HATA' "İşlenemedi: $ad -> $($_.Exception.Message)"
            $hataVar = $true
        }
    }

    Write-Kayit 'BILGI' "Özet: yeni=$yeniSayi, güncellenen=$guncelSayi, atlanan=$atlananSayi, bağlam=$mdSayi, hedef=$HedefKlasor"
} catch {
    $durumKodu = ''
    if ($_.Exception.Response) { $durumKodu = " (HTTP: $([int]$_.Exception.Response.StatusCode))" }
    Write-Kayit 'HATA' "Beklenmeyen hata${durumKodu}: $($_.Exception.Message)"
    $hataVar = $true
} finally {
    if ($kilit) { [void]$mutex.ReleaseMutex() }
    $mutex.Dispose()
}

if ($hataVar) { exit 1 }
exit 0
