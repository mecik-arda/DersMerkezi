# DersMerkezi

Windows masaüstünde çalışan, Python + Rich tabanlı çok dersli içerik çekme aracı. GitHub depolarına eklenen haftalık ders içeriklerini (ör. `Hafta N.pdf`) indirir, Git blob SHA-1 ile doğrular, pypdf ile Markdown bağlamına dönüştürür ve ders bazında haftalık Windows Görev Zamanlayıcı otomasyonu kurar.

Private depo: <https://github.com/mecik-arda/DersMerkezi>

## Dökümanlar

* `belgeler/kurulum.md`: Kurulum, ilk kullanım, sorun giderme.
* `belgeler/mimari.md`: Modül haritası, veri akışı, şemalar, güvenlik değişmezleri.
* `belgeler/plan/2026-09-21-dersmerkezi-cli.md`: Keşif/plan belgesi ve doğrulama kanıtları.
* `belgeler/plan/2026-09-21-cli-gelistirme-onerileri.md`: CLI geliştirme önerileri (öncelikli; 0.1.2 ve 0.1.3 dilimleri uygulandı, Sol denetimli).
* `belgeler/gecmis/`: Taşıma kanıtları ve Sol bağımsız denetim raporu.
* `AGENTS.md`: Ajan/geliştirme kuralları ve bağlayıcı bağlam; `CHANGELOG.md`: sürüm kaydı.

## Kurulum

* Python 3.13 (Anaconda) ve şu paketler gerekir: `rich`, `requests`, `pypdf` (bu makinede kurulu).
* Klonlama: `git clone https://github.com/mecik-arda/DersMerkezi.git`
* Çalıştırma: `baslat.cmd` dosyasına çift tıklayın veya masaüstündeki `DersMerkezi.bat` kısayolunu kullanın.
* Masaüstü başlatıcı: `C:\Users\ardam\Desktop\DersMerkezi.bat`
* Sürüm kontrolü dışında tutulanlar: `dersler/` (indirilen içerik), `gunluk.log`, `ayarlar.json` ve geçici/yedek dosyalar (`.gitignore`).

## Kullanım (TUI)

* **Dersleri Çek:** İşaretli derslerin içeriklerini canlı yüzde çubuğuyla indirir ve bağlam üretir; menüden "Önizleme (kuru çalışma)" ve zorla yenileme seçilebilir. Kilit doluyken "Bekle/Atla" sorulur.
* **Dersler:** Ders ekleme (ad, `owner/repo`, dal, desen), çıkarma, listeleme.
* **Ayarlar:** Hangi derslerin çekileceğinin işaretlenmesi.
* **Otomasyon Ayarla:** Ders bazında haftalık gün(ler) + saat seçimi; "Tümü"/"Hafta içi" kısayolları, görev kurma, "Kur ve hemen dene" ve kaldırma.
* **Durum / Sağlık:** Görev durumu, son çalışma/sonuç, eylem ve durum dosyası özeti; ağsız veya ağlı sağlık kontrolü.

## Komut Satırı (headless)

* Ders ekleme: `python dersmerkezi.py --ekle --ad "Dosya Organizasyonu" --depo emirozturk/Dosya-Organizasyonu-2026`
* Listeleme: `python dersmerkezi.py --listele` / JSON: `python dersmerkezi.py --listele --json`
* Ders silme: `python dersmerkezi.py --sil --ders dosya-organizasyonu --onayla` (onaysız çağrı exit 2; varsa görevi de kaldırır)
* Çekme: `python dersmerkezi.py --cek --ders dosya-organizasyonu --sessiz`
* Kuru çekme (önizleme): `python dersmerkezi.py --cek --ders dosya-organizasyonu --kuru`
* Zorla yenileme: `python dersmerkezi.py --cek --zorla --sessiz` (yalnız bağlam: `--zorla-md`)
* Boyut sınırı: `python dersmerkezi.py --cek --sinir 100 --kuru`
* Kilit bekleme: `python dersmerkezi.py --cek --kilit-bekle 60`
* Otomasyon kurma: `python dersmerkezi.py --otomasyon-kur --ders dosya-organizasyonu --gunler PZT --saat 09:00`
* Gün kısayolları: `--her-gun` veya `--hafta-ici` (`--gunler` ile birlikte kullanılamaz)
* Kur ve hemen dene: `python dersmerkezi.py --otomasyon-kur --ders dosya-organizasyonu --tetikle`
* Otomasyon kaldırma: `python dersmerkezi.py --otomasyon-kaldir --ders dosya-organizasyonu`
* Durum: `python dersmerkezi.py --durum` (ayrıntılı: `--durum --ayrintili`)
* Ayar görünümü: `python dersmerkezi.py --ayarlar` (tek ders: `--ayarlar --ders <kimlik>`, JSON: `--json`)
* Seçim değiştirme: `python dersmerkezi.py --ayarlar --ders <kimlik> --secili evet|hayir`
* Sağlık kontrolü: `python dersmerkezi.py --saglik` (ders için ağ: `--saglik --ders <kimlik>`; tümü: `--saglik --ag`)
* JSON çıktı: `--durum`, `--listele`, `--cek`, `--saglik`, `--surum`, `--oto-tamamlama`, `--ayarlar` ile `--json`
* Sürüm: `python dersmerkezi.py --surum`
* PowerShell tamamlama: `python dersmerkezi.py --oto-tamamlama` (çıktı: `tamamlama/dersmerkezi-tamamlama.ps1`)
* Alternatif günlük: `python dersmerkezi.py --durum --log alt/gunluk.log`
* Taşıma (kuru çalışma): `python dersmerkezi.py --tasima --kuru`
* Taşıma (uygula, eski görevi kaldırmadan): `python dersmerkezi.py --tasima`
* Taşıma (eski görevi de kaldır): `python dersmerkezi.py --tasima --onayla`
* Çıkış kodları: 0 başarı, 1 hata, 2 kullanım hatası. Geçersiz bayrak kombinasyonları hiçbir yan etki oluşturmadan exit 2 verir.

## Dizin Yapısı

* `dersmerkezi.py`: Giriş noktası (CLI argümanları ve TUI başlatma).
* `merkez/komut.py`: Argüman ayrıştırıcı, mod/bayrak matrisi doğrulaması, JSON çıktı sözleşmesi ve Türkçe ayrıştırma hataları.
* `merkez/ayarlar.py`: `ayarlar.json` şeması, doğrulama, atomik yazım, migration.
* `merkez/indirici.py`: GitHub Contents API listeleme (kota meta verisi), akışlı indirme, blob SHA doğrulama, Markdown dönüşümü, kuru çalışma.
* `merkez/durum.py`: Ders/görev durum kayıtları ve ayrıntılı durum verisi (CLI + TUI ortak).
* `merkez/saglik.py`: Ağsız varsayılan sağlık denetimi, isteğe bağlı depo/kota kontrolü.
* `merkez/tamamlama.py`: PowerShell tamamlama betiği üretimi.
* `merkez/zamanlayici.py`: PowerShell köprüsü ile görev kurma, kaldırma, sorgulama, tetikleme ve sahiplik denetimli silme.
* `merkez/tasima.py`: Eski otomasyonun güvenli sırayla taşınması (kanıt kayıtları, manifest doğrulaması).
* `merkez/ps/`: Sabit PowerShell betikleri (`gorev_kur.ps1`, `gorev_kaldir.ps1`, `gorev_sorgu.ps1`, `gorev_tetikle.ps1`, `gorev_sil.ps1`, `gorev_yukle.ps1`).
* `merkez/arayuz.py`: Rich + msvcrt tabanlı menüler ve canlı ilerleme ekranı.
* `merkez/gunluk.py`: `gunluk.log` (UTF-8, 1 MB rotasyon), alternatif günlük yolu ve `Local\DersMerkezi` kilidi.
* `tamamlama/`: Üretilen PowerShell tamamlama betiği (`.gitignore` dışındadır).
* `belgeler/plan/`: Keşif ve plan belgesi.
* `belgeler/referans/eski-otomasyon/`: Taşınacak eski PowerShell otomasyon kopyaları.
* `belgeler/gecmis/`: Taşıma kanıtları (görev XML'i, manifestler, doğrulama çıktısı).
* `AGENTS.md`: Ajan kuralları ve proje bağlamı (opencode/Codex otomatik okur); `CLAUDE.md` işaretçi; `CHANGELOG.md` sürüm kaydı.

## Çalışma Kuralları

* Durum dosyası: `dersler/<slug>/indirilenler.json` (şema sürümü 2; eski sürüm 1 kayıtları taşınır; `md_sha`/`md_boyut` alanları Markdown bütünlüğünü taşır).
* Depo adresi `owner/repo` ya da `https://github.com/owner/repo[.git]` biçiminde verilir; yalnızca GitHub HTTPS adresleri kabul edilir.
* İndirme: `raw.githubusercontent.com` üzerinden; dosya başına 200 MB sınırı (liste meta verisinde aşılırsa indirilmeden reddedilir); `.part` geçici dosyası SHA doğrulanmadan nihai ada taşınmaz.
* Bütünlük: Git blob SHA-1 (`blob <boyut>\0<veri>`) karşılaştırması; ikinci koşuda yerel dosya yeniden doğrulanır; Markdown bağlamı `md_sha`/`md_boyut` ile doğrulanır, eksik veya bozuksa yeniden üretilir.
* Eşzamanlılık: Aynı anda ikinci bir çalışma kilit nedeniyle atlanır; ayar, durum ve günlük yazımları `Local\DersMerkezi` kilidi altındadır.
* Görevler: `DersMerkezi_<slug>` adıyla kurulur; `StartWhenAvailable`, `MultipleInstances IgnoreNew`, 30 dakika zaman aşımı, pilde de çalışır; zamanlanmış koşularda `pythonw.exe` kullanılır.
* Ders silme: `--sil` (ve TUI ders çıkarma) varsa `DersMerkezi_<slug>` görevini önce kaldırır; görev kaldırılamazsa ders kaydı silinmez.
* Günlükler: `gunluk.log`; hata ve özet satırları kategori sayaçlarıyla yazılır.

## Mevcut Otomasyonun Taşınması

`--tasima` komutu plan belgesindeki güvenli sırayı uygular: eski görev XML'i ve manifest kanıtlarını kaydeder, içeriği kopyalar ve manifest ile doğrular, ders kaydını ekler, yeniden indirme olmadığını kanıtlar, yeni görevi kurup doğrular. Eski görev yalnızca `--onayla` verildiğinde kaldırılır; herhangi bir adımda hata olursa yeni görev ve yeni ders kaydı geri alınır, mevcut kaydın otomasyon ayarı eski değerine döner ve eski görev çalışır kalır. `--tasima --kuru` yalnızca `belgeler/gecmis/tasima-dogrulama-kuru.txt` yazar; gerçek taşıma kanıtını değiştirmez.

Bu makinede taşıma 2026-09-21 tarihinde çalıştırıldı: eski `DosyaOrganizasyonu_HaftalikCek` görevi kaldırıldı, içerik `dersler/dosya-organizasyonu/` altına alındı, yeni `DersMerkezi_dosya-organizasyonu` görevi kuruldu ve kanıtlar `belgeler/gecmis/` altında saklandı.

## Notlar

* Python bulunamazsa `baslat.cmd` uyarı verir.
* Ağ hatalarında (404/403/429/5xx) anlaşılır hata mesajı ve sıfır olmayan çıkış kodu üretilir.
* Kamuya açık depolarda `GITHUB_TOKEN` gerekmez; tanımlanırsa API limiti yükselir.
* Görev tetiklemesi test kapsamında doğrulandı (elle koşu, tek seferlik ve haftalık tetikleyici; `LastTaskResult=0`); üretim görevinin takvimli koşusu `gunluk.log` ile teyit edilir.
* TUI iş mantığı scriptli tuş girdisiyle test edilir; gerçek konsol görünümü kullanıcı tarafındadır.
